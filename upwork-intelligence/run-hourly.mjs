#!/usr/bin/env node
/**
 * Hourly tracker runner (automation agent should populate .run-raw.json via Upwork MCP, then execute this).
 * Usage: RUN_NUMBER=1 RUN_AT=ISO node run-hourly.mjs [--first-run]
 */
import { spawnSync } from 'child_process';
import path from 'path';

const dir = path.dirname(new URL(import.meta.url).pathname);
const args = process.argv.includes('--first-run') ? ['--first-run'] : [];
const env = { ...process.env, RUN_NUMBER: process.env.RUN_NUMBER || '1', RUN_AT: process.env.RUN_AT || new Date().toISOString() };
spawnSync('node', [path.join(dir, 'assemble-raw.mjs')], { env, stdio: 'inherit' });
const r = spawnSync('node', [path.join(dir, 'process-run.mjs'), path.join(dir, '.run-raw.json'), ...args], { env, stdio: 'inherit' });
process.exit(r.status ?? 1);
