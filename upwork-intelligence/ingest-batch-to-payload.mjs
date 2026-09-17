#!/usr/bin/env node
import fs from 'fs';
import path from 'path';

const dir = path.dirname(new URL(import.meta.url).pathname);
const keywords = JSON.parse(fs.readFileSync(path.join(dir, 'keywords.json'), 'utf8'));
const payloadPath = path.join(dir, '.run-payload.json');

function trimJob(j) {
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
let payload = fs.existsSync(payloadPath)
  ? JSON.parse(fs.readFileSync(payloadPath, 'utf8'))
  : { keywordsAttempted: keywords.length, keywordsCompleted: 0, searches: [] };

const byKw = new Map((payload.searches || []).map((s) => [s.keyword, s]));
for (const entry of batch) {
  const jobs = (entry.jobs || entry.response?.jobs || []).map(trimJob);
  byKw.set(entry.keyword, {
    keyword: entry.keyword,
    jobs,
    error: entry.error,
  });
}

const searches = keywords.map((kw) => {
  const ex = byKw.get(kw);
  if (ex && !ex.error) return ex;
  if (ex?.error) return ex;
  return { keyword: kw, error: 'not_run', jobs: [] };
});
const completed = searches.filter((s) => !s.error).length;
payload = { keywordsAttempted: keywords.length, keywordsCompleted: completed, searches };
fs.writeFileSync(payloadPath, JSON.stringify(payload));
console.log(JSON.stringify({ completed, total: keywords.length }));
