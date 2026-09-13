#!/usr/bin/env node
import fs from 'fs';
import path from 'path';

const batchPath = process.argv[2];
const keyword = process.argv[3];
const group = process.argv[4];
const responsePath = process.argv[5];

if (!batchPath || !keyword || !group || !responsePath) {
  console.error('Usage: append-search-results.mjs <batch.json> <keyword> <group> <response.json>');
  process.exit(1);
}

const response = JSON.parse(fs.readFileSync(responsePath, 'utf8'));
let batch = { keywordsAttempted: 93, keywordsCompleted: 0, errors: [], results: [] };
if (fs.existsSync(batchPath)) {
  batch = JSON.parse(fs.readFileSync(batchPath, 'utf8'));
}
batch.results.push({ keyword, group, response });
if (response.status === 'error') {
  batch.errors.push(keyword);
} else {
  batch.keywordsCompleted = batch.results.filter((r) => r.response?.status === 'ok').length;
}
fs.mkdirSync(path.dirname(batchPath), { recursive: true });
fs.writeFileSync(batchPath, JSON.stringify(batch, null, 2));
