#!/usr/bin/env node
/** Write one keyword result file: node mcp-fetch-keyword.mjs "keyword" < response.json */
import fs from 'fs';
import path from 'path';
const keyword = process.argv[2];
if (!keyword) process.exit(1);
const body = JSON.parse(fs.readFileSync(0, 'utf8'));
const jobs = body.jobs || [];
const dir = path.join(path.dirname(new URL(import.meta.url).pathname), 'mcp-results');
fs.mkdirSync(dir, { recursive: true });
const safe = keyword.replace(/\//g, '_');
fs.writeFileSync(path.join(dir, `${safe}.json`), JSON.stringify({ keyword, jobs, error: body.error || null }));
