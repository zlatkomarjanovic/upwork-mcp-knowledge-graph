#!/usr/bin/env node
import fs from 'fs';
import path from 'path';
const [keyword, file] = process.argv.slice(2);
const body = JSON.parse(fs.readFileSync(file, 'utf8'));
const dir = path.join(path.dirname(new URL(import.meta.url).pathname), 'mcp-results');
fs.mkdirSync(dir, { recursive: true });
const safe = keyword.replace(/\//g, '_');
fs.writeFileSync(path.join(dir, `${safe}.json`), JSON.stringify({ keyword, jobs: body.jobs || [], error: body.error || null }));
