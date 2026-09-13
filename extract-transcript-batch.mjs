#!/usr/bin/env node
/**
 * Extract Upwork find_jobs search results from a cloud agent transcript JSON.
 * Pairs MCP results in transcript order with ALL_SEARCHES keyword order.
 * Usage: node extract-transcript-batch.mjs <transcript.json> [out-batch.json]
 */
import fs from 'fs';
import { ALL_SEARCHES } from './run-all-keywords.mjs';

const transcriptPath = process.argv[2];
const outPath = process.argv[3] || 'upwork-intelligence/run-batch.json';
if (!transcriptPath) {
  console.error('Usage: node extract-transcript-batch.mjs transcript.json [out-batch.json]');
  process.exit(1);
}

const transcript = JSON.parse(fs.readFileSync(transcriptPath, 'utf8'));
const messages = transcript.messages || transcript.turns || transcript.items || [];

const results = [];
for (const m of messages) {
  const v = m.tool_result?.value;
  if (v?.selectedTool !== 'upwork__find_jobs' || !v.result) continue;
  try {
    const parsed = typeof v.result === 'string' ? JSON.parse(v.result) : v.result;
    if (parsed.status === 'error') {
      results.push({ error: parsed.error || parsed.message || 'error', jobs: [] });
    } else {
      results.push({ jobs: parsed.jobs || [], error: null });
    }
  } catch (e) {
    results.push({ jobs: [], error: String(e.message) });
  }
}

const searches = ALL_SEARCHES.map(({ keyword, group }, i) => {
  const r = results[i];
  if (!r) {
    return { keyword, group, status: 'error', jobs: [], error: 'search not run' };
  }
  if (r.error) {
    return { keyword, group, status: 'error', jobs: [], error: r.error };
  }
  return { keyword, group, status: 'ok', jobs: r.jobs };
});

fs.mkdirSync('upwork-intelligence', { recursive: true });
fs.writeFileSync(outPath, JSON.stringify({ searches }, null, 2));
console.log(JSON.stringify({
  outPath,
  total: searches.length,
  mcpResults: results.length,
  withJobs: searches.filter((s) => s.jobs?.length).length,
  errors: searches.filter((s) => s.status === 'error').length,
}));
