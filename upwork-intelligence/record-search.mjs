#!/usr/bin/env node
import fs from 'fs';
import path from 'path';

const ROOT = path.dirname(new URL(import.meta.url).pathname);
const [, , keyword, group] = process.argv;
const jobs = JSON.parse(fs.readFileSync(0, 'utf8'));
fs.appendFileSync(
  path.join(ROOT, 'run-results.jsonl'),
  JSON.stringify({ keyword, group, jobs }) + '\n'
);
