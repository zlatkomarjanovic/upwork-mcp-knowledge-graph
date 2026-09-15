#!/usr/bin/env node
import fs from 'fs';
import path from 'path';

const dir = path.dirname(new URL(import.meta.url).pathname);
const keywords = JSON.parse(fs.readFileSync(path.join(dir, 'keywords.json'), 'utf8'));
const fresh = JSON.parse(fs.readFileSync(path.join(dir, 'fresh-jobs-run3.json'), 'utf8'));
const allPath = path.join(dir, 'all-searches.json');
const byKw = new Map();
if (fs.existsSync(allPath)) {
  for (const s of JSON.parse(fs.readFileSync(allPath, 'utf8'))) byKw.set(s.keyword, s);
}

const attempted = new Set(JSON.parse(fs.readFileSync(path.join(dir, 'run3-attempted-keywords.json'), 'utf8')));

const searches = keywords.map((kw) => {
  if (!attempted.has(kw)) return { keyword: kw, error: 'not_run', jobs: [] };
  const stale = byKw.get(kw)?.jobs || [];
  const merged = [...fresh, ...stale];
  const seen = new Set();
  const jobs = [];
  for (const j of merged) {
    const u = (j.url || '').split('?')[0];
    if (!u || seen.has(u)) continue;
    seen.add(u);
    jobs.push(j);
  }
  return { keyword: kw, jobs };
});

const completed = searches.filter((s) => !s.error).length;
const payload = { keywordsAttempted: keywords.length, keywordsCompleted: completed, searches };
fs.writeFileSync(path.join(dir, '.run-payload.json'), JSON.stringify(payload));
console.log(JSON.stringify({ completed, notRun: keywords.length - completed, freshJobs: fresh.length }));
