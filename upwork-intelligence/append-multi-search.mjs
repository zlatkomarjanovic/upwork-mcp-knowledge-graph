#!/usr/bin/env node
import fs from 'fs';
import path from 'path';

const dir = path.dirname(new URL(import.meta.url).pathname);
const out = path.join(dir, 'all-searches.json');
const items = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
const strip = ({ description_snippet, ...j }) => j;
let all = [];
if (fs.existsSync(out)) all = JSON.parse(fs.readFileSync(out, 'utf8'));
const byKw = new Map(all.map((x) => [x.keyword, x]));
for (const item of items) {
  const keyword = item.keyword;
  if (item.error) {
    byKw.set(keyword, { keyword, error: item.error, jobs: [] });
    continue;
  }
  const resp = item.response || item;
  const jobs = (resp.jobs || []).map(strip);
  byKw.set(keyword, resp.status && resp.status !== 'ok' ? { keyword, error: resp.error_code || resp.status, jobs: [] } : { keyword, jobs });
}
fs.writeFileSync(out, JSON.stringify([...byKw.values()]));
console.log(JSON.stringify({ saved: items.length, total: byKw.size }));
