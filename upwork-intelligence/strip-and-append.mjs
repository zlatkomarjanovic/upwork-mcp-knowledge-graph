#!/usr/bin/env node
import fs from 'fs';
import path from 'path';

const ROOT = path.dirname(new URL(import.meta.url).pathname);
const out = path.join(ROOT, 'run-results.jsonl');

function stripJob(j) {
  return {
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
  };
}

const items = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
for (const item of items) {
  const jobs = (item.jobs || item.response?.jobs || []).map(stripJob);
  fs.appendFileSync(out, JSON.stringify({ keyword: item.keyword, group: item.group, jobs }) + '\n');
}
console.log('appended', items.length);
