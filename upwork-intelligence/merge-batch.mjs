#!/usr/bin/env node
import fs from 'fs';
import path from 'path';

const ROOT = path.dirname(new URL(import.meta.url).pathname);
const mapPath = path.join(ROOT, 'search-results-map.json');
const map = fs.existsSync(mapPath) ? JSON.parse(fs.readFileSync(mapPath, 'utf8')) : {};
const batch = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
for (const item of batch) {
  map[item.keyword] = { group: item.group, jobs: item.jobs || [] };
}
fs.writeFileSync(mapPath, JSON.stringify(map, null, 2));
console.log('map size', Object.keys(map).length);
