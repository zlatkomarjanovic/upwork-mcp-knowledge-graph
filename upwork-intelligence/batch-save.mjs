import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
const DIR = path.dirname(fileURLToPath(import.meta.url));
const rawDir = path.join(DIR, 'mcp_raw');
fs.mkdirSync(rawDir, { recursive: true });
const items = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
for (const { keyword, response: resp } of items) {
  const jobs = (resp.jobs || []).map(({ description_snippet, ...rest }) => rest);
  const out = {
    keyword,
    error: resp.status === 'error' ? resp.message || resp.error || 'error' : null,
    jobs,
  };
  const slug = keyword.replace(/[^a-z0-9]+/gi, '_').slice(0, 80);
  fs.writeFileSync(path.join(rawDir, `${slug}.json`), JSON.stringify(out));
}
