#!/usr/bin/env node
import fs from 'fs';
import path from 'path';

const dir = path.dirname(new URL(import.meta.url).pathname);
const keywords = JSON.parse(fs.readFileSync(path.join(dir, 'keywords.json'), 'utf8'));
const allPath = path.join(dir, 'all-searches.json');
const byKw = new Map();
if (fs.existsSync(allPath)) {
  for (const s of JSON.parse(fs.readFileSync(allPath, 'utf8'))) byKw.set(s.keyword, s);
}
const searches = keywords.map((kw) => {
  const ex = byKw.get(kw);
  if (ex?.error) return { keyword: kw, error: ex.error, jobs: [] };
  if (ex?.jobs) return { keyword: kw, jobs: ex.jobs };
  return { keyword: kw, error: 'not_run', jobs: [] };
});
const completed = searches.filter((s) => !s.error).length;
const payload = { keywordsAttempted: keywords.length, keywordsCompleted: completed, searches };
fs.writeFileSync(path.join(dir, '.run-payload.json'), JSON.stringify(payload));
console.log(JSON.stringify({ completed, missing: keywords.length - completed }));
