/** Normalize search vs smart_search job shape for build pipeline. */
export function normalizeRawJob(raw) {
  const jt = (raw.job_type || '').toLowerCase();
  let proposal_count = raw.proposal_count;
  if (proposal_count == null && raw.proposals_tier) {
    const tier = String(raw.proposals_tier);
    const map = {
      'less than 5': 2,
      '5 to 10': 7,
      '10 to 15': 12,
      '15 to 20': 17,
      '20 to 50': 35,
      '50+': 55,
    };
    proposal_count = map[tier.toLowerCase()] ?? tier;
  }
  const client = raw.client || {};
  const verification = client.verification_status || client.verificationStatus;
  return {
    ...raw,
    job_type: jt === 'hourly' ? 'hourly' : jt === 'fixed' ? 'fixed' : raw.job_type,
    proposal_count,
    client: {
      ...client,
      verification_status: verification,
    },
  };
}
