#!/usr/bin/env node
import fs from 'fs';
import path from 'path';
import { KEYWORD_GROUPS } from './run-all-keywords.mjs';

const RAW = path.join(process.cwd(), 'upwork-intelligence', 'raw');
const batchPath = path.join(process.cwd(), 'upwork-intelligence', 'run-batch.json');

const flat = Object.entries(KEYWORD_GROUPS).flatMap(([group, kws]) =>
  kws.map((keyword) => ({ keyword, group }))
);

function slug(kw) {
  return kw.replace(/[^a-z0-9]+/gi, '_').replace(/^_|_$/g, '').toLowerCase();
}

const results = [];
const errors = [];

for (const { keyword, group } of flat) {
  const f = path.join(RAW, `${slug(keyword)}.json`);
  if (!fs.existsSync(f)) {
    errors.push(keyword);
    continue;
  }
  const response = JSON.parse(fs.readFileSync(f, 'utf8'));
  results.push({ keyword, group, response });
  if (response.status === 'error') errors.push(keyword);
}

const batch = {
  keywordsAttempted: flat.length,
  keywordsCompleted: results.filter((r) => r.response?.status === 'ok').length,
  errors: [...new Set(errors)],
  results,
};

fs.mkdirSync(path.dirname(batchPath), { recursive: true });
fs.writeFileSync(batchPath, JSON.stringify(batch));
console.log(
  JSON.stringify({
    attempted: batch.keywordsAttempted,
    completed: batch.keywordsCompleted,
    missing: flat.length - results.length,
    errors: batch.errors.length,
  })
);
