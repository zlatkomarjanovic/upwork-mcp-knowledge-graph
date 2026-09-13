#!/usr/bin/env node
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { keywordsForSlot, slotForHour, ROTATION } from './keywords-config.mjs';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const PARTIAL = path.resolve(__dirname, '../../partial');
const OUT = path.resolve(__dirname, '../../cycle-searches.json');

const slot = slotForHour(new Date().getUTCHours());
const expected = keywordsForSlot(slot);
const groups = ROTATION[slot];

const bySlug = new Map();
if (fs.existsSync(PARTIAL)) {
  for (const f of fs.readdirSync(PARTIAL).filter((x) => x.endsWith('.json'))) {
    const o = JSON.parse(fs.readFileSync(path.join(PARTIAL, f), 'utf8'));
    bySlug.set(f.replace(/\.json$/, ''), o);
  }
}

function slug(kw) {
  return kw.toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_|_$/g, '').slice(0, 80);
}

const searches = [];
const failures = [];
for (const { keyword, group } of expected) {
  const s = bySlug.get(slug(keyword));
  if (s) searches.push(s);
  else failures.push({ keyword, error: 'missing partial (rate limit or not run)' });
}

const jobsReturned = searches.reduce((n, s) => n + (s.jobs?.length || 0), 0);
const doc = {
  meta: {
    timestamp: new Date().toISOString(),
    slot,
    groups,
    keywordsSearched: searches.map((s) => s.keyword),
    jobsReturned,
  },
  searches,
  failures,
};
fs.writeFileSync(OUT, JSON.stringify(doc, null, 2));
console.log(JSON.stringify({ out: OUT, searches: searches.length, expected: expected.length, failures: failures.length, jobsReturned }));
