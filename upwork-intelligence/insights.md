# Upwork Intelligence Insights

## 2026-09-16

- **Blocker:** Freelancer account (Zlatko Marjanovic) cannot use marketplace job search via API. Upwork returns: "Your access to search has been restricted due to violations of our Terms of Service."
- **Action:** Contact Upwork support to restore search access. Until then, hourly tracker runs will log zero new jobs.
- **Note:** `smart_search` endpoints respond OK but return no jobs (`no_personalization`), so they cannot substitute for keyword marketplace search.
