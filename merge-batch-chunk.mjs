#!/usr/bin/env node
import fs from 'fs';

const batchPath = process.argv[2];
const chunkPath = process.argv[3];
const batch = JSON.parse(fs.readFileSync(batchPath, 'utf8'));
const chunk = JSON.parse(fs.readFileSync(chunkPath, 'utf8'));
for (const entry of chunk) {
  batch.results.push(entry);
}
batch.keywordsCompleted = batch.results.filter((r) => r.response?.status === 'ok').length;
batch.keywordsAttempted = 93;
fs.writeFileSync(batchPath, JSON.stringify(batch));
