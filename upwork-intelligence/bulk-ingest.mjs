#!/usr/bin/env node
import fs from 'fs';
import path from 'path';
import { entryFromMcp } from './slim-job.mjs';

const dir = path.dirname(new URL(import.meta.url).pathname);
const input = process.argv[2];
if (!input) {
  console.error('Usage: node bulk-ingest.mjs <entries.json>');
  process.exit(1);
}
const items = JSON.parse(fs.readFileSync(input, 'utf8'));
if (!Array.isArray(items)) {
  console.error('Expected JSON array of {keyword, jobs} or {keyword, mcp}');
  process.exit(1);
}
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
  let entry;
  if (item.mcp) entry = entryFromMcp(item.keyword, item.mcp);
  else if (item.jobs) entry = { keyword: item.keyword, jobs: item.jobs };
  else if (item.error) entry = { keyword: item.keyword, error: item.error, jobs: [] };
  else entry = entryFromMcp(item.keyword, item);
  byKw.set(item.keyword, entry);
}
fs.writeFileSync(jsonlPath, [...byKw.values()].map((r) => JSON.stringify(r)).join('\n') + '\n');
console.log(JSON.stringify({ total: byKw.size }));
