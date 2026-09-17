#!/usr/bin/env node
import fs from 'fs';
import path from 'path';

const dir = path.dirname(new URL(import.meta.url).pathname);
const batchDir = path.join(dir, 'raw_batches');
fs.mkdirSync(batchDir, { recursive: true });

function trimJob(j) {
  if (!j) return j;
  return {
    url: j.url,
    title: j.title,
    job_type: j.job_type,
    budget: j.budget,
    published_date: j.published_date,
    created_date: j.created_date,
    proposal_count: j.proposal_count,
    proposals_tier: j.proposals_tier,
    duration: j.duration,
    experience_level: j.experience_level,
    skills: j.skills,
    client: j.client,
    description_snippet: j.description_snippet,
  };
}

const batch = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
const out = batch.map((entry) => ({
  keyword: entry.keyword,
  error: entry.error,
  jobs: (entry.jobs || []).map(trimJob),
}));
const name = process.argv[3] || `batch-${Date.now()}.json`;
fs.writeFileSync(path.join(batchDir, name), JSON.stringify(out));
console.log(path.join(batchDir, name), out.length);
