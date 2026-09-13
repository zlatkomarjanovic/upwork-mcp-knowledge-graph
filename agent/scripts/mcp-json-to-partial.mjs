#!/usr/bin/env node
/** node mcp-json-to-partial.mjs "keyword" "Group" path/to/mcp-response.json */
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const PARTIAL = path.resolve(__dirname, '../partial');

function slug(kw) {
  return kw.toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_|_$/g, '').slice(0, 80);
}

const [keyword, group, respPath] = process.argv.slice(2);
const resp = JSON.parse(fs.readFileSync(respPath, 'utf8'));
const jobs = resp.jobs || [];
fs.mkdirSync(PARTIAL, { recursive: true });
fs.writeFileSync(
  path.join(PARTIAL, `${slug(keyword)}.json`),
  JSON.stringify({ keyword, group, jobs }),
);
console.log(keyword, jobs.length);
