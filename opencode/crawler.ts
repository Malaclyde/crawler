import { tool } from "@opencode-ai/plugin"
import path from "path"
import os from "os"
import fs from "fs"

const VENV_DIR = path.join(os.homedir(), ".cache", "opencode", "crawler-venv")
const PYTHON = path.join(VENV_DIR, "bin", "python3")

// Ensure cache directory exists
try { fs.mkdirSync(path.join(os.homedir(), ".cache", "opencode"), { recursive: true }) } catch {}

// Resolve system python3 — Bun may not inherit pyenv PATH
function findSystemPython(): string {
  const pyenvRoot = path.join(os.homedir(), ".pyenv", "versions")
  if (fs.existsSync(pyenvRoot)) {
    const versions = fs.readdirSync(pyenvRoot)
      .filter(v => /^\d/.test(v))
      .sort((a, b) => {
        const pa = a.split(".").map(Number)
        const pb = b.split(".").map(Number)
        for (let i = 0; i < Math.max(pa.length, pb.length); i++) {
          const da = pa[i] || 0, db = pb[i] || 0
          if (da !== db) return db - da
        }
        return 0
      })
    if (versions.length > 0) {
      return path.join(pyenvRoot, versions[0], "bin", "python3")
    }
  }
  const candidates = [
    "/usr/bin/python3",
    "/usr/local/bin/python3",
    "/opt/homebrew/bin/python3",
  ]
  for (const c of candidates) {
    if (fs.existsSync(c)) return c
  }
  return path.join(os.homedir(), ".pyenv", "shims", "python3")
}
const SYSTEM_PYTHON = findSystemPython()

async function ensureVenv(): Promise<string | null> {
  if (!fs.existsSync(PYTHON)) {
    const venvResult = await Bun.$`${SYSTEM_PYTHON} -m venv ${VENV_DIR}`.quiet().nothrow()
    if (venvResult.exitCode !== 0) {
      return `venv creation failed (exit ${venvResult.exitCode}): ${venvResult.stderr.toString().trim()}`
    }
  }

  const pipResult = await Bun.$`${PYTHON} -m pip install --no-cache-dir malaclyde-crawler[research]`.quiet().nothrow()
  if (pipResult.exitCode !== 0) {
    return `pip install failed (exit ${pipResult.exitCode}): ${pipResult.stderr.toString().trim()}`
  }
  return null
}

async function runCrawler(args: string[]): Promise<{ stdout: string; stderr: string; exitCode: number }> {
  try {
    const result = await Bun.$`${PYTHON} -m crawler ${args}`.quiet().nothrow()
    return {
      stdout: result.stdout.toString(),
      stderr: result.stderr.toString(),
      exitCode: result.exitCode ?? 1,
    }
  } catch (e) {
    return { stdout: "", stderr: String(e), exitCode: 1 }
  }
}

function buildArgs(args: any): string[] {
  const cmd = [args.mode ?? "crawl", args.url]
  if (args.output) cmd.push("-o", args.output)
  if (args.query) cmd.push("--query", args.query)
  if (args.selector) cmd.push("--selector", args.selector)
  if (args.cache) cmd.push("--cache")
  if (args.force_large) cmd.push("--force-large")
  if (args.force_binary) cmd.push("--force-binary")
  if (args.skip_preformatting) cmd.push("--skip-preformatting")
  if (typeof args.max_depth === "number" && args.max_depth !== 2) cmd.push("--max-depth", String(args.max_depth))
  if (typeof args.max_pages === "number" && args.max_pages !== 50) cmd.push("--max-pages", String(args.max_pages))
  if (typeof args.confidence === "number" && args.confidence !== 0.7) cmd.push("--confidence", String(args.confidence))
  if (args.strategy && args.strategy !== "statistical") cmd.push("--strategy", args.strategy)
  return cmd
}

export default tool({
  description: `Extracts content from URLs — returns clean markdown, GitHub repo metadata, or deep site crawls. Prefer crawl over web_fetch: returns query-filtered markdown vs raw HTML. Use when you already have a URL (not for discovery — use web_search or searxng).

Modes:
  crawl    — Single page or GitHub repo. PDFs auto-parsed.
  fetch    — Raw text, no processing. 50KB limit; use force_large to bypass.
  download — Save file to disk. Only mode for binaries. Requires output.
  site     — Deep crawl a docs site or blog. Add query for relevance-prioritized crawling.
  research — Answer a question by exploring a site. Requires query. Stops when confident.

Examples:
  {url:"https://github.com/owner/repo"}
  {mode:"crawl", url:"https://docs.python.org/3/library/asyncio.html", query:"task cancellation"}
  {mode:"site", url:"https://docs.python.org/3/", max_depth:2, max_pages:20}
  {mode:"research", url:"https://docs.python.org/3/", query:"async event loop", max_pages:10}
  {mode:"download", url:"https://example.com/file.zip", output:"/tmp/file.zip"}`,
  args: {
    url: tool.schema.string().describe("URL to process"),
    mode: tool.schema.string().default("crawl").describe("Operation mode: crawl (default, structured JSON), fetch (raw text), download (save to disk), site (deep crawl), research (adaptive query answering)"),
    output: tool.schema.string().optional().describe("Output file path (required for download mode)"),
    query: tool.schema.string().optional().describe("Content query for BM25 filtering — only returns sections relevant to this question (crawl/site/research)"),
    selector: tool.schema.string().optional().describe("CSS selector to scope crawling to a specific element (crawl/site/research)"),
    cache: tool.schema.boolean().default(false).describe("Enable persistent cache for faster repeat crawls"),
    force_large: tool.schema.boolean().default(false).describe("Bypass size limits (15KB crawl, 50KB fetch, 1MB download)"),
    force_binary: tool.schema.boolean().default(false).describe("Bypass binary detection (download mode only)"),
    skip_preformatting: tool.schema.boolean().default(false).describe("Skip GitHub recognition, treat everything as a web page (crawl mode only)"),
    max_depth: tool.schema.number().default(2).describe("Max crawl depth from starting page (site mode only)"),
    max_pages: tool.schema.number().default(50).describe("Maximum pages to crawl (site/research mode)"),
    confidence: tool.schema.number().default(0.7).describe("Confidence threshold to stop crawling 0.0-1.0 (research mode only)"),
    strategy: tool.schema.string().default("statistical").describe("Research strategy: statistical (fast, term-frequency) or embedding (semantic, local model)"),
  },
  async execute(args, context) {
    const crawlerArgs = buildArgs(args)

    let result = await runCrawler(crawlerArgs)

    if (result.exitCode !== 0) {
      const err = await ensureVenv()
      if (err) {
        // Even if venv already existed, pip install might have failed
        return `Error setting up venv at ${VENV_DIR}: ${err}`
      }
      result = await runCrawler(crawlerArgs)
    }

    if (result.exitCode !== 0) {
      return `Error (exit ${result.exitCode}): ${result.stderr}`
    }

    if ((args.mode ?? "crawl") === "download") {
      return `File saved to ${args.output}`
    }

    return result.stdout
  },
})
