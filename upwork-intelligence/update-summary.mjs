#!/usr/bin/env node
import fs from "fs";
import path from "path";

const dir = path.dirname(new URL(import.meta.url).pathname);
const kw = JSON.parse(fs.readFileSync(path.join(dir, "keyword-stats.json"), "utf8"));
const gr = JSON.parse(fs.readFileSync(path.join(dir, "group-stats.json"), "utf8"));
const pl = JSON.parse(fs.readFileSync(path.join(dir, "platform-stats.json"), "utf8"));
const state = fs.existsSync(path.join(dir, "state.json"))
  ? JSON.parse(fs.readFileSync(path.join(dir, "state.json"), "utf8"))
  : {};

const jobs = fs.readFileSync(path.join(dir, "jobs.jsonl"), "utf8").trim().split("\n").filter(Boolean).length;

const topKw = Object.values(kw)
  .sort((a, b) => b.opportunityScore - a.opportunityScore)
  .slice(0, 10);
const topGr = Object.entries(gr).sort((a, b) => b[1].opportunityScore - a[1].opportunityScore);
const topPl = Object.entries(pl)
  .filter(([, v]) => v.jobs > 0)
  .sort((a, b) => b[1].opportunityScore - a[1].opportunityScore);

const primary = topKw[0]?.keyword || "web developer";
const secondary = topKw[1]?.keyword || "web design";
const bestPlatform = topPl[0]?.[0] || "WordPress";

const md = `# Upwork Market Intelligence

Last updated: ${new Date().toISOString()}
Total jobs: ${jobs}
Latest cycle: ${state.lastCycle || "A"} (run ${state.runCount || 1})

## Top Opportunities

${topKw.map((k, i) => `${i + 1}. **${k.keyword}** (${k.group}) — score ${k.opportunityScore}, ${k.jobsLast24h} jobs/24h, confidence ${k.sampleConfidence}`).join("\n")}

## Group Ranking

${topGr.map(([g, s], i) => `${i + 1}. ${g} — score ${s.opportunityScore}, ${s.totalJobs} jobs`).join("\n")}

## Platform Ranking

${topPl.length ? topPl.map(([p, s], i) => `${i + 1}. ${p} — score ${s.opportunityScore}, ${s.jobs} jobs`).join("\n") : "Insufficient platform-tagged jobs yet."}

## Positioning Recommendation

Primary keyword: ${primary}
Secondary keyword: ${secondary}
Best platform/service: ${bestPlatform}
Overview keywords: ${topKw.slice(0, 5).map((k) => k.keyword).join(", ")}
Skill tags: ${[bestPlatform, "Web Development", "Web Design", "Responsive Design"].join(", ")}

## Current Verdicts

WordPress: Strong baseline demand in title searches; budgets mixed, competition moderate on redesign posts.
Webflow vs Framer: Webflow shows fresher hourly/fixed posts in the last 2h; Framer titles skew slightly older in this sample.
GoHighLevel: Automation and CRM manager roles dominate; recurring part-time potential, rates often $15–25/hr.
AI/Vibe Coding: Few pure title matches; broader AI web roles often blend WordPress/Shopify stacks.
Ecommerce: Shopify developer titles active; liquid/CWV posts appear alongside generic store builds.
Maintenance: Agency ongoing website specialist posts imply retainer-style work (watch hourly without fixed scope).

## Important Changes

First pipeline run in repo: intelligence folder initialized, cycle A partial (16 title searches, 2h ingest window).
`;

fs.writeFileSync(path.join(dir, "current-summary.md"), md);
console.log("summary updated");
