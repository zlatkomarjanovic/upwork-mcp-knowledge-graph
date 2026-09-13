#!/usr/bin/env node
/** Save {searches:[{keyword,group,jobs}]} to agent/partial/*.json */
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const PARTIAL = path.resolve(__dirname, '../partial');

function slug(kw) {
  return kw.toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_|_$/g, '').slice(0, 80);
}

const batchPath = process.argv[2];
const batch = JSON.parse(fs.readFileSync(batchPath, 'utf8'));
const items = batch.searches || batch;
fs.mkdirSync(PARTIAL, { recursive: true });
for (const { keyword, group, jobs } of items) {
  fs.writeFileSync(
    path.join(PARTIAL, `${slug(keyword)}.json`),
    JSON.stringify({ keyword, group, jobs: jobs || [] }),
  );
}
console.log('saved partials', items.length);
