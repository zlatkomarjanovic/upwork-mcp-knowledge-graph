#!/usr/bin/env node
/** Save search results to agent/partial/*.json — stdin: {searches:[{keyword,group,jobs}]} */
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const PARTIAL = path.resolve(__dirname, '../../partial');

function slug(kw) {
  return kw.toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_|_$/g, '').slice(0, 80);
}

const raw = fs.readFileSync(0, 'utf8');
const data = JSON.parse(raw);
const items = data.searches || data;
fs.mkdirSync(PARTIAL, { recursive: true });
let n = 0;
for (const { keyword, group, jobs } of items) {
  fs.writeFileSync(
    path.join(PARTIAL, `${slug(keyword)}.json`),
    JSON.stringify({ keyword, group, jobs: jobs || [] }),
  );
  n++;
}
console.log('saved', n, 'partials');
