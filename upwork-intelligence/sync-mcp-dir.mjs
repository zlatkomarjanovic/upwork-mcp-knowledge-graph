#!/usr/bin/env node
import fs from 'fs';
import path from 'path';
import { entryFromMcp } from './slim-job.mjs';

const dir = path.dirname(new URL(import.meta.url).pathname);
const mcpDir = path.join(dir, 'raw_batches', 'mcp');
const jsonlPath = path.join(dir, 'search-results.jsonl');
const byKw = new Map();

if (fs.existsSync(jsonlPath)) {
  for (const line of fs.readFileSync(jsonlPath, 'utf8').split('\n')) {
    if (!line.trim()) continue;
    const row = JSON.parse(line);
    if (row.keyword) byKw.set(row.keyword, row);
  }
}

if (!fs.existsSync(mcpDir)) {
  console.log(JSON.stringify({ updated: 0 }));
  process.exit(0);
}

for (const f of fs.readdirSync(mcpDir).filter((x) => x.endsWith('.json'))) {
  const keyword = f.replace(/\.json$/i, '').replace(/__/g, ' ');
  const mcp = JSON.parse(fs.readFileSync(path.join(mcpDir, f), 'utf8'));
  byKw.set(keyword, entryFromMcp(keyword, mcp));
}

fs.writeFileSync(jsonlPath, [...byKw.values()].map((r) => JSON.stringify(r)).join('\n') + '\n');
console.log(JSON.stringify({ keywords: byKw.size }));
