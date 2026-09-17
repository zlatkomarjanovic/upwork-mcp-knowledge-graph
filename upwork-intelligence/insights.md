# Upwork intelligence insights

## 2026-09-17

- Marketplace keyword search via Upwork MCP (`find_jobs` action=search) is **globally blocked** for org `1472686528932380673` with: "Your access to search has been restricted due to violations of our Terms of Service."
- Tracker cannot ingest demand data until search access is restored. Hourly runs should still attempt all 93 keywords and log failures.
- Use sequential searches (~10/min) once access returns; parallel bursts may have contributed to restriction.
