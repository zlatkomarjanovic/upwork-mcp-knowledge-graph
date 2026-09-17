#!/usr/bin/env node
import fs from 'fs';
import path from 'path';
const dir = path.dirname(new URL(import.meta.url).pathname);
const log = path.join(dir, 'mcp-responses.jsonl');
const batch = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
const slim = (jobs) =>
  (jobs || []).map((j) => ({
    url: j.url,
    title: j.title,
    published_date: j.published_date,
    created_date: j.created_date,
    job_type: j.job_type,
    budget: j.budget,
    duration: j.duration,
    proposals_tier: j.proposals_tier,
    proposals_count: j.proposals_count,
    experience_level: j.experience_level,
    skills: j.skills,
    client: j.client,
    description_snippet: j.description_snippet,
  }));
for (const b of batch) {
  fs.appendFileSync(
    log,
    JSON.stringify({
      keyword: b.keyword,
      group: b.group,
      jobs: slim(b.jobs),
      error: b.error || null,
    }) + '\n'
  );
}
console.log('ingested', batch.length);
