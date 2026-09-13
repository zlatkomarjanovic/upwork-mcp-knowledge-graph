#!/usr/bin/env node
/** Append one keyword result to _kw_batches.jsonl: node append-kw-batch.mjs keyword GROUP jobs.json | node append-kw-batch.mjs keyword GROUP --error "msg" */
import fs from 'fs';
import path from 'path';

const ROOT = path.dirname(new URL(import.meta.url).pathname);
const [, , keyword, group, third, fourth] = process.argv;
const out = path.join(ROOT, '_kw_batches.jsonl');
let row;
if (third === '--error') {
  row = { keyword, group, error: fourth || 'search_failed' };
} else {
  const jobs = JSON.parse(fs.readFileSync(third, 'utf8'));
  row = { keyword, group, jobs };
}
fs.appendFileSync(out, JSON.stringify(row) + '\n');
console.log(keyword, row.error ? 'ERR' : jobs.length);
