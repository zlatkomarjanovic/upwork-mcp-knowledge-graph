#!/usr/bin/env node
/**
 * Records keyword search intent and merges MCP batch files from search-batches/*.json
 * Each batch file: [{ keyword, group, response: { jobs: [...] } }]
 */
import fs from 'fs';
import path from 'path';

const ROOT = path.dirname(new URL(import.meta.url).pathname);
const KEYWORDS = JSON.parse(fs.readFileSync(path.join(ROOT, 'keywords.json'), 'utf8'));
const batchDir = path.join(ROOT, 'search-batches');
const out = path.join(ROOT, 'run-results.jsonl');

fs.mkdirSync(batchDir, { recursive: true });

if (process.argv.includes('--clear')) {
  fs.writeFileSync(out, '');
}

const seen = new Set();
if (fs.existsSync(out)) {
  for (const line of fs.readFileSync(out, 'utf8').split('\n')) {
    if (!line.trim()) continue;
    seen.add(JSON.parse(line).keyword);
  }
}

let added = 0;
for (const f of fs.readdirSync(batchDir).filter(x => x.endsWith('.json')).sort()) {
  const batch = JSON.parse(fs.readFileSync(path.join(batchDir, f), 'utf8'));
  for (const item of batch) {
    if (seen.has(item.keyword)) continue;
    const jobs = item.response?.jobs || item.jobs || [];
    fs.appendFileSync(out, JSON.stringify({ keyword: item.keyword, group: item.group, jobs }) + '\n');
    seen.add(item.keyword);
    added++;
  }
}

const missing = KEYWORDS.filter(k => !seen.has(k.keyword)).map(k => k.keyword);
console.log(JSON.stringify({ recorded: seen.size, addedThisRun: added, missing: missing.length, missingKeywords: missing }));
