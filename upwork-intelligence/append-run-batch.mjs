#!/usr/bin/env node
import fs from 'fs';
import path from 'path';
const ROOT = path.dirname(new URL(import.meta.url).pathname);
const batch = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
const out = path.join(ROOT, 'run-results.jsonl');
for (const item of batch) {
  fs.appendFileSync(out, JSON.stringify({ keyword: item.keyword, group: item.group, jobs: item.jobs || [] }) + '\n');
}
console.log('appended', batch.length);
