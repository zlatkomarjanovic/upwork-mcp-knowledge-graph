#!/usr/bin/env node
import fs from 'fs';
import path from 'path';

const DIR = path.dirname(new URL(import.meta.url).pathname);
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

const ALL_KEYWORDS = Object.keys(KEYWORD_GROUPS);

const PLATFORMS = {
  WordPress: ['wordpress'],
  Webflow: ['webflow'],
  Framer: ['framer'],
  GoHighLevel: ['gohighlevel', 'go high level', 'GHL'],
  Shopify: ['shopify'],
  WooCommerce: ['woocommerce'],
  Shopware: ['shopware'],
  Lovable: ['lovable'],
  Bolt: ['bolt'],
  v0: ['v0'],
  'Next.js': ['nextjs', 'next.js'],
};

const SKIP_RE =
  /\b(crypto\s*trading|bitcoin\s*trading|forex\s*trading|casino|gambling|poker|betting|adult\s*content|escort|dating\s*app|onlyfans|alcohol\s*brand|liquor\s*store)\b/i;

function readJson(p, fallback) {
  try {
    return JSON.parse(fs.readFileSync(p, 'utf8'));
  } catch {
    return fallback;
  }
}

function normUrl(url) {
  if (!url) return null;
  return url.split('?')[0];
}

function parseMoney(s) {
  if (!s || typeof s !== 'string') return null;
  const m = s.replace(/,/g, '').match(/([\d.]+)/);
  return m ? parseFloat(m[1]) : null;
}

function parseHourlyRate(budget) {
  if (!budget) return null;
  const parts = budget.split(/–|-/);
  const nums = parts.map(parseMoney).filter((n) => n != null);
  if (!nums.length) return parseMoney(budget);
  return nums.reduce((a, b) => a + b, 0) / nums.length;
}

function isHighBudget(job) {
  if (job.job_type === 'fixed') {
    const v = parseMoney(job.budget);
    return v != null && v >= 1000;
  }
  if (job.job_type === 'hourly') {
    const r = parseHourlyRate(job.budget);
    return r != null && r >= 40;
  }
  return false;
}

function shouldSkipJob(job) {
  const text = `${job.title || ''} ${job.description_snippet || ''}`;
  return SKIP_RE.test(text);
}

function mapJob(raw, keyword, group) {
  const url = normUrl(raw.url);
  if (!url) return null;
  const posted = raw.published_date || raw.created_date;
  const c = raw.client || {};
  return {
    url,
    title: raw.title || null,
    matchedKeyword: [keyword],
    keywordGroup: group,
    postedAt: posted || null,
    type: raw.job_type || null,
    budget: raw.job_type === 'fixed' ? raw.budget || null : null,
    hourlyRate: raw.job_type === 'hourly' ? raw.budget || null : null,
    duration: raw.duration || null,
    proposals: raw.proposal_count ?? null,
    clientCountry: c.country || null,
    paymentVerified: c.verification_status === 'VERIFIED' ? true : c.verification_status ? false : null,
    clientSpend: c.total_spent || null,
    clientHireRate: null,
    clientRating: c.rating ?? null,
    experienceLevel: raw.experience_level || null,
    skills: raw.skills || null,
  };
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
  const m = Math.floor(a.length / 2);
  return a.length % 2 ? a[m] : (a[m - 1] + a[m]) / 2;
}

function avg(arr) {
  const a = arr.filter((x) => x != null);
  return a.length ? a.reduce((s, x) => s + x, 0) / a.length : null;
}

function opportunityScore(stats) {
  const recent = Math.min(stats.jobsLast24h || 0, 20) / 20;
  const budget = Math.min((stats.avgBudgetFixed || 0) / 5000, 1) * 0.5 + Math.min((stats.avgRateHourly || 0) / 80, 1) * 0.5;
  const props = stats.medianProposals != null ? Math.max(0, 1 - stats.medianProposals / 100) : 0.3;
  const high = stats.pctHighBudget || 0;
  const ver = stats.pctVerified || 0;
  const raw = recent * 30 + budget * 25 + props * 20 + high * 15 + ver * 10;
  return Math.max(1, Math.min(100, Math.round(raw)));
}

function computeKeywordStats(jobs) {
  const now = Date.now();
  const dayAgo = now - 24 * 60 * 60 * 1000;
  const byKw = {};
  for (const j of jobs) {
    for (const kw of j.matchedKeyword) {
      if (!byKw[kw]) byKw[kw] = [];
      byKw[kw].push(j);
    }
  }
  const out = {};
  for (const kw of ALL_KEYWORDS) {
    const list = byKw[kw] || [];
    const last24 = list.filter((j) => j.postedAt && new Date(j.postedAt).getTime() >= dayAgo);
    const fixed = list.filter((j) => j.type === 'fixed').map((j) => parseMoney(j.budget));
    const hourly = list.filter((j) => j.type === 'hourly').map((j) => parseHourlyRate(j.hourlyRate));
    const props = list.map((j) => j.proposals);
    const verified = list.filter((j) => j.paymentVerified === true);
    const spend = list.map((j) => parseMoney(j.clientSpend));
    const high = list.filter((j) => {
      if (j.type === 'fixed') return parseMoney(j.budget) >= 1000;
      if (j.type === 'hourly') return parseHourlyRate(j.hourlyRate) >= 40;
      return false;
    });
    const stats = {
      totalJobs: list.length,
      jobsLast24h: last24.length,
      avgBudgetFixed: avg(fixed),
      avgRateHourly: avg(hourly),
      medianProposals: median(props),
      pctVerified: list.length ? verified.length / list.length : 0,
      avgClientSpend: avg(spend),
      pctHighBudget: list.length ? high.length / list.length : 0,
      sampleConfidence: confidenceLabel(list.length),
    };
    stats.opportunityScore = opportunityScore(stats);
    out[kw] = stats;
  }
  return out;
}

function computeGroupStats(keywordStats) {
  const groups = {};
  for (const [kw, st] of Object.entries(keywordStats)) {
    const g = KEYWORD_GROUPS[kw];
    if (!groups[g]) groups[g] = [];
    groups[g].push(st);
  }
  const out = {};
  for (const [g, list] of Object.entries(groups)) {
    out[g] = {
      totalJobs: list.reduce((s, x) => s + x.totalJobs, 0),
      jobsLast24h: list.reduce((s, x) => s + x.jobsLast24h, 0),
      avgOpportunityScore: avg(list.map((x) => x.opportunityScore)),
      keywordCount: list.length,
    };
  }
  return out;
}

function computePlatformStats(jobs) {
  const out = {};
  for (const [name, kws] of Object.entries(PLATFORMS)) {
    const list = jobs.filter((j) => j.matchedKeyword.some((mk) => kws.some((p) => mk.toLowerCase().includes(p))));
    const fixed = list.filter((j) => j.type === 'fixed').map((j) => parseMoney(j.budget));
    const hourly = list.filter((j) => j.type === 'hourly').map((j) => parseHourlyRate(j.hourlyRate));
    const props = list.map((j) => j.proposals);
    const st = {
      jobs: list.length,
      avgBudgetFixed: avg(fixed),
      avgRateHourly: avg(hourly),
      medianProposals: median(props),
      sampleConfidence: confidenceLabel(list.length),
    };
    st.opportunityScore = opportunityScore({
      jobsLast24h: list.filter((j) => j.postedAt && Date.now() - new Date(j.postedAt).getTime() < 86400000).length,
      avgBudgetFixed: st.avgBudgetFixed,
      avgRateHourly: st.avgRateHourly,
      medianProposals: st.medianProposals,
      pctHighBudget: list.length
        ? list.filter((j) => (j.type === 'fixed' ? parseMoney(j.budget) >= 1000 : parseHourlyRate(j.hourlyRate) >= 40)).length /
          list.length
        : 0,
      pctVerified: list.length ? list.filter((j) => j.paymentVerified).length / list.length : 0,
    });
    out[name] = st;
  }
  return out;
}

const payloadPath = process.argv[2];
if (!payloadPath) {
  console.error('Usage: node process-run.mjs <payload.json>');
  process.exit(1);
}

const payload = readJson(payloadPath, null);
if (!payload) {
  console.error('Invalid payload');
  process.exit(1);
}

const statePath = path.join(DIR, 'state.json');
const state = readJson(statePath, { runNumber: 0, totalJobs: 0, knownJobUrls: [], lastInsightRefresh: null });
const runNumber = (state.runNumber || 0) + 1;
const firstRun = !state.lastRunAt;
const windowMs = firstRun ? WINDOW_MS_FIRST : WINDOW_MS;
const cutoff = Date.now() - windowMs;
const known = new Set((state.knownJobUrls || []).map(normUrl));

const errors = [];
const merged = new Map();

for (const entry of payload.searches || []) {
  const kw = entry.keyword;
  const group = KEYWORD_GROUPS[kw] || entry.group;
  if (entry.error) {
    errors.push({ keyword: kw, error: entry.error });
    continue;
  }
  const jobs = entry.jobs || entry.response?.jobs || [];
  for (const raw of jobs) {
    if (shouldSkipJob(raw)) continue;
    const posted = raw.published_date || raw.created_date;
    if (posted && new Date(posted).getTime() < cutoff) continue;
    const row = mapJob(raw, kw, group);
    if (!row) continue;
    const ex = merged.get(row.url);
    if (ex) {
      if (!ex.matchedKeyword.includes(kw)) ex.matchedKeyword.push(kw);
    } else merged.set(row.url, row);
  }
}

const newJobs = [];
for (const [url, job] of merged) {
  if (!known.has(url)) {
    newJobs.push(job);
    known.add(url);
  }
}

const jobsPath = path.join(DIR, 'jobs.jsonl');
for (const job of newJobs) {
  fs.appendFileSync(jobsPath, JSON.stringify(job) + '\n');
}

const allJobs = [];
if (fs.existsSync(jobsPath)) {
  for (const line of fs.readFileSync(jobsPath, 'utf8').split('\n')) {
    if (line.trim()) allJobs.push(JSON.parse(line));
  }
}

const keywordStats = computeKeywordStats(allJobs);
const groupStats = computeGroupStats(keywordStats);
const platformStats = computePlatformStats(allJobs);

fs.writeFileSync(path.join(DIR, 'keyword-stats.json'), JSON.stringify(keywordStats, null, 2));
fs.writeFileSync(path.join(DIR, 'group-stats.json'), JSON.stringify(groupStats, null, 2));
fs.writeFileSync(path.join(DIR, 'platform-stats.json'), JSON.stringify(platformStats, null, 2));

const top3 = Object.entries(keywordStats)
  .sort((a, b) => b[1].opportunityScore - a[1].opportunityScore)
  .slice(0, 3)
  .map(([k]) => k);

const runLog = {
  timestamp: new Date().toISOString(),
  runNumber,
  keywordsAttempted: payload.keywordsAttempted ?? ALL_KEYWORDS.length,
  keywordsCompleted: payload.keywordsCompleted ?? ALL_KEYWORDS.length - errors.length,
  newJobs: newJobs.length,
  totalJobs: allJobs.length,
  top3Keywords: top3,
  errors,
};
fs.appendFileSync(path.join(DIR, 'run-log.jsonl'), JSON.stringify(runLog) + '\n');

const newState = {
  lastRunAt: runLog.timestamp,
  runNumber,
  totalJobs: allJobs.length,
  knownJobUrls: [...known],
  lastInsightRefresh: state.lastInsightRefresh,
};
fs.writeFileSync(statePath, JSON.stringify(newState, null, 2));

const top10 = Object.entries(keywordStats)
  .sort((a, b) => b[1].opportunityScore - a[1].opportunityScore)
  .slice(0, 10);

const topGroups = Object.entries(groupStats).sort((a, b) => (b[1].avgOpportunityScore || 0) - (a[1].avgOpportunityScore || 0));

const primary = top10[0]?.[0] || 'wordpress developer';
const secondary = top10[1]?.[0] || 'webflow developer';

let summary = `# Upwork Market Intelligence

Last updated: ${runLog.timestamp}
Run: ${runNumber}
Total jobs tracked: ${allJobs.length}
Keywords attempted: ${runLog.keywordsAttempted}
Keywords completed: ${runLog.keywordsCompleted}

## Top Opportunities

`;
for (const [kw, st] of top10) {
  summary += `### ${kw}
- jobsLast24h: ${st.jobsLast24h}
- totalJobs: ${st.totalJobs}
- avg fixed: ${st.avgBudgetFixed != null ? '$' + Math.round(st.avgBudgetFixed) : 'n/a'}
- avg hourly: ${st.avgRateHourly != null ? '$' + Math.round(st.avgRateHourly) + '/hr' : 'n/a'}
- median proposals: ${st.medianProposals ?? 'n/a'}
- opportunityScore: ${st.opportunityScore}
- confidence: ${st.sampleConfidence}

`;
}

summary += `## Strongest Groups

`;
for (const [g, st] of topGroups) {
  summary += `- ${g}: jobs24h ${st.jobsLast24h}, total ${st.totalJobs}, avg score ${Math.round(st.avgOpportunityScore || 0)}
`;
}

summary += `
## Platform Ranking

`;
const platRank = Object.entries(platformStats).sort((a, b) => b[1].opportunityScore - a[1].opportunityScore);
for (const [p, st] of platRank) {
  summary += `- ${p}: score ${st.opportunityScore}, jobs ${st.jobs}, confidence ${st.sampleConfidence}
`;
}

summary += `
## Positioning Recommendation

Primary keyword: ${primary}
Secondary keyword: ${secondary}
Best platform/service: WordPress + Next.js hybrid positioning
Overview keywords: ${primary}, ${secondary}, full stack developer, website redesign
Skill tags: WordPress, Webflow, Next.js, React, SEO, Elementor

## Current Verdicts

WordPress: Steady volume; mix of low-budget fixes and solid rebuild/redesign posts.
Webflow: Niche but cleaner budgets on redesign/migration work.
Framer: Lower volume; good for fast landing/funnel builds.
GoHighLevel: Funnel and migration demand; often bundled with WordPress.
AI/Vibe Coding: Growing; many MVP and agent posts with wide budget spread.
Ecommerce: WooCommerce and Shopify both active; verify scope before applying.
Maintenance: Retainer posts exist; filter for real ongoing dev vs VA overlap.

## Important Changes

${runNumber === 1 ? 'Initial baseline run. No prior comparison.' : 'See run log for delta vs previous run.'}
`;

fs.writeFileSync(path.join(DIR, 'current-summary.md'), summary);

if (runNumber === 1 && !fs.existsSync(path.join(DIR, 'insights.md'))) {
  fs.writeFileSync(
    path.join(DIR, 'insights.md'),
    `# Durable insights\n\n- Baseline established run ${runNumber}.\n- WordPress keyword family shows the broadest simultaneous demand.\n- Premium fixed posts ($1000+) appear under custom website and full stack searches.\n`
  );
}

const report = {
  runNumber,
  keywordsAttempted: runLog.keywordsAttempted,
  keywordsCompleted: runLog.keywordsCompleted,
  newJobs: newJobs.length,
  totalJobs: allJobs.length,
  top10: top10.map(([k, st]) => ({ keyword: k, ...st })),
  topGroups: topGroups.slice(0, 5),
  platformStats,
  newJobsList: newJobs,
  errors: errors.map((e) => e.keyword),
  primary,
  secondary,
};
fs.writeFileSync(path.join(DIR, '.last-chat-report.json'), JSON.stringify(report, null, 2));
console.log(JSON.stringify({ ok: true, runNumber, newJobs: newJobs.length, totalJobs: allJobs.length }));
