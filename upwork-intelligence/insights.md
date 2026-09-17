# Upwork tracker insights

## 2026-09-17

- Upwork API/MCP `find_jobs` search for freelancer org `1472686528932380673` returns persistent CLIENT error: search access restricted (TOS). Affects all 93 configured keywords.
- `smart_search` (best_match and most_recent) returns empty with `no_personalization` / `filters_no_match`; not a substitute for full keyword sweeps.
- Prior automation memory noted parallel bursts may trigger restrictions; this run used mixed batching but single sequential calls also fail with the same TOS message.
- Action: contact Upwork support to restore search access; future runs should stay at ~10-12 search calls/min when access returns.
