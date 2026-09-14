import fs from 'fs';
const jobs = JSON.parse(fs.readFileSync(0, 'utf8'));
const out = jobs.map(j => ({
  id: j.id,
  url: j.url,
  title: j.title,
  job_type: j.job_type,
  budget: j.budget,
  duration: j.duration,
  engagement: j.engagement,
  experience_level: j.experience_level,
  proposal_count: j.proposal_count,
  published_date: j.published_date,
  created_date: j.created_date,
  description_snippet: j.description_snippet,
  skills: j.skills,
  client: j.client ? {
    country: j.client.country,
    rating: j.client.rating,
    total_spent: j.client.total_spent,
    verification_status: j.client.verification_status,
    total_posted_jobs: j.client.total_posted_jobs,
    total_reviews: j.client.total_reviews,
  } : undefined,
}));
