#!/usr/bin/env node
import fs from 'fs';
import path from 'path';

const chunkPath = process.argv[2];
const batchPath = path.join(process.cwd(), 'upwork-intelligence', 'run-batch.json');
const chunk = JSON.parse(fs.readFileSync(chunkPath, 'utf8'));
let batch = { keywordsAttempted: 93, keywordsCompleted: 0, errors: [], results: [] };
if (fs.existsSync(batchPath)) {
  batch = JSON.parse(fs.readFileSync(batchPath, 'utf8'));
}
const seen = new Set(batch.results.map((r) => r.keyword));
for (const entry of chunk) {
  if (seen.has(entry.keyword)) continue;
  batch.results.push(entry);
  seen.add(entry.keyword);
  if (entry.response?.status === 'error') batch.errors.push(entry.keyword);
}
batch.keywordsCompleted = batch.results.filter((r) => r.response?.status === 'ok').length;
batch.keywordsAttempted = 93;
batch.errors = [...new Set(batch.errors)];
fs.mkdirSync(path.dirname(batchPath), { recursive: true });
fs.writeFileSync(batchPath, JSON.stringify(batch));
console.log(JSON.stringify({ total: batch.results.length, completed: batch.keywordsCompleted }));
