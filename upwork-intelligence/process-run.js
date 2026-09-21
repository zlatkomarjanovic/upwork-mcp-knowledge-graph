#!/usr/bin/env node
/**
 * One-time processor: reads raw search batch JSON from stdin, updates intelligence files.
 * Invoked by automation after MCP searches complete.
 */
const fs = require('fs');
const path = require('path');

const DIR = path.join(__dirname);
const WINDOW_MS_FIRST = 2 * 60 * 60 * 1000;
const WINDOW_MS = 60 * 60 * 1000;

const KEYWORD_GROUPS = {
  'web development': 'CORE WEB DEVELOPMENT',
  'website development': 'CORE WEB DEVELOPMENT',
  'web developer': 'CORE WEB DEVELOPMENT',
  'custom website': 'CORE WEB DEVELOPMENT',
  'frontend developer': 'CORE WEB DEVELOPMENT',
  'full stack developer': 'CORE WEB DEVELOPMENT',
  'web design': 'WEB DESIGN',
  'website design': 'WEB DESIGN',
  'website redesign': 'WEB DESIGN',
  'landing page design': 'WEB DESIGN',
  'UI UX website': 'WEB DESIGN',
  'responsive web design': 'WEB DESIGN',
  wordpress: 'WORDPRESS',
  'wordpress developer': 'WORDPRESS',
  'wordpress website': 'WORDPRESS',
  'wordpress development': 'WORDPRESS',
  'wordpress redesign': 'WORDPRESS',
  'wordpress customization': 'WORDPRESS',
  'wordpress migration': 'WORDPRESS',
  'wordpress speed optimization': 'WORDPRESS',
  'wordpress maintenance': 'WORDPRESS',
  woocommerce: 'WORDPRESS',
  'elementor developer': 'WORDPRESS',
  'bricks builder': 'WORDPRESS',
  webflow: 'WEBFLOW / FRAMER',
  'webflow developer': 'WEBFLOW / FRAMER',
  'webflow website': 'WEBFLOW / FRAMER',
  'webflow redesign': 'WEBFLOW / FRAMER',
  'figma to webflow': 'WEBFLOW / FRAMER',
  framer: 'WEBFLOW / FRAMER',
  'framer developer': 'WEBFLOW / FRAMER',
  'framer website': 'WEBFLOW / FRAMER',
  'framer redesign': 'WEBFLOW / FRAMER',
  'figma to framer': 'WEBFLOW / FRAMER',
  'AI web development': 'AI / VIBE CODING',
  'AI web developer': 'AI / VIBE CODING',
  'vibe coding': 'AI / VIBE CODING',
  'claude code developer': 'AI / VIBE CODING',
  'cursor AI developer': 'AI / VIBE CODING',
  'lovable developer': 'AI / VIBE CODING',
  'lovable app': 'AI / VIBE CODING',
  'bolt developer': 'AI / VIBE CODING',
  'bolt.new': 'AI / VIBE CODING',
  'v0 developer': 'AI / VIBE CODING',
  'v0 vercel': 'AI / VIBE CODING',
  'replit developer': 'AI / VIBE CODING',
  'supabase developer': 'AI / VIBE CODING',
  'AI agent integration website': 'AI / VIBE CODING',
  gohighlevel: 'GOHIGHLEVEL',
  'go high level': 'GOHIGHLEVEL',
  GHL: 'GOHIGHLEVEL',
  'gohighlevel developer': 'GOHIGHLEVEL',
  'gohighlevel website': 'GOHIGHLEVEL',
  'gohighlevel funnel': 'GOHIGHLEVEL',
  'gohighlevel automation': 'GOHIGHLEVEL',
  'gohighlevel CRM': 'GOHIGHLEVEL',
  'squarespace website': 'ADJACENT PLATFORMS',
  'wix website': 'ADJACENT PLATFORMS',
  'wix studio': 'ADJACENT PLATFORMS',
  'bubble developer': 'ADJACENT PLATFORMS',
  'nextjs developer': 'MODERN STACK',
  'next.js developer': 'MODERN STACK',
  'nextjs website': 'MODERN STACK',
  'react developer': 'MODERN STACK',
  'figma to nextjs': 'MODERN STACK',
  'tailwind developer': 'MODERN STACK',
  'astro developer': 'MODERN STACK',
  'sanity CMS': 'MODERN STACK',
  'ecommerce website': 'ECOMMERCE',
  'ecommerce developer': 'ECOMMERCE',
  'shopify developer': 'ECOMMERCE',
  'shopify website': 'ECOMMERCE',
  'woocommerce developer': 'ECOMMERCE',
  shopware: 'ECOMMERCE',
  'shopware developer': 'ECOMMERCE',
  'shopware 6': 'ECOMMERCE',
  'headless ecommerce': 'ECOMMERCE',
  'website maintenance': 'MAINTENANCE / RETAINERS',
  'website maintenance monthly': 'MAINTENANCE / RETAINERS',
  'website support ongoing': 'MAINTENANCE / RETAINERS',
  'website management ongoing': 'MAINTENANCE / RETAINERS',
  'wordpress support retainer': 'MAINTENANCE / RETAINERS',
  'webflow maintenance': 'MAINTENANCE / RETAINERS',
  'shopify maintenance': 'MAINTENANCE / RETAINERS',
  'ongoing web developer': 'MAINTENANCE / RETAINERS',
  'web development retainer': 'MAINTENANCE / RETAINERS',
  'conversion rate optimization': 'CONVERSION / PERFORMANCE',
  'landing page optimization': 'CONVERSION / PERFORMANCE',
  'website audit': 'CONVERSION / PERFORMANCE',
  'core web vitals': 'CONVERSION / PERFORMANCE',
  'page speed optimization': 'CONVERSION / PERFORMANCE',
  'website speed optimization': 'CONVERSION / PERFORMANCE',
  'technical SEO website': 'CONVERSION / PERFORMANCE',
};

const SKIP_RE =
  /\b(crypto\s*trading|bitcoin\s*trading|forex\s*trading|gambling|casino|betting|adult\s*content|escort|dating\s*app|alcohol\s*brand)\b/i;

const PLATFORM_MAP = [
  ['WordPress', /\bwordpress\b/i],
  ['Webflow', /\bwebflow\b/i],
  ['Framer', /\bframer\b/i],
  ['GoHighLevel', /\b(gohighlevel|go high level|ghl|highlevel)\b/i],
  ['Shopify', /\bshopify\b/i],
  ['WooCommerce', /\bwoocommerce\b/i],
  ['Shopware', /\bshopware\b/i],
  ['Lovable', /\blovable\b/i],
  ['Bolt', /\b(bolt\.new|bolt developer)\b/i],
  ['v0', /\bv0\b/i],
  ['Next.js', /\b(next\.?js|nextjs)\b/i],
];

function readJson(p, fallback) {
  try {
    return JSON.parse(fs.readFileSync(p, 'utf8'));
  } catch {
    return fallback;
  }
}

function readJsonl(p) {
  if (!fs.existsSync(p)) return [];
  return fs
    .readFileSync(p, 'utf8')
    .split('\n')
    .filter(Boolean)
    .map((l) => JSON.parse(l));
}

function appendJsonl(p, obj) {
  fs.appendFileSync(p, JSON.stringify(obj) + '\n');
}

function normalizeUrl(url) {
  if (!url) return null;
  return url.split('?')[0];
}

function tierMid(tier) {
  if (!tier) return null;
  if (tier === 'Fewer than 5') return 2;
  if (tier === '5 to 10') return 7;
  if (tier === '10 to 15') return 12;
  if (tier === '15 to 20') return 17;
  if (tier === '20 to 50') return 35;
  if (tier === '50+') return 55;
  const n = parseInt(tier, 10);
  return Number.isFinite(n) ? n : null;
}

function parseBudget(budget, jobType) {
  if (!budget) return { fixed: null, hourly: null };
  const s = String(budget).replace(/,/g, '');
  if (jobType === 'hourly' || s.includes('/hr') || s.includes('hr')) {
    const m = s.match(/([\d.]+)\s*[–-]\s*([\d.]+)/);
    if (m) return { fixed: null, hourly: (parseFloat(m[1]) + parseFloat(m[2])) / 2 };
    const m2 = s.match(/([\d.]+)/);
    return { fixed: null, hourly: m2 ? parseFloat(m2[1]) : null };
  }
  const m = s.match(/([\d.]+)/);
  return { fixed: m ? parseFloat(m[1]) : null, hourly: null };
}

function isHighBudget(job) {
  const { fixed, hourly } = parseBudget(job.budget, job.job_type);
  if (job.job_type === 'fixed' && fixed != null) return fixed >= 1000;
  if (job.job_type === 'hourly' && hourly != null) return hourly >= 40;
  if (fixed != null && fixed >= 1000) return true;
  if (hourly != null && hourly >= 40) return true;
  return false;
}

function confidenceLabel(n) {
  if (n <= 4) return 'Very Low';
  if (n <= 14) return 'Low';
  if (n <= 39) return 'Medium';
  if (n <= 99) return 'High';
  return 'Very High';
}

function median(arr) {
  const a = arr.filter((x) => x != null).sort((x, y) => x - y);
  if (!a.length) return null;
  const mid = Math.floor(a.length / 2);
  return a.length % 2 ? a[mid] : (a[mid - 1] + a[mid]) / 2;
}

function avg(arr) {
  const a = arr.filter((x) => x != null);
  if (!a.length) return null;
  return a.reduce((s, x) => s + x, 0) / a.length;
}

function opportunityScore(jobs) {
  if (!jobs.length) return 1;
  const now = Date.now();
  let score = 0;
  for (const j of jobs) {
    const ageH = (now - new Date(j.postedAt).getTime()) / 3600000;
    const recency = Math.max(0, 24 - ageH) / 24;
    const { fixed, hourly } = parseBudget(j.budget, j.type);
    const pay = fixed != null ? Math.min(fixed / 2000, 1) : hourly != null ? Math.min(hourly / 80, 1) : 0.2;
    const prop = j.proposals != null ? Math.max(0, 1 - j.proposals / 50) : 0.5;
    const verified = j.paymentVerified ? 1 : 0.3;
    const high = isHighBudget({ budget: j.budget, job_type: j.type }) ? 1 : 0;
    score += recency * 30 + pay * 25 + prop * 25 + verified * 10 + high * 10;
  }
  return Math.min(100, Math.max(1, Math.round(score / jobs.length)));
}

function jobFromRaw(raw, keyword, group) {
  const url = normalizeUrl(raw.url);
  if (!url) return null;
  const title = raw.title || '';
  const desc = raw.description_snippet || '';
  if (SKIP_RE.test(title + ' ' + desc)) return null;
  const client = raw.client || {};
  return {
    url,
    title,
    matchedKeyword: [keyword],
    keywordGroup: group,
    postedAt: raw.published_date || raw.created_date || null,
    type: raw.job_type || null,
    budget: raw.budget || null,
    duration: raw.duration || null,
    proposals: raw.proposals_tier ? tierMid(raw.proposals_tier) : raw.proposal_count ?? null,
    proposalsTier: raw.proposals_tier || null,
    clientCountry: client.country || null,
    paymentVerified: client.verification_status === 'VERIFIED',
    clientSpend: client.total_spent || null,
    clientHireRate: null,
    clientRating: client.rating ?? null,
    experienceLevel: raw.experience_level || null,
    skills: raw.skills || [],
  };
}

function detectPlatforms(text) {
  const found = [];
  for (const [name, re] of PLATFORM_MAP) {
    if (re.test(text)) found.push(name);
  }
  return found;
}

const input = JSON.parse(fs.readFileSync(0, 'utf8'));
const { searchResults, runStartedAt, errors = [] } = input;
const statePath = path.join(DIR, 'state.json');
const state = readJson(statePath, { runNumber: 0, totalJobs: 0, knownJobUrls: [] });
const isFirstRun = state.runNumber === 0;
const windowMs = isFirstRun ? WINDOW_MS_FIRST : WINDOW_MS;
const cutoff = new Date(runStartedAt).getTime() - windowMs;

const known = new Set((state.knownJobUrls || []).map(normalizeUrl));
const existingJobs = readJsonl(path.join(DIR, 'jobs.jsonl'));
const byUrl = new Map();
for (const j of existingJobs) {
  byUrl.set(j.url, j);
}

const newThisRun = [];
let keywordsAttempted = 0;
let keywordsCompleted = 0;

for (const { keyword, response } of searchResults) {
  keywordsAttempted++;
  if (!response || response.status === 'error') continue;
  keywordsCompleted++;
  const group = KEYWORD_GROUPS[keyword] || 'OTHER';
  const jobs = response.jobs || [];
  for (const raw of jobs) {
    const posted = raw.published_date || raw.created_date;
    if (posted && new Date(posted).getTime() < cutoff) continue;
    const job = jobFromRaw(raw, keyword, group);
    if (!job) continue;
    const prev = byUrl.get(job.url);
    if (prev) {
      const mk = new Set([...(prev.matchedKeyword || []), keyword]);
      prev.matchedKeyword = [...mk];
      if (!known.has(job.url)) {
        /* merged existing from window */
      }
    } else {
      byUrl.set(job.url, job);
      if (!known.has(job.url)) {
        newThisRun.push(job);
        known.add(job.url);
      }
    }
  }
}

for (const j of newThisRun) {
  appendJsonl(path.join(DIR, 'jobs.jsonl'), j);
}

const allJobs = [...byUrl.values()];
const now = Date.now();
const jobs24h = allJobs.filter((j) => j.postedAt && now - new Date(j.postedAt).getTime() <= 24 * 3600000);

const keywordStats = {};
for (const kw of Object.keys(KEYWORD_GROUPS)) {
  const matched = allJobs.filter((j) => (j.matchedKeyword || []).includes(kw));
  const m24 = matched.filter((j) => j.postedAt && now - new Date(j.postedAt).getTime() <= 24 * 3600000);
  const fixed = matched.map((j) => parseBudget(j.budget, j.type).fixed).filter((x) => x != null);
  const hourly = matched.map((j) => parseBudget(j.budget, j.type).hourly).filter((x) => x != null);
  const props = matched.map((j) => j.proposals).filter((x) => x != null);
  const verified = matched.filter((j) => j.paymentVerified).length;
  const highB = matched.filter((j) => isHighBudget({ budget: j.budget, job_type: j.type })).length;
  const spend = matched
    .map((j) => {
      if (!j.clientSpend) return null;
      const n = parseFloat(String(j.clientSpend).replace(/[^0-9.]/g, ''));
      return Number.isFinite(n) ? n : null;
    })
    .filter((x) => x != null);
  keywordStats[kw] = {
    totalJobs: matched.length,
    jobsLast24h: m24.length,
    avgBudgetFixed: avg(fixed),
    avgRateHourly: avg(hourly),
    medianProposals: median(props),
    pctVerified: matched.length ? Math.round((verified / matched.length) * 100) : 0,
    avgClientSpend: avg(spend),
    pctHighBudget: matched.length ? Math.round((highB / matched.length) * 100) : 0,
    opportunityScore: opportunityScore(matched),
    sampleConfidence: confidenceLabel(matched.length),
  };
}

const groupStats = {};
for (const group of new Set(Object.values(KEYWORD_GROUPS))) {
  const matched = allJobs.filter((j) => j.keywordGroup === group);
  groupStats[group] = {
    totalJobs: matched.length,
    jobsLast24h: matched.filter((j) => j.postedAt && now - new Date(j.postedAt).getTime() <= 24 * 3600000).length,
    opportunityScore: opportunityScore(matched),
    sampleConfidence: confidenceLabel(matched.length),
  };
}

const platformStats = {};
for (const [platform] of PLATFORM_MAP) {
  const matched = allJobs.filter((j) => {
    const text = `${j.title} ${(j.skills || []).join(' ')} ${(j.matchedKeyword || []).join(' ')}`;
    return detectPlatforms(text).includes(platform);
  });
  platformStats[platform] = {
    jobs: matched.length,
    avgBudgetFixed: avg(matched.map((j) => parseBudget(j.budget, j.type).fixed).filter((x) => x != null)),
    avgRateHourly: avg(matched.map((j) => parseBudget(j.budget, j.type).hourly).filter((x) => x != null)),
    medianProposals: median(matched.map((j) => j.proposals)),
    opportunityScore: opportunityScore(matched),
    sampleConfidence: confidenceLabel(matched.length),
  };
}

const runNumber = (state.runNumber || 0) + 1;
const top3Keywords = Object.entries(keywordStats)
  .sort((a, b) => b[1].opportunityScore - a[1].opportunityScore)
  .slice(0, 3)
  .map(([k]) => k);

appendJsonl(path.join(DIR, 'run-log.jsonl'), {
  timestamp: runStartedAt,
  runNumber,
  keywordsAttempted,
  keywordsCompleted,
  newJobs: newThisRun.length,
  totalJobs: allJobs.length,
  top3Keywords,
  errors,
});

fs.writeFileSync(
  path.join(DIR, 'state.json'),
  JSON.stringify(
    {
      lastRunAt: runStartedAt,
      runNumber,
      totalJobs: allJobs.length,
      knownJobUrls: [...known],
      lastInsightRefresh: state.lastInsightRefresh || null,
    },
    null,
    2
  )
);

fs.writeFileSync(path.join(DIR, 'keyword-stats.json'), JSON.stringify(keywordStats, null, 2));
fs.writeFileSync(path.join(DIR, 'group-stats.json'), JSON.stringify(groupStats, null, 2));
fs.writeFileSync(path.join(DIR, 'platform-stats.json'), JSON.stringify(platformStats, null, 2));

const top10 = Object.entries(keywordStats)
  .sort((a, b) => b[1].opportunityScore - a[1].opportunityScore)
  .slice(0, 10);

const topGroups = Object.entries(groupStats).sort((a, b) => b[1].opportunityScore - a[1].opportunityScore);

const primary = top10[0]?.[0] || 'web development';
const secondary = top10[1]?.[0] || 'wordpress developer';
const bestPlatform = Object.entries(platformStats).sort((a, b) => b[1].opportunityScore - a[1].opportunityScore)[0]?.[0] || 'WordPress';

const summary = `# Upwork Market Intelligence

Last updated: ${runStartedAt}
Run: ${runNumber}
Total jobs tracked: ${allJobs.length}
Keywords attempted: ${keywordsAttempted}
Keywords completed: ${keywordsCompleted}

## Top Opportunities

${top10
  .map(
    ([k, s]) =>
      `- **${k}** — score ${s.opportunityScore}, jobs24h ${s.jobsLast24h}, total ${s.totalJobs}, avg fixed ${s.avgBudgetFixed != null ? '$' + Math.round(s.avgBudgetFixed) : 'n/a'}, avg hourly ${s.avgRateHourly != null ? '$' + Math.round(s.avgRateHourly) + '/hr' : 'n/a'}, median proposals ${s.medianProposals ?? 'n/a'}, confidence ${s.sampleConfidence}`
  )
  .join('\n')}

## Strongest Groups

${topGroups.map(([g, s], i) => `${i + 1}. ${g} — score ${s.opportunityScore}, jobs24h ${s.jobsLast24h}, total ${s.totalJobs}`).join('\n')}

## Platform Ranking

${Object.entries(platformStats)
  .sort((a, b) => b[1].opportunityScore - a[1].opportunityScore)
  .map(([p, s], i) => `${i + 1}. ${p} — jobs ${s.jobs}, score ${s.opportunityScore}`)
  .join('\n')}

## Positioning Recommendation

Primary keyword: ${primary}
Secondary keyword: ${secondary}
Best platform/service: ${bestPlatform}
Overview keywords: ${top10
  .slice(0, 5)
  .map(([k]) => k)
  .join(', ')}
Skill tags: WordPress, Webflow, Next.js, Shopify, Elementor, Figma, SEO

## Current Verdicts

WordPress: Steady volume in CMS and Elementor builds; mixed budgets.
Webflow: Lower volume than WordPress; agency-style design/dev posts appear.
Framer: Niche; fewer dedicated posts than Webflow.
GoHighLevel: CRM/automation posts; website builder mentions appear in agency work.
AI/Vibe Coding: Growing AI website builder and Claude artifact-to-WordPress demand.
Ecommerce: Shopify theme and store setup remain active.
Maintenance: Retainer keywords need more sample depth on first run.

## Important Changes

${isFirstRun ? 'Initial baseline run — no prior comparison.' : 'See run log for deltas.'}
`;

fs.writeFileSync(path.join(DIR, 'current-summary.md'), summary);

if (isFirstRun) {
  fs.writeFileSync(
    path.join(DIR, 'insights.md'),
    `# Upwork Intelligence Insights

- Baseline established ${runStartedAt}. Hourly tracking active across ${keywordsAttempted} keywords.
- WordPress and Shopify show the broadest cross-keyword overlap in the first window.
- AI website builder posts (Claude artifacts, AI builders) appear alongside traditional WordPress work.
`
  );
}

const report = {
  runNumber,
  keywordsAttempted,
  keywordsCompleted,
  newJobs: newThisRun.length,
  totalJobs: allJobs.length,
  top10,
  topGroups: topGroups.slice(0, 5),
  platformStats,
  newThisRun,
  errors,
  primary,
  secondary,
  bestPlatform,
};
console.log(JSON.stringify(report, null, 2));
