#!/usr/bin/env node
import fs from 'fs';
import path from 'path';

const dir = path.dirname(new URL(import.meta.url).pathname);
const file = process.argv[2];
if (!file) {
  console.error('Usage: node persist-searches.mjs <batch.json>');
  process.exit(1);
}
const batch = JSON.parse(fs.readFileSync(file, 'utf8'));
const list = Array.isArray(batch) ? batch : batch.searches || [];
const out = path.join(dir, 'search-results.jsonl');
for (const entry of list) {
  if (!entry?.keyword) continue;
  fs.appendFileSync(out, JSON.stringify(entry) + '\n');
}
const batchDir = path.join(dir, 'raw_batches');
fs.mkdirSync(batchDir, { recursive: true });
fs.writeFileSync(path.join(batchDir, `batch-${Date.now()}.json`), JSON.stringify(list));
console.log(JSON.stringify({ appended: list.length, out }));
