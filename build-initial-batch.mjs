#!/usr/bin/env node
import fs from 'fs';
import path from 'path';
import { KEYWORD_GROUPS } from './run-all-keywords.mjs';

const flat = Object.entries(KEYWORD_GROUPS).flatMap(([group, kws]) =>
  kws.map((keyword) => ({ keyword, group }))
);
const RAW = path.join(process.cwd(), 'upwork-intelligence', 'raw');
const batchPath = path.join(process.cwd(), 'upwork-intelligence', 'run-batch.json');

const results = [];
const errors = [];

for (const { keyword, group } of flat) {
  const slug = keyword.replace(/[^a-z0-9]+/gi, '_').replace(/^_|_$/g, '').toLowerCase();
  const f = path.join(RAW, `${slug}.json`);
  if (fs.existsSync(f)) {
    const response = JSON.parse(fs.readFileSync(f, 'utf8'));
    results.push({ keyword, group, response });
    if (response.status === 'error') errors.push(keyword);
  } else {
    results.push({
      keyword,
      group,
      response: { status: 'error', message: 'search_not_persisted_this_run' },
    });
    errors.push(keyword);
  }
}

const batch = {
  keywordsAttempted: flat.length,
  keywordsCompleted: results.filter((r) => r.response?.status === 'ok').length,
  errors: [...new Set(errors)],
  results,
};
fs.mkdirSync(path.dirname(batchPath), { recursive: true });
fs.writeFileSync(batchPath, JSON.stringify(batch));
console.log(JSON.stringify({ completed: batch.keywordsCompleted, attempted: batch.keywordsAttempted }));
