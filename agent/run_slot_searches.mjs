#!/usr/bin/env node
/**
 * Run Upwork title searches for current rotation slot via sequential HTTP to MCP proxy.
 * Fallback: merge existing partials only.
 */
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { keywordsForSlot, slotForHour, ROTATION } from './scripts/keywords-config.mjs';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const PARTIAL = path.join(__dirname, 'partial');
const ORG = '1472686528932380673';

function slug(kw) {
  return kw.toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_|_$/g, '').slice(0, 80);
}

function savePartial(keyword, group, jobs) {
  fs.mkdirSync(PARTIAL, { recursive: true });
  const out = path.join(PARTIAL, `${slug(keyword)}.json`);
  fs.writeFileSync(out, JSON.stringify({ keyword, group, jobs: jobs || [] }, null, 2));
}

async function searchTitle(title) {
  const body = {
    action: 'search',
    org_uid: ORG,
    params: { title, sort: 'recency', limit: 10 },
  };
  const url = process.env.UPWORK_MCP_URL;
  if (!url) return null;
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

async function main() {
  const hour = new Date().getUTCHours();
  const slot = slotForHour(hour);
  const list = keywordsForSlot(slot);
  const failures = [];
  let done = 0;

  for (const { keyword, group } of list) {
    const partialPath = path.join(PARTIAL, `${slug(keyword)}.json`);
    if (fs.existsSync(partialPath)) {
      done++;
      continue;
    }
    if (!process.env.UPWORK_MCP_URL) {
      failures.push({ keyword, error: 'no UPWORK_MCP_URL' });
      continue;
    }
    try {
      let data = await searchTitle(keyword);
      if (data?.status === 'error' && /rate/i.test(String(data.message))) {
        await new Promise((r) => setTimeout(r, 6500));
        data = await searchTitle(keyword);
      }
      if (data?.status === 'error') {
        failures.push({ keyword, error: data.message || 'error' });
        continue;
      }
      savePartial(keyword, group, data.jobs || []);
      done++;
      await new Promise((r) => setTimeout(r, 5500));
    } catch (e) {
      failures.push({ keyword, error: String(e.message || e) });
    }
  }

  console.log(JSON.stringify({ slot, groups: ROTATION[slot], done, total: list.length, failures }));
}

main();
