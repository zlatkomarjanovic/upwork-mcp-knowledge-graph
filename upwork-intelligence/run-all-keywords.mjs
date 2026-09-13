#!/usr/bin/env node
/**
 * Lists keywords for hourly MCP search (invoked by automation agent).
 * Persistence: append MCP batches to run-results.jsonl via append-search-results.mjs
 */
import fs from 'fs';
import path from 'path';

const ROOT = path.dirname(new URL(import.meta.url).pathname);
const KEYWORDS = JSON.parse(fs.readFileSync(path.join(ROOT, 'keywords.json'), 'utf8'));
const start = Number(process.argv[2] || 0);
const count = Number(process.argv[3] || KEYWORDS.length);
const slice = KEYWORDS.slice(start, start + count);
console.log(JSON.stringify(slice, null, 0));
