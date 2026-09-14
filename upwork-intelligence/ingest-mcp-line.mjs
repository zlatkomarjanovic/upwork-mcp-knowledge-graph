#!/usr/bin/env node
import fs from 'fs';
import path from 'path';

const ROOT = path.dirname(new URL(import.meta.url).pathname);
const out = path.join(ROOT, 'run-results.jsonl');
const { keyword, group, response } = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
const jobs = (response?.jobs || []).map((j) => ({
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
fs.appendFileSync(out, JSON.stringify({ keyword, group, jobs }) + '\n');
console.log(keyword, jobs.length);
