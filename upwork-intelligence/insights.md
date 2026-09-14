# Upwork demand insights

## Baseline (run 1, 2026-09-14)

- First hourly ingest: 93/93 keyword searches completed, 41 unique jobs in the 2-hour bootstrap window.
- Broad `query` search pulls heavy overlap; WordPress, web design, and GoHighLevel clusters share the same fresh postings.
- AI / VIBE CODING and MAINTENANCE / RETAINERS groups score well on opportunity despite smaller explicit keyword volume (jobs match multiple AI-related queries).
- Platform signal: WordPress has the widest sample (15 jobs in window); Shopify/WooCommerce show fewer posts but higher rate/budget outliers.
- GoHighLevel: steady funnel/CRM posts; US clients mix low hourly ($5–12) with verified spend.
- Retainer-specific keywords (`website maintenance`, `webflow maintenance`) returned little in the last 2 hours; general dev keywords carry more volume.
- Hourly workflow: extract MCP `find_jobs` results from the run transcript into `raw-search-batch.jsonl`, then `process_run.py`.
