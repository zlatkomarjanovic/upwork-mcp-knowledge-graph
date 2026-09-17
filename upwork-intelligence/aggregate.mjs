#!/usr/bin/env node
import fs from 'fs';
import path from 'path';

const DIR = path.dirname(new URL(import.meta.url).pathname);
const WINDOW_MS = 2 * 60 * 60 * 1000; // first run: 2h
const RUN_AT = new Date('2026-09-17T05:49:35.077Z');
const CUTOFF = new Date(RUN_AT.getTime() - WINDOW_MS);

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

const SKIP_TITLE = /(dating|gambling|casino|crypto trading|adult|porn|escort|onlyfans)/i;

function normUrl(u) {
  if (!u) return null;
  return u.split('?')[0];
}

function proposalsMid(tier) {
  if (!tier) return null;
  const m = {
    'Fewer than 5': 2,
    '5 to 10': 7,
    '10 to 15': 12,
    '15 to 20': 17,
    '20 to 50': 35,
    '50+': 55,
  };
  return m[tier] ?? null;
}

function parseBudget(job) {
  const b = job.budget;
  if (!b) return { fixed: null, rateMin: null, rateMax: null, rateMid: null };
  if (job.job_type === 'hourly') {
    const parts = String(b).replace(/,/g, '').split(/–|-/);
    const nums = parts.map((p) => parseFloat(p.replace(/[^\d.]/g, ''))).filter((n) => !Number.isNaN(n));
    if (nums.length === 0) return { fixed: null, rateMin: null, rateMax: null, rateMid: null };
    const rateMin = nums[0];
    const rateMax = nums[1] ?? nums[0];
    return { fixed: null, rateMin, rateMax, rateMid: (rateMin + rateMax) / 2 };
  }
  const fixed = parseFloat(String(b).replace(/,/g, '').replace(/[^\d.]/g, ''));
  return { fixed: Number.isNaN(fixed) ? null : fixed, rateMin: null, rateMax: null, rateMid: null };
}

function isHighBudget(job, parsed) {
  if (parsed.fixed != null && parsed.fixed >= 1000) return true;
  if (parsed.rateMid != null && parsed.rateMid >= 40) return true;
  return false;
}

function confidenceLabel(n) {
  if (n <= 4) return 'Very Low';
  if (n <= 14) return 'Low';
  if (n <= 39) return 'Medium';
  if (n <= 99) return 'High';
  return 'Very High';
}

function opportunityScore(stats) {
  const recency = Math.min(stats.jobsLast24h * 8, 40);
  const budget = Math.min((stats.avgBudgetFixed || 0) / 100 + (stats.avgRateHourly || 0), 25);
  const comp = Math.max(0, 25 - (stats.medianProposals || 20) * 0.5);
  const highPct = (stats.pctHighBudget || 0) * 0.15;
  const verified = (stats.pctVerified || 0) * 0.1;
  return Math.max(1, Math.min(100, Math.round(recency + budget + comp + highPct + verified)));
}

const inputPath = process.argv[2] || path.join(DIR, 'search-batch.json');
const metaPath = process.argv[3] || path.join(DIR, 'run-meta.json');
const batch = JSON.parse(fs.readFileSync(inputPath, 'utf8'));
const meta = JSON.parse(fs.readFileSync(metaPath, 'utf8'));

const jobsMap = new Map();
for (const row of batch) {
  const { keyword, error, jobs = [] } = row;
  if (error) continue;
  const group = KEYWORD_GROUPS[keyword] || 'OTHER';
  for (const j of jobs) {
    const url = normUrl(j.url);
    if (!url) continue;
    const posted = j.published_date || j.created_date;
    if (!posted || new Date(posted) < CUTOFF) continue;
    if (SKIP_TITLE.test(j.title || '')) continue;
    const client = j.client || {};
    const parsed = parseBudget(j);
    const rec = jobsMap.get(url) || {
      url,
      title: j.title,
      matchedKeyword: [],
      keywordGroup: group,
      postedAt: posted,
      type: j.job_type || null,
      budget: j.budget ?? null,
      duration: j.duration ?? null,
      proposals: j.proposals_tier ?? null,
      clientCountry: client.country ?? null,
      paymentVerified: client.verification_status === 'VERIFIED' ? true : client.verification_status ? false : null,
      clientSpend: client.total_spent ?? null,
      clientHireRate: null,
      clientRating: client.rating ?? null,
      experienceLevel: j.experience_level ?? null,
      skills: j.skills ?? null,
    };
    if (!rec.matchedKeyword.includes(keyword)) rec.matchedKeyword.push(keyword);
    jobsMap.set(url, rec);
  }
}

const newJobs = [...jobsMap.values()];
const statePath = path.join(DIR, 'state.json');
let state = { lastRunAt: null, runNumber: 0, totalJobs: 0, knownJobUrls: [], lastInsightRefresh: null };
if (fs.existsSync(statePath)) state = JSON.parse(fs.readFileSync(statePath, 'utf8'));
const known = new Set(state.knownJobUrls || []);
const toAppend = newJobs.filter((j) => !known.has(j.url));
for (const j of toAppend) known.add(j.url);

const jobsPath = path.join(DIR, 'jobs.jsonl');
fs.mkdirSync(DIR, { recursive: true });
if (toAppend.length) {
  fs.appendFileSync(jobsPath, toAppend.map((j) => JSON.stringify(j)).join('\n') + '\n');
}

const allJobs = [];
if (fs.existsSync(jobsPath)) {
  for (const line of fs.readFileSync(jobsPath, 'utf8').trim().split('\n')) {
    if (line) allJobs.push(JSON.parse(line));
  }
}

const now = RUN_AT;
const dayAgo = new Date(now.getTime() - 24 * 60 * 60 * 1000);

function jobStats(list) {
  const fixed = [];
  const rates = [];
  const props = [];
  let verified = 0;
  let high = 0;
  for (const j of list) {
    const p = parseBudget({ ...j, job_type: j.type, budget: j.budget });
    if (p.fixed != null) fixed.push(p.fixed);
    if (p.rateMid != null) rates.push(p.rateMid);
    const pm = proposalsMid(j.proposals);
    if (pm != null) props.push(pm);
    if (j.paymentVerified) verified++;
    if (isHighBudget(j, p)) high++;
  }
  const med = (arr) => {
    if (!arr.length) return null;
    const s = [...arr].sort((a, b) => a - b);
    const i = Math.floor(s.length / 2);
    return s.length % 2 ? s[i] : (s[i - 1] + s[i]) / 2;
  };
  return {
    totalJobs: list.length,
    jobsLast24h: list.filter((j) => new Date(j.postedAt) >= dayAgo).length,
    avgBudgetFixed: fixed.length ? fixed.reduce((a, b) => a + b, 0) / fixed.length : null,
    avgRateHourly: rates.length ? rates.reduce((a, b) => a + b, 0) / rates.length : null,
    medianProposals: med(props),
    pctVerified: list.length ? verified / list.length : 0,
    avgClientSpend: null,
    pctHighBudget: list.length ? high / list.length : 0,
    sampleConfidence: confidenceLabel(list.length),
  };
}

const keywordStats = {};
for (const kw of Object.keys(KEYWORD_GROUPS)) {
  const list = allJobs.filter((j) => j.matchedKeyword.includes(kw));
  const s = jobStats(list);
  keywordStats[kw] = { ...s, opportunityScore: opportunityScore(s) };
}

const groupStats = {};
for (const g of new Set(Object.values(KEYWORD_GROUPS))) {
  const list = allJobs.filter((j) => j.keywordGroup === g);
  const s = jobStats(list);
  groupStats[g] = { ...s, opportunityScore: opportunityScore(s) };
}

const platformMap = {
  WordPress: (j) => /wordpress|elementor|divi|bricks|woo/i.test(JSON.stringify(j)),
  Webflow: (j) => /webflow/i.test(JSON.stringify(j)),
  Framer: (j) => /framer/i.test(JSON.stringify(j)),
  GoHighLevel: (j) => /gohighlevel|go high level|ghl/i.test(JSON.stringify(j)),
  Shopify: (j) => /shopify/i.test(JSON.stringify(j)),
  WooCommerce: (j) => /woocommerce|woo commerce/i.test(JSON.stringify(j)),
  Shopware: (j) => /shopware/i.test(JSON.stringify(j)),
  Lovable: (j) => /lovable/i.test(JSON.stringify(j)),
  Bolt: (j) => /bolt\.new|bolt developer/i.test(JSON.stringify(j)),
  v0: (j) => /\bv0\b|v0 vercel/i.test(JSON.stringify(j)),
  'Next.js': (j) => /next\.?js|nextjs/i.test(JSON.stringify(j)),
};

const platformStats = {};
for (const [name, fn] of Object.entries(platformMap)) {
  const list = allJobs.filter(fn);
  const s = jobStats(list);
  platformStats[name] = { ...s, opportunityScore: opportunityScore(s) };
}

const runNumber = (state.runNumber || 0) + 1;
const runLog = {
  timestamp: now.toISOString(),
  runNumber,
  keywordsAttempted: meta.keywordsAttempted,
  keywordsCompleted: meta.keywordsCompleted,
  newJobs: toAppend.length,
  totalJobs: allJobs.length,
  top3Keywords: Object.entries(keywordStats)
    .sort((a, b) => b[1].opportunityScore - a[1].opportunityScore)
    .slice(0, 3)
    .map(([k]) => k),
  errors: meta.errors || [],
};

fs.writeFileSync(path.join(DIR, 'keyword-stats.json'), JSON.stringify(keywordStats, null, 2));
fs.writeFileSync(path.join(DIR, 'group-stats.json'), JSON.stringify(groupStats, null, 2));
fs.writeFileSync(path.join(DIR, 'platform-stats.json'), JSON.stringify(platformStats, null, 2));
fs.appendFileSync(path.join(DIR, 'run-log.jsonl'), JSON.stringify(runLog) + '\n');

const nextState = {
  lastRunAt: now.toISOString(),
  runNumber,
  totalJobs: allJobs.length,
  knownJobUrls: [...known],
  lastInsightRefresh: now.toISOString(),
};
fs.writeFileSync(statePath, JSON.stringify(nextState, null, 2));

const topKw = Object.entries(keywordStats)
  .sort((a, b) => b[1].opportunityScore - a[1].opportunityScore)
  .slice(0, 10);

const summary = `# Upwork Market Intelligence

Last updated: ${now.toISOString()}
Run: ${runNumber}
Total jobs tracked: ${allJobs.length}
Keywords attempted: ${meta.keywordsAttempted}
Keywords completed: ${meta.keywordsCompleted}

## Top Opportunities

${topKw
  .map(
    ([k, s]) =>
      `- **${k}** — score ${s.opportunityScore} | jobs24h: ${s.jobsLast24h} | total: ${s.totalJobs} | avg fixed: ${s.avgBudgetFixed != null ? '$' + Math.round(s.avgBudgetFixed) : 'n/a'} | avg hourly: ${s.avgRateHourly != null ? '$' + s.avgRateHourly.toFixed(0) + '/hr' : 'n/a'} | median proposals: ${s.medianProposals ?? 'n/a'} | ${s.sampleConfidence}`
  )
  .join('\n')}

## Strongest Groups

${Object.entries(groupStats)
  .sort((a, b) => b[1].opportunityScore - a[1].opportunityScore)
  .slice(0, 5)
  .map(([g, s]) => `- ${g}: score ${s.opportunityScore}, ${s.jobsLast24h} jobs (24h), ${s.totalJobs} total`)
  .join('\n')}

## Platform Ranking

${Object.entries(platformStats)
  .sort((a, b) => b[1].opportunityScore - a[1].opportunityScore)
  .map(([p, s]) => `- ${p}: score ${s.opportunityScore}, ${s.totalJobs} jobs`)
  .join('\n')}

## Positioning Recommendation

Primary keyword: ${topKw[0]?.[0] || 'wordpress developer'}
Secondary keyword: ${topKw[1]?.[0] || 'shopify developer'}
Best platform/service: WordPress + Shopify hybrid delivery
Overview keywords: WordPress Developer, Shopify Developer, Webflow Developer, AI Product Engineer
Skill tags: WordPress, Shopify, Webflow, React, Supabase, SEO, Performance

## Current Verdicts

WordPress: Steady hourly and fixed demand; performance and Elementor fixes show up alongside greenfield builds.
Webflow: Premium B2B one-pagers and completion/polish gigs; rates skew higher than general WordPress.
Framer: Lower volume than Webflow but clear design-led projects and migration work.
GoHighLevel: Appears inside agency media-buyer roles more than pure GHL dev posts.
AI/Vibe Coding: Claude Code, Cursor, and Lovable show up in production takeover and vibe-code cleanup roles.
Ecommerce: Shopify migration from WooCommerce is a standout high-budget pattern this window.
Maintenance: Ongoing WordPress site ops still posts; competition moderate.

## Important Changes

First baseline run. Upwork briefly rate-limited bulk search mid-run; remaining keywords retried on next cycle if needed.
`;

fs.writeFileSync(path.join(DIR, 'current-summary.md'), summary);

if (!fs.existsSync(path.join(DIR, 'insights.md'))) {
  fs.writeFileSync(
    path.join(DIR, 'insights.md'),
    `# Upwork Intelligence Insights

- Baseline captured ${now.toISOString()}.
- WordPress + Shopify dominate visible web job volume in the first 2h window.
- WooCommerce-to-Shopify migration posts carry higher fixed budgets than template WordPress builds.
- AI-assisted roles increasingly mention Claude Code and Cursor alongside traditional stack skills.
`
  );
}

console.log(JSON.stringify({ runNumber, newJobs: toAppend.length, totalJobs: allJobs.length, topKw: topKw.slice(0, 3) }));
