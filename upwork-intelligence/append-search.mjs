#!/usr/bin/env node
import fs from 'fs';
import path from 'path';
const dir = path.dirname(new URL(import.meta.url).pathname);
const line = JSON.parse(fs.readFileSync(0, 'utf8'));
fs.appendFileSync(path.join(dir, 'search-results.jsonl'), JSON.stringify(line) + '\n');
