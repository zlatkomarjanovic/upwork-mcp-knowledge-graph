#!/usr/bin/env node
import fs from 'fs';
import path from 'path';

const keyword = process.argv[2];
const inFile = process.argv[3];
if (!keyword || !inFile) {
  console.error('Usage: save-tail-response.mjs <keyword> <response.json>');
  process.exit(1);
}
const slug = keyword
  .replace(/[^a-z0-9]+/gi, '_')
  .replace(/^_|_$/g, '')
  .toLowerCase();
const dir = path.join(process.cwd(), 'upwork-intelligence', 'raw-tail');
fs.mkdirSync(dir, { recursive: true });
fs.copyFileSync(inFile, path.join(dir, `${slug}.json`));
fs.writeFileSync(path.join(dir, `${slug}.meta.json`), JSON.stringify({ keyword }));
console.log(slug);
