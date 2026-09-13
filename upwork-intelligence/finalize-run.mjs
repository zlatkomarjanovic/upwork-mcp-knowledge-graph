#!/usr/bin/env node
import fs from "fs";
import path from "path";
import { spawnSync } from "child_process";
import { CYCLES, cycleForHour } from "./lib.mjs";

const dir = path.dirname(new URL(import.meta.url).pathname);
const batchFile = path.join(dir, "_pending-batch.json");
const ts = process.env.RUN_TS || new Date().toISOString();
const hour = new Date(ts).getUTCHours();
const cycle = process.env.CYCLE || cycleForHour(hour);
const windowHours = Number(process.env.WINDOW_HOURS || "2");
const runCount = Number(process.env.RUN_COUNT || "0");

if (!fs.existsSync(batchFile)) {
  console.error("No pending batch");
  process.exit(1);
}
const pending = JSON.parse(fs.readFileSync(batchFile, "utf8"));
const batch = {
  timestamp: ts,
  cycle,
  windowHours,
  runCount,
  groupsSearched: CYCLES[cycle],
  keywordsSearched: pending.searches.map((s) => s.keyword),
  searches: pending.searches,
};
const tmp = path.join(dir, "_run-batch.json");
fs.writeFileSync(tmp, JSON.stringify(batch));
const r = spawnSync("node", [path.join(dir, "process-batch.mjs"), tmp], { encoding: "utf8" });
console.log(r.stdout);
if (r.stderr) console.error(r.stderr);
fs.unlinkSync(batchFile);
fs.unlinkSync(tmp);
process.exit(r.status ?? 0);
