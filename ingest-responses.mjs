#!/usr/bin/env node
import fs from 'fs';
import path from 'path';

const file = process.argv[2];
const entries = JSON.parse(fs.readFileSync(file, 'utf8'));
const RAW = path.join(process.cwd(), 'upwork-intelligence', 'raw');
fs.mkdirSync(RAW, { recursive: true });

for (const { keyword, response } of entries) {
  const slug = keyword.replace(/[^a-z0-9]+/gi, '_').replace(/^_|_$/g, '').toLowerCase();
  fs.writeFileSync(path.join(RAW, `${slug}.json`), JSON.stringify(response));
}
console.log(`ingested ${entries.length} -> ${RAW}`);
