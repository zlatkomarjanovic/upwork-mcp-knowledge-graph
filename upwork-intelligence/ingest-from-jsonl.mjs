#!/usr/bin/env node
import fs from 'fs';
import path from 'path';
import { entryFromMcp } from './slim-job.mjs';

const dir = path.dirname(new URL(import.meta.url).pathname);
const input = process.argv[2];
if (!input) {
  console.error('Usage: node ingest-from-jsonl.mjs <lines.jsonl>');
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
for (const line of fs.readFileSync(input, 'utf8').split('\n')) {
  if (!line.trim()) continue;
  const row = JSON.parse(line);
  if (!row.keyword) continue;
  const entry = row.mcp ? entryFromMcp(row.keyword, row.mcp) : row.jobs ? { keyword: row.keyword, jobs: row.jobs } : entryFromMcp(row.keyword, row);
  byKw.set(row.keyword, entry);
}
fs.writeFileSync(jsonlPath, [...byKw.values()].map((r) => JSON.stringify(r)).join('\n') + '\n');
console.log(JSON.stringify({ keywords: byKw.size }));
