#!/usr/bin/env node
import fs from 'fs';
import path from 'path';
import { entryFromMcp } from './slim-job.mjs';

const dir = path.dirname(new URL(import.meta.url).pathname);
const input = process.argv[2];
if (!input) {
  console.error('Usage: node merge-mcp-into-jsonl.mjs <batch.json>');
  process.exit(1);
}
const items = JSON.parse(fs.readFileSync(input, 'utf8'));
const jsonlPath = path.join(dir, 'search-results.jsonl');
const byKw = new Map();
if (fs.existsSync(jsonlPath)) {
  for (const line of fs.readFileSync(jsonlPath, 'utf8').split('\n')) {
    if (!line.trim()) continue;
    const row = JSON.parse(line);
    if (row.keyword) byKw.set(row.keyword, row);
  }
}
for (const item of items) {
  const entry = item.mcp
    ? entryFromMcp(item.keyword, item.mcp)
    : item.jobs
      ? { keyword: item.keyword, jobs: item.jobs }
      : entryFromMcp(item.keyword, item);
  byKw.set(item.keyword, entry);
  const slug = item.keyword.replace(/ /g, '__');
  const mcpDir = path.join(dir, 'raw_batches', 'mcp');
  fs.mkdirSync(mcpDir, { recursive: true });
  const mcpBody = item.mcp || { status: 'ok', jobs: item.jobs || entry.jobs || [] };
  fs.writeFileSync(path.join(mcpDir, `${slug}.json`), JSON.stringify(mcpBody));
}
fs.writeFileSync(jsonlPath, [...byKw.values()].map((r) => JSON.stringify(r)).join('\n') + '\n');
console.log(JSON.stringify({ keywords: byKw.size }));
