#!/usr/bin/env node
/** Append one MCP find_jobs response: node mcp-batch-save.mjs "keyword" "GROUP" /path/to/response.json */
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
  description_snippet: j.description_snippet,
}));
fs.appendFileSync(
  path.join(ROOT, 'run-results.jsonl'),
  JSON.stringify({ keyword, group, jobs }) + '\n'
);
console.log(keyword, jobs.length);
