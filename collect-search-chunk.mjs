#!/usr/bin/env node
import fs from 'fs';
import path from 'path';
const batchPath = path.join(process.cwd(), 'upwork-intelligence/run-batch.json');
const chunk = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
let batch = { searches: [] };
if (fs.existsSync(batchPath)) batch = JSON.parse(fs.readFileSync(batchPath, 'utf8'));
batch.searches.push(...chunk);
fs.mkdirSync(path.dirname(batchPath), { recursive: true });
fs.writeFileSync(batchPath, JSON.stringify(batch));
console.log('total searches:', batch.searches.length);
