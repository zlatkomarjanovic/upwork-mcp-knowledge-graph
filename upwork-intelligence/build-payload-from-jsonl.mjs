#!/usr/bin/env node
import fs from 'fs';
import path from 'path';

const dir = path.dirname(new URL(import.meta.url).pathname);
const keywords = JSON.parse(fs.readFileSync(path.join(dir, 'keywords.json'), 'utf8'));
const jsonlPath = path.join(dir, 'search-results.jsonl');
const byKw = new Map();

if (fs.existsSync(jsonlPath)) {
  for (const line of fs.readFileSync(jsonlPath, 'utf8').split('\n')) {
    if (!line.trim()) continue;
    const row = JSON.parse(line);
    if (row.keyword) byKw.set(row.keyword, row);
  }
}

const searches = keywords.map((kw) => {
  const ex = byKw.get(kw);
  if (!ex) return { keyword: kw, error: 'not_run', jobs: [] };
  if (ex.error) return { keyword: kw, error: ex.error, jobs: [] };
  return { keyword: kw, jobs: ex.jobs || [] };
});

const completed = searches.filter((s) => !s.error).length;
const payload = { keywordsAttempted: keywords.length, keywordsCompleted: completed, searches };
fs.writeFileSync(path.join(dir, '.run-payload.json'), JSON.stringify(payload));
console.log(JSON.stringify({ completed, missing: keywords.length - completed }));
