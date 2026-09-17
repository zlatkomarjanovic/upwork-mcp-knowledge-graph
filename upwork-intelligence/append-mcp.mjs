#!/usr/bin/env node
import fs from 'fs';
import path from 'path';
const DIR = path.dirname(new URL(import.meta.url).pathname);
const log = path.join(DIR, 'mcp-responses.jsonl');
const items = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
for (const it of items) fs.appendFileSync(log, JSON.stringify(it) + '\n');
