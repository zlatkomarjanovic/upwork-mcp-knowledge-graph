# Hourly Upwork tracker run

1. `python3 fetch_pending.py` (optional: list missing cache)
2. Upwork MCP: `find_jobs` for every keyword in `keywords.json` (recency, limit 10). After each batch, `python3 save_batch.py /tmp/batch.json`
3. `python3 build_search_responses.py` (from `cache/`) OR merge `mcp_raw/`
4. `python3 process_run.py`

First run window: 2 hours. Later runs: 1 hour (`process_run.py`).
