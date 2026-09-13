#!/usr/bin/env node
/** {searches:[{keyword,jobs}]} -> mcp-cache + partials */
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { KEYWORDS } from './keywords-config.mjs';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const CACHE = path.resolve(__dirname, '../mcp-cache');
const PARTIAL = path.resolve(__dirname, '../partial');

function slug(kw) {
  return kw.toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_|_$/g, '').slice(0, 80);
}

const groupByKw = new Map(KEYWORDS.map((k) => [k.keyword.toLowerCase(), k.group]));
const batch = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
const items = batch.searches || batch;
fs.mkdirSync(CACHE, { recursive: true });
fs.mkdirSync(PARTIAL, { recursive: true });
for (const { keyword, group, jobs } of items) {
  const g = group || groupByKw.get(keyword.toLowerCase());
  const j = jobs || [];
  fs.writeFileSync(path.join(CACHE, `${slug(keyword)}.json`), JSON.stringify({ jobs: j }));
  fs.writeFileSync(
    path.join(PARTIAL, `${slug(keyword)}.json`),
    JSON.stringify({ keyword, group: g, jobs: j }),
  );
}
console.log('cached', items.length);
