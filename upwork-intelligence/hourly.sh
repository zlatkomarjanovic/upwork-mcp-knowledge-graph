#!/usr/bin/env bash
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"
# Agent must populate raw_batches/*.json via apply-search-batch.mjs after MCP searches (~12 find_jobs/min).
node merge-raw.mjs
node process-run.mjs "$DIR/.run-payload.json"
