import fs from 'fs';
import path from 'path';
const DIR = path.dirname(new URL(import.meta.url).pathname);
const rawDir = path.join(DIR, 'mcp_raw');
fs.mkdirSync(rawDir, { recursive: true });
const keyword = process.argv[2];
const resp = JSON.parse(process.argv[3]);
const slug = keyword.replace(/[^a-z0-9]+/gi, '_').slice(0, 80);
const jobs = (resp.jobs || []).map(({ description_snippet, ...rest }) => rest);
const out = {
  keyword,
  error: resp.status === 'error' ? resp.message || resp.error || 'error' : null,
  jobs,
};
fs.writeFileSync(path.join(rawDir, `${slug}.json`), JSON.stringify(out));
