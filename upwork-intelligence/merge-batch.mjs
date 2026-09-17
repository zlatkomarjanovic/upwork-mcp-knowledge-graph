#!/usr/bin/env node
import fs from 'fs';
import path from 'path';
const rawPath = path.join(path.dirname(new URL(import.meta.url).pathname), '.run-raw.json');
const batch = JSON.parse(fs.readFileSync(0, 'utf8'));
const data = JSON.parse(fs.readFileSync(rawPath, 'utf8'));
for (const { keyword, jobs, error } of batch) {
  const entry = { keyword, jobs: jobs || [], error: error || null };
  const i = data.searches.findIndex((s) => s.keyword === keyword);
  if (i >= 0) data.searches[i] = entry;
  else data.searches.push(entry);
  if (error) data.errors = [...new Set([...(data.errors || []), keyword])];
}
fs.writeFileSync(rawPath, JSON.stringify(data));
