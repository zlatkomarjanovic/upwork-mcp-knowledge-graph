#!/usr/bin/env node
import fs from "fs";
import path from "path";
import { keywordToGroup } from "./lib.mjs";

const dir = path.dirname(new URL(import.meta.url).pathname);
const cacheDir = path.join(dir, "mcp-cache");
const files = fs.readdirSync(cacheDir).filter((f) => f.endsWith(".json"));
const searches = [];
for (const f of files) {
  const data = JSON.parse(fs.readFileSync(path.join(cacheDir, f), "utf8"));
  for (const entry of data) {
    searches.push({
      keyword: entry.keyword,
      group: keywordToGroup(entry.keyword),
      jobs: entry.jobs || [],
    });
  }
}
fs.writeFileSync(path.join(dir, "_pending-batch.json"), JSON.stringify({ searches }, null, 0));
console.log(`Merged ${searches.length} searches from ${files.length} files`);
