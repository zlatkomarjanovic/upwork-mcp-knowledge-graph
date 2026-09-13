#!/usr/bin/env node
/** Save jobs to agent/mcp-cache/{slug}.json — usage: node mcp-cache-save.mjs "keyword" path/to/jobs-or-mcp.json */
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const CACHE = path.resolve(__dirname, '../mcp-cache');

function slug(kw) {
  return kw.toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_|_$/g, '').slice(0, 80);
}

const [keyword, src] = process.argv.slice(2);
const raw = JSON.parse(fs.readFileSync(src, 'utf8'));
const jobs = raw.jobs || raw;
fs.mkdirSync(CACHE, { recursive: true });
fs.writeFileSync(path.join(CACHE, `${slug(keyword)}.json`), JSON.stringify({ jobs }));
console.log('cache', keyword, jobs.length);
