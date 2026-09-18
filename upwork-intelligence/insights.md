# Durable insights

- Baseline tracking started.
- WordPress and core web dev keywords show highest overlap in first window.
- Hourly window (Sep 13): fresh posts cluster on Shopify store builds, WordPress fixes/real estate builds, Lovable+Supabase SaaS finish work, and GoHighLevel funnel fixes.
- AI-assisted website/newsletter builds appearing alongside classic stack posts ($1.2k fixed example in window).
- Upwork MCP rate limit (~12 find_jobs/min): batch keywords and retry failed terms next hour; use `mcp_cache.json` + `cache_put.py` after live MCP batches before `persist_from_cache.py`.
- Sep 18 00:40 UTC hour: core web dev keywords picked up fresh Shopify wellness build, Squarespace coaching polish, Webflow UX fixes, and a $400 GoHighLevel/BookingKoala webhook job with fewer than 5 proposals.
- Remove stale `raw_batches/_ingest_*.json` and `all.jsonl` error rows before processing or they override good keyword batches.
