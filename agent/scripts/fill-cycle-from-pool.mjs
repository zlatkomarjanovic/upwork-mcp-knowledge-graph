#!/usr/bin/env node
/**
 * Build cycle-searches.json for current slot: use existing partials, else title-filter jobs from pool.
 */
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { keywordsForSlot, slotForHour, ROTATION } from './keywords-config.mjs';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const PARTIAL = path.resolve(__dirname, '../../partial');
const POOL = process.argv[2] || path.resolve(__dirname, '../../pool-jobs.json');
const OUT = path.resolve(__dirname, '../cycle-searches.json');

function slug(kw) {
  return kw.toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_|_$/g, '').slice(0, 80);
}

function titleMatches(keyword, job) {
  const words = keyword.toLowerCase().split(/\s+/).filter(Boolean);
  const hay = [
    job.title || '',
    ...(job.skills || []),
    job.description_snippet || '',
  ]
    .join(' ')
    .toLowerCase();
  return words.every((w) => hay.includes(w));
}

const pool = JSON.parse(fs.readFileSync(POOL, 'utf8'));
const poolJobs = pool.jobs || pool;

const slot = slotForHour(new Date().getUTCHours());
const expected = keywordsForSlot(slot);
const groups = ROTATION[slot];
const failures = [];
const searches = [];

for (const { keyword, group } of expected) {
  const partialPath = path.join(PARTIAL, `${slug(keyword)}.json`);
  if (fs.existsSync(partialPath)) {
    searches.push(JSON.parse(fs.readFileSync(partialPath, 'utf8')));
    continue;
  }
  const jobs = poolJobs.filter((j) => titleMatches(keyword, j));
  if (!jobs.length) {
    failures.push({ keyword, error: 'no partial and no pool title match' });
  }
  searches.push({ keyword, group, jobs });
}

const doc = {
  meta: {
    timestamp: new Date().toISOString(),
    slot,
    groups,
    keywordsSearched: searches.map((s) => s.keyword),
    jobsReturned: searches.reduce((n, s) => n + (s.jobs?.length || 0), 0),
    poolFallback: true,
  },
  searches,
  failures,
};
fs.writeFileSync(OUT, JSON.stringify(doc, null, 2));
console.log(JSON.stringify({ searches: searches.length, failures: failures.length, out: OUT }));
