#!/usr/bin/env node
import fs from 'fs';
import path from 'path';

const batchPath = process.argv[2] || 'upwork-intelligence/run-batch.json';
const chunkPath = process.argv[3];
if (!chunkPath) {
  console.error('Usage: append-search-results.mjs [batchPath] chunk.json');
  process.exit(1);
}
const chunk = JSON.parse(fs.readFileSync(chunkPath, 'utf8'));
let batch = { searches: [] };
if (fs.existsSync(batchPath)) {
  batch = JSON.parse(fs.readFileSync(batchPath, 'utf8'));
}
batch.searches = batch.searches || [];
batch.searches.push(...(Array.isArray(chunk) ? chunk : [chunk]));
fs.mkdirSync(path.dirname(batchPath), { recursive: true });
fs.writeFileSync(batchPath, JSON.stringify(batch));
console.log('searches:', batch.searches.length);
