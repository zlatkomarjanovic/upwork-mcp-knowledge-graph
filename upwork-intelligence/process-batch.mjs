#!/usr/bin/env node
/** Read JSON batch file: { cycle, windowHours, searches: [{ keyword, group, jobs: [...] }] } */
import fs from "fs";
import path from "path";
import {
  DIR,
  appendJsonl,
  inTimeWindow,
  mapUpworkJob,
  mergeJob,
  loadAllJobs,
  computeKeywordStats,
  computeGroupStats,
  computePlatformStats,
  saveStats,
  nextCycle,
} from "./lib.mjs";

const batchPath = process.argv[2];
if (!batchPath) {
  console.error("Usage: process-batch.mjs <batch.json>");
  process.exit(1);
}
const batch = JSON.parse(fs.readFileSync(batchPath, "utf8"));
const windowHours = batch.windowHours ?? 1;
const jobsFile = path.join(DIR, "jobs.jsonl");
const logFile = path.join(DIR, "run-log.jsonl");

const existing = loadAllJobs();
const byUrl = new Map(existing.map((j) => [j.url, j]));
let newCount = 0;
const errors = batch.errors || [];

for (const s of batch.searches || []) {
  const kw = s.keyword;
  const group = s.group;
  for (const raw of s.jobs || []) {
    try {
      const mapped = mapUpworkJob(raw, kw, group);
      if (!mapped) continue;
      if (!inTimeWindow(mapped.postedAt, windowHours)) continue;
      const prev = byUrl.get(mapped.url);
      if (prev) {
        byUrl.set(mapped.url, mergeJob(prev, mapped));
      } else {
        byUrl.set(mapped.url, mapped);
        newCount++;
        appendJsonl(jobsFile, mapped);
      }
    } catch (e) {
      errors.push(`${kw}: ${e.message}`);
    }
  }
}

// Rewrite merged duplicates that gained keywords (only those already on disk)
if (newCount === 0) {
  for (const [url, job] of byUrl) {
    const old = existing.find((j) => j.url === url);
    if (old && (job.matchedKeywords?.length || 0) > (old.matchedKeywords?.length || 0)) {
      const all = loadAllJobs();
      const updated = all.map((j) => (j.url === url ? job : j));
      fs.writeFileSync(jobsFile, updated.map((j) => JSON.stringify(j)).join("\n") + (updated.length ? "\n" : ""));
    }
  }
}

const allJobs = [...byUrl.values()];
const keywordStats = computeKeywordStats(allJobs);
const groupStats = computeGroupStats(allJobs);
const platformStats = computePlatformStats(allJobs);
saveStats(keywordStats, groupStats, platformStats);

const topKeywords = Object.values(keywordStats)
  .sort((a, b) => b.opportunityScore - a.opportunityScore)
  .slice(0, 5)
  .map((k) => ({ keyword: k.keyword, score: k.opportunityScore }));

appendJsonl(logFile, {
  timestamp: batch.timestamp || new Date().toISOString(),
  cycle: batch.cycle,
  groupsSearched: batch.groupsSearched,
  keywordsSearched: batch.keywordsSearched,
  newJobs: newCount,
  totalJobs: allJobs.length,
  topKeywords,
  errors: errors.length ? errors.slice(0, 5) : undefined,
});

const stateFile = path.join(DIR, "state.json");
fs.writeFileSync(
  stateFile,
  JSON.stringify(
    { lastCycle: batch.cycle, lastRun: batch.timestamp || new Date().toISOString(), runCount: (batch.runCount || 0) + 1 },
    null,
    2
  )
);

console.log(
  JSON.stringify({
    newJobs: newCount,
    totalJobs: allJobs.length,
    cycle: batch.cycle,
    nextCycle: nextCycle(batch.cycle),
    topKeywords: topKeywords.slice(0, 3),
    errors: errors.slice(0, 3),
  })
);
