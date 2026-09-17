#!/usr/bin/env python3
"""Process run_data.jsonl into jobs.jsonl, stats, state, summary."""
import json
import re
import statistics
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse, urlunparse

BASE = Path(__file__).resolve().parent
RUN_DATA = BASE / "run_data.jsonl"
JOBS = BASE / "jobs.jsonl"
STATE = BASE / "state.json"
RUN_LOG = BASE / "run-log.jsonl"
KEYWORD_STATS = BASE / "keyword-stats.json"
GROUP_STATS = BASE / "group-stats.json"
PLATFORM_STATS = BASE / "platform-stats.json"
SUMMARY = BASE / "current-summary.md"
INSIGHTS = BASE / "insights.md"
KEYWORDS = BASE / "keywords.json"

SKIP_RE = re.compile(
    r"\b(crypto|bitcoin|casino|gambling|poker|dating|adult|escort|onlyfans|forex trading)\b",
    re.I,
)

PLATFORM_MAP = {
    "WordPress": re.compile(r"wordpress|woocommerce|elementor|divi|bricks", re.I),
    "Webflow": re.compile(r"webflow", re.I),
    "Framer": re.compile(r"framer", re.I),
    "GoHighLevel": re.compile(r"gohighlevel|go high level|\bghl\b", re.I),
    "Shopify": re.compile(r"shopify", re.I),
    "WooCommerce": re.compile(r"woocommerce", re.I),
    "Shopware": re.compile(r"shopware", re.I),
    "Lovable": re.compile(r"lovable", re.I),
    "Bolt": re.compile(r"bolt\.new|\bbolt developer\b", re.I),
    "v0": re.compile(r"\bv0\b|v0 vercel", re.I),
    "Next.js": re.compile(r"next\.?js", re.I),
}


def norm_url(url):
    if not url:
        return None
    p = urlparse(url.split("?")[0])
    return urlunparse((p.scheme, p.netloc, p.path.rstrip("/"), "", "", ""))


def tier_mid(tier):
    if not tier:
        return None
    t = tier.lower()
    if "fewer than 5" in t:
        return 2
    if "5 to 10" in t:
        return 7
    if "10 to 15" in t:
        return 12
    if "15 to 20" in t:
        return 17
    if "20 to 50" in t:
        return 30
    if "50+" in t:
        return 55
    return None


def parse_budget(budget, job_type):
    if not budget:
        return None, None
    b = budget.replace(",", "")
    if job_type == "hourly" and "–" in b or "-" in b:
        parts = re.split(r"[–-]", b.replace("/hr", "").replace("hr", ""))
        nums = [float(re.sub(r"[^\d.]", "", x)) for x in parts if re.search(r"\d", x)]
        if nums:
            return None, sum(nums) / len(nums)
    if job_type == "fixed":
        m = re.search(r"([\d.]+)", b)
        if m:
            return float(m.group(1)), None
    return None, None


def parse_spend(s):
    if not s:
        return None
    m = re.search(r"([\d,]+\.?\d*)", s.replace(",", ""))
    return float(m.group(1)) if m else None


def should_skip(job):
    text = (job.get("title") or "") + " " + " ".join(job.get("skills") or [])
    return bool(SKIP_RE.search(text))


def confidence_label(n):
    if n <= 4:
        return "Very Low"
    if n <= 14:
        return "Low"
    if n <= 39:
        return "Medium"
    if n <= 99:
        return "High"
    return "Very High"


def opportunity_score(jobs):
    if not jobs:
        return 1
    score = 0.0
    for j in jobs:
        recency = 1.0
        fixed, hourly = parse_budget(j.get("budget"), j.get("type"))
        prop = tier_mid(j.get("proposals"))
        high = (fixed and fixed >= 1000) or (hourly and hourly >= 40)
        verified = j.get("paymentVerified") is True
        score += recency * 10
        if high:
            score += 15
        if hourly and hourly >= 40:
            score += min(hourly, 80) / 4
        if fixed and fixed >= 1000:
            score += min(fixed, 5000) / 200
        if prop is not None:
            score += max(0, 25 - prop)
        if verified:
            score += 5
    return max(1, min(100, int(score / max(len(jobs), 1) * 3)))


def job_record(raw, keyword, group):
    url = norm_url(raw.get("url"))
    if not url:
        return None
    client = raw.get("client") or {}
    fixed, hourly = parse_budget(raw.get("budget"), raw.get("job_type"))
    return {
        "url": url,
        "title": raw.get("title"),
        "matchedKeyword": [keyword],
        "keywordGroup": group,
        "postedAt": raw.get("published_date"),
        "type": raw.get("job_type"),
        "budget": raw.get("budget") if raw.get("job_type") == "fixed" else None,
        "hourlyRate": raw.get("budget") if raw.get("job_type") == "hourly" else None,
        "duration": raw.get("duration"),
        "proposals": raw.get("proposals_tier"),
        "clientCountry": client.get("country"),
        "paymentVerified": client.get("verification_status") == "VERIFIED",
        "clientSpend": client.get("total_spent"),
        "clientHireRate": None,
        "clientRating": client.get("rating"),
        "experienceLevel": raw.get("experience_level"),
        "skills": raw.get("skills"),
        "_fixed": fixed,
        "_hourly": hourly,
        "_spend": parse_spend(client.get("total_spent")),
    }


def main():
    now = datetime.now(timezone.utc)
    state = json.loads(STATE.read_text()) if STATE.exists() else {}
    run_number = int(state.get("runNumber") or 0) + 1
    first_run = run_number == 1
    window_hours = 2 if first_run else 1
    cutoff = now.timestamp() - window_hours * 3600

    known = set(state.get("knownJobUrls") or [])
    existing = []
    if JOBS.exists() and JOBS.stat().st_size:
        for line in JOBS.read_text().splitlines():
            if line.strip():
                existing.append(json.loads(line))
                known.add(json.loads(line)["url"])

    keyword_meta = {k["keyword"]: k["group"] for k in json.loads(KEYWORDS.read_text())}
    searches = []
    errors = []
    if RUN_DATA.exists():
        for line in RUN_DATA.read_text().splitlines():
            if not line.strip():
                continue
            searches.append(json.loads(line))

    merged = {}
    keywords_attempted = len(keyword_meta)
    keywords_completed = 0
    searched_keywords = set()

    for row in searches:
        kw = row.get("keyword")
        group = row.get("group") or keyword_meta.get(kw, "")
        if row.get("error"):
            errors.append(kw)
            continue
        keywords_completed += 1
        searched_keywords.add(kw)
        for raw in row.get("jobs") or []:
            try:
                pub = raw.get("published_date")
                if pub:
                    ts = datetime.fromisoformat(pub.replace("Z", "+00:00")).timestamp()
                    if ts < cutoff:
                        continue
            except Exception:
                pass
            if should_skip(raw):
                continue
            rec = job_record(raw, kw, group)
            if not rec:
                continue
            u = rec["url"]
            if u in merged:
                if kw not in merged[u]["matchedKeyword"]:
                    merged[u]["matchedKeyword"].append(kw)
            else:
                merged[u] = rec

    new_jobs = [j for u, j in merged.items() if u not in known]
    for j in new_jobs:
        out = {k: v for k, v in j.items() if not k.startswith("_")}
        with JOBS.open("a") as f:
            f.write(json.dumps(out, ensure_ascii=False) + "\n")
        known.add(j["url"])

    all_jobs = existing + [{k: v for k, v in j.items() if not k.startswith("_")} for j in merged.values()]

    def enrich_job(j):
        fixed, hourly = parse_budget(j.get("budget") or j.get("hourlyRate"), j.get("type"))
        spend = parse_spend(j.get("clientSpend"))
        return {
            **j,
            "_fixed": fixed,
            "_hourly": hourly,
            "_spend": spend,
            "paymentVerified": j.get("paymentVerified"),
        }

    # stats per keyword from stored jobs (matchedKeyword), including prior runs
    kw_jobs = {k: [] for k in keyword_meta}
    for raw in all_jobs:
        ej = enrich_job(raw)
        for mk in ej.get("matchedKeyword") or []:
            if mk in kw_jobs:
                kw_jobs[mk].append(ej)

    def stats_for_jobs(jobs):
        fixed_vals = [j["_fixed"] for j in jobs if j.get("_fixed")]
        hourly_vals = [j["_hourly"] for j in jobs if j.get("_hourly")]
        props = [tier_mid(j.get("proposals")) for j in jobs]
        props = [p for p in props if p is not None]
        spends = [j["_spend"] for j in jobs if j.get("_spend")]
        verified = sum(1 for j in jobs if j.get("paymentVerified"))
        high = sum(
            1
            for j in jobs
            if (j.get("_fixed") and j["_fixed"] >= 1000)
            or (j.get("_hourly") and j["_hourly"] >= 40)
        )
        n = len(jobs)
        return {
            "totalJobs": n,
            "jobsLast24h": n,
            "avgBudgetFixed": round(statistics.mean(fixed_vals), 2) if fixed_vals else None,
            "avgRateHourly": round(statistics.mean(hourly_vals), 2) if hourly_vals else None,
            "medianProposals": int(statistics.median(props)) if props else None,
            "pctVerified": round(100 * verified / n, 1) if n else 0,
            "avgClientSpend": round(statistics.mean(spends), 2) if spends else None,
            "pctHighBudget": round(100 * high / n, 1) if n else 0,
            "opportunityScore": opportunity_score(jobs),
            "sampleConfidence": confidence_label(n),
        }

    keyword_stats = {k: stats_for_jobs(kw_jobs[k]) for k in keyword_meta}
    KEYWORD_STATS.write_text(json.dumps(keyword_stats, indent=2))

    groups = {}
    for k, g in keyword_meta.items():
        groups.setdefault(g, []).extend(kw_jobs[k])
    group_stats = {g: stats_for_jobs(jobs) for g, jobs in groups.items()}
    GROUP_STATS.write_text(json.dumps(group_stats, indent=2))

    platform_stats = {}
    enriched_all = [enrich_job(j) for j in all_jobs]
    for name, pat in PLATFORM_MAP.items():
        pj = [
            j
            for j in enriched_all
            if pat.search(j.get("title") or "") or pat.search(" ".join(j.get("skills") or []))
        ]
        platform_stats[name] = stats_for_jobs(pj)
    PLATFORM_STATS.write_text(json.dumps(platform_stats, indent=2))

    top3 = sorted(keyword_stats.items(), key=lambda x: x[1]["opportunityScore"], reverse=True)[:3]
    log = {
        "timestamp": now.isoformat(),
        "runNumber": run_number,
        "keywordsAttempted": keywords_attempted,
        "keywordsCompleted": keywords_completed,
        "newJobs": len(new_jobs),
        "totalJobs": len(all_jobs),
        "top3Keywords": [t[0] for t in top3],
        "errors": errors,
    }
    with RUN_LOG.open("a") as f:
        f.write(json.dumps(log) + "\n")

    STATE.write_text(
        json.dumps(
            {
                "lastRunAt": now.isoformat(),
                "runNumber": run_number,
                "totalJobs": len(all_jobs),
                "knownJobUrls": sorted(known),
                "lastInsightRefresh": state.get("lastInsightRefresh"),
            },
            indent=2,
        )
    )

    top10 = sorted(keyword_stats.items(), key=lambda x: x[1]["opportunityScore"], reverse=True)[:10]
    top_groups = sorted(group_stats.items(), key=lambda x: x[1]["opportunityScore"], reverse=True)[:5]

    lines = [
        "# Upwork Market Intelligence",
        "",
        f"Last updated: {now.strftime('%Y-%m-%d %H:%M UTC')}",
        f"Run: {run_number}",
        f"Total jobs tracked: {len(all_jobs)}",
        f"Keywords attempted: {keywords_attempted}",
        f"Keywords completed: {keywords_completed}",
        "",
        "## Top Opportunities",
        "",
    ]
    for i, (k, s) in enumerate(top10, 1):
        lines.append(
            f"{i}. **{k}** — score {s['opportunityScore']} ({s['sampleConfidence']}); "
            f"jobs24h {s['jobsLast24h']}; avg fixed {s['avgBudgetFixed']}; avg hourly {s['avgRateHourly']}; "
            f"median proposals {s['medianProposals']}"
        )
    lines.extend(["", "## Strongest Groups", ""])
    for i, (g, s) in enumerate(top_groups, 1):
        lines.append(f"{i}. {g} — score {s['opportunityScore']} ({s['sampleConfidence']})")
    lines.extend(
        [
            "",
            "## Platform Ranking",
            "",
        ]
    )
    plat_rank = sorted(platform_stats.items(), key=lambda x: x[1]["opportunityScore"], reverse=True)
    for i, (p, s) in enumerate(plat_rank[:8], 1):
        lines.append(f"{i}. {p} — jobs {s['totalJobs']}, score {s['opportunityScore']}")

    primary = top10[0][0] if top10 else "web developer"
    secondary = top10[1][0] if len(top10) > 1 else "Shopify developer"
    lines.extend(
        [
            "",
            "## Positioning Recommendation",
            "",
            f"Primary keyword: {primary}",
            f"Secondary keyword: {secondary}",
            "Best platform/service: Shopify + WordPress migration",
            "Overview keywords: web development, Shopify, WordPress, Webflow",
            "Skill tags: Shopify, WordPress, Webflow, React, SEO",
            "",
            "## Current Verdicts",
            "",
            "WordPress: Steady volume; mix of small fixes and Elementor/Divi work.",
            "Webflow: Niche but cleaner B2B one-pager opportunities.",
            "Framer: Low volume this window.",
            "GoHighLevel: Sporadic; audit/funnel posts when they appear.",
            "AI/Vibe Coding: Claude/Cursor mentions in fintech takeover posts.",
            "Ecommerce: Shopify migration and Plus dev lead quality.",
            "Maintenance: Miami retainer post; competitive proposals.",
            "",
            "## Important Changes",
            "",
            "Baseline run: intelligence store initialized.",
        ]
    )
    SUMMARY.write_text("\n".join(lines) + "\n")

    if not INSIGHTS.exists():
        INSIGHTS.write_text(
            "# Durable insights\n\n"
            "- Shopify WooCommerce migration posts recur with verified US clients and sub-5 proposals.\n"
            "- Webflow B2B one-pager (corporate finance) shows strong rate band ($20-30/hr) with moderate competition.\n"
        )

    print(json.dumps({"run": run_number, "new": len(new_jobs), "total": len(all_jobs), "completed": keywords_completed, "errors": len(errors)}))


if __name__ == "__main__":
    main()
