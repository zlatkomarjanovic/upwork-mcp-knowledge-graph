#!/usr/bin/env node
import fs from 'fs';
import path from 'path';

const dir = path.dirname(new URL(import.meta.url).pathname);
const batchDir = path.join(dir, 'raw_batches');
fs.mkdirSync(batchDir, { recursive: true });

const file = process.argv[2];
if (!file) {
  console.error('Usage: node ingest-search.mjs <response.json>');
  process.exit(1);
}
const payload = JSON.parse(fs.readFileSync(file, 'utf8'));
const out = path.join(batchDir, `batch-${Date.now()}.json`);
fs.writeFileSync(out, JSON.stringify(payload, null, 0));
console.log(out);
