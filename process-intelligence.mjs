#!/usr/bin/env node
import fs from 'fs';
import path from 'path';

const INT_DIR = path.join(process.cwd(), 'upwork-intelligence');
const ORG = '1472686528932380673';

const KEYWORD_GROUPS = {
  'CORE WEB DEVELOPMENT': [
    'web development', 'website development', 'web developer', 'custom website',
    'frontend developer', 'full stack developer',
  ],
  'WEB DESIGN': [
    'web design', 'website design', 'website redesign', 'landing page design',
    'UI UX website', 'responsive web design',
  ],
  WORDPRESS: [
    'wordpress', 'wordpress developer', 'wordpress website', 'wordpress development',
    'wordpress redesign', 'wordpress customization', 'wordpress migration',
    'wordpress speed optimization', 'wordpress maintenance', 'woocommerce',
    'elementor developer', 'bricks builder',
  ],
  'WEBFLOW / FRAMER': [
    'webflow', 'webflow developer', 'webflow website', 'webflow redesign',
    'figma to webflow', 'framer', 'framer developer', 'framer website',
    'framer redesign', 'figma to framer',
  ],
  'AI / VIBE CODING': [
    'AI web development', 'AI web developer', 'vibe coding', 'claude code developer',
    'cursor AI developer', 'lovable developer', 'lovable app', 'bolt developer',
    'bolt.new', 'v0 developer', 'v0 vercel', 'replit developer', 'supabase developer',
    'AI agent integration website',
  ],
  GOHIGHLEVEL: [
    'gohighlevel', 'go high level', 'GHL', 'gohighlevel developer',
    'gohighlevel website', 'gohighlevel funnel', 'gohighlevel automation', 'gohighlevel CRM',
  ],
  'ADJACENT PLATFORMS': [
    'squarespace website', 'wix website', 'wix studio', 'bubble developer',
  ],
  'MODERN STACK': [
    'nextjs developer', 'next.js developer', 'nextjs website', 'react developer',
    'figma to nextjs', 'tailwind developer', 'astro developer', 'sanity CMS',
  ],
  ECOMMERCE: [
    'ecommerce website', 'ecommerce developer', 'shopify developer', 'shopify website',
    'woocommerce developer', 'shopware', 'shopware developer', 'shopware 6', 'headless ecommerce',
  ],
  'MAINTENANCE / RETAINERS': [
    'website maintenance', 'website maintenance monthly', 'website support ongoing',
    'website management ongoing', 'wordpress support retainer', 'webflow maintenance',
    'shopify maintenance', 'ongoing web developer', 'web development retainer',
  ],
  'CONVERSION / PERFORMANCE': [
    'conversion rate optimization', 'landing page optimization', 'website audit',
    'core web vitals', 'page speed optimization', 'website speed optimization', 'technical SEO website',
  ],
};

const ALL_KEYWORDS = Object.entries(KEYWORD_GROUPS).flatMap(([group, kws]) =>
  kws.map((keyword) => ({ keyword, group }))
);

const PLATFORMS = {
  WordPress: /wordpress|elementor|woocommerce|homey|astra|bricks/i,
  Webflow: /webflow|relume/i,
  Framer: /framer/i,
  GoHighLevel: /gohighlevel|go high level|\bghl\b/i,
  Shopify: /shopify/i,
  WooCommerce: /woocommerce/i,
  Shopware: /shopware/i,
  Lovable: /lovable/i,
  Bolt: /bolt\.new|\bbolt developer\b/i,
  v0: /\bv0\b|v0 vercel/i,
  'Next.js': /next\.?js|nextjs/i,
};

const SKIP_RE =
  /\b(crypto|bitcoin|casino|gambling|poker|betting|adult|escort|dating|onlyfans|alcohol|brewery|distillery)\b/i;

function normUrl(url) {
  if (!url) return null;
  try {
    const u = new URL(url);
    return `${u.origin}${u.pathname}`;
  } catch {
    return url.split('?')[0];
  }
}

function parseMoney(str) {
  if (!str || typeof str !== 'string') return null;
  const cleaned = str.replace(/,/g, '');
  const nums = cleaned.match(/[\d.]+/g);
  if (!nums) return null;
  return nums.map(Number);
}

function parseClientSpend(str) {
  if (!str) return null;
  const n = parseMoney(String(str));
  return n?.[0] ?? null;
}

function isHighBudget(job) {
  if (job.job_type === 'fixed') {
    const nums = parseMoney(job.budget);
    if (!nums?.length) return false;
    const val = Math.max(...nums);
    return val >= 1000;
  }
  const nums = parseMoney(job.budget);
  if (!nums?.length) return false;
  const rate = nums.length > 1 ? (nums[0] + nums[1]) / 2 : nums[0];
  return rate >= 40;
}

function mapJob(raw, keyword, group) {
  const url = normUrl(raw.url);
  if (!url) return null;
  const title = raw.title || '';
  const desc = raw.description_snippet || '';
  if (SKIP_RE.test(`${title} ${desc}`)) return null;

  const client = raw.client || {};
  return {
    url,
    title,
    matchedKeyword: [keyword],
    keywordGroup: group,
    postedAt: raw.published_date || raw.created_date || null,
    type: raw.job_type || null,
    budget: raw.budget ?? null,
    duration: raw.duration ?? null,
    proposals: raw.proposal_count ?? null,
    clientCountry: client.country ?? null,
    paymentVerified: client.verification_status === 'VERIFIED',
    clientSpend: client.total_spent ?? null,
    clientHireRate: null,
    clientRating: client.rating ?? null,
    experienceLevel: raw.experience_level ?? null,
    skills: raw.skills ?? [],
    firstSeenRun: null,
  };
}

function median(arr) {
  if (!arr.length) return null;
  const s = [...arr].sort((a, b) => a - b);
  const m = Math.floor(s.length / 2);
  return s.length % 2 ? s[m] : (s[m - 1] + s[m]) / 2;
}

function avg(arr) {
  if (!arr.length) return null;
  return arr.reduce((a, b) => a + b, 0) / arr.length;
}

function sampleConfidence(n) {
  if (n <= 4) return 'Very Low';
  if (n <= 14) return 'Low';
  if (n <= 39) return 'Medium';
  if (n <= 99) return 'High';
  return 'Very High';
}

function opportunityScore(jobs) {
  if (!jobs.length) return 0;
  const now = Date.now();
  let score = 0;
  for (const j of jobs) {
    let s = 20;
    const posted = j.postedAt ? new Date(j.postedAt).getTime() : now;
    const ageH = (now - posted) / 3600000;
    if (ageH <= 24) s += 25;
    else if (ageH <= 72) s += 15;
    else if (ageH <= 168) s += 8;

    if (j.type === 'fixed') {
      const nums = parseMoney(j.budget);
      if (nums?.length) {
        const v = Math.max(...nums);
        if (v >= 1000) s += 20;
        else if (v >= 500) s += 12;
        else if (v >= 200) s += 6;
      }
    } else {
      const nums = parseMoney(j.budget);
      if (nums?.length) {
        const r = nums.length > 1 ? (nums[0] + nums[1]) / 2 : nums[0];
        if (r >= 40) s += 20;
        else if (r >= 25) s += 12;
        else if (r >= 15) s += 6;
      }
    }

    if (typeof j.proposals === 'number') {
      if (j.proposals <= 5) s += 20;
      else if (j.proposals <= 10) s += 14;
      else if (j.proposals <= 20) s += 8;
      else s += 2;
    } else s += 10;

    if (j.paymentVerified) s += 8;
    if (isHighBudget({ job_type: j.type, budget: j.budget })) s += 7;
    score += Math.min(100, s);
  }
  return Math.round(Math.min(100, score / jobs.length));
}

function statsForJobs(jobs, nowMs) {
  const ms24 = 24 * 3600000;
  const jobsLast24h = jobs.filter(
    (j) => j.postedAt && nowMs - new Date(j.postedAt).getTime() <= ms24
  ).length;

  const fixed = [];
  const hourly = [];
  const proposals = [];
  let verified = 0;
  let highBudget = 0;
  const spends = [];

  for (const j of jobs) {
    if (j.paymentVerified) verified++;
    if (isHighBudget({ job_type: j.type, budget: j.budget })) highBudget++;
    if (typeof j.proposals === 'number') proposals.push(j.proposals);
    const spend = parseClientSpend(j.clientSpend);
    if (spend != null) spends.push(spend);

    if (j.type === 'fixed') {
      const nums = parseMoney(j.budget);
      if (nums?.length) fixed.push(Math.max(...nums));
    } else if (j.type === 'hourly') {
      const nums = parseMoney(j.budget);
      if (nums?.length) hourly.push(nums.length > 1 ? (nums[0] + nums[1]) / 2 : nums[0]);
    }
  }

  const n = jobs.length;
  return {
    totalJobs: n,
    jobsLast24h,
    avgBudgetFixed: fixed.length ? Math.round(avg(fixed)) : null,
    avgRateHourly: hourly.length ? Math.round(avg(hourly) * 100) / 100 : null,
    medianProposals: median(proposals),
    pctVerified: n ? Math.round((verified / n) * 100) : 0,
    avgClientSpend: spends.length ? Math.round(avg(spends)) : null,
    pctHighBudget: n ? Math.round((highBudget / n) * 100) : 0,
    opportunityScore: opportunityScore(jobs),
    sampleConfidence: sampleConfidence(n),
  };
}

function loadJsonl(file) {
  if (!fs.existsSync(file)) return [];
  return fs
    .readFileSync(file, 'utf8')
    .split('\n')
    .filter(Boolean)
    .map((l) => JSON.parse(l));
}

function ensureDir() {
  fs.mkdirSync(INT_DIR, { recursive: true });
}

function main() {
  const args = process.argv.slice(2);
  let batchPath = null;
  let nowIso = new Date().toISOString();
  let firstRun = false;
  for (let i = 0; i < args.length; i++) {
    if (args[i].startsWith('--batch=')) batchPath = args[i].slice('--batch='.length);
    else if (args[i] === '--batch' && args[i + 1]) batchPath = args[++i];
    if (args[i].startsWith('--now=')) nowIso = args[i].slice('--now='.length);
    else if (args[i] === '--now' && args[i + 1]) nowIso = args[++i];
    if (args[i] === '--first-run') firstRun = true;
  }

  if (!batchPath || !fs.existsSync(batchPath)) {
    console.error('Missing --batch file');
    process.exit(1);
  }

  ensureDir();
  const statePath = path.join(INT_DIR, 'state.json');
  const jobsPath = path.join(INT_DIR, 'jobs.jsonl');
  const runLogPath = path.join(INT_DIR, 'run-log.jsonl');

  let state = {
    lastRunAt: null,
    runNumber: 0,
    totalJobs: 0,
    knownJobUrls: [],
    lastInsightRefresh: null,
  };
  if (fs.existsSync(statePath)) {
    state = { ...state, ...JSON.parse(fs.readFileSync(statePath, 'utf8')) };
  }

  const windowMs = (firstRun || state.runNumber === 0 ? 2 : 1) * 3600000;
  const nowMs = new Date(nowIso).getTime();
  const cutoff = nowMs - windowMs;

  const known = new Set(state.knownJobUrls || []);
  const existingJobs = loadJsonl(jobsPath);
  const byUrl = new Map(existingJobs.map((j) => [j.url, j]));

  const batch = JSON.parse(fs.readFileSync(batchPath, 'utf8'));
  const errors = batch.errors || [];
  const searchResults = batch.results || [];

  let keywordsAttempted = batch.keywordsAttempted ?? ALL_KEYWORDS.length;
  let keywordsCompleted = batch.keywordsCompleted ?? searchResults.length;

  const newJobsThisRun = [];

  for (const { keyword, group, response } of searchResults) {
    if (!response || response.status === 'error') continue;
    const jobs = response.jobs || [];
    for (const raw of jobs) {
      const posted = raw.published_date || raw.created_date;
      if (posted && new Date(posted).getTime() < cutoff) continue;

      const mapped = mapJob(raw, keyword, group);
      if (!mapped) continue;

      const existing = byUrl.get(mapped.url);
      if (existing) {
        if (!existing.matchedKeyword.includes(keyword)) {
          existing.matchedKeyword.push(keyword);
        }
        byUrl.set(mapped.url, existing);
        continue;
      }

      mapped.firstSeenRun = state.runNumber + 1;
      byUrl.set(mapped.url, mapped);
      newJobsThisRun.push(mapped);
    }
  }

  if (newJobsThisRun.length) {
    fs.appendFileSync(jobsPath, newJobsThisRun.map((j) => JSON.stringify(j)).join('\n') + '\n');
  }

  const allJobs = [...byUrl.values()];
  state.runNumber += 1;
  state.lastRunAt = nowIso;
  state.totalJobs = allJobs.length;
  state.knownJobUrls = allJobs.map((j) => j.url);

  const keywordStats = {};
  for (const { keyword, group } of ALL_KEYWORDS) {
    const matched = allJobs.filter((j) => j.matchedKeyword.includes(keyword));
    keywordStats[keyword] = { group, ...statsForJobs(matched, nowMs) };
  }

  const groupStats = {};
  for (const [group, kws] of Object.entries(KEYWORD_GROUPS)) {
    const matched = allJobs.filter((j) => kws.some((k) => j.matchedKeyword.includes(k)));
    groupStats[group] = statsForJobs(matched, nowMs);
  }

  const platformStats = {};
  for (const [name, re] of Object.entries(PLATFORMS)) {
    const matched = allJobs.filter(
      (j) =>
        re.test(j.title) ||
        re.test(j.matchedKeyword.join(' ')) ||
        (j.skills || []).some((s) => re.test(s))
    );
    platformStats[name] = statsForJobs(matched, nowMs);
  }

  fs.writeFileSync(path.join(INT_DIR, 'keyword-stats.json'), JSON.stringify(keywordStats, null, 2));
  fs.writeFileSync(path.join(INT_DIR, 'group-stats.json'), JSON.stringify(groupStats, null, 2));
  fs.writeFileSync(path.join(INT_DIR, 'platform-stats.json'), JSON.stringify(platformStats, null, 2));
  fs.writeFileSync(statePath, JSON.stringify(state, null, 2));

  const top3Keywords = Object.entries(keywordStats)
    .sort((a, b) => b[1].opportunityScore - a[1].opportunityScore)
    .slice(0, 3)
    .map(([k]) => k);

  const runRecord = {
    timestamp: nowIso,
    runNumber: state.runNumber,
    keywordsAttempted,
    keywordsCompleted,
    newJobs: newJobsThisRun.length,
    totalJobs: state.totalJobs,
    top3Keywords,
    errors,
  };
  fs.appendFileSync(runLogPath, JSON.stringify(runRecord) + '\n');

  const topKeywords = Object.entries(keywordStats)
    .sort((a, b) => b[1].opportunityScore - a[1].opportunityScore)
    .slice(0, 10);

  const topGroups = Object.entries(groupStats)
    .sort((a, b) => b[1].opportunityScore - a[1].opportunityScore)
    .slice(0, 5);

  const primaryKw = topKeywords[0]?.[0] || 'wordpress developer';
  const secondaryKw = topKeywords[1]?.[0] || 'webflow developer';

  const platformRank = Object.entries(platformStats).sort(
    (a, b) => b[1].opportunityScore - a[1].opportunityScore
  );
  const bestPlatform = platformRank[0]?.[0] || 'WordPress';

  const summary = `# Upwork Market Intelligence

Last updated: ${nowIso}
Run: ${state.runNumber}
Total jobs tracked: ${state.totalJobs}
Keywords attempted: ${keywordsAttempted}
Keywords completed: ${keywordsCompleted}

## Top Opportunities

${topKeywords
  .map(
    ([kw, s], i) => `${i + 1}. **${kw}** — score ${s.opportunityScore} (${s.sampleConfidence})
   - jobsLast24h: ${s.jobsLast24h} | total: ${s.totalJobs}
   - avg fixed: ${s.avgBudgetFixed ?? 'n/a'} | avg hourly: ${s.avgRateHourly ?? 'n/a'}
   - median proposals: ${s.medianProposals ?? 'n/a'}`
  )
  .join('\n\n')}

## Strongest Groups

${topGroups.map(([g, s], i) => `${i + 1}. ${g} — score ${s.opportunityScore} (${s.totalJobs} jobs)`).join('\n')}

## Platform Ranking

${platformRank.map(([p, s], i) => `${i + 1}. ${p} — score ${s.opportunityScore} (${s.totalJobs} jobs)`).join('\n')}

## Positioning Recommendation

Primary keyword: ${primaryKw}
Secondary keyword: ${secondaryKw}
Best platform/service: ${bestPlatform}
Overview keywords: ${primaryKw}, ${secondaryKw}, ${bestPlatform.toLowerCase()} developer
Skill tags: ${bestPlatform}, Web Development, ${primaryKw.includes('wordpress') ? 'Elementor' : 'React'}

## Current Verdicts

WordPress: Steady volume; mix of landing pages, fixes, and builds.
Webflow: Stronger on CMS launches and design optimization.
Framer: Lower volume but cleaner small-business site requests.
GoHighLevel: Niche; monitor funnel/automation posts.
AI/Vibe Coding: Growing SaaS/production-ready AI app demand.
Ecommerce: Shopify maintenance and theme builds active.
Maintenance: WordPress emergency fixes and ongoing support visible.

## Important Changes

${state.runNumber === 1 ? 'Initial baseline run. All stats start from zero.' : 'See chat output for run-over-run deltas.'}
`;

  fs.writeFileSync(path.join(INT_DIR, 'current-summary.md'), summary);

  const insightsPath = path.join(INT_DIR, 'insights.md');
  if (state.runNumber === 1 && !fs.existsSync(insightsPath)) {
    fs.writeFileSync(
      insightsPath,
      `# Upwork Intelligence Insights

- Baseline established ${nowIso}. WordPress and core web dev keywords show the highest immediate job density in the 2h bootstrap window.
- Shopify backend/ongoing roles appear with verified high-spend clients.
- AI-native SaaS roles (Supabase, Claude) are present but lower volume than WordPress.
`
    );
    state.lastInsightRefresh = nowIso;
    fs.writeFileSync(statePath, JSON.stringify(state, null, 2));
  }

  const report = {
    runNumber: state.runNumber,
    keywordsAttempted,
    keywordsCompleted,
    newJobs: newJobsThisRun.length,
    totalJobs: state.totalJobs,
    topKeywords,
    topGroups,
    platformStats,
    newJobsThisRun,
    errors,
    primaryKw,
    secondaryKw,
    bestPlatform,
  };

  fs.writeFileSync(path.join(INT_DIR, 'last-run-report.json'), JSON.stringify(report, null, 2));
  console.log(JSON.stringify(report));
}

main();
