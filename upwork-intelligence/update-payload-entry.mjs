#!/usr/bin/env node
import fs from 'fs';
import path from 'path';

const dir = path.dirname(new URL(import.meta.url).pathname);
const payloadPath = path.join(dir, '.run-payload.json');
const keywords = JSON.parse(fs.readFileSync(path.join(dir, 'keywords.json'), 'utf8'));

const entry = JSON.parse(fs.readFileSync(0, 'utf8'));
if (!entry.keyword) {
  console.error('Missing keyword');
  process.exit(1);
}

let payload = fs.existsSync(payloadPath)
  ? JSON.parse(fs.readFileSync(payloadPath, 'utf8'))
  : { keywordsAttempted: keywords.length, keywordsCompleted: 0, searches: [] };

const byKw = new Map((payload.searches || []).map((s) => [s.keyword, s]));
byKw.set(entry.keyword, { keyword: entry.keyword, jobs: entry.jobs || [], error: entry.error });

const searches = keywords.map((kw) => byKw.get(kw) || { keyword: kw, error: 'not_run', jobs: [] });
const completed = searches.filter((s) => !s.error).length;
payload = { keywordsAttempted: keywords.length, keywordsCompleted: completed, searches };
fs.writeFileSync(payloadPath, JSON.stringify(payload));
console.log(JSON.stringify({ keyword: entry.keyword, completed }));
