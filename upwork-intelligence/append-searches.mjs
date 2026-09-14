#!/usr/bin/env node
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const DIR = path.dirname(fileURLToPath(import.meta.url));
const main = path.join(DIR, 'search-raw.json');
const addPath = process.argv[2];
if (!addPath) process.exit(1);
const mainData = JSON.parse(fs.readFileSync(main, 'utf8'));
const adds = JSON.parse(fs.readFileSync(addPath, 'utf8'));
const seen = new Set((mainData.searches || []).map((s) => s.keyword));
for (const s of adds.searches || adds) {
  if (!s.keyword || seen.has(s.keyword)) continue;
  mainData.searches.push(s);
  seen.add(s.keyword);
}
if (adds.errors) {
  mainData.errors = [...new Set([...(mainData.errors || []), ...adds.errors])];
}
fs.writeFileSync(main, JSON.stringify(mainData));
console.log(JSON.stringify({ total: mainData.searches.length }));
