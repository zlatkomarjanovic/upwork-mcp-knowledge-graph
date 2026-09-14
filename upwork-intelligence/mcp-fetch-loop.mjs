#!/usr/bin/env node
/**
 * Emit one MCP request per missing keyword (for agent to execute + persist-mcp-json).
 * Usage: node mcp-fetch-loop.mjs | while read line; do ... done
 */
import fs from 'fs';
import path from 'path';

const ORG = '1472686528932380673';
const dir = path.dirname(new URL(import.meta.url).pathname);
const keywords = JSON.parse(fs.readFileSync(path.join(dir, 'keywords.json'), 'utf8'));
const jsonlPath = path.join(dir, 'search-results.jsonl');
const have = new Set();
if (fs.existsSync(jsonlPath)) {
  for (const line of fs.readFileSync(jsonlPath, 'utf8').split('\n')) {
    if (!line.trim()) continue;
    have.add(JSON.parse(line).keyword);
  }
}
for (const keyword of keywords) {
  if (have.has(keyword)) continue;
  console.log(JSON.stringify({ keyword, org_uid: ORG, params: { query: keyword, sort: 'recency', limit: 10 } }));
}
