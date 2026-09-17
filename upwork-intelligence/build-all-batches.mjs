#!/usr/bin/env node
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
const chunkPath = path.join(dir, 'chunk-001.json');
if (fs.existsSync(chunkPath)) {
  for (const row of JSON.parse(fs.readFileSync(chunkPath, 'utf8'))) {
    map.set(row.keyword, { keyword: row.keyword, group: row.group, jobs: row.jobs || [], error: null });
  }
}
const batches = keywords.map(({ keyword, group }) => {
  const row = map.get(keyword);
  if (row) return { keyword, group, jobs: row.jobs || [], error: row.error || null };
  return { keyword, group, jobs: [], error: 'not_searched' };
});
fs.writeFileSync(path.join(dir, 'raw-batches.json'), JSON.stringify(batches));
console.log('logged', [...map.keys()].filter((k) => map.get(k)?.jobs?.length).length, 'with jobs');
