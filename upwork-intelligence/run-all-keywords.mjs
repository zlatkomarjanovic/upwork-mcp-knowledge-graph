#!/usr/bin/env node
/**
 * Re-fetch every keyword via Upwork MCP (Cursor bridge on stdin/stdout).
 * Run from repo root: node upwork-intelligence/run-all-keywords.mjs
 * Expects CURSOR_MCP_BRIDGE=1 and JSON-RPC on stdin for responses (agent-driven).
 * Standalone: writes pending keywords and exits (for agent batching).
 */
import fs from 'fs';
import path from 'path';
import { entryFromMcp } from './slim-job.mjs';

const ORG = '1472686528932380673';
const dir = path.dirname(new URL(import.meta.url).pathname);
const keywords = JSON.parse(fs.readFileSync(path.join(dir, 'keywords.json'), 'utf8'));
const jsonlPath = path.join(dir, 'search-results.jsonl');
const byKw = new Map();

if (fs.existsSync(jsonlPath)) {
  for (const line of fs.readFileSync(jsonlPath, 'utf8').split('\n')) {
    if (!line.trim()) continue;
    const row = JSON.parse(line);
    if (row.keyword) byKw.set(row.keyword, row);
  }
}

const missing = keywords.filter((k) => !byKw.has(k));
console.error(JSON.stringify({ total: keywords.length, have: byKw.size, missing: missing.length }));
for (const kw of missing) {
  process.stdout.write(
    JSON.stringify({
      type: 'mcp_request',
      namespace: 'Upwork',
      tool: 'upwork__find_jobs',
      arguments: {
        action: 'search',
        org_uid: ORG,
        params: { query: kw, sort: 'recency', limit: 10 },
      },
      keyword: kw,
    }) + '\n'
  );
}
