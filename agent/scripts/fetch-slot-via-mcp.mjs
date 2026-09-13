#!/usr/bin/env node
/**
 * Hourly helper: run title searches for current slot and write agent/partial/*.json
 * Requires agent to invoke Upwork MCP and pipe responses:
 *   node agent/scripts/fetch-slot-via-mcp.mjs --ingest agent/mcp-ingest.json
 *
 * mcp-ingest.json shape: { searches: [{ keyword, group, jobs: [...] }] }
 */
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { keywordsForSlot, slotForHour, ROTATION } from './keywords-config.mjs';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const PARTIAL = path.resolve(__dirname, '../partial');

function slug(kw) {
  return kw.toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_|_$/g, '').slice(0, 80);
}

const ingestPath = process.argv.includes('--ingest')
  ? process.argv[process.argv.indexOf('--ingest') + 1]
  : null;

if (!ingestPath) {
  const slot = slotForHour(new Date().getUTCHours());
  const list = keywordsForSlot(slot);
  console.log(
    JSON.stringify({
      slot,
      groups: ROTATION[slot],
      keywords: list.map((k) => k.keyword),
      hint: 'Run upwork__find_jobs title search per keyword, then --ingest combined JSON',
    }),
  );
  process.exit(0);
}

const data = JSON.parse(fs.readFileSync(ingestPath, 'utf8'));
const items = data.searches || [];
fs.mkdirSync(PARTIAL, { recursive: true });
for (const { keyword, group, jobs } of items) {
  fs.writeFileSync(
    path.join(PARTIAL, `${slug(keyword)}.json`),
    JSON.stringify({ keyword, group, jobs: jobs || [] }),
  );
}
console.log('ingested', items.length, 'searches to', PARTIAL);
