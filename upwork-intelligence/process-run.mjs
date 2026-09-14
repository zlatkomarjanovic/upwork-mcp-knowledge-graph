#!/usr/bin/env node
import fs from 'fs';
import path from 'path';

const DIR = path.dirname(new URL(import.meta.url).pathname);
const WINDOW_HOURS_FIRST = 2;
const WINDOW_HOURS = 1;

const KEYWORD_GROUPS = {
  'CORE WEB DEVELOPMENT': ['web development','website development','web developer','custom website','frontend developer','full stack developer'],
  'WEB DESIGN': ['web design','website design','website redesign','landing page design','UI UX website','responsive web design'],
  'WORDPRESS': ['wordpress','wordpress developer','wordpress website','wordpress development','wordpress redesign','wordpress customization','wordpress migration','wordpress speed optimization','wordpress maintenance','woocommerce','elementor developer','bricks builder'],
  'WEBFLOW / FRAMER': ['webflow','webflow developer','webflow website','webflow redesign','figma to webflow','framer','framer developer','framer website','framer redesign','figma to framer'],
  'AI / VIBE CODING': ['AI web development','AI web developer','vibe coding','claude code developer','cursor AI developer','lovable developer','lovable app','bolt developer','bolt.new','v0 developer','v0 vercel','replit developer','supabase developer','AI agent integration website'],
  'GOHIGHLEVEL': ['gohighlevel','go high level','GHL','gohighlevel developer','gohighlevel website','gohighlevel funnel','gohighlevel automation','gohighlevel CRM'],
  'ADJACENT PLATFORMS': ['squarespace website','wix website','wix studio','bubble developer'],
  'MODERN STACK': ['nextjs developer','next.js developer','nextjs website','react developer','figma to nextjs','tailwind developer','astro developer','sanity CMS'],
  'ECOMMERCE': ['ecommerce website','ecommerce developer','shopify developer','shopify website','woocommerce developer','shopware','shopware developer','shopware 6','headless ecommerce'],
  'MAINTENANCE / RETAINERS': ['website maintenance','website maintenance monthly','website support ongoing','website management ongoing','wordpress support retainer','webflow maintenance','shopify maintenance','ongoing web developer','web development retainer'],
  'CONVERSION / PERFORMANCE': ['conversion rate optimization','landing page optimization','website audit','core web vitals','page speed optimization','website speed optimization','technical SEO website'],
};

const SKIP_RE = /\b(crypto|bitcoin|gambling|casino|betting|poker|adult|escort|onlyfans|alcohol|brewery|distillery|dating|hookup)\b/i;

function normUrl(u) {
  if (!u) return null;
  try {
    const x = new URL(u.split('?')[0]);
    return x.origin + x.pathname;
  } catch { return u.split('?')[0]; }
}

function parseMoney(s) {
  if (!s || typeof s !== 'string') return null;
  const m = s.replace(/,/g, '').match(/([\d.]+)/);
  return m ? parseFloat(m[1]) : null;
}

function parseHourly(budget) {
  if (!budget || typeof budget !== 'string') return null;
  const nums = [...budget.replace(/,/g, '').matchAll(/([\d.]+)/g)].map(m => parseFloat(m[1]));
  if (!nums.length) return null;
  return nums.reduce((a, b) => a + b, 0) / nums.length;
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

function isHighBudget(job) {
  if (job.job_type === 'fixed') {
    const v = parseMoney(job.budget);
    return v != null && v >= 1000;
  }
  const hr = parseHourly(job.budget);
  return hr != null && hr >= 40;
}

function mapJob(raw, keyword, group) {
  const url = normUrl(raw.url);
  if (!url) return null;
  const text = `${raw.title || ''} ${raw.description_snippet || ''}`.toLowerCase();
  if (SKIP_RE.test(text)) return null;
  const c = raw.client || {};
  return {
    url,
    title: raw.title || null,
    matchedKeyword: [keyword],
    keywordGroup: group,
    postedAt: raw.published_date || raw.created_date || null,
    type: raw.job_type || null,
    budget: raw.job_type === 'fixed' ? (raw.budget || null) : null,
    hourlyRate: raw.job_type === 'hourly' ? (raw.budget || null) : null,
    duration: raw.duration || null,
    proposals: raw.proposal_count ?? null,
    clientCountry: c.country || null,
    paymentVerified: c.verification_status === 'VERIFIED',
    clientSpend: c.total_spent || null,
    clientHireRate: null,
    clientRating: c.rating ?? null,
    experienceLevel: raw.experience_level || null,
    skills: raw.skills || [],
    _rawBudget: raw.budget || null,
  };
}

function opportunityScore(stats) {
  const rec = Math.min(stats.jobsLast24h * 8, 40);
  const budget = Math.min((stats.avgBudgetFixed || 0) / 50 + (stats.avgRateHourly || 0) * 0.8, 25);
  const comp = stats.medianProposals != null ? Math.max(0, 20 - stats.medianProposals * 0.4) : 10;
  const hi = Math.min((stats.pctHighBudget || 0) * 0.15, 10);
  const ver = Math.min((stats.pctVerified || 0) * 0.05, 5);
  return Math.round(Math.min(100, Math.max(1, rec + budget + comp + hi + ver)));
}

function median(arr) {
  const a = arr.filter(x => x != null).sort((x, y) => x - y);
  if (!a.length) return null;
  const i = Math.floor(a.length / 2);
  return a.length % 2 ? a[i] : (a[i - 1] + a[i]) / 2;
}

function computeKeywordStats(jobs, keyword) {
  const matched = jobs.filter(j => j.matchedKeyword.includes(keyword));
  const now = Date.now();
  const d24 = 24 * 3600 * 1000;
  const last24 = matched.filter(j => j.postedAt && now - new Date(j.postedAt).getTime() <= d24);
  const fixed = matched.filter(j => j.type === 'fixed').map(j => parseMoney(j.budget)).filter(x => x != null);
  const hourly = matched.filter(j => j.type === 'hourly').map(j => parseHourly(j.hourlyRate || j._rawBudget)).filter(x => x != null);
  const props = matched.map(j => j.proposals).filter(x => x != null);
  const verified = matched.filter(j => j.paymentVerified).length;
  const hi = matched.filter(j => {
    if (j.type === 'fixed') { const v = parseMoney(j.budget); return v != null && v >= 1000; }
    const hr = parseHourly(j.hourlyRate || j._rawBudget);
    return hr != null && hr >= 40;
  }).length;
  const spends = matched.map(j => parseSpend(j.clientSpend)).filter(x => x != null);
  const stats = {
    totalJobs: matched.length,
    jobsLast24h: last24.length,
    avgBudgetFixed: fixed.length ? fixed.reduce((a, b) => a + b, 0) / fixed.length : null,
    avgRateHourly: hourly.length ? hourly.reduce((a, b) => a + b, 0) / hourly.length : null,
    medianProposals: median(props),
    pctVerified: matched.length ? Math.round((verified / matched.length) * 100) : null,
    avgClientSpend: spends.length ? spends.reduce((a, b) => a + b, 0) / spends.length : null,
    pctHighBudget: matched.length ? Math.round((hi / matched.length) * 100) : null,
    sampleConfidence: confidence(matched.length),
  };
  stats.opportunityScore = opportunityScore(stats);
  return stats;
}

const PLATFORM_MAP = {
  WordPress: k => /wordpress|elementor|bricks|woo/i.test(k),
  Webflow: k => /webflow|figma to webflow/i.test(k),
  Framer: k => /framer|figma to framer/i.test(k),
  GoHighLevel: k => /gohighlevel|go high level|GHL/i.test(k),
  Shopify: k => /shopify/i.test(k),
  WooCommerce: k => /woocommerce|woo/i.test(k),
  Shopware: k => /shopware/i.test(k),
  Lovable: k => /lovable/i.test(k),
  Bolt: k => /bolt/i.test(k),
  'v0': k => /v0/i.test(k),
  'Next.js': k => /next/i.test(k),
};

function main() {
  const inputPath = process.argv[2] || path.join(DIR, 'search-raw.json');
  const runAt = process.argv[3] || new Date().toISOString();
  const raw = JSON.parse(fs.readFileSync(inputPath, 'utf8'));
  const { searches = [], errors = [] } = raw;

  let state = { runNumber: 0, totalJobs: 0, knownJobUrls: [], lastRunAt: null, lastInsightRefresh: null };
  const statePath = path.join(DIR, 'state.json');
  if (fs.existsSync(statePath)) {
    try { state = { ...state, ...JSON.parse(fs.readFileSync(statePath, 'utf8')) }; } catch {}
  }
  const runNumber = (state.runNumber || 0) + 1;
  const firstRun = !state.lastRunAt;
  const windowMs = (firstRun ? WINDOW_HOURS_FIRST : WINDOW_HOURS) * 3600 * 1000;
  const cutoff = new Date(runAt).getTime() - windowMs;

  const known = new Set((state.knownJobUrls || []).map(normUrl));
  const jobsMap = new Map();

  const allKeywords = [];
  for (const [g, kws] of Object.entries(KEYWORD_GROUPS)) {
    for (const kw of kws) allKeywords.push({ kw, group: g });
  }

  for (const { keyword, group, jobs: jobList = [], error } of searches) {
    if (error) continue;
    for (const rawJob of jobList) {
      const posted = rawJob.published_date || rawJob.created_date;
      if (posted && new Date(posted).getTime() < cutoff) continue;
      const j = mapJob(rawJob, keyword, group);
      if (!j) continue;
      const ex = jobsMap.get(j.url);
      if (ex) {
        if (!ex.matchedKeyword.includes(keyword)) ex.matchedKeyword.push(keyword);
      } else jobsMap.set(j.url, j);
    }
  }

  const newJobs = [];
  for (const j of jobsMap.values()) {
    delete j._rawBudget;
    if (!known.has(j.url)) {
      newJobs.push(j);
      known.add(j.url);
    }
  }

  const jobsPath = path.join(DIR, 'jobs.jsonl');
  for (const j of newJobs) {
    fs.appendFileSync(jobsPath, JSON.stringify(j) + '\n');
  }

  const allJobs = [];
  if (fs.existsSync(jobsPath)) {
    for (const line of fs.readFileSync(jobsPath, 'utf8').split('\n')) {
      if (!line.trim()) continue;
      try { allJobs.push(JSON.parse(line)); } catch {}
    }
  }

  const keywordStats = {};
  for (const { kw } of allKeywords) keywordStats[kw] = computeKeywordStats(allJobs, kw);

  const groupStats = {};
  for (const [g, kws] of Object.entries(KEYWORD_GROUPS)) {
    const agg = { totalJobs: 0, jobsLast24h: 0, scores: [], keywords: kws.length };
    for (const kw of kws) {
      const s = keywordStats[kw];
      agg.totalJobs += s.totalJobs;
      agg.jobsLast24h += s.jobsLast24h;
      agg.scores.push(s.opportunityScore);
    }
    agg.avgOpportunityScore = agg.scores.length ? Math.round(agg.scores.reduce((a, b) => a + b, 0) / agg.scores.length) : 0;
    groupStats[g] = agg;
  }

  const platformStats = {};
  for (const [name, fn] of Object.entries(PLATFORM_MAP)) {
    const kws = allKeywords.filter(x => fn(x.kw)).map(x => x.kw);
    let jobs = allJobs.filter(j => j.matchedKeyword.some(m => kws.includes(m)));
    const now = Date.now();
    const d24 = 24 * 3600 * 1000;
    const fixed = jobs.filter(j => j.type === 'fixed').map(j => parseMoney(j.budget)).filter(x => x != null);
    const hourly = jobs.filter(j => j.type === 'hourly').map(j => parseHourly(j.hourlyRate)).filter(x => x != null);
    const props = jobs.map(j => j.proposals).filter(x => x != null);
    platformStats[name] = {
      jobs: jobs.length,
      jobsLast24h: jobs.filter(j => j.postedAt && now - new Date(j.postedAt).getTime() <= d24).length,
      avgBudgetFixed: fixed.length ? fixed.reduce((a, b) => a + b, 0) / fixed.length : null,
      avgRateHourly: hourly.length ? hourly.reduce((a, b) => a + b, 0) / hourly.length : null,
      medianProposals: median(props),
      sampleConfidence: confidence(jobs.length),
      opportunityScore: opportunityScore({
        jobsLast24h: jobs.filter(j => j.postedAt && now - new Date(j.postedAt).getTime() <= d24).length,
        avgBudgetFixed: fixed.length ? fixed.reduce((a, b) => a + b, 0) / fixed.length : 0,
        avgRateHourly: hourly.length ? hourly.reduce((a, b) => a + b, 0) / hourly.length : 0,
        medianProposals: median(props),
        pctHighBudget: jobs.length ? (jobs.filter(j => {
          if (j.type === 'fixed') return (parseMoney(j.budget) || 0) >= 1000;
          return (parseHourly(j.hourlyRate) || 0) >= 40;
        }).length / jobs.length) * 100 : 0,
        pctVerified: jobs.length ? (jobs.filter(j => j.paymentVerified).length / jobs.length) * 100 : 0,
      }),
    };
  }

  fs.writeFileSync(path.join(DIR, 'keyword-stats.json'), JSON.stringify(keywordStats, null, 2));
  fs.writeFileSync(path.join(DIR, 'group-stats.json'), JSON.stringify(groupStats, null, 2));
  fs.writeFileSync(path.join(DIR, 'platform-stats.json'), JSON.stringify(platformStats, null, 2));

  const top3 = [...allKeywords]
    .map(({ kw }) => ({ kw, ...keywordStats[kw] }))
    .sort((a, b) => b.opportunityScore - a.opportunityScore)
    .slice(0, 3)
    .map(x => x.kw);

  const log = {
    timestamp: runAt,
    runNumber,
    keywordsAttempted: allKeywords.length,
    keywordsCompleted: searches.filter(s => !s.error).length,
    newJobs: newJobs.length,
    totalJobs: allJobs.length,
    top3Keywords: top3,
    errors,
  };
  fs.appendFileSync(path.join(DIR, 'run-log.jsonl'), JSON.stringify(log) + '\n');

  state.lastRunAt = runAt;
  state.runNumber = runNumber;
  state.totalJobs = allJobs.length;
  state.knownJobUrls = [...known];
  fs.writeFileSync(statePath, JSON.stringify(state, null, 2));

  const top10 = Object.entries(keywordStats)
    .map(([keyword, s]) => ({ keyword, ...s }))
    .sort((a, b) => b.opportunityScore - a.opportunityScore)
    .slice(0, 10);

  const topGroups = Object.entries(groupStats)
    .map(([group, s]) => ({ group, ...s }))
    .sort((a, b) => b.avgOpportunityScore - a.avgOpportunityScore);

  const primary = top10[0]?.keyword || 'wordpress developer';
  const secondary = top10[1]?.keyword || 'webflow developer';

  const summary = `# Upwork Market Intelligence

Last updated: ${runAt}
Run: ${runNumber}
Total jobs tracked: ${allJobs.length}
Keywords attempted: ${allKeywords.length}
Keywords completed: ${searches.filter(s => !s.error).length}

## Top Opportunities

${top10.map((t, i) => `${i + 1}. **${t.keyword}** — score ${t.opportunityScore} (${t.sampleConfidence})
   - jobsLast24h: ${t.jobsLast24h} | total: ${t.totalJobs} | avg fixed: ${t.avgBudgetFixed != null ? '$' + Math.round(t.avgBudgetFixed) : 'n/a'} | avg hourly: ${t.avgRateHourly != null ? '$' + Math.round(t.avgRateHourly) + '/hr' : 'n/a'} | median proposals: ${t.medianProposals ?? 'n/a'}`).join('\n\n')}

## Strongest Groups

${topGroups.slice(0, 5).map((g, i) => `${i + 1}. ${g.group} — avg score ${g.avgOpportunityScore} | jobs24h ${g.jobsLast24h} | total ${g.totalJobs}`).join('\n')}

## Platform Ranking

${Object.entries(platformStats).sort((a, b) => b[1].opportunityScore - a[1].opportunityScore).map(([p, s], i) => `${i + 1}. ${p} — score ${s.opportunityScore} | jobs ${s.jobs} | 24h ${s.jobsLast24h}`).join('\n')}

## Positioning Recommendation

Primary keyword: ${primary}
Secondary keyword: ${secondary}
Best platform/service: WordPress + Next.js hybrid delivery
Overview keywords: ${primary}, ${secondary}, full stack developer
Skill tags: WordPress, Webflow, Next.js, Supabase, Shopify, Elementor

## Current Verdicts

WordPress: Steady volume; mix of low-budget fixes and strong retainers ($30–60/hr ongoing).
Webflow: Active updates/migrations; Webflow + automation combos appear.
Framer: Template restyle and build-from-design jobs; moderate competition.
GoHighLevel: Shopify + GHL part-time dev roles posting regularly.
AI/Vibe Coding: Lovable-to-production and Claude/Supabase stacks showing up.
Ecommerce: WooCommerce custom plugin work at $2.5k+; Shopify design noise at low budgets.
Maintenance: WordPress ongoing roles and site support retainers present.

## Important Changes

${firstRun ? 'Initial baseline run — tracking started.' : 'See run log for delta vs prior run.'}
`;

  fs.writeFileSync(path.join(DIR, 'current-summary.md'), summary);

  if (firstRun) {
    fs.writeFileSync(path.join(DIR, 'insights.md'), `# Upwork Intelligence Insights

- Baseline established ${runAt}. WordPress and general web keywords dominate hourly volume.
- Watch WooCommerce engineer posts ($2.5k fixed) and ongoing WordPress roles ($30–60/hr) for high-fit opportunities.
- Webflow "web update" and land-investing redesign + CRM posts signal automation-friendly clients.
`);
  }

  console.log(JSON.stringify({ runNumber, newJobs: newJobs.length, totalJobs: allJobs.length, top10, newJobsList: newJobs, log, platformStats, topGroups: topGroups.slice(0, 5), errors }, null, 2));
}

main();
