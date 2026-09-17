#!/usr/bin/env node
/**
 * Runs all keyword searches via Upwork MCP (requires MCP bridge URL in UPWORK_MCP_BRIDGE).
 * Fallback: agent uses CallDynamicTool and ingest-batch-to-payload.mjs per batch.
 */
import fs from 'fs';
import path from 'path';
import { paramsForKeyword } from './keyword-params.mjs';

const ORG = '1472686528932380673';
const bridge = process.env.UPWORK_MCP_BRIDGE;
const dir = path.dirname(new URL(import.meta.url).pathname);
const keywords = JSON.parse(fs.readFileSync(path.join(dir, 'keywords.json'), 'utf8'));

async function findJobs(params) {
  if (!bridge) throw new Error('UPWORK_MCP_BRIDGE not set');
  const res = await fetch(bridge, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({
      action: 'search',
      org_uid: ORG,
      params,
    }),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

async function main() {
  const out = [];
  const errors = [];
  for (const kw of keywords) {
    const params = paramsForKeyword(kw);
    try {
      const data = await findJobs(params);
      out.push({ keyword: kw, jobs: data.jobs || [] });
      process.stderr.write(`${kw}: ${(data.jobs || []).length}\n`);
    } catch (e) {
      errors.push(kw);
      out.push({ keyword: kw, error: String(e.message || e), jobs: [] });
    }
  }
  fs.writeFileSync(path.join(dir, '.run-payload.json'), JSON.stringify({
    keywordsAttempted: keywords.length,
    keywordsCompleted: out.filter((x) => !x.error).length,
    searches: out,
  }));
  console.log(JSON.stringify({ completed: out.length - errors.length, errors }));
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
