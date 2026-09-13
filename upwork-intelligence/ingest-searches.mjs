#!/usr/bin/env node
/** Append one search result: node ingest-searches.mjs <keyword> < jobs.json */
import fs from "fs";
import path from "path";
import { keywordToGroup } from "./lib.mjs";

const keyword = process.argv[2];
if (!keyword) {
  console.error("Usage: ingest-searches.mjs <keyword> < jobs.json");
  process.exit(1);
}
const raw = fs.readFileSync(0, "utf8");
const parsed = JSON.parse(raw);
const jobs = parsed.jobs || parsed;
const batchFile = path.join(path.dirname(new URL(import.meta.url).pathname), "_pending-batch.json");
let batch = { searches: [] };
if (fs.existsSync(batchFile)) batch = JSON.parse(fs.readFileSync(batchFile, "utf8"));
batch.searches.push({
  keyword,
  group: keywordToGroup(keyword),
  jobs: Array.isArray(jobs) ? jobs : [],
});
fs.writeFileSync(batchFile, JSON.stringify(batch));
console.log(`Added ${keyword}, total searches: ${batch.searches.length}`);
