#!/usr/bin/env node
/**
 * Merge cycle search results into upwork-keyword-report.html and intelligence tree.
 * Usage: node agent/scripts/upwork-build-report.mjs agent/cycle-searches.json
 */
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import {
  KEYWORDS,
  keywordsForSlot,
  slotForHour,
  ROTATION,
} from './keywords-config.mjs';
import {
  jobUrlKey,
  parseBudget,
  parseProposals,
  parseClientSpend,
  shouldSkipJob,
  computeKeywordStats,
  computeGroupStats,
  computePlatformStats,
  globalInsights,
  sampleConfidence,
} from './upwork-stats.mjs';
import { normalizeRawJob } from './normalize-mcp-job.mjs';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, '../..');
const REPORT = path.join(ROOT, 'upwork-keyword-report.html');
const INTEL = path.join(ROOT, 'upwork-intelligence');

function normalizeUpworkJob(raw, keyword, group) {
  raw = normalizeRawJob(raw);
  const client = raw.client || {};
  const prop = parseProposals(raw.proposal_count ?? raw.proposals);
  const budget = parseBudget({ budget: raw.budget, type: raw.job_type });
  return {
    url: raw.url,
    title: raw.title,
    matchedKeyword: [keyword],
    keywordGroup: group,
    postedAt: raw.published_date || raw.created_date,
    type: raw.job_type === 'hourly' ? 'hourly' : raw.job_type === 'fixed' ? 'fixed' : raw.job_type,
    budget: raw.budget ?? null,
    duration: raw.duration ?? null,
    proposals: prop.raw,
    proposalsMid: prop.midpoint,
    clientCountry: client.country ?? null,
    paymentVerified: client.verification_status === 'VERIFIED',
    clientSpend: client.total_spent ?? null,
    clientHireRate: null,
    clientRating: client.rating ?? null,
    connects: raw.connects_cost ?? raw.connect_price ?? null,
    experienceLevel: raw.experience_level ?? null,
    skills: raw.skills ?? [],
    description_snippet: raw.description_snippet,
  };
}

function loadExistingJobs() {
  if (!fs.existsSync(REPORT)) return [];
  const html = fs.readFileSync(REPORT, 'utf8');
  const m = html.match(/<script type="application\/json" id="jobs-data">([\s\S]*?)<\/script>/);
  if (!m) return [];
  try {
    return JSON.parse(m[1].trim());
  } catch {
    return [];
  }
}

function mergeJobs(existing, incoming, maxAgeHours, isFirstRun) {
  const byKey = new Map();
  for (const j of existing) {
    const k = jobUrlKey(j.url);
    if (k) byKey.set(k, j);
  }
  const now = Date.now();
  const maxMs = (isFirstRun ? 2 : maxAgeHours) * 60 * 60 * 1000;
  let added = 0;
  const skipped = { age: 0, blocked: 0, dup: 0, noUrl: 0 };

  for (const j of incoming) {
    const skip = shouldSkipJob(j);
    if (skip === 'invalid_url') {
      skipped.noUrl++;
      continue;
    }
    if (skip === 'blocked_category') {
      skipped.blocked++;
      continue;
    }
    const posted = new Date(j.postedAt).getTime();
    if (Number.isFinite(posted) && now - posted > maxMs) {
      skipped.age++;
      continue;
    }
    const key = jobUrlKey(j.url);
    if (!key) {
      skipped.noUrl++;
      continue;
    }
    if (byKey.has(key)) {
      const prev = byKey.get(key);
      const mk = new Set([...(prev.matchedKeyword || []), ...(j.matchedKeyword || [])]);
      prev.matchedKeyword = [...mk];
      if (!prev.keywordGroup && j.keywordGroup) prev.keywordGroup = j.keywordGroup;
      skipped.dup++;
      continue;
    }
    byKey.set(key, j);
    added++;
  }
  return { jobs: [...byKey.values()], added, skipped };
}

function ingestCycle(cyclePath) {
  const cycle = JSON.parse(fs.readFileSync(cyclePath, 'utf8'));
  const out = [];
  const failures = cycle.failures || [];
  for (const s of cycle.searches || []) {
    if (s.error) {
      failures.push({ keyword: s.keyword, error: s.error });
      continue;
    }
    const jobs = s.jobs || s.response?.jobs || [];
    for (const raw of jobs) {
      out.push(normalizeUpworkJob(raw, s.keyword, s.group));
    }
  }
  return { jobs: out, meta: cycle.meta || {}, failures };
}

function escapeHtml(s) {
  return String(s ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function scoreColor(score) {
  if (score == null) return '#ccc';
  const t = Math.max(0, Math.min(100, score)) / 100;
  const r = Math.round(255 * (1 - t));
  const g = Math.round(200 * t + 55 * (1 - t));
  return `rgb(${r},${g},80)`;
}

function buildInsights(keywordStats, groupStats, platformStats, allJobs, meta) {
  const sorted = [...keywordStats].sort((a, b) => b.opportunityScore - a.opportunityScore);
  const top5 = sorted.slice(0, 5);
  const bottom5 = sorted.slice(-5).reverse();
  const gi = globalInsights(allJobs);
  const lines = [];

  lines.push('TOP KEYWORDS');
  for (const k of top5) {
    lines.push(
      `- ${k.keyword} (score ${k.opportunityScore}, n=${k.totalJobs}, ${k.sampleConfidence}): ${k.jobsLast24h} jobs/24h, median proposals ${k.medianProposals ?? 'n/a'}, high-budget ${k.pctHighBudget?.toFixed(0) ?? 'n/a'}%`,
    );
  }
  lines.push('');
  lines.push('WEAKEST KEYWORDS (lowest opportunity score)');
  for (const k of bottom5) {
    lines.push(
      `- ${k.keyword} (score ${k.opportunityScore}, n=${k.totalJobs}): sparse demand or heavy competition/budget drag`,
    );
  }

  lines.push('');
  lines.push('PLATFORM COMPARISON');
  for (const p of platformStats) {
    lines.push(
      `${p.platform}: jobs=${p.totalJobs}, recent=${p.recentDemand}, fixed med=${p.avgBudgetFixed ?? 'n/a'}, rate med=${p.avgRateHourly ?? 'n/a'}, proposals med=${p.medianProposals ?? 'n/a'}, score=${p.opportunityScore ?? 'n/a'}, confidence=${p.sampleConfidence}`,
    );
  }

  const bestDemand = platformStats.filter((p) => p.totalJobs > 0).sort((a, b) => b.recentDemand - a.recentDemand)[0];
  const bestPay = platformStats.filter((p) => p.avgRateHourly || p.avgBudgetFixed).sort((a, b) => (b.avgRateHourly || 0) - (a.avgRateHourly || 0))[0];
  const bestRatio = platformStats.filter((p) => p.opportunityScore).sort((a, b) => b.opportunityScore - a.opportunityScore)[0];
  lines.push('');
  lines.push(
    `Best recent demand: ${bestDemand?.platform ?? 'n/a'}. Best hourly signals: ${bestPay?.platform ?? 'n/a'}. Best demand/competition ratio: ${bestRatio?.platform ?? 'n/a'}.`,
  );

  lines.push('');
  lines.push('GROUP ROLLUP');
  for (const g of groupStats) {
    lines.push(`${g.group}: jobs=${g.totalJobs}, 24h=${g.jobsLast24h}, avg score=${g.avgOpportunityScore?.toFixed(1) ?? 'n/a'}`);
  }

  const aiGroup = groupStats.find((g) => g.group === 'AI/Vibe Coding');
  lines.push('');
  lines.push(
    `AI DEMAND CHECK: ${aiGroup?.totalJobs ?? 0} tracked jobs in AI/Vibe Coding group (sample builds as rotation runs).`,
  );

  const ghl = platformStats.find((p) => p.platform === 'GoHighLevel');
  lines.push(`GHL CHECK: ${ghl?.totalJobs ?? 0} jobs, med proposals ${ghl?.medianProposals ?? 'n/a'}.`);

  const wf = platformStats.find((p) => p.platform === 'Webflow');
  const fr = platformStats.find((p) => p.platform === 'Framer');
  lines.push(`WEBFLOW VS FRAMER: Webflow ${wf?.totalJobs ?? 0} jobs vs Framer ${fr?.totalJobs ?? 0} jobs.`);

  const wp = platformStats.find((p) => p.platform === 'WordPress');
  lines.push(`WORDPRESS CHECK: ${wp?.totalJobs ?? 0} jobs tracked so far.`);

  lines.push('');
  lines.push('Top skill tags: ' + gi.topSkills.slice(0, 10).map((s) => s.skill).join(', '));
  lines.push(`Hourly vs fixed: ${gi.hourly} hourly / ${gi.fixed} fixed among typed jobs.`);
  lines.push(`Top countries: ${gi.topCountries.slice(0, 5).map((c) => c.country).join(', ')}`);

  const rec = sorted.find((k) => k.totalJobs >= 5 && k.sampleConfidence !== 'Very Low') || sorted[0];
  const rec2 = sorted.filter((k) => k.keyword !== rec?.keyword)[1];
  lines.push('');
  lines.push('PROFILE POSITIONING RECOMMENDATION (early dataset, will refine):');
  lines.push(`Primary title keyword: ${rec?.keyword ?? 'Web Developer'}`);
  lines.push(`Secondary: ${rec2?.keyword ?? 'WordPress'}`);
  lines.push(`Lead platform/service: ${bestRatio?.platform ?? 'WordPress'}`);
  lines.push(`Overview keywords: ${top5.slice(0, 5).map((k) => k.keyword).join(', ')}`);
  lines.push(`Skill tags: ${gi.topSkills.slice(0, 10).map((s) => s.skill).join(', ')}`);

  return lines.join('\n');
}

function trendData(allJobs) {
  const days = [];
  for (let i = 6; i >= 0; i--) {
    const d = new Date();
    d.setUTCHours(0, 0, 0, 0);
    d.setUTCDate(d.getUTCDate() - i);
    days.push(d.toISOString().slice(0, 10));
  }
  const perDay = Object.fromEntries(days.map((d) => [d, 0]));
  const perKwDay = {};
  for (const j of allJobs) {
    const d = (j.postedAt || '').slice(0, 10);
    if (perDay[d] != null) perDay[d]++;
    for (const kw of j.matchedKeyword || []) {
      if (!perKwDay[kw]) perKwDay[kw] = Object.fromEntries(days.map((x) => [x, 0]));
      if (perKwDay[kw][d] != null) perKwDay[kw][d]++;
    }
  }
  return { days, perDay, perKwDay };
}

function writeHtml(allJobs, keywordStats, groupStats, platformStats, runInfo) {
  const gi = globalInsights(allJobs);
  const insights = buildInsights(keywordStats, groupStats, platformStats, allJobs, runInfo);
  const trends = trendData(allJobs);
  const dates = allJobs.map((j) => j.postedAt).filter(Boolean).sort();
  const dateRange =
    dates.length ? `${dates[0].slice(0, 10)} to ${dates[dates.length - 1].slice(0, 10)}` : 'n/a';

  const summaryBar = `Total jobs: ${allJobs.length} | Added this run: ${runInfo.added} | Keywords: ${KEYWORDS.length} | Range: ${dateRange} | Updated: ${runInfo.updatedAt}`;

  const kwRows = keywordStats
    .sort((a, b) => b.opportunityScore - a.opportunityScore)
    .map(
      (k) => `<tr>
      <td>${escapeHtml(k.keyword)}</td>
      <td>${escapeHtml(k.keywordGroup)}</td>
      <td>${k.totalJobs}</td>
      <td>${k.jobsLast24h}</td>
      <td>${k.avgBudgetFixed != null ? k.avgBudgetFixed.toFixed(0) : ''}</td>
      <td>${k.avgRateHourly != null ? k.avgRateHourly.toFixed(0) : ''}</td>
      <td>${k.medianProposals ?? ''}</td>
      <td>${k.pctHighBudget != null ? k.pctHighBudget.toFixed(0) + '%' : ''}</td>
      <td style="background:${scoreColor(k.opportunityScore)}">${k.opportunityScore}</td>
      <td>${k.sampleConfidence}</td>
    </tr>`,
    )
    .join('');

  const jobRows = allJobs
    .map(
      (j) => `<tr data-kw="${escapeHtml((j.matchedKeyword || []).join('|'))}" data-group="${escapeHtml(j.keywordGroup)}" data-country="${escapeHtml(j.clientCountry)}">
      <td><a href="${escapeHtml(j.url)}" target="_blank" rel="noopener">${escapeHtml(j.title)}</a></td>
      <td>${escapeHtml((j.matchedKeyword || []).join(', '))}</td>
      <td>${escapeHtml(j.keywordGroup)}</td>
      <td>${escapeHtml(j.type)}</td>
      <td>${escapeHtml(j.budget)}</td>
      <td>${escapeHtml(j.proposals)}</td>
      <td>${escapeHtml(j.clientCountry)}</td>
      <td>${j.postedAt ? j.postedAt.slice(0, 16) : ''}</td>
    </tr>`,
    )
    .join('');

  const topKwForChart = keywordStats
    .sort((a, b) => b.jobsLast24h - a.jobsLast24h)
    .slice(0, 12);
  const chartH = 220;
  const barW = 24;
  const maxBar = Math.max(1, ...topKwForChart.map((k) => k.jobsLast24h));
  let svgBars = '';
  topKwForChart.forEach((k, i) => {
    const h = (k.jobsLast24h / maxBar) * (chartH - 40);
    svgBars += `<rect x="${20 + i * (barW + 8)}" y="${chartH - h - 20}" width="${barW}" height="${h}" fill="#3b82f6" /><text x="${20 + i * (barW + 8) + barW / 2}" y="${chartH - 4}" font-size="8" text-anchor="middle" transform="rotate(-45 ${20 + i * (barW + 8) + barW / 2} ${chartH - 4})">${escapeHtml(k.keyword.slice(0, 12))}</text>`;
  });

  const dayVals = trends.days.map((d) => trends.perDay[d]);
  const maxDay = Math.max(1, ...dayVals);
  let svgDays = '';
  trends.days.forEach((d, i) => {
    const h = (trends.perDay[d] / maxDay) * (chartH - 40);
    svgDays += `<rect x="${20 + i * 50}" y="${chartH - h - 20}" width="40" height="${h}" fill="#10b981" /><text x="${40 + i * 50}" y="${chartH - 4}" font-size="10" text-anchor="middle">${d.slice(5)}</text>`;
  });

  const trendNote =
    allJobs.length < 20
      ? '<p class="note">Not enough historical data yet for reliable 7-day trends. Charts will stabilize after more hourly runs.</p>'
      : '';

  const html = `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<title>Upwork Keyword Demand Report</title>
<style>
:root { font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif; color: #111; background: #f6f7f9; }
body { margin: 0; padding: 1.5rem; }
.summary { background: #fff; border: 1px solid #ddd; padding: 1rem 1.25rem; margin-bottom: 1rem; border-radius: 8px; position: sticky; top: 0; z-index: 10; box-shadow: 0 1px 3px rgba(0,0,0,.06); }
.tabs { display: flex; gap: .5rem; margin-bottom: 1rem; flex-wrap: wrap; }
.tab-btn { border: 1px solid #ccc; background: #fff; padding: .5rem 1rem; border-radius: 6px; cursor: pointer; }
.tab-btn.active { background: #111; color: #fff; border-color: #111; }
.panel { display: none; background: #fff; border: 1px solid #ddd; border-radius: 8px; padding: 1rem; }
.panel.active { display: block; }
table { width: 100%; border-collapse: collapse; font-size: 14px; }
th, td { border-bottom: 1px solid #eee; padding: .5rem .6rem; text-align: left; vertical-align: top; }
thead th { position: sticky; top: 4.5rem; background: #fafafa; z-index: 2; cursor: pointer; }
.filters { display: flex; gap: .75rem; flex-wrap: wrap; margin-bottom: 1rem; }
.filters input, .filters select { padding: .4rem .5rem; }
.note { color: #555; font-size: 14px; }
pre.insights { white-space: pre-wrap; font-family: inherit; line-height: 1.5; }
</style>
</head>
<body>
<div class="summary" id="summary">${escapeHtml(summaryBar)}</div>
<div class="tabs">
  <button class="tab-btn active" data-tab="rankings">Keyword Rankings</button>
  <button class="tab-btn" data-tab="trends">Trends</button>
  <button class="tab-btn" data-tab="jobs">All Jobs</button>
  <button class="tab-btn" data-tab="insights">Insights</button>
</div>
<div class="panel active" id="panel-rankings">
  <table id="tbl-kw"><thead><tr>
    <th>Keyword</th><th>Group</th><th>Total</th><th>24h</th><th>Med Fixed $</th><th>Med Rate</th><th>Med Proposals</th><th>% High Budget</th><th>Score</th><th>Confidence</th>
  </tr></thead><tbody>${kwRows}</tbody></table>
</div>
<div class="panel" id="panel-trends">
  ${trendNote}
  <h3>Jobs per keyword (last 24h proxy from stats)</h3>
  <svg width="100%" height="${chartH}" viewBox="0 0 400 ${chartH}">${svgBars}</svg>
  <h3>Total jobs captured per day</h3>
  <svg width="100%" height="${chartH}" viewBox="0 0 400 ${chartH}">${svgDays}</svg>
</div>
<div class="panel" id="panel-jobs">
  <div class="filters">
    <input id="f-kw" placeholder="Filter keyword"/>
    <select id="f-group"><option value="">All groups</option>${[...new Set(KEYWORDS.map((k) => k.group))].map((g) => `<option>${escapeHtml(g)}</option>`).join('')}</select>
    <input id="f-country" placeholder="Country"/>
  </div>
  <table id="tbl-jobs"><thead><tr><th>Title</th><th>Keywords</th><th>Group</th><th>Type</th><th>Budget</th><th>Proposals</th><th>Country</th><th>Posted</th></tr></thead><tbody>${jobRows}</tbody></table>
</div>
<div class="panel" id="panel-insights"><pre class="insights">${escapeHtml(insights)}</pre></div>
<script type="application/json" id="jobs-data">${JSON.stringify(allJobs)}</script>
<script>
document.querySelectorAll('.tab-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
    btn.classList.add('active');
    document.getElementById('panel-' + btn.dataset.tab).classList.add('active');
  });
});
function sortTable(table, col) {
  const tbody = table.tBodies[0];
  const rows = [...tbody.rows];
  const asc = table.dataset.sortCol == col ? !(table.dataset.sortAsc === 'true') : false;
  table.dataset.sortCol = col;
  table.dataset.sortAsc = asc;
  rows.sort((a,b) => {
    const av = a.cells[col]?.innerText || '';
    const bv = b.cells[col]?.innerText || '';
    const an = parseFloat(av); const bn = parseFloat(bv);
    const cmp = (Number.isFinite(an) && Number.isFinite(bn)) ? an - bn : av.localeCompare(bv);
    return asc ? cmp : -cmp;
  });
  rows.forEach(r => tbody.appendChild(r));
}
document.querySelectorAll('#tbl-kw th').forEach((th, i) => th.addEventListener('click', () => sortTable(document.getElementById('tbl-kw'), i)));
const fKw = document.getElementById('f-kw');
const fGroup = document.getElementById('f-group');
const fCountry = document.getElementById('f-country');
function filterJobs() {
  const kw = (fKw.value || '').toLowerCase();
  const gr = fGroup.value;
  const co = (fCountry.value || '').toLowerCase();
  document.querySelectorAll('#tbl-jobs tbody tr').forEach(tr => {
    const okKw = !kw || tr.dataset.kw.toLowerCase().includes(kw);
    const okGr = !gr || tr.dataset.group === gr;
    const okCo = !co || (tr.dataset.country || '').toLowerCase().includes(co);
    tr.style.display = okKw && okGr && okCo ? '' : 'none';
  });
}
[fKw, fGroup, fCountry].forEach(el => el.addEventListener('input', filterJobs));
</script>
</body>
</html>`;

  fs.writeFileSync(REPORT, html);
}

function appendJsonl(file, obj) {
  fs.appendFileSync(file, JSON.stringify(obj) + '\n');
}

function loadJsonlUrls(file) {
  const urls = new Set();
  if (!fs.existsSync(file)) return urls;
  for (const line of fs.readFileSync(file, 'utf8').split('\n')) {
    if (!line.trim()) continue;
    try {
      const o = JSON.parse(line);
      const k = jobUrlKey(o.url);
      if (k) urls.add(k);
    } catch { /* ignore */ }
  }
  return urls;
}

function updateIntelligence(allJobs, keywordStats, groupStats, platformStats, runInfo, newJobs, failures) {
  fs.mkdirSync(INTEL, { recursive: true });
  const jobsJsonl = path.join(INTEL, 'jobs.jsonl');
  const existingUrls = loadJsonlUrls(jobsJsonl);
  for (const j of newJobs) {
    const k = jobUrlKey(j.url);
    if (k && !existingUrls.has(k)) {
      appendJsonl(jobsJsonl, j);
      existingUrls.add(k);
    }
  }

  fs.writeFileSync(path.join(INTEL, 'keyword-stats.json'), JSON.stringify(keywordStats, null, 2));
  fs.writeFileSync(path.join(INTEL, 'group-stats.json'), JSON.stringify({ ranking: groupStats }, null, 2));
  fs.writeFileSync(path.join(INTEL, 'platform-stats.json'), JSON.stringify(platformStats, null, 2));

  const sorted = [...keywordStats].sort((a, b) => b.opportunityScore - a.opportunityScore);
  const runLog = {
    timestamp: runInfo.updatedAt,
    groupsSearched: runInfo.groups,
    keywordsSearched: runInfo.keywordsSearched,
    jobsReturned: runInfo.jobsReturned,
    uniqueAdded: runInfo.added,
    totalAccumulated: allJobs.length,
    top5Keywords: sorted.slice(0, 5).map((k) => ({ keyword: k.keyword, score: k.opportunityScore, n: k.totalJobs })),
    topGroups: groupStats.slice(0, 5).map((g) => g.group),
    topPlatform: platformStats[0]?.platform,
    failures,
  };
  appendJsonl(path.join(INTEL, 'run-log.jsonl'), runLog);

  writeCurrentSummary(allJobs, keywordStats, groupStats, platformStats, runInfo);
  writeReadme();
}

function writeReadme() {
  const p = path.join(INTEL, 'README.md');
  const text = `# Upwork Intelligence Knowledge Tree

Primary source of truth: \`../upwork-keyword-report.html\` (embedded \`#jobs-data\` JSON).

| File | Role |
|------|------|
| \`current-summary.md\` | Fast entry point for agents |
| \`keyword-stats.json\` | Latest per-keyword metrics (regenerated each run) |
| \`group-stats.json\` | Keyword group rollup |
| \`platform-stats.json\` | Platform comparison stats |
| \`jobs.jsonl\` | Append-only raw job records |
| \`run-log.jsonl\` | Append-only automation run history |
| \`insights.md\` | Durable cross-run conclusions |

Read \`current-summary.md\` first for positioning questions. Use \`jobs.jsonl\` only for job-level evidence.
`;
  fs.writeFileSync(p, text);
}

function writeCurrentSummary(allJobs, keywordStats, groupStats, platformStats, runInfo) {
  const sorted = [...keywordStats].sort((a, b) => b.opportunityScore - a.opportunityScore);
  const dates = allJobs.map((j) => j.postedAt).filter(Boolean).sort();
  const range = dates.length ? `${dates[0].slice(0, 10)} to ${dates[dates.length - 1].slice(0, 10)}` : 'n/a';
  const top10 = sorted.slice(0, 10);
  const gi = globalInsights(allJobs);
  const rec = sorted.find((k) => k.totalJobs >= 5) || sorted[0];

  const md = `# Upwork Market Intelligence

Last updated: ${runInfo.updatedAt}
Total jobs tracked: ${allJobs.length}
Date range covered: ${range}
Groups searched last run: ${runInfo.groups.join(', ')}

## Current Top Opportunities

${top10
  .map(
    (k) =>
      `- **${k.keyword}** — score ${k.opportunityScore}, n=${k.totalJobs} (${k.sampleConfidence}), med fixed ${k.avgBudgetFixed ?? 'n/a'}, med rate ${k.avgRateHourly ?? 'n/a'}, med proposals ${k.medianProposals ?? 'n/a'}`,
  )
  .join('\n')}

## Strongest Categories

${groupStats.map((g, i) => `${i + 1}. ${g.group} (avg score ${g.avgOpportunityScore?.toFixed(1) ?? 'n/a'}, jobs ${g.totalJobs})`).join('\n')}

## Platform Ranking

${platformStats.map((p, i) => `${i + 1}. ${p.platform} — ${p.totalJobs} jobs, score ${p.opportunityScore ?? 'n/a'}`).join('\n')}

## Current Positioning Recommendation

Primary Upwork title keyword: ${rec?.keyword ?? 'TBD'}
Secondary keyword: ${sorted[1]?.keyword ?? 'TBD'}
Strongest platform/service: ${platformStats[0]?.platform ?? 'TBD'}
Recommended overview keywords: ${top10.slice(0, 5).map((k) => k.keyword).join(', ')}
Recommended skill tags: ${gi.topSkills.slice(0, 10).map((s) => s.skill).join(', ')}

## WordPress

Early sample: ${platformStats.find((p) => p.platform === 'WordPress')?.totalJobs ?? 0} jobs in dataset from rotation cycles completed so far.

## Webflow vs Framer

Webflow ${platformStats.find((p) => p.platform === 'Webflow')?.totalJobs ?? 0} vs Framer ${platformStats.find((p) => p.platform === 'Framer')?.totalJobs ?? 0} (partial coverage until all rotation groups run).

## GoHighLevel

${platformStats.find((p) => p.platform === 'GoHighLevel')?.totalJobs ?? 0} jobs tracked.

## AI / Vibe Coding

Group totals will populate when AI rotation slot runs.

## Ecommerce

Shopify ${platformStats.find((p) => p.platform === 'Shopify')?.totalJobs ?? 0}, WooCommerce ${platformStats.find((p) => p.platform === 'WooCommerce')?.totalJobs ?? 0}, Shopware ${platformStats.find((p) => p.platform === 'Shopware')?.totalJobs ?? 0}.

## Maintenance / Retainers

Maintenance group stats from partial keyword coverage.

## Important Changes

${runInfo.added > 0 ? `- Added ${runInfo.added} new unique jobs this run.` : '- No new unique jobs this run.'}
First baseline build in this repository workspace.

## Current Market Signals

- Dataset is early; treat high scores with \`Very Low\` confidence cautiously.
- WordPress and Web Design keywords appear frequently in title searches.
- Hourly vs fixed split: ${gi.hourly} hourly / ${gi.fixed} fixed in tracked set.
`;
  fs.writeFileSync(path.join(INTEL, 'current-summary.md'), md);

  const insightsPath = path.join(INTEL, 'insights.md');
  let insights = fs.existsSync(insightsPath) ? fs.readFileSync(insightsPath, 'utf8') : '# Durable Insights\n\n';
  if (!insights.includes('Rotation coverage')) {
    insights += `\n- Rotation coverage: keyword stats fill in over 3 hourly slots (Core/Web Design/WP/Webflow, then AI/GHL/Adjacent/Modern, then Ecommerce/Maintenance/CRO).\n`;
  }
  if (allJobs.length >= 15 && !insights.includes('WordPress remains visible')) {
    insights += `- WordPress remains visible in early title-search results alongside general web development demand.\n`;
  }
  fs.writeFileSync(insightsPath, insights);
}

function main() {
  const cyclePath = process.argv[2] || path.join(ROOT, 'agent/cycle-searches.json');
  if (!fs.existsSync(cyclePath)) {
    console.error('Missing cycle file:', cyclePath);
    process.exit(1);
  }
  const { jobs: incoming, meta, failures } = ingestCycle(cyclePath);
  const existing = loadExistingJobs();
  const isFirstRun = existing.length === 0;
  const { jobs: allJobs, added, skipped } = mergeJobs(existing, incoming, 1, isFirstRun);

  const newJobs = [];
  const existingKeys = new Set(existing.map((j) => jobUrlKey(j.url)));
  for (const j of allJobs) {
    const k = jobUrlKey(j.url);
    if (k && !existingKeys.has(k)) newJobs.push(j);
  }

  const now = new Date();
  const keywordStats = computeKeywordStats(allJobs, now);
  const groupStats = computeGroupStats(keywordStats);
  const platformStats = computePlatformStats(allJobs, keywordStats);

  const hour = now.getUTCHours();
  const slot = meta.slot ?? slotForHour(hour);
  const groups = meta.groups ?? ROTATION[slot];

  const runInfo = {
    added,
    skipped,
    updatedAt: now.toISOString(),
    groups,
    keywordsSearched: meta.keywordsSearched || [],
    jobsReturned: meta.jobsReturned ?? incoming.length,
  };

  writeHtml(allJobs, keywordStats, groupStats, platformStats, runInfo);
  updateIntelligence(allJobs, keywordStats, groupStats, platformStats, runInfo, newJobs, failures);

  const top3 = [...keywordStats].sort((a, b) => b.opportunityScore - a.opportunityScore).slice(0, 3);
  console.log(
    JSON.stringify({
      added,
      total: allJobs.length,
      top3,
      skipped,
      failures,
      report: REPORT,
    }),
  );
}

main();
