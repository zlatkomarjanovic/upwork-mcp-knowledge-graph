#!/usr/bin/env node
/** Run via automation: append {keyword,jobs} to .run-raw.json from MCP search results passed on stdin as NDJSON lines. */
import fs from 'fs';
import path from 'path';
import readline from 'readline';

const DIR = path.dirname(new URL(import.meta.url).pathname);
const rawPath = path.join(DIR, '.run-raw.json');

function load() {
  try {
    return JSON.parse(fs.readFileSync(rawPath, 'utf8'));
  } catch {
    return { searches: [], errors: [] };
  }
}

const rl = readline.createInterface({ input: process.stdin });
for await (const line of rl) {
  if (!line.trim()) continue;
  const row = JSON.parse(line);
  const data = load();
  const idx = data.searches.findIndex((s) => s.keyword === row.keyword);
  const entry = { keyword: row.keyword, jobs: row.jobs || [], error: row.error || null };
  if (idx >= 0) data.searches[idx] = entry;
  else data.searches.push(entry);
  if (row.error) data.errors = [...new Set([...(data.errors || []), row.keyword])];
  fs.writeFileSync(rawPath, JSON.stringify(data));
}
