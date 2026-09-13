#!/usr/bin/env node
/**
 * Hourly Upwork keyword cycle: merge partials (or pool fill), build report + intelligence.
 * Title searches should land in agent/partial/*.json via append-batch.mjs before this runs.
 */
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { spawnSync } from 'child_process';
import { keywordsForSlot, slotForHour } from './keywords-config.mjs';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, '../..');

function run(cmd, args) {
  const r = spawnSync(cmd, args, { cwd: ROOT, stdio: 'inherit', encoding: 'utf8' });
  if (r.status !== 0) process.exit(r.status ?? 1);
}

function slug(kw) {
  return kw.toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_|_$/g, '').slice(0, 80);
}

const poolPath = path.join(ROOT, 'agent/pool-jobs.json');
const partialDir = path.join(ROOT, 'agent/partial');
const slot = slotForHour(new Date().getUTCHours());
const expected = keywordsForSlot(slot);
const allPartials = expected.every(({ keyword }) =>
  fs.existsSync(path.join(partialDir, `${slug(keyword)}.json`)),
);

if (allPartials) {
  run('node', ['agent/scripts/merge-partials-to-cycle.mjs']);
} else if (fs.existsSync(poolPath)) {
  run('node', ['agent/scripts/fill-cycle-from-pool.mjs', poolPath]);
} else {
  run('node', ['agent/scripts/merge-partials-to-cycle.mjs']);
}

run('node', ['agent/scripts/upwork-build-report.mjs', 'agent/cycle-searches.json']);
