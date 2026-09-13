#!/usr/bin/env node
import fs from 'fs';
import { ALL_KEYWORDS } from './run-all-keywords.mjs';

const transcriptPath = process.argv[2];
const outPath = process.argv[3] || 'upwork-intelligence/run-batch.json';

const transcript = JSON.parse(fs.readFileSync(transcriptPath, 'utf8'));
const hits = [];

for (const m of transcript.messages || []) {
  if (m.role !== 'tool' || m.tool_result?.resultType !== 'mcpResult') continue;
  const v = m.tool_result.value;
  if (v?.selectedTool !== 'upwork__find_jobs') continue;
  let response = v.result;
  if (typeof response === 'string') {
    try {
      response = JSON.parse(response);
    } catch {
      continue;
    }
  }
  hits.push(response);
}

const results = [];
const errors = [];

for (let i = 0; i < ALL_KEYWORDS.length; i++) {
  const { keyword, group } = ALL_KEYWORDS[i];
  const response = hits[i];
  if (response?.status === 'ok') {
    results.push({ keyword, group, response });
  } else if (response?.status === 'error') {
    results.push({ keyword, group, response });
    errors.push(keyword);
  } else {
    results.push({
      keyword,
      group,
      response: { status: 'error', message: 'search_not_in_transcript' },
    });
    errors.push(keyword);
  }
}

const batch = {
  keywordsAttempted: ALL_KEYWORDS.length,
  keywordsCompleted: results.filter((r) => r.response?.status === 'ok').length,
  errors: [...new Set(errors)],
  results,
};

fs.mkdirSync('upwork-intelligence', { recursive: true });
fs.writeFileSync(outPath, JSON.stringify(batch));
console.log(
  JSON.stringify({
    mcpHits: hits.length,
    completed: batch.keywordsCompleted,
    attempted: batch.keywordsAttempted,
    missing: ALL_KEYWORDS.length - hits.length,
  })
);
