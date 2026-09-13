# Upwork Intelligence Knowledge Tree

Primary source of truth: `../upwork-keyword-report.html` (embedded `#jobs-data` JSON).

| File | Role |
|------|------|
| `current-summary.md` | Fast entry point for agents |
| `keyword-stats.json` | Latest per-keyword metrics (regenerated each run) |
| `group-stats.json` | Keyword group rollup |
| `platform-stats.json` | Platform comparison stats |
| `jobs.jsonl` | Append-only raw job records |
| `run-log.jsonl` | Append-only automation run history |
| `insights.md` | Durable cross-run conclusions |

Read `current-summary.md` first for positioning questions. Use `jobs.jsonl` only for job-level evidence.
