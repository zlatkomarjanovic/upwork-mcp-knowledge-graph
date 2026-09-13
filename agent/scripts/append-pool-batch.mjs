#!/usr/bin/env node
/** Merge jobs from MCP response JSON file(s) into agent/pool-jobs.json (dedupe by url). */
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const POOL = path.resolve(__dirname, '../pool-jobs.json');

const existing = fs.existsSync(POOL) ? JSON.parse(fs.readFileSync(POOL, 'utf8')) : { jobs: [] };
const byUrl = new Map();
for (const j of existing.jobs || []) {
  if (j?.url) byUrl.set(j.url.split('?')[0], j);
}

for (const f of process.argv.slice(2)) {
  const data = JSON.parse(fs.readFileSync(f, 'utf8'));
  const jobs = data.jobs || (Array.isArray(data) ? data : []);
  for (const j of jobs) {
    if (j?.url) byUrl.set(j.url.split('?')[0], j);
  }
}

const out = { jobs: [...byUrl.values()] };
fs.writeFileSync(POOL, JSON.stringify(out, null, 2));
console.log('pool size', out.jobs.length);
