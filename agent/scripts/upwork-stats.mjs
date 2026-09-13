import { KEYWORDS, PLATFORMS } from './keywords-config.mjs';

export function jobUrlKey(url) {
  if (!url) return null;
  try {
    const u = new URL(url);
    return u.origin + u.pathname;
  } catch {
    return url.split('?')[0];
  }
}

export function parseMoney(str) {
  if (str == null || str === '') return null;
  const s = String(str).replace(/,/g, '');
  const m = s.match(/([\d.]+)/);
  return m ? parseFloat(m[1]) : null;
}

export function parseBudget(job) {
  const b = job.budget;
  if (!b) return { type: job.type, fixed: null, hourlyMin: null, hourlyMax: null, display: null };
  const display = b;
  if (job.type === 'hourly' || /\/hr/i.test(b)) {
    const parts = b.replace(/,/g, '').match(/([\d.]+)\s*[–-]\s*([\d.]+)/);
    if (parts) {
      return {
        type: 'hourly',
        fixed: null,
        hourlyMin: parseFloat(parts[1]),
        hourlyMax: parseFloat(parts[2]),
        display,
      };
    }
    const one = parseMoney(b);
    return { type: 'hourly', fixed: null, hourlyMin: one, hourlyMax: one, display };
  }
  const fixed = parseMoney(b);
  return { type: 'fixed', fixed, hourlyMin: null, hourlyMax: null, display };
}

export function parseProposals(val) {
  if (val == null || val === '') return { raw: val ?? null, midpoint: null };
  const s = String(val);
  const range = s.match(/([\d.]+)\s*[–-]\s*([\d.]+)/);
  if (range) {
    const a = parseFloat(range[1]);
    const b = parseFloat(range[2]);
    return { raw: s, midpoint: (a + b) / 2 };
  }
  const n = parseFloat(s.replace(/,/g, ''));
  return { raw: s, midpoint: Number.isFinite(n) ? n : null };
}

export function parseClientSpend(spent) {
  if (!spent) return null;
  return parseMoney(String(spent).replace(/\$/g, ''));
}

export function sampleConfidence(totalJobs) {
  if (totalJobs <= 4) return 'Very Low';
  if (totalJobs <= 14) return 'Low';
  if (totalJobs <= 39) return 'Medium';
  if (totalJobs <= 99) return 'High';
  return 'Very High';
}

const BLOCK_PATTERNS =
  /\b(crypto trading|bitcoin trading|forex trading|adult content|porn|escort|gambling casino|online casino|dating app|hookup)\b/i;

export function shouldSkipJob(job) {
  if (!job.url || !/^https:\/\/www\.upwork\.com\//i.test(job.url)) return 'invalid_url';
  const text = `${job.title || ''} ${job.description_snippet || ''}`;
  if (BLOCK_PATTERNS.test(text)) return 'blocked_category';
  return null;
}

export function isHighBudget(job) {
  const p = parseBudget(job);
  if (p.type === 'fixed' && p.fixed != null && p.fixed >= 1000) return true;
  if (p.type === 'hourly') {
    const rate = p.hourlyMax ?? p.hourlyMin;
    if (rate != null && rate >= 40) return true;
  }
  return false;
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

function cappedMedianFixed(values) {
  const capped = values.map((v) => (v != null ? Math.min(v, 10000) : null));
  return median(capped);
}

export function jobsForKeyword(allJobs, keyword) {
  return allJobs.filter((j) => j.matchedKeyword?.includes(keyword));
}

export function computeKeywordStats(allJobs, now = new Date()) {
  const day24 = now.getTime() - 24 * 60 * 60 * 1000;
  const rawMetrics = KEYWORDS.map(({ keyword, group }) => {
    const jobs = jobsForKeyword(allJobs, keyword);
    const jobsLast24h = jobs.filter((j) => new Date(j.postedAt).getTime() >= day24).length;
    const fixedVals = [];
    const rateVals = [];
    const proposals = [];
    let verified = 0;
    const spends = [];
    let highBudget = 0;

    for (const j of jobs) {
      const p = parseBudget(j);
      if (p.type === 'fixed' && p.fixed != null) fixedVals.push(p.fixed);
      if (p.type === 'hourly') {
        const r = p.hourlyMax ?? p.hourlyMin;
        if (r != null) rateVals.push(r);
      }
      const prop = parseProposals(j.proposals);
      if (prop.midpoint != null) proposals.push(prop.midpoint);
      if (j.paymentVerified) verified++;
      const spend = parseClientSpend(j.clientSpend);
      if (spend != null) spends.push(spend);
      if (isHighBudget(j)) highBudget++;
    }

    const totalJobs = jobs.length;
    return {
      keyword,
      keywordGroup: group,
      totalJobs,
      jobsLast24h,
      avgBudgetFixed: cappedMedianFixed(fixedVals),
      avgRateHourly: median(rateVals),
      medianProposals: median(proposals),
      pctVerified: totalJobs ? (verified / totalJobs) * 100 : null,
      avgClientSpend: avg(spends),
      pctHighBudget: totalJobs ? (highBudget / totalJobs) * 100 : null,
      sampleConfidence: sampleConfidence(totalJobs),
      _jobsLast24h: jobsLast24h,
      _competition: median(proposals),
      _budgetScore: cappedMedianFixed(fixedVals) ?? median(rateVals) ?? 0,
      _verifiedPct: totalJobs ? verified / totalJobs : 0,
      _highPct: totalJobs ? highBudget / totalJobs : 0,
    };
  });

  const maxRecent = Math.max(1, ...rawMetrics.map((m) => m._jobsLast24h));
  const budgetScores = rawMetrics.map((m) => m._budgetScore).filter((n) => n > 0);
  const maxBudget = Math.max(1, ...budgetScores);
  const compValues = rawMetrics.map((m) => m._competition).filter((n) => n != null);
  const maxComp = Math.max(1, ...compValues);

  return rawMetrics.map((m) => {
    const recentNorm = m._jobsLast24h / maxRecent;
    const budgetNorm = m._budgetScore / maxBudget;
    const compNorm = m._competition != null ? 1 - m._competition / maxComp : 0.5;
    const raw =
      recentNorm * 0.35 +
      budgetNorm * 0.25 +
      compNorm * 0.2 +
      m._verifiedPct * 0.1 +
      m._highPct * 0.1;
    const opportunityScore = Math.round(Math.min(100, Math.max(1, raw * 100)));
    const {
      _jobsLast24h,
      _competition,
      _budgetScore,
      _verifiedPct,
      _highPct,
      ...rest
    } = m;
    return { ...rest, opportunityScore };
  });
}

export function computeGroupStats(keywordStats) {
  const groups = [...new Set(KEYWORDS.map((k) => k.group))];
  return groups
    .map((group) => {
      const rows = keywordStats.filter((k) => k.keywordGroup === group);
      const totalJobs = rows.reduce((s, r) => s + r.totalJobs, 0);
      const jobsLast24h = rows.reduce((s, r) => s + r.jobsLast24h, 0);
      const opp = avg(rows.map((r) => r.opportunityScore));
      return {
        group,
        totalJobs,
        jobsLast24h,
        avgOpportunityScore: opp,
        keywordCount: rows.length,
        sampleConfidence: sampleConfidence(totalJobs),
      };
    })
    .sort((a, b) => (b.avgOpportunityScore ?? 0) - (a.avgOpportunityScore ?? 0));
}

function jobMatchesPlatform(job, platform) {
  const text = `${job.title} ${(job.skills || []).join(' ')} ${(job.matchedKeyword || []).join(' ')}`.toLowerCase();
  if (platform.keywords) {
    return platform.keywords.some((k) => text.includes(k.toLowerCase()));
  }
  return false;
}

export function computePlatformStats(allJobs, keywordStats) {
  return PLATFORMS.map((platform) => {
    const jobs = allJobs.filter((j) => jobMatchesPlatform(j, platform));
    const kwRow = keywordStats.find((k) =>
      platform.keywords?.some((pk) => k.keyword.toLowerCase().includes(pk.toLowerCase())),
    );
    const totalJobs = jobs.length;
    const day24 = Date.now() - 24 * 60 * 60 * 1000;
    const recent = jobs.filter((j) => new Date(j.postedAt).getTime() >= day24).length;
    const fixedVals = [];
    const rateVals = [];
    const proposals = [];
    let highBudget = 0;
    for (const j of jobs) {
      const p = parseBudget(j);
      if (p.type === 'fixed' && p.fixed != null) fixedVals.push(p.fixed);
      if (p.type === 'hourly') {
        const r = p.hourlyMax ?? p.hourlyMin;
        if (r != null) rateVals.push(r);
      }
      const prop = parseProposals(j.proposals);
      if (prop.midpoint != null) proposals.push(prop.midpoint);
      if (isHighBudget(j)) highBudget++;
    }
    return {
      platform: platform.name,
      totalJobs,
      recentDemand: recent,
      avgBudgetFixed: cappedMedianFixed(fixedVals),
      avgRateHourly: median(rateVals),
      medianProposals: median(proposals),
      pctHighBudget: totalJobs ? (highBudget / totalJobs) * 100 : null,
      opportunityScore: kwRow?.opportunityScore ?? null,
      sampleConfidence: sampleConfidence(totalJobs),
    };
  }).sort((a, b) => (b.opportunityScore ?? 0) - (a.opportunityScore ?? 0));
}

export function globalInsights(allJobs) {
  const skillCounts = new Map();
  const countryCounts = new Map();
  const countrySpend = new Map();
  let hourly = 0;
  let fixed = 0;
  const buckets = { under500: 0, b500_1000: 0, b1000_3000: 0, b3000_10000: 0, b10000plus: 0 };

  for (const j of allJobs) {
    for (const sk of j.skills || []) {
      skillCounts.set(sk, (skillCounts.get(sk) || 0) + 1);
    }
    const c = j.clientCountry || 'Unknown';
    countryCounts.set(c, (countryCounts.get(c) || 0) + 1);
    const spend = parseClientSpend(j.clientSpend);
    if (spend != null) {
      if (!countrySpend.has(c)) countrySpend.set(c, []);
      countrySpend.get(c).push(spend);
    }
    if (j.type === 'hourly') hourly++;
    else if (j.type === 'fixed') fixed++;
    const p = parseBudget(j);
    if (p.type === 'fixed' && p.fixed != null) {
      if (p.fixed < 500) buckets.under500++;
      else if (p.fixed < 1000) buckets.b500_1000++;
      else if (p.fixed < 3000) buckets.b1000_3000++;
      else if (p.fixed < 10000) buckets.b3000_10000++;
      else buckets.b10000plus++;
    }
  }

  const topSkills = [...skillCounts.entries()]
    .sort((a, b) => b[1] - a[1])
    .slice(0, 20)
    .map(([skill, count]) => ({ skill, count }));

  const topCountries = [...countryCounts.entries()]
    .sort((a, b) => b[1] - a[1])
    .slice(0, 10)
    .map(([country, count]) => ({
      country,
      count,
      avgSpend: avg(countrySpend.get(country) || []),
    }));

  return { topSkills, topCountries, hourly, fixed, buckets };
}
