#!/usr/bin/env node
import fs from 'fs';
import path from 'path';

const DIR = path.join(process.cwd(), 'upwork-intelligence');
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

const PLATFORMS = [
  'WordPress', 'Webflow', 'Framer', 'GoHighLevel', 'Shopify', 'WooCommerce',
  'Shopware', 'Lovable', 'Bolt', 'v0', 'Next.js',
];

const SKIP_RE =
  /\b(alcohol|gambling|adult|crypto trading|dating|casino|porn|escort)\b/i;

function normUrl(url) {
  if (!url) return null;
  try {
    const u = new URL(url.split('?')[0]);
    return u.origin + u.pathname;
  } catch {
    return url.split('?')[0];
  }
}

function parseBudget(job) {
  const b = job.budget;
  if (!b) return { fixed: null, hourlyMin: null, hourlyMax: null, raw: null };
  const raw = b;
  if (job.job_type === 'hourly' || /\/hr/i.test(b)) {
    const m = b.replace(/,/g, '').match(/([\d.]+)\s*[–-]\s*([\d.]+)/);
    if (m) return { fixed: null, hourlyMin: parseFloat(m[1]), hourlyMax: parseFloat(m[2]), raw };
    const s = b.replace(/[^\d.]/g, '');
    const n = parseFloat(s);
    return { fixed: null, hourlyMin: n || null, hourlyMax: n || null, raw };
  }
  const n = parseFloat(b.replace(/,/g, '').replace(/[^\d.]/g, ''));
  return { fixed: Number.isFinite(n) ? n : null, hourlyMin: null, hourlyMax: null, raw };
}

function parseSpend(s) {
  if (!s) return null;
  const n = parseFloat(String(s).replace(/[^0-9.]/g, ''));
  return Number.isFinite(n) ? n : null;
}

function isHighBudget(job, parsed) {
  if (job.job_type === 'hourly') {
    const rate = parsed.hourlyMax ?? parsed.hourlyMin;
    return rate != null && rate >= 40;
  }
  return parsed.fixed != null && parsed.fixed >= 1000;
}

function mapJob(raw, keyword, group) {
  const url = normUrl(raw.url);
  if (!url) return null;
  const title = raw.title || '';
  const snippet = raw.description_snippet || '';
  if (SKIP_RE.test(title + snippet)) return null;
  const parsed = parseBudget(raw);
  const client = raw.client || {};
  return {
    url,
    title,
    matchedKeyword: [keyword],
    keywordGroup: group,
    postedAt: raw.published_date || raw.created_date || null,
    type: raw.job_type || null,
    budget: parsed.raw,
    budgetFixed: parsed.fixed,
    hourlyMin: parsed.hourlyMin,
    hourlyMax: parsed.hourlyMax,
    duration: raw.duration || null,
    proposals: raw.proposal_count ?? null,
    clientCountry: client.country ?? null,
    paymentVerified: client.verification_status === 'VERIFIED',
    clientSpend: parseSpend(client.total_spent),
    clientHireRate: null,
    clientRating: client.rating ?? null,
    experienceLevel: raw.experience_level ?? null,
    skills: raw.skills || [],
  };
}

function median(nums) {
  const a = nums.filter((n) => n != null && Number.isFinite(n)).sort((x, y) => x - y);
  if (!a.length) return null;
  const mid = Math.floor(a.length / 2);
  return a.length % 2 ? a[mid] : (a[mid - 1] + a[mid]) / 2;
}

function avg(nums) {
  const a = nums.filter((n) => n != null && Number.isFinite(n));
  if (!a.length) return null;
  return a.reduce((s, n) => s + n, 0) / a.length;
}

function confidenceLabel(n) {
  if (n <= 4) return 'Very Low';
  if (n <= 14) return 'Low';
  if (n <= 39) return 'Medium';
  if (n <= 99) return 'High';
  return 'Very High';
}

function opportunityScore(jobs, jobs24h) {
  if (!jobs.length) return 1;
  const recency = Math.min(jobs24h * 8, 40);
  const fixed = jobs.map((j) => j.budgetFixed).filter(Boolean);
  const rates = jobs.map((j) => j.hourlyMax ?? j.hourlyMin).filter(Boolean);
  const budgetScore = Math.min(((avg(fixed) || 0) / 50 + (avg(rates) || 0)) / 2, 25);
  const props = jobs.map((j) => j.proposals).filter((p) => p != null);
  const propMed = median(props) ?? 20;
  const compScore = Math.max(0, 25 - propMed * 0.5);
  const highPct = jobs.filter((j) => {
    if (j.type === 'hourly') return (j.hourlyMax ?? j.hourlyMin ?? 0) >= 40;
    return (j.budgetFixed ?? 0) >= 1000;
  }).length / jobs.length;
  const highScore = highPct * 15;
  const verPct = jobs.filter((j) => j.paymentVerified).length / jobs.length;
  const verScore = verPct * 10;
  return Math.round(Math.min(100, Math.max(1, recency + budgetScore + compScore + highScore + verScore)));
}

function loadJsonl(file) {
  if (!fs.existsSync(file)) return [];
  return fs
    .readFileSync(file, 'utf8')
    .split('\n')
    .filter(Boolean)
    .map((l) => JSON.parse(l));
}

function appendJsonl(file, rows) {
  fs.mkdirSync(path.dirname(file), { recursive: true });
  const chunk = rows.map((r) => JSON.stringify(r)).join('\n') + (rows.length ? '\n' : '');
  fs.appendFileSync(file, chunk);
}

function writeCurrentSummary({
  nowIso,
  runNumber,
  catalog,
  keywordsAttempted,
  keywordsCompleted,
  keywordStats,
  groupStats,
  platformStats,
}) {
  const topKw = Object.entries(keywordStats)
    .sort((a, b) => b[1].opportunityScore - a[1].opportunityScore || b[1].jobsLast24h - a[1].jobsLast24h)
    .slice(0, 10);
  const topGroups = Object.entries(groupStats)
    .sort((a, b) => b[1].opportunityScore - a[1].opportunityScore)
    .slice(0, 5);
  const topPlatforms = Object.entries(platformStats)
    .filter(([, s]) => s.totalJobs > 0)
    .sort((a, b) => b[1].opportunityScore - a[1].opportunityScore);

  const primary = topKw.find(([, s]) => s.jobsLast24h >= 3)?.[0] || topKw[0]?.[0] || 'website development';
  const secondary =
    topKw.find(([k]) => k !== primary && /AI|gohighlevel|wordpress|shopify/i.test(k))?.[0] ||
    topKw[1]?.[0] ||
    primary;
  const bestPlatform = topPlatforms[0]?.[0] || 'WordPress';

  const lines = [
    '# Upwork Market Intelligence',
    '',
    `Last updated: ${nowIso}`,
    `Run: ${runNumber}`,
    `Total jobs tracked: ${catalog.length}`,
    `Keywords attempted: ${keywordsAttempted}`,
    `Keywords completed: ${keywordsCompleted}`,
    '',
    '## Top Opportunities',
    '',
    '| Keyword | jobsLast24h | totalJobs | avg fixed | avg hourly | median proposals | score | confidence |',
    '|---------|-------------|-----------|-----------|------------|------------------|-------|------------|',
  ];
  for (const [k, s] of topKw) {
    const af = s.avgBudgetFixed != null ? `$${s.avgBudgetFixed}` : '—';
    const ah = s.avgRateHourly != null ? `$${s.avgRateHourly}` : '—';
    const mp = s.medianProposals != null ? s.medianProposals : '—';
    lines.push(`| ${k} | ${s.jobsLast24h} | ${s.totalJobs} | ${af} | ${ah} | ${mp} | ${s.opportunityScore} | ${s.sampleConfidence} |`);
  }
  lines.push('', '## Strongest Groups', '');
  topGroups.forEach(([g, s], i) => {
    lines.push(`${i + 1}. ${g} (score ${s.opportunityScore}, ${s.jobsLast24h} jobs / 24h)`);
  });
  lines.push('', '## Platform Ranking', '');
  topPlatforms.slice(0, 8).forEach(([p, s], i) => {
    lines.push(`${i + 1}. ${p} (${s.totalJobs} jobs, score ${s.opportunityScore})`);
  });
  lines.push(
    '',
    '## Positioning Recommendation',
    '',
    `Primary keyword: **${primary}**`,
    `Secondary keyword: **${secondary}**`,
    `Best platform/service: **${bestPlatform}**`,
    `Overview keywords: ${topKw.slice(0, 5).map(([k]) => k).join(', ')}`,
    '',
    '## Current Verdicts',
    '',
    'See insights.md for durable notes; update verdicts when patterns shift across runs.',
    '',
    '## Important Changes',
    '',
    runNumber === 1 ? 'First baseline run. No prior comparison.' : '(Compare to previous run in chat output.)',
    ''
  );
  fs.writeFileSync(path.join(DIR, 'current-summary.md'), lines.join('\n'));
}

function detectPlatform(job) {
  const text = `${job.title} ${(job.skills || []).join(' ')} ${job.matchedKeyword.join(' ')}`.toLowerCase();
  if (/wordpress|elementor|woocommerce|bricks/.test(text)) return 'WordPress';
  if (/webflow/.test(text)) return 'Webflow';
  if (/framer/.test(text)) return 'Framer';
  if (/gohighlevel|go high level|\bghl\b/.test(text)) return 'GoHighLevel';
  if (/shopify/.test(text)) return 'Shopify';
  if (/woocommerce/.test(text)) return 'WooCommerce';
  if (/shopware/.test(text)) return 'Shopware';
  if (/lovable/.test(text)) return 'Lovable';
  if (/bolt\.new|\bbolt developer\b/.test(text)) return 'Bolt';
  if (/\bv0\b|v0 vercel/.test(text)) return 'v0';
  if (/next\.?js/.test(text)) return 'Next.js';
  return null;
}

function main() {
  const args = process.argv.slice(2);
  let batchPath = 'upwork-intelligence/run-batch.json';
  let nowIso = new Date().toISOString();
  let firstRun = false;
  for (let i = 0; i < args.length; i++) {
    if (args[i] === '--batch') batchPath = args[++i];
    if (args[i] === '--now') nowIso = args[++i];
    if (args[i] === '--first-run') firstRun = true;
  }

  const batch = JSON.parse(fs.readFileSync(batchPath, 'utf8'));
  const statePath = path.join(DIR, 'state.json');
  let state = { lastRunAt: null, runNumber: 0, totalJobs: 0, knownJobUrls: [], lastInsightRefresh: null };
  if (fs.existsSync(statePath)) state = JSON.parse(fs.readFileSync(statePath, 'utf8'));
  if (firstRun || state.runNumber === 0) firstRun = true;

  const runNumber = (state.runNumber || 0) + 1;
  const nowMs = new Date(nowIso).getTime();
  const windowMs = (firstRun ? 2 : 1) * 60 * 60 * 1000;

  const known = new Set((state.knownJobUrls || []).map(normUrl));
  const existingJobs = loadJsonl(path.join(DIR, 'jobs.jsonl'));
  for (const j of existingJobs) known.add(normUrl(j.url));

  const merged = new Map();
  const errors = [];
  let keywordsAttempted = batch.searches?.length || ALL_KEYWORDS.length;
  let keywordsCompleted = 0;
  const keywordHits = {};

  for (const search of batch.searches || []) {
    const { keyword, group, status, jobs = [], error } = search;
    keywordsAttempted = batch.searches.length;
    if (status === 'error') {
      errors.push({ keyword, error: error || 'unknown' });
      continue;
    }
    keywordsCompleted++;
    keywordHits[keyword] = (keywordHits[keyword] || 0);
    for (const raw of jobs) {
      const mapped = mapJob(raw, keyword, group);
      if (!mapped) continue;
      const posted = mapped.postedAt ? new Date(mapped.postedAt).getTime() : null;
      if (posted && nowMs - posted > windowMs) continue;
      const key = mapped.url;
      if (merged.has(key)) {
        const ex = merged.get(key);
        if (!ex.matchedKeyword.includes(keyword)) ex.matchedKeyword.push(keyword);
      } else {
        merged.set(key, mapped);
      }
      keywordHits[keyword]++;
    }
  }

  const newJobs = [];
  for (const job of merged.values()) {
    if (!known.has(job.url)) {
      newJobs.push(job);
      known.add(job.url);
    }
  }

  appendJsonl(path.join(DIR, 'jobs.jsonl'), newJobs);
  const allJobs = [...existingJobs];
  const byUrl = new Map(allJobs.map((j) => [normUrl(j.url), j]));
  for (const j of newJobs) byUrl.set(j.url, j);
  const catalog = [...byUrl.values()];

  const ms24h = 24 * 60 * 60 * 1000;
  const keywordStats = {};
  for (const { keyword, group } of ALL_KEYWORDS) {
    const jobs = catalog.filter((j) => j.matchedKeyword?.includes(keyword));
    const jobsLast24h = jobs.filter((j) => j.postedAt && nowMs - new Date(j.postedAt).getTime() <= ms24h).length;
    const fixed = jobs.map((j) => j.budgetFixed).filter((n) => n != null);
    const rates = jobs.map((j) => j.hourlyMax ?? j.hourlyMin).filter((n) => n != null);
    const props = jobs.map((j) => j.proposals).filter((n) => n != null);
    const spend = jobs.map((j) => j.clientSpend).filter((n) => n != null);
    const verified = jobs.filter((j) => j.paymentVerified).length;
    const high = jobs.filter((j) => isHighBudget(j, { fixed: j.budgetFixed, hourlyMin: j.hourlyMin, hourlyMax: j.hourlyMax })).length;
    const total = jobs.length;
    keywordStats[keyword] = {
      group,
      totalJobs: total,
      jobsLast24h,
      avgBudgetFixed: avg(fixed) != null ? Math.round(avg(fixed)) : null,
      avgRateHourly: avg(rates) != null ? Math.round(avg(rates) * 100) / 100 : null,
      medianProposals: median(props) != null ? Math.round(median(props)) : null,
      pctVerified: total ? Math.round((verified / total) * 100) : null,
      avgClientSpend: avg(spend) != null ? Math.round(avg(spend)) : null,
      pctHighBudget: total ? Math.round((high / total) * 100) : null,
      opportunityScore: opportunityScore(jobs, jobsLast24h),
      sampleConfidence: confidenceLabel(total),
    };
  }

  const groupStats = {};
  for (const [group, kws] of Object.entries(KEYWORD_GROUPS)) {
    const jobs = catalog.filter((j) => kws.some((k) => j.matchedKeyword?.includes(k)));
    const jobsLast24h = jobs.filter((j) => j.postedAt && nowMs - new Date(j.postedAt).getTime() <= ms24h).length;
    groupStats[group] = {
      totalJobs: jobs.length,
      jobsLast24h,
      opportunityScore: opportunityScore(jobs, jobsLast24h),
      sampleConfidence: confidenceLabel(jobs.length),
    };
  }

  const platformStats = {};
  for (const p of PLATFORMS) {
    const jobs = catalog.filter((j) => detectPlatform(j) === p);
    const jobsLast24h = jobs.filter((j) => j.postedAt && nowMs - new Date(j.postedAt).getTime() <= ms24h).length;
    const fixed = jobs.map((j) => j.budgetFixed).filter(Boolean);
    const rates = jobs.map((j) => j.hourlyMax ?? j.hourlyMin).filter(Boolean);
    const props = jobs.map((j) => j.proposals).filter(Boolean);
    platformStats[p] = {
      totalJobs: jobs.length,
      jobsLast24h,
      avgBudgetFixed: avg(fixed) != null ? Math.round(avg(fixed)) : null,
      avgRateHourly: avg(rates) != null ? Math.round(avg(rates) * 100) / 100 : null,
      medianProposals: median(props) != null ? Math.round(median(props)) : null,
      opportunityScore: opportunityScore(jobs, jobsLast24h),
      sampleConfidence: confidenceLabel(jobs.length),
    };
  }

  fs.mkdirSync(DIR, { recursive: true });
  fs.writeFileSync(path.join(DIR, 'keyword-stats.json'), JSON.stringify(keywordStats, null, 2));
  fs.writeFileSync(path.join(DIR, 'group-stats.json'), JSON.stringify(groupStats, null, 2));
  fs.writeFileSync(path.join(DIR, 'platform-stats.json'), JSON.stringify(platformStats, null, 2));

  const top3Keywords = Object.entries(keywordStats)
    .sort((a, b) => b[1].opportunityScore - a[1].opportunityScore)
    .slice(0, 3)
    .map(([k]) => k);

  appendJsonl(path.join(DIR, 'run-log.jsonl'), [{
    timestamp: nowIso,
    runNumber,
    keywordsAttempted,
    keywordsCompleted,
    newJobs: newJobs.length,
    totalJobs: catalog.length,
    top3Keywords,
    errors: errors.map((e) => e.keyword),
  }]);

  state = {
    lastRunAt: nowIso,
    runNumber,
    totalJobs: catalog.length,
    knownJobUrls: [...known].slice(-5000),
    lastInsightRefresh: state.lastInsightRefresh,
  };
  fs.writeFileSync(statePath, JSON.stringify(state, null, 2));

  const report = {
    runNumber,
    nowIso,
    keywordsAttempted,
    keywordsCompleted,
    newJobs,
    catalog,
    keywordStats,
    groupStats,
    platformStats,
    errors,
    firstRun,
  };
  fs.writeFileSync(path.join(DIR, 'last-run-report.json'), JSON.stringify(report, null, 2));
  writeCurrentSummary({
    nowIso,
    runNumber,
    catalog,
    keywordsAttempted,
    keywordsCompleted,
    keywordStats,
    groupStats,
    platformStats,
  });
  console.log(JSON.stringify({ runNumber, newJobs: newJobs.length, total: catalog.length, errors: errors.length }));
}

main();
