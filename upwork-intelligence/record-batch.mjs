#!/usr/bin/env node
import fs from 'fs';
import path from 'path';

const ROOT = path.dirname(new URL(import.meta.url).pathname);
const out = path.join(ROOT, 'run-results.jsonl');
const batch = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
for (const { keyword, group, response } of batch) {
  const jobs = response?.jobs || [];
  fs.appendFileSync(out, JSON.stringify({ keyword, group, jobs }) + '\n');
}
console.log('recorded', batch.length, 'keywords');
