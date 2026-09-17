#!/usr/bin/env node
import fs from 'fs';
import path from 'path';

const dir = path.dirname(new URL(import.meta.url).pathname);
const keywords = JSON.parse(fs.readFileSync(path.join(dir, 'keywords.json'), 'utf8'));
const jsonl = path.join(dir, 'search-results.jsonl');
const byKw = new Map();
if (fs.existsSync(jsonl)) {
  for (const line of fs.readFileSync(jsonl, 'utf8').split('\n')) {
    if (!line.trim()) continue;
    const row = JSON.parse(line);
    if (row.keyword) byKw.set(row.keyword, row);
  }
}
const searches = keywords.map((kw) => byKw.get(kw) || { keyword: kw, error: 'not_run', jobs: [] });
const completed = searches.filter((s) => !s.error).length;
const payload = { keywordsAttempted: keywords.length, keywordsCompleted: completed, searches };
fs.writeFileSync(path.join(dir, '.run-payload.json'), JSON.stringify(payload));
console.log(JSON.stringify({ completed, missing: keywords.length - completed }));
