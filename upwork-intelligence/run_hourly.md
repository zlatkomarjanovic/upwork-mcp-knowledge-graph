# Hourly Upwork keyword tracker

1. Load `state.json` and `current-summary.md` only at start.
2. For each keyword in `keywords.json`, call `upwork__find_jobs` (search, sort recency, limit 10).
3. After every batch of ~4 searches, write `[{keyword, response}, ...]` and run `python3 save_batch.py < batch.json` (or `python3 record_batch.py batch.json`). Do not proceed to the next batch until saved.
4. Run once: `python3 process_run.py`
5. Return chat summary from `process_run.py` output and `keyword-stats.json`.

Rate limit: ~12 find_jobs calls/minute. Use batches of 4, no long sleeps; retry failed keywords next hour.

Shell cannot call Upwork MCP. Only the agent `CallDynamicTool` works.
