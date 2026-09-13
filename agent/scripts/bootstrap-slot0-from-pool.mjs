#!/usr/bin/env node
/** After pool is expanded, build cycle-searches via fill-cycle-from-pool then report. */
import { spawnSync } from 'child_process';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, '../..');

function run(cmd, args) {
  const r = spawnSync(cmd, args, { cwd: ROOT, stdio: 'inherit' });
  if (r.status !== 0) process.exit(r.status ?? 1);
}

run('node', ['agent/scripts/fill-cycle-from-pool.mjs', 'agent/pool-jobs.json']);
run('node', ['agent/scripts/upwork-build-report.mjs', 'agent/cycle-searches.json']);
