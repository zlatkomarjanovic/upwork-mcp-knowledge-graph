#!/usr/bin/env node
import fs from 'fs';
import path from 'path';
import { entryFromMcp } from './slim-job.mjs';

const dir = path.dirname(new URL(import.meta.url).pathname);
const [keyword, mcpFile] = process.argv.slice(2);
if (!keyword || !mcpFile) {
  console.error('Usage: node ingest-keyword.mjs <keyword> <mcp-response.json>');
  process.exit(1);
}
const resp = JSON.parse(fs.readFileSync(mcpFile, 'utf8'));
const entry = entryFromMcp(keyword, resp);
const jsonlPath = path.join(dir, 'search-results.jsonl');
const byKw = new Map();
if (fs.existsSync(jsonlPath)) {
  for (const line of fs.readFileSync(jsonlPath, 'utf8').split('\n')) {
    if (!line.trim()) continue;
    const row = JSON.parse(line);
    if (row.keyword) byKw.set(row.keyword, row);
  }
}
byKw.set(keyword, entry);
fs.writeFileSync(jsonlPath, [...byKw.values()].map((r) => JSON.stringify(r)).join('\n') + '\n');
console.log(JSON.stringify({ keyword, jobs: entry.jobs?.length ?? 0, error: entry.error }));
