#!/usr/bin/env node
import fs from 'fs';
import { KEYWORD_GROUPS } from './run-all-keywords.mjs';

const transcriptPath = process.argv[2];
if (!transcriptPath) {
  console.error('Usage: extract-mcp-from-transcript.mjs <transcript.json>');
  process.exit(1);
}

const flat = Object.entries(KEYWORD_GROUPS).flatMap(([group, kws]) =>
  kws.map((keyword) => ({ keyword, group }))
);
const keywordSet = new Set(flat.map((k) => k.keyword));

const raw = JSON.parse(fs.readFileSync(transcriptPath, 'utf8'));
const messages = raw.messages || raw;

const byKeyword = new Map();

function walk(node) {
  if (!node) return;
  if (Array.isArray(node)) {
    for (const x of node) walk(x);
    return;
  }
  if (typeof node !== 'object') return;

  if (node.selectedTool === 'upwork__find_jobs' && node.arguments) {
    let args = node.arguments;
    if (typeof args === 'string') {
      try {
        args = JSON.parse(args);
      } catch {
        /* ignore */
      }
    }
    const query = args?.params?.query || args?.params?.title;
    if (query && keywordSet.has(query) && node.result) {
      let result = node.result;
      if (typeof result === 'string') {
        try {
          result = JSON.parse(result);
        } catch {
          /* ignore */
        }
      }
      if (result?.status === 'ok' || result?.jobs) {
        byKeyword.set(query, result);
      }
    }
  }

  for (const v of Object.values(node)) walk(v);
}

walk(messages);

// Also walk tool_result blocks in transcript format
function walkMessages(msgs) {
  for (const m of msgs) {
    if (m.role === 'assistant' && Array.isArray(m.content)) {
      for (const block of m.content) {
        if (block.type === 'tool_use' && block.name === 'upwork__find_jobs') {
          const query = block.input?.params?.query;
          // result may be in following tool_result message
        }
      }
    }
    if (m.toolResults) {
      for (const tr of m.toolResults) {
        if (tr.toolName === 'upwork__find_jobs' || tr.name === 'upwork__find_jobs') {
          const query = tr.arguments?.params?.query || tr.input?.params?.query;
          const result = tr.result || tr.content;
          if (query && keywordSet.has(query)) {
            let parsed = result;
            if (typeof parsed === 'string') {
              try {
                parsed = JSON.parse(parsed);
              } catch {
                continue;
              }
            }
            if (parsed?.status === 'ok' || parsed?.jobs) byKeyword.set(query, parsed);
          }
        }
      }
    }
    if (Array.isArray(m.children)) walkMessages(m.children);
  }
}

if (Array.isArray(messages)) walkMessages(messages);

const results = [];
const errors = [];
for (const { keyword, group } of flat) {
  const response = byKeyword.get(keyword);
  if (response) {
    results.push({ keyword, group, response });
  } else {
    results.push({
      keyword,
      group,
      response: { status: 'error', message: 'no_mcp_result_in_transcript' },
    });
    errors.push(keyword);
  }
}

const batch = {
  keywordsAttempted: flat.length,
  keywordsCompleted: results.filter((r) => r.response?.status === 'ok').length,
  errors: [...new Set(errors)],
  results,
};

const out = process.argv[3] || 'upwork-intelligence/run-batch.json';
fs.mkdirSync('upwork-intelligence', { recursive: true });
fs.writeFileSync(out, JSON.stringify(batch));
console.log(
  JSON.stringify({
    extracted: byKeyword.size,
    completed: batch.keywordsCompleted,
    attempted: batch.keywordsAttempted,
    out,
  })
);
