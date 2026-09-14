#!/usr/bin/env node
import fs from 'fs';
import path from 'path';

const dir = path.dirname(new URL(import.meta.url).pathname);
const keywords = JSON.parse(fs.readFileSync(path.join(dir, 'keywords.json'), 'utf8'));
const old = JSON.parse(fs.readFileSync(path.join(dir, '.run-payload.json'), 'utf8'));
const failed = JSON.parse(process.argv[2] || '[]');

const failedSet = new Set(failed);
const byKw = new Map(old.searches.map((s) => [s.keyword, s]));

const searches = keywords.map((kw) => {
  if (failedSet.has(kw)) return { keyword: kw, error: 'mcp_error', jobs: [] };
  const ex = byKw.get(kw);
  if (ex && !ex.error && (ex.jobs?.length || ex.jobs)) return { keyword: kw, jobs: ex.jobs || [] };
  if (ex && ex.jobs?.length) return { keyword: kw, jobs: ex.jobs };
  return { keyword: kw, jobs: [] };
});

const completed = searches.filter((s) => !s.error).length;
const payload = { keywordsAttempted: keywords.length, keywordsCompleted: completed, searches };
fs.writeFileSync(path.join(dir, '.run-payload.json'), JSON.stringify(payload));
console.log(JSON.stringify({ completed, failed: failed.length }));
