#!/usr/bin/env node
import fs from 'fs';
import path from 'path';

const keyword = process.argv[2];
if (!keyword) {
  console.error('Usage: save-mcp-response.mjs <keyword> < response.json');
  process.exit(1);
}
const dir = path.dirname(new URL(import.meta.url).pathname);
const slug = keyword.replace(/ /g, '__');
const mcpDir = path.join(dir, 'raw_batches', 'mcp');
fs.mkdirSync(mcpDir, { recursive: true });
const body = fs.readFileSync(0, 'utf8');
fs.writeFileSync(path.join(mcpDir, `${slug}.json`), body);
console.log(JSON.stringify({ keyword, file: `${slug}.json` }));
