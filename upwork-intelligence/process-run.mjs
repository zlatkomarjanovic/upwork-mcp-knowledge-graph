import fs from 'fs';
import path from 'path';

const DIR = path.dirname(new URL(import.meta.url).pathname);
const WINDOW_MS = 2 * 60 * 60 * 1000; // first run: 2h
const SKIP_PATTERNS = /\b(crypto trading|gambling|iGaming|adult|dating|alcohol)\b/i;

const keywordsByGroup = JSON.parse(fs.readFileSync(path.join(DIR, 'keywords.json'), 'utf8'));
const keywordToGroup = {};
for (const [g, kws] of Object.entries(keywordsByGroup)) {
  for (const k of kws) keywordToGroup[k] = g;
}

function normUrl(url) {
  if (!url) return null;
  const m = url.match(/(https:\/\/www\.upwork\.com\/jobs\/~[^?]+)/);
  return m ? m[1] : url.split('?')[0];
}

function parseMoney(s) {
  if (!s) return null;
  const n = parseFloat(String(s).replace(/[^0-9.]/g, ''));
  return Number.isFinite(n) ? n : null;
}

function parseHourlyRate(budget) {
  if (!budget || !String(budget).includes('/hr')) return null;
  const parts = String(budget).split('–').map((p) => parseMoney(p));
  if (parts.length === 2) return (parts[0] + parts[1]) / 2;
  return parts[0];
}

function parseClientSpend(s) {
  if (!s) return null;
  return parseMoney(s);
}

function jobFromRaw(j, keyword, group) {
  const url = normUrl(j.url);
  if (!url) return null;
  const title = j.title || '';
  const snippet = j.description_snippet || '';
  if (SKIP_PATTERNS.test(title + snippet)) return null;

  const postedAt = j.published_date || j.created_date;
  if (!postedAt) return null;
  const t = new Date(postedAt).getTime();
  if (Date.now() - t > WINDOW_MS) return null;

  const client = j.client || {};
  return {
    url,
    title,
    matchedKeyword: [keyword],
    keywordGroup: group,
    postedAt,
    type: j.job_type || null,
    budget: j.job_type === 'fixed' ? j.budget || null : null,
    hourlyRate: j.job_type === 'hourly' ? j.budget || null : null,
    duration: j.duration || null,
    proposals: j.proposal_count ?? null,
    clientCountry: client.country || null,
    paymentVerified: client.verification_status === 'VERIFIED',
    clientSpend: client.total_spent || null,
    clientHireRate: null,
    clientRating: client.rating ?? null,
    experienceLevel: j.experience_level || null,
    skills: j.skills || [],
  };
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

function confidence(n) {
  if (n >= 100) return 'Very High';
  if (n >= 40) return 'High';
  if (n >= 15) return 'Medium';
  if (n >= 5) return 'Low';
  return 'Very Low';
}

function median(arr) {
  if (!arr.length) return null;
  const s = [...arr].sort((a, b) => a - b);
  const m = Math.floor(s.length / 2);
  return s.length % 2 ? s[m] : (s[m - 1] + s[m]) / 2;
}

function avg(arr) {
  return arr.length ? arr.reduce((a, b) => a + b, 0) / arr.length : null;
}

function isHighBudget(job) {
  if (job.type === 'fixed') {
    const b = parseMoney(job.budget);
    return b != null && b >= 1000;
  }
  const r = parseHourlyRate(job.hourlyRate);
  return r != null && r >= 40;
}

function opportunityScore(jobs, jobs24h) {
  if (!jobs.length) return 1;
  const recency = Math.min(jobs24h * 8, 40);
  const fixed = jobs.filter((j) => j.type === 'fixed').map((j) => parseMoney(j.budget)).filter(Boolean);
  const hourly = jobs.filter((j) => j.type === 'hourly').map((j) => parseHourlyRate(j.hourlyRate)).filter(Boolean);
  const budgetScore = Math.min(((avg(fixed) || 0) / 50 + (avg(hourly) || 0) * 2) / 2, 25);
  const props = jobs.map((j) => j.proposals).filter((p) => p != null);
  const medP = median(props);
  const compScore = medP == null ? 10 : Math.max(0, 20 - medP / 2);
  const hi = jobs.filter(isHighBudget).length / jobs.length;
  const hiScore = hi * 10;
  const ver = jobs.filter((j) => j.paymentVerified).length / jobs.length;
  const verScore = ver * 5;
  return Math.round(Math.min(100, Math.max(1, recency + budgetScore + compScore + hiScore + verScore)));
}

function platformFromJob(job) {
  const text = [job.title, ...(job.skills || [])].join(' ').toLowerCase();
  const map = [
    ['WordPress', /wordpress|elementor|woocommerce|bricks/],
    ['Webflow', /webflow/],
    ['Framer', /framer/],
    ['GoHighLevel', /gohighlevel|go high level|ghl/],
    ['Shopify', /shopify/],
    ['WooCommerce', /woocommerce/],
    ['Shopware', /shopware/],
    ['Lovable', /lovable/],
    ['Bolt', /bolt\.new|bolt developer/],
    ['v0', /\bv0\b|v0 vercel/],
    ['Next.js', /next\.?js/],
  ];
  for (const [name, re] of map) if (re.test(text)) return name;
  return null;
}

const rawPath = process.argv[2] || path.join(DIR, 'raw-searches.json');
const metaPath = process.argv[3] || path.join(DIR, 'run-meta.json');
const raw = JSON.parse(fs.readFileSync(rawPath, 'utf8'));
const meta = JSON.parse(fs.readFileSync(metaPath, 'utf8'));

const existing = loadJobs();
const known = new Set(existing.map((j) => j.url));
const merged = new Map(existing.map((j) => [j.url, { ...j }]));
const newThisRun = [];

for (const entry of raw) {
  const { keyword, group, status, jobs, error } = entry;
  if (status !== 'ok' || !jobs) continue;
  for (const j of jobs) {
    const rec = jobFromRaw(j, keyword, group);
    if (!rec) continue;
    if (merged.has(rec.url)) {
      const ex = merged.get(rec.url);
      if (!ex.matchedKeyword.includes(keyword)) ex.matchedKeyword.push(keyword);
    } else {
      merged.set(rec.url, rec);
      if (!known.has(rec.url)) {
        newThisRun.push(rec);
        known.add(rec.url);
      }
    }
  }
}

const allJobs = [...merged.values()];
if (newThisRun.length) {
  fs.appendFileSync(path.join(DIR, 'jobs.jsonl'), newThisRun.map((j) => JSON.stringify(j)).join('\n') + '\n');
}

const now = Date.now();
const ms24 = 24 * 60 * 60 * 1000;

const keywordStats = {};
for (const [group, kws] of Object.entries(keywordsByGroup)) {
  for (const kw of kws) {
    const matched = allJobs.filter((j) => j.matchedKeyword.includes(kw));
    const last24 = matched.filter((j) => now - new Date(j.postedAt).getTime() <= ms24);
    const fixed = matched.filter((j) => j.type === 'fixed').map((j) => parseMoney(j.budget)).filter(Boolean);
    const hourly = matched.filter((j) => j.type === 'hourly').map((j) => parseHourlyRate(j.hourlyRate)).filter(Boolean);
    const props = matched.map((j) => j.proposals).filter((p) => p != null);
    const spends = matched.map((j) => parseClientSpend(j.clientSpend)).filter(Boolean);
    keywordStats[kw] = {
      keywordGroup: group,
      totalJobs: matched.length,
      jobsLast24h: last24.length,
      avgBudgetFixed: avg(fixed),
      avgRateHourly: avg(hourly),
      medianProposals: median(props),
      pctVerified: matched.length ? matched.filter((j) => j.paymentVerified).length / matched.length : 0,
      avgClientSpend: avg(spends),
      pctHighBudget: matched.length ? matched.filter(isHighBudget).length / matched.length : 0,
      opportunityScore: opportunityScore(matched, last24.length),
      sampleConfidence: confidence(matched.length),
    };
  }
}

const groupStats = {};
for (const group of Object.keys(keywordsByGroup)) {
  const matched = allJobs.filter((j) => j.keywordGroup === group || keywordsByGroup[group].some((k) => j.matchedKeyword.includes(k)));
  const last24 = matched.filter((j) => now - new Date(j.postedAt).getTime() <= ms24);
  groupStats[group] = {
    totalJobs: matched.length,
    jobsLast24h: last24.length,
    opportunityScore: opportunityScore(matched, last24.length),
    sampleConfidence: confidence(matched.length),
  };
}

const platformStats = {};
const platforms = ['WordPress', 'Webflow', 'Framer', 'GoHighLevel', 'Shopify', 'WooCommerce', 'Shopware', 'Lovable', 'Bolt', 'v0', 'Next.js'];
for (const p of platforms) {
  const matched = allJobs.filter((j) => platformFromJob(j) === p);
  const last24 = matched.filter((j) => now - new Date(j.postedAt).getTime() <= ms24);
  const fixed = matched.filter((j) => j.type === 'fixed').map((j) => parseMoney(j.budget)).filter(Boolean);
  const hourly = matched.filter((j) => j.type === 'hourly').map((j) => parseHourlyRate(j.hourlyRate)).filter(Boolean);
  const props = matched.map((j) => j.proposals).filter((p) => p != null);
  platformStats[p] = {
    totalJobs: matched.length,
    jobsLast24h: last24.length,
    avgBudgetFixed: avg(fixed),
    avgRateHourly: avg(hourly),
    medianProposals: median(props),
    opportunityScore: opportunityScore(matched, last24.length),
    sampleConfidence: confidence(matched.length),
  };
}

fs.writeFileSync(path.join(DIR, 'keyword-stats.json'), JSON.stringify(keywordStats, null, 2));
fs.writeFileSync(path.join(DIR, 'group-stats.json'), JSON.stringify(groupStats, null, 2));
fs.writeFileSync(path.join(DIR, 'platform-stats.json'), JSON.stringify(platformStats, null, 2));

const runNumber = meta.runNumber;
const state = {
  lastRunAt: new Date().toISOString(),
  runNumber,
  totalJobs: allJobs.length,
  knownJobUrls: [...known],
  lastInsightRefresh: null,
};
fs.writeFileSync(path.join(DIR, 'state.json'), JSON.stringify(state));

const topKw = Object.entries(keywordStats)
  .sort((a, b) => b[1].opportunityScore - a[1].opportunityScore)
  .slice(0, 3)
  .map(([k]) => k);

const log = {
  timestamp: new Date().toISOString(),
  runNumber,
  keywordsAttempted: meta.keywordsAttempted,
  keywordsCompleted: meta.keywordsCompleted,
  newJobs: newThisRun.length,
  totalJobs: allJobs.length,
  top3Keywords: topKw,
  errors: meta.errors || [],
};
fs.appendFileSync(path.join(DIR, 'run-log.jsonl'), JSON.stringify(log) + '\n');

const top10 = Object.entries(keywordStats)
  .sort((a, b) => b[1].opportunityScore - a[1].opportunityScore)
  .slice(0, 10);

const topGroups = Object.entries(groupStats).sort((a, b) => b[1].opportunityScore - a[1].opportunityScore);

const primary = top10[0]?.[0] || 'web development';
const secondary = top10[1]?.[0] || 'wordpress developer';

const summary = `# Upwork Market Intelligence

Last updated: ${new Date().toISOString()}
Run: ${runNumber}
Total jobs tracked: ${allJobs.length}
Keywords attempted: ${meta.keywordsAttempted}
Keywords completed: ${meta.keywordsCompleted}

## Top Opportunities

${top10
  .map(
    ([k, s]) =>
      `- **${k}** — score ${s.opportunityScore}, confidence ${s.sampleConfidence}, jobs24h ${s.jobsLast24h}, total ${s.totalJobs}, avg fixed ${s.avgBudgetFixed?.toFixed(0) ?? 'n/a'}, avg hourly ${s.avgRateHourly?.toFixed(1) ?? 'n/a'}, median proposals ${s.medianProposals ?? 'n/a'}`
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
Best platform/service: WordPress / Next.js (by volume in window)
Overview keywords: ${top10.slice(0, 5).map(([k]) => k).join(', ')}
Skill tags: Web Development, WordPress, Next.js, Web Design, Supabase

## Current Verdicts

WordPress: Steady small-project and Elementor demand in window.
Webflow: Lower volume; design-heavy hybrid posts.
Framer: Niche; appears in multi-tool design posts.
GoHighLevel: Low sample this window.
AI/Vibe Coding: Claude/Supabase/AI-assisted web posts active.
Ecommerce: Shopify setup demand present.
Maintenance: DevOps + long-term ownership posts appearing.

## Important Changes

Initial baseline run — no prior comparison.
`;

fs.writeFileSync(path.join(DIR, 'current-summary.md'), summary);

const out = {
  runNumber,
  meta,
  newThisRun,
  keywordStats,
  groupStats,
  platformStats,
  top10,
  topGroups: topGroups.slice(0, 5),
};
fs.writeFileSync(path.join(DIR, 'chat-out.json'), JSON.stringify(out, null, 2));
console.log(JSON.stringify({ newJobs: newThisRun.length, total: allJobs.length, completed: meta.keywordsCompleted, attempted: meta.keywordsAttempted }));
