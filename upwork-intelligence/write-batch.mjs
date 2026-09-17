#!/usr/bin/env node
import fs from 'fs';
import path from 'path';
const dir = path.dirname(new URL(import.meta.url).pathname);
const batchDir = path.join(dir, 'raw_batches');
fs.mkdirSync(batchDir, { recursive: true });
const name = process.argv[2] || `batch-${Date.now()}.json`;
const data = JSON.parse(fs.readFileSync(0, 'utf8'));
fs.writeFileSync(path.join(batchDir, name), JSON.stringify(data));
console.log(path.join(batchDir, name));
