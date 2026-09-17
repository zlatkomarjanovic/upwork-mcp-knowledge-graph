#!/usr/bin/env node
/**
 * Sequential Upwork search runner for hourly automation.
 * Requires UPWORK_MCP_JSONL: path to append {keyword, group, response} lines from MCP calls.
 * This script merges keywords.json + responses into raw-batches.json then runs process-run.mjs.
 */
import fs from 'fs';
import path from 'path';
import { spawnSync } from 'child_process';

const DIR = path.dirname(new URL(import.meta.url).pathname);
const KEYWORDS = JSON.parse(fs.readFileSync(path.join(DIR, 'keywords.json'), 'utf8'));
const MCP_LOG = process.env.UPWORK_MCP_JSONL || path.join(DIR, 'mcp-responses.jsonl');
const RAW = path.join(DIR, 'raw-batches.json');

const byKeyword = new Map(KEYWORDS.map((k) => [k.keyword, { ...k, jobs: [], error: null }]));

if (fs.existsSync(MCP_LOG)) {
  for (const line of fs.readFileSync(MCP_LOG, 'utf8').split('\n')) {
    if (!line.trim()) continue;
    try {
      const row = JSON.parse(line);
      const entry = byKeyword.get(row.keyword);
      if (!entry) continue;
      if (row.error) entry.error = row.error;
      else if (row.jobs) entry.jobs = row.jobs;
    } catch {}
  }
}

const batches = KEYWORDS.map(({ keyword, group }) => {
  const e = byKeyword.get(keyword);
  return { keyword, group, jobs: e?.jobs || [], error: e?.error || null };
});

fs.writeFileSync(RAW, JSON.stringify(batches, null, 2));

const proc = spawnSync('node', [path.join(DIR, 'process-run.mjs')], { stdio: 'inherit' });
process.exit(proc.status ?? 0);
