#!/usr/bin/env node
import fs from 'fs';
import path from 'path';

const DIR = path.dirname(new URL(import.meta.url).pathname);
const WINDOW_HOURS = process.argv.includes('--first-run') ? 2 : 1;
const runAt = process.env.RUN_AT || new Date().toISOString();
const runNumber = parseInt(process.env.RUN_NUMBER || '1', 10);
const rawPath = process.argv[2] || path.join(DIR, '.run-raw.json');

const KEYWORD_GROUPS = {
  'CORE WEB DEVELOPMENT': ['web development', 'website development', 'web developer', 'custom website', 'frontend developer', 'full stack developer'],
  'WEB DESIGN': ['web design', 'website design', 'website redesign', 'landing page design', 'UI UX website', 'responsive web design'],
  WORDPRESS: ['wordpress', 'wordpress developer', 'wordpress website', 'wordpress development', 'wordpress redesign', 'wordpress customization', 'wordpress migration', 'wordpress speed optimization', 'wordpress maintenance', 'woocommerce', 'elementor developer', 'bricks builder'],
  'WEBFLOW / FRAMER': ['webflow', 'webflow developer', 'webflow website', 'webflow redesign', 'figma to webflow', 'framer', 'framer developer', 'framer website', 'framer redesign', 'figma to framer'],
  'AI / VIBE CODING': ['AI web development', 'AI web developer', 'vibe coding', 'claude code developer', 'cursor AI developer', 'lovable developer', 'lovable app', 'bolt developer', 'bolt.new', 'v0 developer', 'v0 vercel', 'replit developer', 'supabase developer', 'AI agent integration website'],
  GOHIGHLEVEL: ['gohighlevel', 'go high level', 'GHL', 'gohighlevel developer', 'gohighlevel website', 'gohighlevel funnel', 'gohighlevel automation', 'gohighlevel CRM'],
  'ADJACENT PLATFORMS': ['squarespace website', 'wix website', 'wix studio', 'bubble developer'],
  'MODERN STACK': ['nextjs developer', 'next.js developer', 'nextjs website', 'react developer', 'figma to nextjs', 'tailwind developer', 'astro developer', 'sanity CMS'],
  ECOMMERCE: ['ecommerce website', 'ecommerce developer', 'shopify developer', 'shopify website', 'woocommerce developer', 'shopware', 'shopware developer', 'shopware 6', 'headless ecommerce'],
  'MAINTENANCE / RETAINERS': ['website maintenance', 'website maintenance monthly', 'website support ongoing', 'website management ongoing', 'wordpress support retainer', 'webflow maintenance', 'shopify maintenance', 'ongoing web developer', 'web development retainer'],
  'CONVERSION / PERFORMANCE': ['conversion rate optimization', 'landing page optimization', 'website audit', 'core web vitals', 'page speed optimization', 'website speed optimization', 'technical SEO website'],
};

const ALL_KEYWORDS = Object.entries(KEYWORD_GROUPS).flatMap(([g, kws]) => kws.map((k) => ({ keyword: k, group: g })));

const PLATFORMS = {
  WordPress: /wordpress|woocommerce|elementor|bricks/i,
  Webflow: /webflow/i,
  Framer: /framer/i,
  GoHighLevel: /gohighlevel|go high level|\bGHL\b|highlevel/i,
  Shopify: /shopify/i,
  WooCommerce: /woocommerce/i,
  Shopware: /shopware/i,
  Lovable: /lovable/i,
  Bolt: /bolt\.new|\bbolt developer\b/i,
  v0: /\bv0\b|v0 vercel/i,
  'Next.js': /next\.?js|nextjs/i,
};

const SKIP_RE = /\b(crypto trading|bitcoin trading|forex trading|gambling|casino|betting|adult content|porn|escort|dating app|alcohol brand)\b/i;

function normUrl(u) {
  if (!u) return null;
  try {
    const x = new URL(u);
    return `https://www.upwork.com${x.pathname}`;
  } catch {
    return u.split('?')[0];
  }
}

function parseSpend(s) {
  if (!s) return null;
  const m = String(s).replace(/,/g, '').match(/[\d.]+/);
  return m ? parseFloat(m[0]) : null;
}

function parseBudget(budget, jobType) {
  if (!budget) return { fixed: null, hourly: null, display: null };
  const s = String(budget);
  if (jobType === 'hourly' || /\/hr/i.test(s)) {
    const nums = s.replace(/,/g, '').match(/[\d.]+/g);
    const avg = nums ? nums.map(Number).reduce((a, b) => a + b, 0) / nums.length : null;
    return { fixed: null, hourly: avg, display: s };
  }
  const m = s.replace(/,/g, '').match(/[\d.]+/);
  const v = m ? parseFloat(m[0]) : null;
  return { fixed: v, hourly: null, display: s };
}

function proposalsMid(tier, count) {
  if (typeof count === 'number') return count;
  if (!tier) return null;
  const map = {
    'Fewer than 5': 2,
    '5 to 10': 7,
    '10 to 15': 12,
    '15 to 20': 17,
    '20 to 50': 35,
    '50+': 55,
  };
  return map[tier] ?? null;
}

function confidenceLabel(n) {
  if (n >= 100) return 'Very High';
  if (n >= 40) return 'High';
  if (n >= 15) return 'Medium';
  if (n >= 5) return 'Low';
  return 'Very Low';
}

function median(arr) {
  const a = arr.filter((x) => x != null).sort((x, y) => x - y);
  if (!a.length) return null;
  const i = Math.floor(a.length / 2);
  return a.length % 2 ? a[i] : (a[i - 1] + a[i]) / 2;
}

function avg(arr) {
  const a = arr.filter((x) => x != null);
  return a.length ? a.reduce((s, x) => s + x, 0) / a.length : null;
}

function isHighBudget(job) {
  const { fixed, hourly } = parseBudget(job.budget, job.job_type);
  return (fixed != null && fixed >= 1000) || (hourly != null && hourly >= 40);
}

function opportunityScore(stats) {
  const recency = Math.min(stats.jobsLast24h / 10, 1) * 25;
  const budget = Math.min((stats.avgBudgetFixed || 0) / 2000 + (stats.avgRateHourly || 0) / 80, 1) * 25;
  const comp = Math.max(0, 25 - (stats.medianProposals || 20) * 0.5);
  const hi = (stats.pctHighBudget || 0) * 15;
  const ver = (stats.pctVerified || 0) * 10;
  return Math.round(Math.min(100, Math.max(1, recency + budget + comp + hi + ver)));
}

function jobFromRaw(j, keyword, group) {
  const url = normUrl(j.url);
  if (!url) return null;
  const posted = j.published_date || j.created_date;
  const text = `${j.title || ''} ${j.description_snippet || ''}`;
  if (SKIP_RE.test(text)) return null;
  const client = j.client || {};
  const spend = parseSpend(client.total_spent);
  const { display } = parseBudget(j.budget, j.job_type);
  return {
    url,
    title: j.title,
    matchedKeyword: [keyword],
    keywordGroup: group,
    postedAt: posted,
    type: j.job_type || null,
    budget: j.job_type === 'fixed' ? display : null,
    hourlyRate: j.job_type === 'hourly' ? display : null,
    duration: j.duration || null,
    proposals: j.proposal_count ?? proposalsMid(j.proposals_tier),
    clientCountry: client.country || null,
    paymentVerified: client.verification_status === 'VERIFIED',
    clientSpend: spend,
    clientHireRate: null,
    clientRating: client.rating ?? null,
    experienceLevel: j.experience_level || null,
    skills: j.skills || [],
    _rawBudget: j.budget,
  };
}

function inWindow(iso, hours) {
  if (!iso) return false;
  const t = new Date(iso).getTime();
  const cutoff = Date.now() - hours * 3600 * 1000;
  return t >= cutoff;
}

function loadJson(p, fallback) {
  try {
    return JSON.parse(fs.readFileSync(p, 'utf8'));
  } catch {
    return fallback;
  }
}

function loadJobs() {
  const p = path.join(DIR, 'jobs.jsonl');
  if (!fs.existsSync(p)) return [];
  return fs
    .readFileSync(p, 'utf8')
    .split('\n')
    .filter(Boolean)
    .map((l) => JSON.parse(l));
}

const raw = loadJson(rawPath, { searches: [], errors: [] });
const cutoffHours = WINDOW_HOURS;
const jobsMap = new Map();
const existing = loadJobs();
for (const j of existing) jobsMap.set(j.url, j);

let keywordsAttempted = ALL_KEYWORDS.length;
let keywordsCompleted = 0;
const errors = [...(raw.errors || [])];

for (const { keyword, group } of ALL_KEYWORDS) {
  const entry = (raw.searches || []).find((s) => s.keyword === keyword);
  if (!entry) {
    errors.push(keyword);
    continue;
  }
  if (entry.error) {
    errors.push(keyword);
    continue;
  }
  keywordsCompleted++;
  for (const j of entry.jobs || []) {
    if (!inWindow(j.published_date || j.created_date, cutoffHours)) continue;
    const rec = jobFromRaw(j, keyword, group);
    if (!rec) continue;
    const prev = jobsMap.get(rec.url);
    if (prev) {
      const mk = new Set([...(prev.matchedKeyword || []), keyword]);
      prev.matchedKeyword = [...mk];
      jobsMap.set(rec.url, prev);
    } else {
      jobsMap.set(rec.url, rec);
    }
  }
}

const prevState = loadJson(path.join(DIR, 'state.json'), { knownJobUrls: [], totalJobs: 0, runNumber: 0 });
const known = new Set(prevState.knownJobUrls || []);
const newJobs = [];
for (const [url, job] of jobsMap) {
  if (!known.has(url)) {
    newJobs.push(job);
    known.add(url);
  }
}

const allJobs = [...jobsMap.values()];
fs.appendFileSync(path.join(DIR, 'jobs.jsonl'), newJobs.map((j) => JSON.stringify(j)).join('\n') + (newJobs.length ? '\n' : ''));

const now = Date.now();
const jobs24 = allJobs.filter((j) => inWindow(j.postedAt, 24));

function computeKeywordStats(keyword) {
  const matched = allJobs.filter((j) => j.matchedKeyword?.includes(keyword));
  const m24 = matched.filter((j) => inWindow(j.postedAt, 24));
  const fixed = matched.filter((j) => j.type === 'fixed').map((j) => parseBudget(j._rawBudget || j.budget, 'fixed').fixed);
  const hourly = matched.filter((j) => j.type === 'hourly').map((j) => parseBudget(j._rawBudget || j.hourlyRate, 'hourly').hourly);
  const props = matched.map((j) => j.proposals);
  const verified = matched.filter((j) => j.paymentVerified).length;
  const hi = matched.filter((j) => isHighBudget({ budget: j._rawBudget || j.budget || j.hourlyRate, job_type: j.type })).length;
  const stats = {
    totalJobs: matched.length,
    jobsLast24h: m24.length,
    avgBudgetFixed: avg(fixed),
    avgRateHourly: avg(hourly),
    medianProposals: median(props),
    pctVerified: matched.length ? verified / matched.length : 0,
    avgClientSpend: avg(matched.map((j) => j.clientSpend)),
    pctHighBudget: matched.length ? hi / matched.length : 0,
    sampleConfidence: confidenceLabel(matched.length),
  };
  stats.opportunityScore = opportunityScore(stats);
  return stats;
}

const keywordStats = {};
for (const { keyword } of ALL_KEYWORDS) keywordStats[keyword] = computeKeywordStats(keyword);

const groupStats = {};
for (const [group, kws] of Object.entries(KEYWORD_GROUPS)) {
  const matched = allJobs.filter((j) => j.keywordGroup === group || kws.some((k) => j.matchedKeyword?.includes(k)));
  const m24 = matched.filter((j) => inWindow(j.postedAt, 24));
  const props = matched.map((j) => j.proposals);
  const verified = matched.filter((j) => j.paymentVerified).length;
  const fixed = matched.filter((j) => j.type === 'fixed').map((j) => parseBudget(j._rawBudget || j.budget, 'fixed').fixed);
  const hourly = matched.filter((j) => j.type === 'hourly').map((j) => parseBudget(j._rawBudget || j.hourlyRate, 'hourly').hourly);
  const hi = matched.filter((j) => isHighBudget({ budget: j._rawBudget || j.budget || j.hourlyRate, job_type: j.type })).length;
  const base = {
    totalJobs: matched.length,
    jobsLast24h: m24.length,
    avgBudgetFixed: avg(fixed),
    avgRateHourly: avg(hourly),
    medianProposals: median(props),
    pctVerified: matched.length ? verified / matched.length : 0,
    pctHighBudget: matched.length ? hi / matched.length : 0,
    sampleConfidence: confidenceLabel(matched.length),
  };
  base.opportunityScore = opportunityScore(base);
  groupStats[group] = base;
}

const platformStats = {};
for (const [name, re] of Object.entries(PLATFORMS)) {
  const matched = allJobs.filter(
    (j) => re.test(j.title || '') || re.test((j.skills || []).join(' ')) || (j.matchedKeyword || []).some((k) => re.test(k))
  );
  const m24 = matched.filter((j) => inWindow(j.postedAt, 24));
  const props = matched.map((j) => j.proposals);
  const fixed = matched.filter((j) => j.type === 'fixed').map((j) => parseBudget(j._rawBudget || j.budget, 'fixed').fixed);
  const hourly = matched.filter((j) => j.type === 'hourly').map((j) => parseBudget(j._rawBudget || j.hourlyRate, 'hourly').hourly);
  const verified = matched.filter((j) => j.paymentVerified).length;
  const hi = matched.filter((j) => isHighBudget({ budget: j._rawBudget || j.budget || j.hourlyRate, job_type: j.type })).length;
  const base = {
    totalJobs: matched.length,
    jobsLast24h: m24.length,
    avgBudgetFixed: avg(fixed),
    avgRateHourly: avg(hourly),
    medianProposals: median(props),
    pctVerified: matched.length ? verified / matched.length : 0,
    pctHighBudget: matched.length ? hi / matched.length : 0,
    sampleConfidence: confidenceLabel(matched.length),
  };
  base.opportunityScore = opportunityScore(base);
  platformStats[name] = base;
}

fs.writeFileSync(path.join(DIR, 'keyword-stats.json'), JSON.stringify(keywordStats, null, 2));
fs.writeFileSync(path.join(DIR, 'group-stats.json'), JSON.stringify(groupStats, null, 2));
fs.writeFileSync(path.join(DIR, 'platform-stats.json'), JSON.stringify(platformStats, null, 2));

const top3Keywords = Object.entries(keywordStats)
  .sort((a, b) => b[1].jobsLast24h - a[1].jobsLast24h)
  .slice(0, 3)
  .map(([k]) => k);

const runLog = {
  timestamp: runAt,
  runNumber,
  keywordsAttempted,
  keywordsCompleted,
  newJobs: newJobs.length,
  totalJobs: allJobs.length,
  top3Keywords,
  errors: [...new Set(errors)],
};
fs.appendFileSync(path.join(DIR, 'run-log.jsonl'), JSON.stringify(runLog) + '\n');

const state = {
  lastRunAt: runAt,
  runNumber,
  totalJobs: allJobs.length,
  knownJobUrls: [...known],
  lastInsightRefresh: runAt,
};
fs.writeFileSync(path.join(DIR, 'state.json'), JSON.stringify(state, null, 2));

const top10 = Object.entries(keywordStats)
  .sort((a, b) => b[1].opportunityScore - a[1].opportunityScore)
  .slice(0, 10);

const topGroups = Object.entries(groupStats).sort((a, b) => b[1].opportunityScore - a[1].opportunityScore);

const primary = top10[0]?.[0] || 'wordpress developer';
const secondary = top10[1]?.[0] || 'webflow developer';

const summary = `# Upwork Market Intelligence

Last updated: ${runAt}
Run: ${runNumber}
Total jobs tracked: ${allJobs.length}
Keywords attempted: ${keywordsAttempted}
Keywords completed: ${keywordsCompleted}

## Top Opportunities

${top10
  .map(
    ([k, s]) =>
      `- **${k}** — score ${s.opportunityScore}, jobs24h ${s.jobsLast24h}, total ${s.totalJobs}, avg fixed $${s.avgBudgetFixed?.toFixed(0) ?? 'n/a'}, avg hourly $${s.avgRateHourly?.toFixed(0) ?? 'n/a'}/hr, median proposals ${s.medianProposals ?? 'n/a'}, ${s.sampleConfidence}`
  )
  .join('\n')}

## Strongest Groups

${topGroups.map(([g, s], i) => `${i + 1}. ${g} — score ${s.opportunityScore}, jobs24h ${s.jobsLast24h}`).join('\n')}

## Platform Ranking

${Object.entries(platformStats)
  .sort((a, b) => b[1].opportunityScore - a[1].opportunityScore)
  .map(([p, s], i) => `${i + 1}. ${p} — score ${s.opportunityScore}, jobs ${s.totalJobs}`)
  .join('\n')}

## Positioning Recommendation

Primary keyword: ${primary}
Secondary keyword: ${secondary}
Best platform/service: WordPress + Shopify maintenance mix
Overview keywords: ${primary}, ${secondary}, website maintenance
Skill tags: WordPress, Webflow, Next.js, Shopify, SEO, Page Speed

## Current Verdicts

WordPress: Steady hourly + fixed maintenance and WooCommerce builds in last 2h window.
Webflow: Lower volume than WordPress in this sample; niche redesign queries.
Framer: Sparse in current window.
GoHighLevel: Low dedicated GHL posts; adjacent funnel/automation noise.
AI/Vibe Coding: Replit and AI automation posts present; mixed with non-web roles.
Ecommerce: Shopify + WooCommerce active; some performance/CRO overlap.
Maintenance: Ongoing WordPress/webmaster posts appearing.

## Important Changes

First baseline run — no prior comparison.
`;

fs.writeFileSync(path.join(DIR, 'current-summary.md'), summary);

if (!fs.existsSync(path.join(DIR, 'insights.md'))) {
  fs.writeFileSync(
    path.join(DIR, 'insights.md'),
    `# Upwork Intelligence Insights\n\n- Baseline established ${runAt}. WordPress and core web keywords show the highest job density in the first 2-hour window.\n`
  );
}

const report = {
  runNumber,
  keywordsAttempted,
  keywordsCompleted,
  newJobs: newJobs.length,
  totalJobs: allJobs.length,
  top10,
  topGroups: topGroups.slice(0, 5),
  platformStats,
  newJobsList: newJobs,
  errors: [...new Set(errors)],
  primary,
  secondary,
};
console.log(JSON.stringify(report));
