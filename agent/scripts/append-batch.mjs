#!/usr/bin/env node
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const PARTIAL = path.resolve(__dirname, '../../partial');

function slug(kw) {
  return kw.toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_|_$/g, '').slice(0, 80);
}

const batchPath = process.argv[2];
const batch = JSON.parse(fs.readFileSync(batchPath, 'utf8'));
const items = batch.searches || batch;
fs.mkdirSync(PARTIAL, { recursive: true });
for (const item of items) {
  const { keyword, group, jobs } = item;
  fs.writeFileSync(
    path.join(PARTIAL, `${slug(keyword)}.json`),
    JSON.stringify({ keyword, group, jobs: jobs || [] }),
  );
}
console.log('wrote', items.length, 'partials');
