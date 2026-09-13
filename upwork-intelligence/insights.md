# Durable insights

## Upwork MCP search restriction (2026-09-13)

`find_jobs` action `search` returns CLIENT ToS restriction for freelancer org `1472686528932380673`. Run 7 could not ingest any new marketplace jobs. `smart_search` with `mode=most_recent` still responds but returned zero jobs for `days_posted=1` on this run. Retry keyword searches on the next hourly run; do not parallelize search calls when access is restored (~12/min sequential max).

## Positioning (from runs 1–6 sample, stale until search works)

- Primary demand volume: core web dev and web design keywords (35 and 24 tracked jobs in last bootstrap window).
- Highest opportunity scores in sample: GoHighLevel developer/automation ($1200 fixed), Framer developer ($85/hr), Shopware (mixed fixed/hourly).
- AI/vibe coding: `claude code developer` shows high fixed budgets in small sample; Lovable/Bolt/v0 had zero matches in tracked set.
- WordPress remains steady volume; Webflow/Framer niche with higher rates but fewer posts and higher proposals on Framer.
