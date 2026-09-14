#!/usr/bin/env node
/** Append or write raw_batches from MCP capture file (JSON array). */
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const DIR = path.dirname(fileURLToPath(import.meta.url));
const BATCH = path.join(DIR, 'raw_batches');
const capPath = process.argv[2] || path.join(DIR, 'mcp-capture.json');

if (!fs.existsSync(capPath)) {
  console.error('missing', capPath);
  process.exit(1);
}
const items = JSON.parse(fs.readFileSync(capPath, 'utf8'));
fs.mkdirSync(BATCH, { recursive: true });

for (const item of items) {
  if (item.error || !item.keyword) continue;
  const slug = item.keyword
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-|-$/g, '')
    .slice(0, 80);
  const out = { keyword: item.keyword, group: item.group, jobs: item.jobs || [] };
  fs.writeFileSync(path.join(BATCH, `${slug}.json`), JSON.stringify(out));
}
console.log(JSON.stringify({ written: items.filter((i) => !i.error).length }));
