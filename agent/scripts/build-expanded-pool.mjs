#!/usr/bin/env node
/** Merge job arrays from JSON files into agent/pool-jobs.json (dedupe by URL). */
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const OUT = path.resolve(__dirname, '../pool-jobs.json');

const files = process.argv.slice(2);
const byUrl = new Map();
for (const f of files) {
  const data = JSON.parse(fs.readFileSync(f, 'utf8'));
  const jobs = data.jobs || data;
  for (const j of jobs) {
    if (!j?.url) continue;
    byUrl.set(j.url.split('?')[0], j);
  }
}
fs.writeFileSync(OUT, JSON.stringify({ jobs: [...byUrl.values()] }, null, 2));
console.log('pool size', byUrl.size);
