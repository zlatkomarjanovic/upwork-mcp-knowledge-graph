#!/usr/bin/env node
/** node ingest-mcp-batch.mjs batch.json — array of { keyword, group, jobs } or { keyword, group, response } */
import fs from 'fs';
import path from 'path';

const ROOT = path.dirname(new URL(import.meta.url).pathname);
const batch = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
const out = path.join(ROOT, 'run-results.jsonl');
const seen = new Set();
if (fs.existsSync(out)) {
  for (const line of fs.readFileSync(out, 'utf8').split('\n')) {
    if (!line.trim()) continue;
    seen.add(JSON.parse(line).keyword);
  }
}

function stripJob(j) {
  return {
    url: j.url?.split('?')[0],
    title: j.title,
    published_date: j.published_date,
    created_date: j.created_date,
    job_type: j.job_type,
    budget: j.budget,
    duration: j.duration,
    proposal_count: j.proposal_count,
    experience_level: j.experience_level,
    skills: j.skills,
    client: j.client,
    description_snippet: j.description_snippet?.slice?.(0, 120) ?? '',
  };
}

let added = 0;
for (const item of batch) {
  if (seen.has(item.keyword)) continue;
  const jobs = (item.jobs || item.response?.jobs || []).map(stripJob);
  fs.appendFileSync(out, JSON.stringify({ keyword: item.keyword, group: item.group, jobs }) + '\n');
  seen.add(item.keyword);
  added++;
}
console.log(JSON.stringify({ added, total: seen.size }));
