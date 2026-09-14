#!/usr/bin/env node
import fs from 'fs';
import path from 'path';

const dir = path.dirname(new URL(import.meta.url).pathname);
const batchDir = path.join(dir, 'raw_batches');
fs.mkdirSync(batchDir, { recursive: true });

const batch = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
if (!Array.isArray(batch)) {
  console.error('Expected JSON array of {keyword, jobs?, error?}');
  process.exit(1);
}
const out = path.join(batchDir, `batch-${Date.now()}.json`);
fs.writeFileSync(out, JSON.stringify(batch));
console.log(out);
