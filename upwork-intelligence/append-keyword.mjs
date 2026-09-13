#!/usr/bin/env node
import fs from 'fs';
import path from 'path';

const ROOT = path.dirname(new URL(import.meta.url).pathname);
const [, , keyword, group, jobsPath] = process.argv;
const jobs = JSON.parse(fs.readFileSync(jobsPath, 'utf8'));
const out = path.join(ROOT, 'run-results.jsonl');
fs.appendFileSync(out, JSON.stringify({ keyword, group, jobs }) + '\n');
console.log(keyword, jobs.length);
