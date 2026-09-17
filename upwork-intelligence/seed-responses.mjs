#!/usr/bin/env node
/** Ensure one mcp-responses line per keyword (empty jobs if missing). */
import fs from 'fs';
import path from 'path';
const dir = path.dirname(new URL(import.meta.url).pathname);
const keywords = JSON.parse(fs.readFileSync(path.join(dir, 'keywords.json'), 'utf8'));
const logPath = path.join(dir, 'mcp-responses.jsonl');
const map = new Map();
if (fs.existsSync(logPath)) {
  for (const line of fs.readFileSync(logPath, 'utf8').split('\n')) {
    if (!line.trim()) continue;
    try {
      const row = JSON.parse(line);
      map.set(row.keyword, row);
    } catch {}
  }
}
const out = fs.createWriteStream(logPath, { flags: 'w' });
for (const { keyword, group } of keywords) {
  const row = map.get(keyword) || { keyword, group, jobs: [], error: null };
  out.write(JSON.stringify(row) + '\n');
}
out.end();
