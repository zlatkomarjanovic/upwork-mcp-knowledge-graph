#!/usr/bin/env node
import fs from 'fs';
import path from 'path';
import { entryFromMcp } from './slim-job.mjs';

const keyword = process.argv[2];
if (!keyword) {
  console.error('Usage: node persist-mcp-json.mjs <keyword> < mcp.json');
  process.exit(1);
}
const dir = path.dirname(new URL(import.meta.url).pathname);
const mcp = JSON.parse(fs.readFileSync(0, 'utf8'));
const slug = keyword.replace(/ /g, '__');
const mcpDir = path.join(dir, 'raw_batches', 'mcp');
fs.mkdirSync(mcpDir, { recursive: true });
fs.writeFileSync(path.join(mcpDir, `${slug}.json`), JSON.stringify(mcp));

const jsonlPath = path.join(dir, 'search-results.jsonl');
const byKw = new Map();
if (fs.existsSync(jsonlPath)) {
  for (const line of fs.readFileSync(jsonlPath, 'utf8').split('\n')) {
    if (!line.trim()) continue;
    const row = JSON.parse(line);
    if (row.keyword) byKw.set(row.keyword, row);
  }
}
byKw.set(keyword, entryFromMcp(keyword, mcp));
fs.writeFileSync(jsonlPath, [...byKw.values()].map((r) => JSON.stringify(r)).join('\n') + '\n');
console.log(JSON.stringify({ keyword, jobs: byKw.get(keyword).jobs?.length ?? 0 }));
