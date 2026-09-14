#!/usr/bin/env node
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const DIR = path.dirname(fileURLToPath(import.meta.url));
const file = process.argv[2];
const items = JSON.parse(fs.readFileSync(file, 'utf8'));
const cap = path.join(DIR, 'mcp-capture.json');
let arr = [];
if (fs.existsSync(cap)) {
  try {
    arr = JSON.parse(fs.readFileSync(cap, 'utf8'));
  } catch {
    arr = [];
  }
}
const seen = new Set(arr.map((x) => x.keyword));
for (const it of items) {
  if (seen.has(it.keyword)) continue;
  arr.push(it);
  seen.add(it.keyword);
}
fs.writeFileSync(cap, JSON.stringify(arr));
console.log(arr.length);
