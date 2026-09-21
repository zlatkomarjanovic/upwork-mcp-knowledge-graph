#!/usr/bin/env node
/**
 * Builds .run-payload.json from raw_batches/*.json
 * Missing keywords get { keyword, error: 'not_run' } for retry next hour.
 */
import fs from 'fs';
import path from 'path';

const dir = path.dirname(new URL(import.meta.url).pathname);
const keywords = JSON.parse(fs.readFileSync(path.join(dir, 'keywords.json'), 'utf8'));
const batchDir = path.join(dir, 'raw_batches');
const byKw = new Map();

if (fs.existsSync(batchDir)) {
  for (const f of fs.readdirSync(batchDir).filter((x) => x.endsWith('.json'))) {
    const batch = JSON.parse(fs.readFileSync(path.join(batchDir, f), 'utf8'));
    const list = Array.isArray(batch) ? batch : batch.searches || [];
    for (const s of list) {
      if (s?.keyword) byKw.set(s.keyword, s);
    }
  }
}

const searches = keywords.map((kw) => byKw.get(kw) || { keyword: kw, error: 'not_run', jobs: [] });
const completed = searches.filter((s) => !s.error).length;
const payload = { keywordsAttempted: keywords.length, keywordsCompleted: completed, searches };
fs.writeFileSync(path.join(dir, '.run-payload.json'), JSON.stringify(payload));
console.log(JSON.stringify({ completed, missing: keywords.length - completed }));
