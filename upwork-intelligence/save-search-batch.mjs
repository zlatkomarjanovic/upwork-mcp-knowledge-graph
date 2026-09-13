#!/usr/bin/env node
import fs from 'fs';
import path from 'path';

const ROOT = path.dirname(new URL(import.meta.url).pathname);
const rawDir = path.join(ROOT, 'search-raw');
fs.mkdirSync(rawDir, { recursive: true });

const batch = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
for (const item of batch) {
  const slug = item.keyword.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
  fs.writeFileSync(path.join(rawDir, `${slug}.json`), JSON.stringify(item));
}
console.log('saved', batch.length);
