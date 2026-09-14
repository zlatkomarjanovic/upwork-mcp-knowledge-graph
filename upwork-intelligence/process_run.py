#!/usr/bin/env python3
"""Process raw Upwork search responses into intelligence store."""
from __future__ import annotations

import json
import re
import statistics
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse, urlunparse

ROOT = Path(__file__).resolve().parent


def load_run_config(state: dict) -> tuple[datetime, int]:
    import os

    run_at_raw = os.environ.get("RUN_AT_ISO") or state.get("lastRunAt")
    if run_at_raw:
        try:
            run_at = datetime.fromisoformat(run_at_raw.replace("Z", "+00:00"))
        except ValueError:
            run_at = datetime.now(timezone.utc)
    else:
        run_at = datetime.now(timezone.utc)
    window_hours = 2 if int(state.get("runNumber", 0)) == 0 else 1
    return run_at, window_hours

SKIP_TITLE_PATTERNS = re.compile(
    r"\b(crypto|bitcoin|trading|gambling|casino|betting|adult|porn|escort|dating|hookup|alcohol|brewery|distillery)\b",
    re.I,
)

PLATFORM_KEYWORDS = {
    "WordPress": ["wordpress"],
    "Webflow": ["webflow"],
    "Framer": ["framer"],
    "GoHighLevel": ["gohighlevel", "go high level", "ghl"],
    "Shopify": ["shopify"],
    "WooCommerce": ["woocommerce"],
    "Shopware": ["shopware"],
    "Lovable": ["lovable"],
    "Bolt": ["bolt.new", "bolt developer"],
    "v0": ["v0 developer", "v0 vercel"],
    "Next.js": ["nextjs", "next.js"],
}


def normalize_url(url: str) -> str:
    if not url:
        return ""
    p = urlparse(url.split("?")[0])
    return urlunparse((p.scheme, p.netloc, p.path.rstrip("/"), "", "", ""))


def parse_money(s: str | None) -> float | None:
    if not s:
        return None
    s = s.replace(",", "").strip()
    m = re.search(r"([\d.]+)", s)
    return float(m.group(1)) if m else None


def parse_budget(job: dict) -> tuple[str | None, float | None, float | None]:
    b = job.get("budget")
    jt = job.get("job_type")
    if not b:
        return jt, None, None
    if "–" in b or "-" in b:
        parts = re.split(r"[–-]", b)
        nums = [parse_money(p) for p in parts]
        nums = [n for n in nums if n is not None]
        if jt == "hourly" and nums:
            return jt, nums[0], nums[-1] if len(nums) > 1 else nums[0]
    val = parse_money(b)
    return jt, val, val


def parse_client_spend(s: str | None) -> float | None:
    if not s:
        return None
    s = s.replace(",", "").replace("$", "").strip()
    try:
        return float(s)
    except ValueError:
        return None


def confidence_label(n: int) -> str:
    if n <= 4:
        return "Very Low"
    if n <= 14:
        return "Low"
    if n <= 39:
        return "Medium"
    if n <= 99:
        return "High"
    return "Very High"


def opportunity_score(jobs: list[dict]) -> int:
    if not jobs:
        return 0
    score = 0.0
    for j in jobs:
        jt, lo, hi = parse_budget(j)
        proposals = j.get("proposal_count") or 50
        verified = 1 if (j.get("client") or {}).get("verification_status") == "VERIFIED" else 0
        high = 0
        if jt == "fixed" and hi and hi >= 1000:
            high = 1
        if jt == "hourly" and lo and lo >= 40:
            high = 1
        score += 15 * high + 10 * verified + max(0, 25 - min(proposals, 25))
        if hi:
            score += min(hi / 200, 15)
    return max(1, min(100, int(score / len(jobs))))


def job_record(job: dict, keyword: str, group: str, window_start_ms: float) -> dict | None:
    url = job.get("url")
    if not url:
        return None
    pub = job.get("published_date") or job.get("created_date")
    if pub:
        try:
            ts = datetime.fromisoformat(pub.replace("Z", "+00:00")).timestamp() * 1000
            if ts < window_start_ms:
                return None
        except ValueError:
            pass
    title = job.get("title") or ""
    if SKIP_TITLE_PATTERNS.search(title):
        return None
    desc = job.get("description_snippet") or ""
    if SKIP_TITLE_PATTERNS.search(desc):
        return None

    client = job.get("client") or {}
    jt, budget_lo, budget_hi = parse_budget(job)
    budget_str = job.get("budget")

    return {
        "url": normalize_url(url),
        "title": title,
        "matchedKeyword": [keyword],
        "keywordGroup": group,
        "postedAt": pub,
        "type": jt,
        "budget": budget_str if jt == "fixed" else None,
        "hourlyRate": budget_str if jt == "hourly" else None,
        "budgetFixed": budget_lo if jt == "fixed" else None,
        "rateHourlyMin": budget_lo if jt == "hourly" else None,
        "rateHourlyMax": budget_hi if jt == "hourly" else None,
        "duration": job.get("duration"),
        "proposals": job.get("proposal_count"),
        "clientCountry": client.get("country"),
        "paymentVerified": client.get("verification_status") == "VERIFIED",
        "clientSpend": client.get("total_spent"),
        "clientSpendNum": parse_client_spend(client.get("total_spent")),
        "clientHireRate": None,
        "clientRating": client.get("rating"),
        "experienceLevel": job.get("experience_level"),
        "skills": job.get("skills") or [],
    }


def load_json(path: Path, default):
    if path.exists():
        return json.loads(path.read_text())
    return default


def main() -> None:
    keywords = json.loads((ROOT / "keywords.json").read_text())
    raw_path = ROOT / "search_responses.json"
    if not raw_path.exists():
        print("No search_responses.json")
        return

    raw = json.loads(raw_path.read_text())
    state = load_json(ROOT / "state.json", {"runNumber": 0, "totalJobs": 0, "knownJobUrls": []})
    run_number = int(state.get("runNumber", 0)) + 1
    known = set(state.get("knownJobUrls") or [])

    run_at, window_hours = load_run_config(state)
    window_ms = window_hours * 3600 * 1000
    window_start_ms = run_at.timestamp() * 1000 - window_ms
    now_iso = run_at.isoformat().replace("+00:00", "Z")

    jobs_by_url: dict[str, dict] = {}
    keyword_hits: dict[str, list[dict]] = defaultdict(list)
    errors: list[str] = []
    attempted = len(keywords)
    completed = 0

    for entry in raw:
        if "response" in entry and "jobs" not in entry:
            resp = entry.get("response") or {}
            if isinstance(resp, dict):
                entry["jobs"] = resp.get("jobs") or []
                if not entry.get("error"):
                    entry["error"] = resp.get("error") or resp.get("error_code")
        kw = entry.get("keyword")
        group = entry.get("group")
        if entry.get("error"):
            errors.append(kw)
            continue
        completed += 1
        for job in entry.get("jobs") or []:
            rec = job_record(job, kw, group, window_start_ms)
            if not rec:
                continue
            url = rec["url"]
            keyword_hits[kw].append(rec)
            if url in jobs_by_url:
                existing = jobs_by_url[url]
                for k in rec["matchedKeyword"]:
                    if k not in existing["matchedKeyword"]:
                        existing["matchedKeyword"].append(k)
            else:
                jobs_by_url[url] = rec

    new_jobs = [j for u, j in jobs_by_url.items() if u not in known]
    jobs_path = ROOT / "jobs.jsonl"
    with jobs_path.open("a") as f:
        for j in new_jobs:
            f.write(json.dumps(j, ensure_ascii=False) + "\n")

    all_jobs = []
    if jobs_path.exists():
        for line in jobs_path.read_text().splitlines():
            if line.strip():
                all_jobs.append(json.loads(line))

    known.update(j["url"] for j in new_jobs)
    total_jobs = len(all_jobs) if all_jobs else len(known)

    # Stats from all tracked jobs
    kw_stats = {}
    for kdef in keywords:
        kw = kdef["keyword"]
        subset = [j for j in all_jobs if kw in j.get("matchedKeyword", [])]
        fixed = [j["budgetFixed"] for j in subset if j.get("budgetFixed")]
        hourly = [j["rateHourlyMin"] for j in subset if j.get("rateHourlyMin")]
        props = [j["proposals"] for j in subset if j.get("proposals") is not None]
        verified = [j for j in subset if j.get("paymentVerified")]
        spend = [j["clientSpendNum"] for j in subset if j.get("clientSpendNum")]
        high = [
            j
            for j in subset
            if (j.get("budgetFixed") and j["budgetFixed"] >= 1000)
            or (j.get("rateHourlyMin") and j["rateHourlyMin"] >= 40)
        ]
        ts24 = run_at.timestamp() * 1000 - 86400000
        last24 = []
        for j in subset:
            pa = j.get("postedAt")
            if not pa:
                continue
            try:
                if datetime.fromisoformat(pa.replace("Z", "+00:00")).timestamp() * 1000 >= ts24:
                    last24.append(j)
            except ValueError:
                pass
        n = len(subset)
        kw_stats[kw] = {
            "keyword": kw,
            "group": kdef["group"],
            "totalJobs": n,
            "jobsLast24h": len(last24),
            "avgBudgetFixed": round(statistics.mean(fixed), 2) if fixed else None,
            "avgRateHourly": round(statistics.mean(hourly), 2) if hourly else None,
            "medianProposals": int(statistics.median(props)) if props else None,
            "pctVerified": round(100 * len(verified) / n, 1) if n else 0,
            "avgClientSpend": round(statistics.mean(spend), 2) if spend else None,
            "pctHighBudget": round(100 * len(high) / n, 1) if n else 0,
            "opportunityScore": opportunity_score(subset),
            "sampleConfidence": confidence_label(n),
        }

    (ROOT / "keyword-stats.json").write_text(json.dumps(kw_stats, indent=2))

    group_agg = defaultdict(list)
    for s in kw_stats.values():
        group_agg[s["group"]].append(s)
    group_stats = {}
    for g, items in group_agg.items():
        scores = [i["opportunityScore"] for i in items]
        group_stats[g] = {
            "group": g,
            "totalJobs": sum(i["totalJobs"] for i in items),
            "jobsLast24h": sum(i["jobsLast24h"] for i in items),
            "avgOpportunityScore": round(statistics.mean(scores), 1) if scores else 0,
            "keywordCount": len(items),
        }
    ranked_groups = sorted(group_stats.values(), key=lambda x: -x["avgOpportunityScore"])
    (ROOT / "group-stats.json").write_text(json.dumps({"groups": ranked_groups, "byGroup": group_stats}, indent=2))

    platform_stats = {}
    for plat, kws in PLATFORM_KEYWORDS.items():
        subset = [j for j in all_jobs if any(k in j.get("matchedKeyword", []) for k in kws)]
        fixed = [j["budgetFixed"] for j in subset if j.get("budgetFixed")]
        hourly = [j["rateHourlyMin"] for j in subset if j.get("rateHourlyMin")]
        props = [j["proposals"] for j in subset if j.get("proposals") is not None]
        n = len(subset)
        platform_stats[plat] = {
            "platform": plat,
            "jobs": n,
            "avgBudgetFixed": round(statistics.mean(fixed), 2) if fixed else None,
            "avgRateHourly": round(statistics.mean(hourly), 2) if hourly else None,
            "medianProposals": int(statistics.median(props)) if props else None,
            "opportunityScore": opportunity_score(subset),
            "sampleConfidence": confidence_label(n),
        }
    (ROOT / "platform-stats.json").write_text(json.dumps(platform_stats, indent=2))

    top3 = sorted(kw_stats.values(), key=lambda x: (-x["jobsLast24h"], -x["opportunityScore"]))[:3]
    log = {
        "timestamp": now_iso,
        "runNumber": run_number,
        "keywordsAttempted": attempted,
        "keywordsCompleted": completed,
        "newJobs": len(new_jobs),
        "totalJobs": total_jobs,
        "top3Keywords": [t["keyword"] for t in top3],
        "errors": errors,
    }
    with (ROOT / "run-log.jsonl").open("a") as f:
        f.write(json.dumps(log) + "\n")

    state_out = {
        "lastRunAt": now_iso,
        "runNumber": run_number,
        "totalJobs": total_jobs,
        "knownJobUrls": sorted(known),
        "lastInsightRefresh": state.get("lastInsightRefresh"),
    }
    (ROOT / "state.json").write_text(json.dumps(state_out, indent=2))

    top10 = sorted(kw_stats.values(), key=lambda x: (-x["opportunityScore"], -x["jobsLast24h"]))[:10]
    primary = top10[0]["keyword"] if top10 else "wordpress developer"
    secondary = top10[1]["keyword"] if len(top10) > 1 else "webflow developer"

    summary = f"""# Upwork Market Intelligence

Last updated: {now_iso}
Run: {run_number}
Total jobs tracked: {total_jobs}
Keywords attempted: {attempted}
Keywords completed: {completed}

## Top Opportunities

"""
    for i, t in enumerate(top10, 1):
        summary += f"""{i}. **{t['keyword']}** — score {t['opportunityScore']}, confidence {t['sampleConfidence']}
   - jobsLast24h: {t['jobsLast24h']}, totalJobs: {t['totalJobs']}
   - avg fixed: {t['avgBudgetFixed']}, avg hourly: {t['avgRateHourly']}
   - median proposals: {t['medianProposals']}

"""

    summary += "## Strongest Groups\n\n"
    for i, g in enumerate(ranked_groups[:8], 1):
        summary += f"{i}. {g['group']} — avg score {g['avgOpportunityScore']}, jobs24h {g['jobsLast24h']}\n"

    summary += "\n## Platform Ranking\n\n"
    plat_rank = sorted(platform_stats.values(), key=lambda x: -x["opportunityScore"])
    for i, p in enumerate(plat_rank, 1):
        summary += f"{i}. {p['platform']} — score {p['opportunityScore']}, jobs {p['jobs']}, confidence {p['sampleConfidence']}\n"

    summary += f"""
## Positioning Recommendation

Primary keyword: {primary}
Secondary keyword: {secondary}
Best platform/service: WordPress + Next.js hybrid positioning
Overview keywords: {primary}, {secondary}, full stack developer, website redesign
Skill tags: WordPress, Elementor, Next.js, React, Webflow, Framer, SEO

## Current Verdicts

WordPress: Steady volume; mix of maintenance and builds; watch low-budget outliers.
Webflow: Lower title-match volume than WordPress; specialized opportunities.
Framer: Niche but visible in dev titles; good for premium fixed builds.
GoHighLevel: Sparse in title search; funnel/agency angle still valid.
AI/Vibe Coding: Growing mention in full-stack/AI SaaS posts; pair with Next.js/Supabase.
Ecommerce: Shopify and WooCommerce both active; verify budget before applying.
Maintenance: Retainer keywords surface ongoing WordPress and agency support posts.

## Important Changes

First baseline run — no prior comparison.
"""
    (ROOT / "current-summary.md").write_text(summary)

    if not (ROOT / "insights.md").exists():
        (ROOT / "insights.md").write_text(
            "# Upwork Intelligence Insights\n\n"
            "- Baseline established on first hourly run (Sep 2026).\n"
            "- WordPress title searches return the highest overlap with core web keywords.\n"
            "- Rate limit: ~12 find_jobs/min; run keywords sequentially in automation.\n"
        )

    print(json.dumps({"run": run_number, "new": len(new_jobs), "total": total_jobs, "completed": completed, "errors": len(errors)}))


if __name__ == "__main__":
    main()
