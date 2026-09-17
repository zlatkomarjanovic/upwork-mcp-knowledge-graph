#!/usr/bin/env node
import fs from 'fs';
import path from 'path';
const DIR = path.dirname(new URL(import.meta.url).pathname);
const resultsDir = path.join(DIR, 'mcp-results');
fs.mkdirSync(resultsDir, { recursive: true });
const batch = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
for (const item of batch) {
  const slug = item.keyword.replace(/[^a-z0-9]+/gi, '_').replace(/^_|_$/g, '').slice(0, 80);
  fs.writeFileSync(path.join(resultsDir, `${slug}.json`), JSON.stringify(item.result));
}
