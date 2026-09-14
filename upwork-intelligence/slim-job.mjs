export function slimJob(j) {
  return {
    url: j.url,
    title: j.title,
    job_type: j.job_type,
    budget: j.budget ?? null,
    published_date: j.published_date,
    created_date: j.created_date,
    proposal_count: j.proposal_count ?? null,
    client: j.client,
    skills: j.skills,
    description_snippet: j.description_snippet,
    experience_level: j.experience_level,
    duration: j.duration,
  };
}

export function entryFromMcp(keyword, resp) {
  if (resp.status && resp.status !== 'ok') {
    return { keyword, error: resp.status, jobs: [] };
  }
  if (resp.error) {
    return { keyword, error: String(resp.error), jobs: [] };
  }
  const jobs = (resp.jobs || []).map(slimJob);
  return { keyword, jobs };
}
