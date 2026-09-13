#!/usr/bin/env node
import fs from 'fs';
import path from 'path';

const batchPath = path.join(process.cwd(), 'upwork-intelligence', 'run-batch.json');
const patchDir = path.join(process.cwd(), 'upwork-intelligence', 'raw-tail');

const batch = JSON.parse(fs.readFileSync(batchPath, 'utf8'));
if (!fs.existsSync(patchDir)) {
  console.error('Missing patch dir:', patchDir);
  process.exit(1);
}

const files = fs.readdirSync(patchDir).filter((f) => f.endsWith('.json'));
const slugToKeyword = new Map(
  files.map((f) => {
    const slug = f.replace(/\.json$/, '');
    const metaPath = path.join(patchDir, `${slug}.meta.json`);
    let keyword = slug.replace(/_/g, ' ');
    if (fs.existsSync(metaPath)) {
      keyword = JSON.parse(fs.readFileSync(metaPath, 'utf8')).keyword;
    }
    return [slug, keyword];
  })
);

for (const file of files) {
  if (file.endsWith('.meta.json')) continue;
  const slug = file.replace(/\.json$/, '');
  const keyword = slugToKeyword.get(slug);
  const response = JSON.parse(fs.readFileSync(path.join(patchDir, file), 'utf8'));
  const idx = batch.results.findIndex((r) => r.keyword === keyword);
  if (idx === -1) {
    console.warn('No batch entry for', keyword);
    continue;
  }
  batch.results[idx].response = response;
}

batch.keywordsCompleted = batch.results.filter((r) => r.response?.status === 'ok').length;
batch.keywordsAttempted = 93;
batch.errors = batch.results
  .filter((r) => r.response?.status === 'error')
  .map((r) => r.keyword);

fs.writeFileSync(batchPath, JSON.stringify(batch));
console.log(
  JSON.stringify({
    keywordsCompleted: batch.keywordsCompleted,
    errors: batch.errors,
  })
);
