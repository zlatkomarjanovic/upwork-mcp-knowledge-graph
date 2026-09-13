# Durable insights

## 2026-09-13: Upwork search access restricted

Repeated hourly tracker runs hit Upwork MCP `find_jobs` action=search with error: search access restricted (Terms of Service). Likely exacerbated by parallel keyword batches exceeding safe request patterns (~12/min sustained).

**Mitigation:** Run keywords strictly sequentially with 6+ second spacing. Avoid parallel MCP search calls in automation runs. If restriction persists 24h+, contact Upwork support for the freelancer account tied to org_uid 1472686528932380673.

**Data impact:** Runs while blocked append zero new jobs; keyword/group/platform stats reflect last successful ingest (run 6, 78 jobs).
