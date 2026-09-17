import fs from 'fs';
import path from 'path';
const DIR = path.dirname(new URL(import.meta.url).pathname);
const rawDir = path.join(DIR, 'mcp_raw');
const keywords = JSON.parse(fs.readFileSync(path.join(DIR, 'keywords.json'), 'utf8')).keywords;
const batch = [];
const errors = [];
for (const kw of keywords) {
  const slug = kw.replace(/[^a-z0-9]+/gi, '_').slice(0, 80);
  const f = path.join(rawDir, `${slug}.json`);
  if (!fs.existsSync(f)) {
    errors.push(kw);
    continue;
  }
  const row = JSON.parse(fs.readFileSync(f, 'utf8'));
  if (row.error) {
    batch.push({ keyword: kw, error: row.error, jobs: [] });
    errors.push(kw);
  } else {
    batch.push({ keyword: kw, jobs: row.jobs });
  }
}
fs.writeFileSync(path.join(DIR, 'search-batch.json'), JSON.stringify(batch));
const meta = {
  keywordsAttempted: keywords.length,
  keywordsCompleted: batch.filter((r) => !r.error).length,
  errors,
};
fs.writeFileSync(path.join(DIR, 'run-meta.json'), JSON.stringify(meta, null, 2));
console.log(JSON.stringify(meta));
