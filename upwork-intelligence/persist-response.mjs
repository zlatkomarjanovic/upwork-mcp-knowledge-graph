#!/usr/bin/env node
/** node persist-response.mjs "keyword" "GROUP" response.json */
import fs from 'fs';
import path from 'path';

const ROOT = path.dirname(new URL(import.meta.url).pathname);
const [, , keyword, group, respPath] = process.argv;
const resp = JSON.parse(fs.readFileSync(respPath, 'utf8'));
const jobs = (resp.jobs || []).map((j) => ({
  url: j.url,
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
  description_snippet: j.description_snippet?.slice?.(0, 200) ?? j.description_snippet,
}));
const out = path.join(ROOT, 'run-results.jsonl');
const seen = new Set();
if (fs.existsSync(out)) {
  for (const line of fs.readFileSync(out, 'utf8').split('\n')) {
    if (!line.trim()) continue;
    seen.add(JSON.parse(line).keyword);
  }
}
if (seen.has(keyword)) {
  console.log('skip duplicate', keyword);
  process.exit(0);
}
fs.appendFileSync(out, JSON.stringify({ keyword, group, jobs }) + '\n');
console.log(keyword, jobs.length);
