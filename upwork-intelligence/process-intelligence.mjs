#!/usr/bin/env node
import fs from 'fs';
import path from 'path';

const ROOT = path.dirname(new URL(import.meta.url).pathname);
const KEYWORDS = JSON.parse(fs.readFileSync(path.join(ROOT, 'keywords.json'), 'utf8'));
const WINDOW_HOURS = process.argv.includes('--first-run') ? 2 : 1;
const NOW = Date.parse(process.argv.find(a => a.startsWith('--now='))?.slice(6) || new Date().toISOString());
const RUN = Number(process.argv.find(a => a.startsWith('--run='))?.slice(6) || 1);

const RAW = path.join(ROOT, 'search-raw');
const jobsPath = path.join(ROOT, 'jobs.jsonl');
const statePath = path.join(ROOT, 'state.json');

const SKIP_RE = /gambling|casino|crypto trading|onlyfans|adult content|dating app|igaming/i;

function normUrl(u) {
  if (!u) return null;
  return u.split('?')[0];
}

function parseBudget(job) {
  const b = job.budget;
  if (!b) return { fixed: null, rateMin: null, rateMax: null };
  const hr = b.match(/([\d,]+(?:\.\d+)?)\s*[–-]\s*([\d,]+(?:\.\d+)?)\s*\/hr/i);
  if (hr) return { fixed: null, rateMin: parseFloat(hr[1].replace(/,/g, '')), rateMax: parseFloat(hr[2].replace(/,/g, '')) };
  const singleHr = b.match(/([\d,]+(?:\.\d+)?)\s*\/hr/i);
  if (singleHr) {
    const v = parseFloat(singleHr[1].replace(/,/g, ''));
    return { fixed: null, rateMin: v, rateMax: v };
  }
  const fixed = b.match(/^([\d,]+(?:\.\d+)?)/);
  if (fixed) return { fixed: parseFloat(fixed[1].replace(/,/g, '')), rateMin: null, rateMax: null };
  return { fixed: null, rateMin: null, rateMax: null };
}

function parseSpend(s) {
  if (!s) return null;
  const m = String(s).replace(/,/g, '').match(/([\d.]+)/);
  return m ? parseFloat(m[1]) : null;
}

function confidence(n) {
  if (n <= 4) return 'Very Low';
  if (n <= 14) return 'Low';
  if (n <= 39) return 'Medium';
  if (n <= 99) return 'High';
  return 'Very High';
}

function median(arr) {
  if (!arr.length) return null;
  const s = [...arr].sort((a, b) => a - b);
  const mid = Math.floor(s.length / 2);
  return s.length % 2 ? s[mid] : (s[mid - 1] + s[mid]) / 2;
}

function opportunityScore(stats) {
  const recency = Math.min(stats.jobsLast24h / 5, 1) * 25;
  const budget = Math.min((stats.avgBudgetFixed || 0) / 2000 + (stats.avgRateHourly || 0) / 80, 1) * 25;
  const props = stats.medianProposals == null ? 10 : Math.max(0, 25 - stats.medianProposals);
  const highB = Math.min(stats.pctHighBudget / 100, 1) * 15;
  const ver = Math.min(stats.pctVerified / 100, 1) * 10;
  return Math.round(Math.min(100, Math.max(1, recency + budget + props + highB + ver)));
}

function jobFromRaw(job, keyword, group) {
  const url = normUrl(job.url);
  if (!url) return null;
  const posted = job.published_date || job.created_date;
  const ts = posted ? Date.parse(posted) : null;
  if (ts && NOW - ts > WINDOW_HOURS * 3600 * 1000) return null;
  const text = `${job.title || ''} ${job.description_snippet || ''}`;
  if (SKIP_RE.test(text)) return null;
  const { fixed, rateMin, rateMax } = parseBudget(job);
  const client = job.client || {};
  return {
    url,
    title: job.title,
    matchedKeyword: [keyword],
    keywordGroup: group,
    postedAt: posted || null,
    type: job.job_type || null,
    budget: job.budget || null,
    budgetFixed: fixed,
    rateMin,
    rateMax,
    duration: job.duration || null,
    proposals: job.proposal_count ?? null,
    clientCountry: client.country || null,
    paymentVerified: client.verification_status === 'VERIFIED',
    clientSpend: parseSpend(client.total_spent),
    clientHireRate: null,
    clientRating: client.rating ?? null,
    experienceLevel: job.experience_level || null,
    skills: job.skills || [],
  };
}

function loadExistingJobs() {
  const map = new Map();
  if (!fs.existsSync(jobsPath)) return map;
  for (const line of fs.readFileSync(jobsPath, 'utf8').split('\n')) {
    if (!line.trim()) continue;
    const j = JSON.parse(line);
    map.set(j.url, j);
  }
  return map;
}

function ingestRawSearches() {
  const ingested = [];
  const batchDir = path.join(ROOT, 'search-batches');
  if (fs.existsSync(batchDir)) {
    for (const f of fs.readdirSync(batchDir).filter(x => x.endsWith('.json')).sort()) {
      const batch = JSON.parse(fs.readFileSync(path.join(batchDir, f), 'utf8'));
      for (const item of batch) {
        const jobs = item.response?.jobs || item.jobs || [];
        for (const job of jobs) {
          const rec = jobFromRaw(job, item.keyword, item.group);
          if (rec) ingested.push(rec);
        }
      }
    }
  }
  const runResults = path.join(ROOT, 'run-results.jsonl');
  if (fs.existsSync(runResults)) {
    for (const line of fs.readFileSync(runResults, 'utf8').split('\n')) {
      if (!line.trim()) continue;
      const { keyword, group, jobs } = JSON.parse(line);
      if (!jobs?.length) continue;
      for (const job of jobs) {
        const rec = jobFromRaw(job, keyword, group);
        if (rec) ingested.push(rec);
      }
    }
  }
  if (!fs.existsSync(RAW)) return ingested;
  for (const f of fs.readdirSync(RAW).filter(x => x.endsWith('.json'))) {
    const meta = JSON.parse(fs.readFileSync(path.join(RAW, f), 'utf8'));
    const { keyword, group, response } = meta;
    if (!response?.jobs) continue;
    for (const job of response.jobs) {
      const rec = jobFromRaw(job, keyword, group);
      if (rec) ingested.push(rec);
    }
  }
  return ingested;
}

const jobsMap = loadExistingJobs();
const newThisRun = [];
for (const rec of ingestRawSearches()) {
  const existing = jobsMap.get(rec.url);
  if (existing) {
    for (const kw of rec.matchedKeyword) {
      if (!existing.matchedKeyword.includes(kw)) existing.matchedKeyword.push(kw);
    }
  } else {
    jobsMap.set(rec.url, rec);
    newThisRun.push(rec);
  }
}

if (newThisRun.length) {
  fs.appendFileSync(jobsPath, newThisRun.map(j => JSON.stringify(j)).join('\n') + '\n');
}

const allJobs = [...jobsMap.values()];
const ms24 = 24 * 3600 * 1000;

const keywordStats = {};
for (const { keyword, group } of KEYWORDS) {
  keywordStats[keyword] = {
    keyword,
    group,
    totalJobs: 0,
    jobsLast24h: 0,
    fixedBudgets: [],
    hourlyRates: [],
    proposals: [],
    verified: 0,
    spends: [],
    highBudget: 0,
  };
}

for (const j of allJobs) {
  for (const kw of j.matchedKeyword || []) {
    const s = keywordStats[kw];
    if (!s) continue;
    s.totalJobs++;
    if (j.postedAt && NOW - Date.parse(j.postedAt) <= ms24) s.jobsLast24h++;
    if (j.budgetFixed != null) s.fixedBudgets.push(j.budgetFixed);
    if (j.rateMin != null) s.hourlyRates.push((j.rateMin + (j.rateMax ?? j.rateMin)) / 2);
    if (j.proposals != null) s.proposals.push(j.proposals);
    if (j.paymentVerified) s.verified++;
    if (j.clientSpend != null) s.spends.push(j.clientSpend);
    const high = (j.budgetFixed != null && j.budgetFixed >= 1000) || (j.rateMin != null && j.rateMin >= 40);
    if (high) s.highBudget++;
  }
}

const keywordStatsOut = {};
for (const [kw, s] of Object.entries(keywordStats)) {
  const n = s.totalJobs;
  const avgBudgetFixed = s.fixedBudgets.length ? s.fixedBudgets.reduce((a, b) => a + b, 0) / s.fixedBudgets.length : null;
  const avgRateHourly = s.hourlyRates.length ? s.hourlyRates.reduce((a, b) => a + b, 0) / s.hourlyRates.length : null;
  const row = {
    totalJobs: n,
    jobsLast24h: s.jobsLast24h,
    avgBudgetFixed: avgBudgetFixed != null ? Math.round(avgBudgetFixed) : null,
    avgRateHourly: avgRateHourly != null ? Math.round(avgRateHourly * 100) / 100 : null,
    medianProposals: median(s.proposals),
    pctVerified: n ? Math.round((s.verified / n) * 100) : 0,
    avgClientSpend: s.spends.length ? Math.round(s.spends.reduce((a, b) => a + b, 0) / s.spends.length) : null,
    pctHighBudget: n ? Math.round((s.highBudget / n) * 100) : 0,
    sampleConfidence: confidence(n),
  };
  row.opportunityScore = opportunityScore({ ...row, medianProposals: row.medianProposals ?? 50 });
  keywordStatsOut[kw] = row;
}

fs.writeFileSync(path.join(ROOT, 'keyword-stats.json'), JSON.stringify(keywordStatsOut, null, 2));

const groups = {};
for (const { group } of KEYWORDS) groups[group] = { group, keywords: [], totalJobs: 0, jobsLast24h: 0, scores: [] };
for (const [kw, st] of Object.entries(keywordStatsOut)) {
  const g = groups[KEYWORDS.find(k => k.keyword === kw).group];
  g.keywords.push(kw);
  g.totalJobs += st.totalJobs;
  g.jobsLast24h += st.jobsLast24h;
  g.scores.push(st.opportunityScore);
}
const groupStatsOut = Object.values(groups).map(g => ({
  group: g.group,
  totalJobs: g.totalJobs,
  jobsLast24h: g.jobsLast24h,
  avgOpportunityScore: g.scores.length ? Math.round(g.scores.reduce((a, b) => a + b, 0) / g.scores.length) : 0,
  keywordCount: g.keywords.length,
})).sort((a, b) => b.jobsLast24h - a.jobsLast24h);
fs.writeFileSync(path.join(ROOT, 'group-stats.json'), JSON.stringify(groupStatsOut, null, 2));

const platformMap = {
  WordPress: k => /wordpress|woocommerce|elementor|bricks/i.test(k),
  Webflow: k => /webflow|figma to webflow/i.test(k),
  Framer: k => /framer|figma to framer/i.test(k),
  GoHighLevel: k => /gohighlevel|go high level|GHL/i.test(k),
  Shopify: k => /shopify/i.test(k),
  WooCommerce: k => /woocommerce/i.test(k),
  Shopware: k => /shopware/i.test(k),
  Lovable: k => /lovable/i.test(k),
  Bolt: k => /bolt/i.test(k),
  v0: k => /v0|vercel/i.test(k),
  'Next.js': k => /next/i.test(k),
};

const platformStatsOut = {};
for (const [name, pred] of Object.entries(platformMap)) {
  const kws = KEYWORDS.filter(k => pred(k.keyword)).map(k => k.keyword);
  let totalJobs = 0, jobsLast24h = 0, scores = [], fixed = [], rates = [], props = [];
  for (const kw of kws) {
    const st = keywordStatsOut[kw];
    if (!st) continue;
    totalJobs += st.totalJobs;
    jobsLast24h += st.jobsLast24h;
    scores.push(st.opportunityScore);
    if (st.avgBudgetFixed) fixed.push(st.avgBudgetFixed);
    if (st.avgRateHourly) rates.push(st.avgRateHourly);
    if (st.medianProposals != null) props.push(st.medianProposals);
  }
  platformStatsOut[name] = {
    jobs: totalJobs,
    jobsLast24h,
    avgBudgetFixed: fixed.length ? Math.round(fixed.reduce((a, b) => a + b, 0) / fixed.length) : null,
    avgRateHourly: rates.length ? Math.round(rates.reduce((a, b) => a + b, 0) / rates.length * 100) / 100 : null,
    medianProposals: median(props),
    score: scores.length ? Math.round(scores.reduce((a, b) => a + b, 0) / scores.length) : 0,
    confidence: confidence(totalJobs),
  };
}
fs.writeFileSync(path.join(ROOT, 'platform-stats.json'), JSON.stringify(platformStatsOut, null, 2));

const knownUrls = [...jobsMap.keys()];
const attempted = Number(process.env.KEYWORDS_ATTEMPTED || KEYWORDS.length);
const completed = Number(process.env.KEYWORDS_COMPLETED || KEYWORDS.length);
const failed = (process.env.KEYWORDS_FAILED || '').split('|').filter(Boolean);

const state = {
  lastRunAt: new Date(NOW).toISOString(),
  runNumber: RUN,
  totalJobs: jobsMap.size,
  knownJobUrls: knownUrls,
  lastInsightRefresh: null,
};
fs.writeFileSync(statePath, JSON.stringify(state, null, 2));

const runLog = {
  timestamp: state.lastRunAt,
  runNumber: RUN,
  keywordsAttempted: attempted,
  keywordsCompleted: completed,
  newJobs: newThisRun.length,
  totalJobs: jobsMap.size,
  top3Keywords: Object.entries(keywordStatsOut).sort((a, b) => b[1].opportunityScore - a[1].opportunityScore).slice(0, 3).map(([k]) => k),
  errors: failed,
};
fs.appendFileSync(path.join(ROOT, 'run-log.jsonl'), JSON.stringify(runLog) + '\n');

const top10 = Object.entries(keywordStatsOut)
  .sort((a, b) => b[1].opportunityScore - a[1].opportunityScore)
  .slice(0, 10);

let summary = `# Upwork Market Intelligence

Last updated: ${state.lastRunAt}
Run: ${RUN}
Total jobs tracked: ${jobsMap.size}
Keywords attempted: ${attempted}
Keywords completed: ${completed}

## Top Opportunities

`;
for (const [kw, st] of top10) {
  summary += `- **${kw}** — score ${st.opportunityScore}, jobs24h ${st.jobsLast24h}, total ${st.totalJobs}, avg fixed $${st.avgBudgetFixed ?? 'n/a'}, avg hourly $${st.avgRateHourly ?? 'n/a'}/hr, median proposals ${st.medianProposals ?? 'n/a'}, ${st.sampleConfidence}\n`;
}

summary += `\n## Strongest Groups\n\n`;
for (const g of groupStatsOut.slice(0, 8)) {
  summary += `- ${g.group}: ${g.jobsLast24h} jobs (24h), score avg ${g.avgOpportunityScore}\n`;
}

summary += `\n## Platform Ranking\n\n`;
for (const [p, st] of Object.entries(platformStatsOut).sort((a, b) => b[1].score - a[1].score)) {
  summary += `- ${p}: score ${st.score}, jobs ${st.jobs}, jobs24h ${st.jobsLast24h}\n`;
}

summary += `\n## Positioning Recommendation\n\n`;
const primary = top10[0]?.[0] || 'wordpress developer';
const secondary = top10[1]?.[0] || 'webflow developer';
summary += `Primary keyword: ${primary}\nSecondary keyword: ${secondary}\nBest platform/service: WordPress + Next.js hybrid delivery\nOverview keywords: ${primary}, ${secondary}, SaaS, Web Development\nSkill tags: WordPress, Webflow, Next.js, Supabase, SEO\n`;

fs.writeFileSync(path.join(ROOT, 'current-summary.md'), summary);

console.log(JSON.stringify({ newJobs: newThisRun.length, totalJobs: jobsMap.size, top10: top10.map(([k, s]) => ({ k, score: s.opportunityScore })) }));
