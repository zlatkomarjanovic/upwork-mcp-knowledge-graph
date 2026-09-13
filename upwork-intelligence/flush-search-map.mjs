#!/usr/bin/env node
import fs from 'fs';
import path from 'path';

const ROOT = path.dirname(new URL(import.meta.url).pathname);
const map = JSON.parse(fs.readFileSync(path.join(ROOT, 'search-results-map.json'), 'utf8'));
const out = path.join(ROOT, 'run-results.jsonl');
fs.writeFileSync(out, '');
for (const [keyword, { group, jobs }] of Object.entries(map)) {
  fs.appendFileSync(out, JSON.stringify({ keyword, group, jobs }) + '\n');
}
console.log('flushed', Object.keys(map).length, 'keywords to run-results.jsonl');
