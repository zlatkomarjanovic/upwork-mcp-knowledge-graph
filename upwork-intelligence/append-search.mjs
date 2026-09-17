#!/usr/bin/env node
import fs from 'fs';
import path from 'path';
const rawPath = path.join(path.dirname(new URL(import.meta.url).pathname), '.run-raw.json');
const keyword = process.argv[2];
const payload = JSON.parse(fs.readFileSync(0, 'utf8'));
const data = JSON.parse(fs.readFileSync(rawPath, 'utf8'));
const entry = { keyword, jobs: payload.jobs || [], error: payload.error || null };
const i = data.searches.findIndex((s) => s.keyword === keyword);
if (i >= 0) data.searches[i] = entry; else data.searches.push(entry);
if (payload.error) data.errors = [...new Set([...(data.errors || []), keyword])];
fs.writeFileSync(rawPath, JSON.stringify(data));
