#!/usr/bin/env node
import fs from 'fs';
import path from 'path';
const dir = path.join(path.dirname(new URL(import.meta.url).pathname), 'mcp-results');
fs.mkdirSync(dir, { recursive: true });
const batch = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
for (const { keyword, jobs, error } of batch) {
  const safe = keyword.replace(/\//g, '_');
  fs.writeFileSync(path.join(dir, `${safe}.json`), JSON.stringify({ keyword, jobs: jobs || [], error: error || null }));
}
