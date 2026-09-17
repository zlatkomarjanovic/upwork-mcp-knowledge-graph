#!/usr/bin/env node
/** One line per keyword; last write wins. */
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
      map.set(JSON.parse(line).keyword, JSON.parse(line));
    } catch {}
  }
}
const out = keywords.map(({ keyword, group }) => {
  const row = map.get(keyword);
  if (row) return row;
  return { keyword, group, jobs: [], error: 'not_searched' };
});
fs.writeFileSync(logPath, out.map((r) => JSON.stringify(r)).join('\n') + '\n');
console.log('keywords with data:', out.filter((r) => r.jobs?.length && !r.error).length, '/', keywords.length);
