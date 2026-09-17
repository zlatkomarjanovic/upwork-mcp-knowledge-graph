#!/usr/bin/env node
/**
 * Process raw search batches into jobs.jsonl, stats, state, summary.
 * Input: upwork-intelligence/raw-batches.json (array of {keyword, group, jobs, error?})
 */
import fs from 'fs';
import path from 'path';

const DIR = path.dirname(new URL(import.meta.url).pathname);
const RAW = path.join(DIR, 'raw-batches.json');
const STATE_PATH = path.join(DIR, 'state.json');
const JOBS_PATH = path.join(DIR, 'jobs.jsonl');
const RUN_LOG = path.join(DIR, 'run-log.jsonl');

const SKIP_TITLE_RE = /\b(crypto|betting|casino|gambl|adult|dating|onlyfans|porn|escort|alcohol|liquor|distillery)\b/i;

function normUrl(u) {
  if (!u) return null;
  try {
    const url = new URL(u.split('?')[0]);
    return url.origin + url.pathname;
  } catch {
    return u.split('?')[0];
  }
}

function parseMoney(s) {
  if (!s || typeof s !== 'string') return null;
  const m = s.replace(/,/g, '').match(/([\d.]+)/);
  return m ? parseFloat(m[1]) : null;
}

function parseHourlyMid(budget) {
  if (!budget || typeof budget !== 'string') return null;
  const nums = budget.replace(/,/g, '').match(/[\d.]+/g);
  if (!nums?.length) return null;
  if (nums.length >= 2) return (parseFloat(nums[0]) + parseFloat(nums[1])) / 2;
  return parseFloat(nums[0]);
}

function tierMid(tier) {
  const map = {
    'Fewer than 5': 2,
    '5 to 10': 7,
    '10 to 15': 12,
    '15 to 20': 17,
    '20 to 50': 35,
    '50+': 55,
  };
  return tier ? map[tier] ?? null : null;
}

function parseSpend(s) {
  if (!s) return null;
  const m = String(s).replace(/,/g, '').match(/([\d.]+)/);
  return m ? parseFloat(m[1]) : null;
}

function jobFromRaw(j, keyword, group) {
  const url = normUrl(j.url);
  if (!url) return null;
  if (SKIP_TITLE_RE.test(j.title || '') || SKIP_TITLE_RE.test(j.description_snippet || '')) return null;
  const client = j.client || {};
  return {
    url,
    title: j.title,
    matchedKeyword: [keyword],
    keywordGroup: group,
    postedAt: j.published_date || j.created_date || null,
    type: j.job_type || null,
    budget: j.budget ?? null,
    duration: j.duration ?? null,
    proposals: j.proposals_count ?? j.proposals_tier ?? null,
    proposalsMid: j.proposals_count ?? tierMid(j.proposals_tier),
    clientCountry: client.country ?? null,
    paymentVerified: client.verification_status === 'VERIFIED',
    clientSpend: client.total_spent ?? null,
    clientSpendNum: parseSpend(client.total_spent),
    clientHireRate: null,
    clientRating: client.rating ?? null,
    experienceLevel: j.experience_level ?? null,
    skills: j.skills ?? [],
  };
}

function loadState() {
  if (fs.existsSync(STATE_PATH)) return JSON.parse(fs.readFileSync(STATE_PATH, 'utf8'));
  return { lastRunAt: null, runNumber: 0, totalJobs: 0, knownJobUrls: [], lastInsightRefresh: null };
}

function loadJobsIndex(urls) {
  const set = new Set(urls);
  if (fs.existsSync(JOBS_PATH)) {
    for (const line of fs.readFileSync(JOBS_PATH, 'utf8').split('\n')) {
      if (!line.trim()) continue;
      try {
        const o = JSON.parse(line);
        if (o.url) set.add(o.url);
      } catch {}
    }
  }
  return set;
}

function confidence(n) {
  if (n >= 100) return 'Very High';
  if (n >= 40) return 'High';
  if (n >= 15) return 'Medium';
  if (n >= 5) return 'Low';
  return 'Very Low';
}

function median(arr) {
  const a = arr.filter((x) => x != null && !Number.isNaN(x)).sort((x, y) => x - y);
  if (!a.length) return null;
  const i = Math.floor(a.length / 2);
  return a.length % 2 ? a[i] : (a[i - 1] + a[i]) / 2;
}

function avg(arr) {
  const a = arr.filter((x) => x != null && !Number.isNaN(x));
  return a.length ? a.reduce((s, x) => s + x, 0) / a.length : null;
}

function isHighBudget(job) {
  if (job.type === 'fixed') {
    const n = parseMoney(job.budget);
    return n != null && n >= 1000;
  }
  if (job.type === 'hourly') {
    const n = parseHourlyMid(job.budget);
    return n != null && n >= 40;
  }
  return false;
}

function opportunityScore(kwJobs) {
  if (!kwJobs.length) return 1;
  const now = Date.now();
  let score = 0;
  for (const j of kwJobs) {
    const posted = j.postedAt ? new Date(j.postedAt).getTime() : now;
    const ageH = (now - posted) / 3600000;
    const recency = Math.max(0, 48 - ageH) / 48;
    let pay = 0.3;
    if (j.type === 'fixed') {
      const n = parseMoney(j.budget);
      if (n != null) pay = Math.min(1, n / 5000);
    } else if (j.type === 'hourly') {
      const n = parseHourlyMid(j.budget);
      if (n != null) pay = Math.min(1, n / 80);
    }
    const prop = j.proposalsMid != null ? Math.max(0, 1 - j.proposalsMid / 50) : 0.5;
    const ver = j.paymentVerified ? 0.15 : 0;
    const hb = isHighBudget(j) ? 0.2 : 0;
    score += recency * 0.35 + pay * 0.35 + prop * 0.25 + ver + hb;
  }
  return Math.min(100, Math.max(1, Math.round((score / kwJobs.length) * 40)));
}

const PLATFORM_MAP = {
  WordPress: ['WORDPRESS'],
  Webflow: ['WEBFLOW / FRAMER'],
  Framer: ['WEBFLOW / FRAMER'],
  GoHighLevel: ['GOHIGHLEVEL'],
  Shopify: ['ECOMMERCE'],
  WooCommerce: ['WORDPRESS', 'ECOMMERCE'],
  Shopware: ['ECOMMERCE'],
  Lovable: ['AI / VIBE CODING'],
  Bolt: ['AI / VIBE CODING'],
  v0: ['AI / VIBE CODING'],
  'Next.js': ['MODERN STACK'],
};

function platformJobs(allJobs, platform) {
  const groups = PLATFORM_MAP[platform] || [];
  const kws = {
    WordPress: /wordpress/i,
    Webflow: /webflow/i,
    Framer: /framer/i,
    GoHighLevel: /gohighlevel|go high level|\bghl\b/i,
    Shopify: /shopify/i,
    WooCommerce: /woocommerce/i,
    Shopware: /shopware/i,
    Lovable: /lovable/i,
    Bolt: /bolt\.new|bolt developer/i,
    v0: /\bv0\b|v0 vercel/i,
    'Next.js': /next\.?js/i,
  };
  const re = kws[platform];
  if (!re) return [];
  return allJobs.filter((j) => j.matchedKeyword.some((k) => re.test(k)) || (j.skills || []).some((s) => re.test(s)));
}

function main() {
  const batches = JSON.parse(fs.readFileSync(RAW, 'utf8'));
  const state = loadState();
  const runNumber = (state.runNumber || 0) + 1;
  const windowStart = new Date(Date.now() - (state.runNumber === 0 ? 2 : 1) * 3600000);

  const known = loadJobsIndex(state.knownJobUrls || []);
  const merged = new Map();

  let keywordsAttempted = batches.length;
  let keywordsCompleted = 0;
  const errors = [];

  for (const batch of batches) {
    if (batch.error) {
      errors.push(batch.keyword);
      continue;
    }
    keywordsCompleted++;
    for (const j of batch.jobs || []) {
      const posted = j.published_date || j.created_date;
      if (posted && new Date(posted) < windowStart) continue;
      const rec = jobFromRaw(j, batch.keyword, batch.group);
      if (!rec) continue;
      const existing = merged.get(rec.url);
      if (existing) {
        if (!existing.matchedKeyword.includes(batch.keyword)) existing.matchedKeyword.push(batch.keyword);
      } else merged.set(rec.url, rec);
    }
  }

  const newJobs = [];
  for (const [url, job] of merged) {
    if (!known.has(url)) {
      newJobs.push(job);
      known.add(url);
    }
  }

  if (newJobs.length) {
    fs.appendFileSync(JOBS_PATH, newJobs.map((j) => JSON.stringify(j)).join('\n') + '\n');
  }

  const allJobs = [];
  if (fs.existsSync(JOBS_PATH)) {
    for (const line of fs.readFileSync(JOBS_PATH, 'utf8').split('\n')) {
      if (!line.trim()) continue;
      try {
        allJobs.push(JSON.parse(line));
      } catch {}
    }
  }

  const now = Date.now();
  const d24 = now - 24 * 3600000;

  const keywordStats = {};
  for (const batch of batches) {
    if (batch.error) continue;
    const kw = batch.keyword;
    const kwJobs = allJobs.filter((j) => j.matchedKeyword?.includes(kw));
    const j24 = kwJobs.filter((j) => j.postedAt && new Date(j.postedAt).getTime() >= d24);
    const fixed = kwJobs.filter((j) => j.type === 'fixed').map((j) => parseMoney(j.budget)).filter((x) => x != null);
    const hourly = kwJobs.filter((j) => j.type === 'hourly').map((j) => parseHourlyMid(j.budget)).filter((x) => x != null);
    const props = kwJobs.map((j) => j.proposalsMid).filter((x) => x != null);
    const verified = kwJobs.filter((j) => j.paymentVerified).length;
    const spend = kwJobs.map((j) => j.clientSpendNum).filter((x) => x != null);
    const highB = kwJobs.filter(isHighBudget).length;
    keywordStats[kw] = {
      totalJobs: kwJobs.length,
      jobsLast24h: j24.length,
      avgBudgetFixed: avg(fixed),
      avgRateHourly: avg(hourly),
      medianProposals: median(props),
      pctVerified: kwJobs.length ? Math.round((verified / kwJobs.length) * 100) : 0,
      avgClientSpend: avg(spend),
      pctHighBudget: kwJobs.length ? Math.round((highB / kwJobs.length) * 100) : 0,
      opportunityScore: opportunityScore(j24.length ? j24 : kwJobs.slice(0, 10)),
      sampleConfidence: confidence(kwJobs.length),
      group: batch.group,
    };
  }

  const groupStats = {};
  for (const [kw, st] of Object.entries(keywordStats)) {
    const g = st.group;
    if (!groupStats[g]) groupStats[g] = { keywords: 0, totalJobs: 0, jobsLast24h: 0, scores: [] };
    groupStats[g].keywords++;
    groupStats[g].totalJobs += st.totalJobs;
    groupStats[g].jobsLast24h += st.jobsLast24h;
    groupStats[g].scores.push(st.opportunityScore);
  }
  for (const g of Object.keys(groupStats)) {
    groupStats[g].avgOpportunityScore = Math.round(avg(groupStats[g].scores) || 0);
    delete groupStats[g].scores;
  }

  const platformStats = {};
  for (const p of Object.keys(PLATFORM_MAP)) {
    const pj = platformJobs(allJobs, p);
    const j24 = pj.filter((j) => j.postedAt && new Date(j.postedAt).getTime() >= d24);
    const fixed = pj.filter((j) => j.type === 'fixed').map((j) => parseMoney(j.budget)).filter((x) => x != null);
    const hourly = pj.filter((j) => j.type === 'hourly').map((j) => parseHourlyMid(j.budget)).filter((x) => x != null);
    const props = pj.map((j) => j.proposalsMid).filter((x) => x != null);
    platformStats[p] = {
      jobs: pj.length,
      jobsLast24h: j24.length,
      avgBudgetFixed: avg(fixed),
      avgRateHourly: avg(hourly),
      medianProposals: median(props),
      opportunityScore: opportunityScore(j24.length ? j24 : pj.slice(0, 15)),
      sampleConfidence: confidence(pj.length),
    };
  }

  fs.writeFileSync(path.join(DIR, 'keyword-stats.json'), JSON.stringify(keywordStats, null, 2));
  fs.writeFileSync(path.join(DIR, 'group-stats.json'), JSON.stringify(groupStats, null, 2));
  fs.writeFileSync(path.join(DIR, 'platform-stats.json'), JSON.stringify(platformStats, null, 2));

  const top3 = Object.entries(keywordStats)
    .sort((a, b) => b[1].jobsLast24h - a[1].jobsLast24h || b[1].opportunityScore - a[1].opportunityScore)
    .slice(0, 3)
    .map(([k]) => k);

  const runRec = {
    timestamp: new Date().toISOString(),
    runNumber,
    keywordsAttempted,
    keywordsCompleted,
    newJobs: newJobs.length,
    totalJobs: allJobs.length,
    top3Keywords: top3,
    errors,
  };
  fs.appendFileSync(RUN_LOG, JSON.stringify(runRec) + '\n');

  const newState = {
    lastRunAt: runRec.timestamp,
    runNumber,
    totalJobs: allJobs.length,
    knownJobUrls: [...known].slice(-5000),
    lastInsightRefresh: state.lastInsightRefresh,
  };
  fs.writeFileSync(STATE_PATH, JSON.stringify(newState, null, 2));

  const top10 = Object.entries(keywordStats)
    .sort((a, b) => b[1].opportunityScore - a[1].opportunityScore || b[1].jobsLast24h - a[1].jobsLast24h)
    .slice(0, 10);

  const topGroups = Object.entries(groupStats).sort((a, b) => b[1].jobsLast24h - a[1].jobsLast24h).slice(0, 5);

  const primary = top10[0]?.[0] || 'wordpress developer';
  const secondary = top10[1]?.[0] || 'webflow developer';

  const summary = `# Upwork Market Intelligence

Last updated: ${runRec.timestamp}
Run: ${runNumber}
Total jobs tracked: ${allJobs.length}
Keywords attempted: ${keywordsAttempted}
Keywords completed: ${keywordsCompleted}

## Top Opportunities

${top10
  .map(
    ([k, s]) => `- **${k}** — score ${s.opportunityScore}, ${s.jobsLast24h} jobs (24h), ${s.totalJobs} total, avg fixed $${s.avgBudgetFixed?.toFixed(0) ?? 'n/a'}, avg hourly $${s.avgRateHourly?.toFixed(0) ?? 'n/a'}/hr, median proposals ${s.medianProposals ?? 'n/a'}, ${s.sampleConfidence} confidence`
  )
  .join('\n')}

## Strongest Groups

${topGroups.map(([g, s], i) => `${i + 1}. ${g} — ${s.jobsLast24h} jobs (24h), avg score ${s.avgOpportunityScore}`).join('\n')}

## Platform Ranking

${Object.entries(platformStats)
  .sort((a, b) => b[1].jobsLast24h - a[1].jobsLast24h)
  .map(([p, s], i) => `${i + 1}. ${p} — ${s.jobsLast24h} jobs (24h), score ${s.opportunityScore}`)
  .join('\n')}

## Positioning Recommendation

Primary keyword: ${primary}
Secondary keyword: ${secondary}
Best platform/service: WordPress + Elementor (volume) / Webflow (premium builds)
Overview keywords: ${top10.slice(0, 5).map(([k]) => k).join(', ')}
Skill tags: WordPress, Elementor, Webflow, Next.js, WooCommerce, Figma, SEO, Page Speed

## Current Verdicts

WordPress: Steady hourly + fixed volume; Elementor and maintenance posts common.
Webflow: Lower title-match volume than WordPress; design-led homepage work appears.
Framer: Sparse in title searches; monitor via query in future runs.
GoHighLevel: Funnel/landing page demand tied to marketing clients.
AI/Vibe Coding: Next.js + Supabase stacks show up in full-stack searches more than vibe keywords.
Ecommerce: Shopify ad-hoc updates and WooCommerce builds both active.
Maintenance: Wix/WordPress ongoing support posts continue.

## Important Changes

First baseline run — no prior comparison.
`;

  fs.writeFileSync(path.join(DIR, 'current-summary.md'), summary);

  console.log(JSON.stringify({ runRec, newJobsCount: newJobs.length, top10: top10.map(([k, s]) => ({ k, ...s })) }));
}

main();
