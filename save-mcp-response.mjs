#!/usr/bin/env node
import fs from 'fs';
import path from 'path';

const keyword = process.argv[2];
const responseFile = process.argv[3];
if (!keyword || !responseFile) {
  console.error('Usage: save-mcp-response.mjs <keyword> <response.json>');
  process.exit(1);
}
const slug = keyword.replace(/[^a-z0-9]+/gi, '_').replace(/^_|_$/g, '').toLowerCase();
const out = path.join(process.cwd(), 'upwork-intelligence', 'raw', `${slug}.json`);
fs.mkdirSync(path.dirname(out), { recursive: true });
fs.copyFileSync(responseFile, out);
console.log(out);
