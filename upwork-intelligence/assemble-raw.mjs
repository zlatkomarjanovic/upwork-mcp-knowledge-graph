#!/usr/bin/env node
import fs from 'fs';
import path from 'path';
const DIR = path.dirname(new URL(import.meta.url).pathname);
const KEYWORDS = JSON.parse(fs.readFileSync(path.join(DIR, 'keywords.json'), 'utf8'));
const resDir = path.join(DIR, 'mcp-results');
const searches = [];
const errors = [];
for (const keyword of KEYWORDS) {
  const safe = keyword.replace(/\//g, '_');
  const p = path.join(resDir, `${safe}.json`);
  if (!fs.existsSync(p)) {
    errors.push(keyword);
    continue;
  }
  const row = JSON.parse(fs.readFileSync(p, 'utf8'));
  searches.push(row);
  if (row.error) errors.push(keyword);
}
fs.writeFileSync(path.join(DIR, '.run-raw.json'), JSON.stringify({ searches, errors: [...new Set(errors)] }));
