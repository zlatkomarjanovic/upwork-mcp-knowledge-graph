# Upwork Intelligence Insights

## 2026-09-14 — Search API blocked

Upwork `find_jobs` with `action=search` returns a CLIENT error: marketplace search access is restricted on the connected freelancer account (Terms of Service). Hourly keyword tracking cannot collect marketplace data until Upwork restores search access or the MCP integration uses an authorized search path.

`smart_search` (personalized feed) responds but returned no jobs on the first run (`no_personalization` / empty filters), so it is not a substitute for keyword-wide market scans.

**Action:** Contact Upwork support to lift search restrictions on the Zlatko Marjanovic freelancer account, then re-run the tracker.
