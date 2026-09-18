#!/usr/bin/env node
import fs from 'fs';
import path from 'path';

const dir = path.dirname(new URL(import.meta.url).pathname);
const batchDir = path.join(dir, 'raw_batches');
const keywords = JSON.parse(fs.readFileSync(path.join(dir, 'keywords.json'), 'utf8'));

const searches = [];
const errors = [];

if (fs.existsSync(batchDir)) {
  for (const f of fs.readdirSync(batchDir).filter((x) => x.endsWith('.json'))) {
    const batch = JSON.parse(fs.readFileSync(path.join(batchDir, f), 'utf8'));
    if (Array.isArray(batch)) {
      for (const entry of batch) searches.push(entry);
    } else if (batch.searches) {
      searches.push(...batch.searches);
    }
  }
}

const byKw = new Map();
for (const s of searches) {
  if (s.keyword) byKw.set(s.keyword, s);
}

const merged = [];
for (const kw of keywords) {
  const ex = byKw.get(kw);
  if (ex) merged.push(ex);
  else errors.push(kw);
}

const payload = {
  keywordsAttempted: keywords.length,
  keywordsCompleted: merged.filter((s) => !s.error).length,
  searches: merged,
};
const out = path.join(dir, '.run-payload.json');
fs.writeFileSync(out, JSON.stringify(payload));
console.log(JSON.stringify({ out, merged: merged.length, missing: errors.length, errors }));
