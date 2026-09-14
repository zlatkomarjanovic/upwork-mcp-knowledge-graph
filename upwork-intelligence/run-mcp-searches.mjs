#!/usr/bin/env node
/**
 * Sequential Upwork find_jobs via Cursor dynamic MCP bridge (stdin/stdout JSON-RPC).
 * Usage: node run-mcp-searches.mjs [startIndex] [count]
 */
import fs from 'fs';
import path from 'path';
import readline from 'readline';

const ORG = '1472686528932380673';
const dir = path.dirname(new URL(import.meta.url).pathname);
const keywords = JSON.parse(fs.readFileSync(path.join(dir, 'keywords.json'), 'utf8'));
const start = parseInt(process.argv[2] || '0', 10);
const count = parseInt(process.argv[3] || String(keywords.length), 10);
const slice = keywords.slice(start, start + count);

function post(msg) {
  process.stdout.write(JSON.stringify(msg) + '\n');
}

for (const keyword of slice) {
  post({
    type: 'mcp_request',
    namespace: 'Upwork',
    tool: 'upwork__find_jobs',
    arguments: {
      action: 'search',
      org_uid: ORG,
      params: { query: keyword, sort: 'recency', limit: 10 },
    },
    keyword,
  });
}
