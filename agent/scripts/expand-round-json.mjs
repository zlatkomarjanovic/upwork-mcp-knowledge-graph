#!/usr/bin/env node
/** Expand agent/round-N.json keyed by keyword into agent/partial/*.json */
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { KEYWORDS } from './keywords-config.mjs';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const PARTIAL = path.resolve(__dirname, '../partial');

function slug(kw) {
  return kw.toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_|_$/g, '').slice(0, 80);
}

const roundPath = process.argv[2];
if (!roundPath) {
  console.error('Usage: node expand-round-json.mjs agent/round-1.json');
  process.exit(1);
}

const round = JSON.parse(fs.readFileSync(roundPath, 'utf8'));
const groupByKw = new Map(KEYWORDS.map((k) => [k.keyword.toLowerCase(), k.group]));
fs.mkdirSync(PARTIAL, { recursive: true });
let n = 0;
for (const [keyword, payload] of Object.entries(round)) {
  const group = groupByKw.get(keyword.toLowerCase()) || payload.group;
  const jobs = payload.jobs || (Array.isArray(payload) ? payload : []);
  fs.writeFileSync(
    path.join(PARTIAL, `${slug(keyword)}.json`),
    JSON.stringify({ keyword, group, jobs }),
  );
  n++;
}
console.log('partials from', path.basename(roundPath), n);
