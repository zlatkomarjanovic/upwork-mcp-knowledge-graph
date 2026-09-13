#!/usr/bin/env python3
"""Process Upwork keyword search batches into jobs.jsonl and stats."""
from __future__ import annotations

import json
import re
import statistics
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent
STATE_PATH = ROOT / "state.json"
JOBS_PATH = ROOT / "jobs.jsonl"
RUN_LOG_PATH = ROOT / "run-log.jsonl"
SEARCH_GLOB = "search_batch_*.json"
KEYWORD_STATS_PATH = ROOT / "keyword-stats.json"
GROUP_STATS_PATH = ROOT / "group-stats.json"
PLATFORM_STATS_PATH = ROOT / "platform-stats.json"
SUMMARY_PATH = ROOT / "current-summary.md"

SKIP_PATTERNS = re.compile(
    r"\b(crypto|bitcoin|casino|gambling|poker|betting|adult|escort|onlyfans|dating app)\b",
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

GROUPS_ORDER = [
    "CORE WEB DEVELOPMENT",
    "WEB DESIGN",
    "WORDPRESS",
    "WEBFLOW / FRAMER",
    "AI / VIBE CODING",
    "GOHIGHLEVEL",
    "ADJACENT PLATFORMS",
    "MODERN STACK",
    "ECOMMERCE",
    "MAINTENANCE / RETAINERS",
    "CONVERSION / PERFORMANCE",
]


def parse_money(val: str | None) -> float | None:
    if not val:
        return None
    s = val.replace(",", "").replace("$", "").strip()
    if "–" in s or "-" in s:
        part = re.split(r"[–-]", s)[0].strip()
        s = part.replace("/hr", "").strip()
    else:
        s = s.replace("/hr", "").strip()
    try:
        return float(s)
    except ValueError:
        return None


def parse_hourly_mid(val: str | None) -> float | None:
    if not val:
        return None
    s = val.replace("$", "").replace("/hr", "").strip()
    if "–" in s:
        a, b = s.split("–", 1)
        try:
            return (float(a.strip()) + float(b.strip())) / 2
        except ValueError:
            return parse_money(val)
    return parse_money(val)


def normalize_url(url: str) -> str:
    return url.split("?")[0].rstrip("/")


def job_from_api(j: dict, keyword: str, group: str) -> dict | None:
    url = j.get("url")
    if not url:
        return None
    snippet = j.get("description_snippet") or ""
    title = j.get("title") or ""
    if SKIP_PATTERNS.search(snippet) or SKIP_PATTERNS.search(title):
        return None
    client = j.get("client") or {}
    budget_raw = j.get("budget")
    jtype = j.get("job_type")
    return {
        "url": normalize_url(url),
        "title": title,
        "matchedKeyword": [keyword],
        "keywordGroup": group,
        "postedAt": j.get("published_date") or j.get("created_date"),
        "type": jtype,
        "budget": budget_raw if jtype == "fixed" else None,
        "hourlyRate": budget_raw if jtype == "hourly" else None,
        "duration": j.get("duration"),
        "proposals": j.get("proposal_count"),
        "clientCountry": client.get("country"),
        "paymentVerified": client.get("verification_status") == "VERIFIED",
        "clientSpend": client.get("total_spent"),
        "clientHireRate": None,
        "clientRating": client.get("rating"),
        "experienceLevel": j.get("experience_level"),
        "skills": j.get("skills") or [],
    }


def load_state() -> dict:
    if STATE_PATH.exists():
        return json.loads(STATE_PATH.read_text())
    return {
        "lastRunAt": None,
        "runNumber": 0,
        "totalJobs": 0,
        "knownJobUrls": [],
        "lastInsightRefresh": None,
        "firstRunComplete": False,
    }


def load_jobs_index() -> dict[str, dict]:
    index: dict[str, dict] = {}
    if not JOBS_PATH.exists():
        return index
    with JOBS_PATH.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            url = row.get("url")
            if url:
                index[url] = row
    return index


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


def is_high_budget(job: dict) -> bool:
    if job.get("type") == "fixed":
        b = parse_money(job.get("budget"))
        return b is not None and b >= 1000
    if job.get("type") == "hourly":
        r = parse_hourly_mid(job.get("hourlyRate"))
        return r is not None and r >= 40
    return False


def opportunity_score(jobs: list[dict]) -> int:
    if not jobs:
        return 1
    score = 0.0
    now = datetime.now(timezone.utc)
    for j in jobs:
        recency = 0.5
        if j.get("postedAt"):
            try:
                posted = datetime.fromisoformat(j["postedAt"].replace("Z", "+00:00"))
                hours = (now - posted).total_seconds() / 3600
                recency = max(0.2, 1.0 - min(hours, 48) / 48)
            except ValueError:
                pass
        props = j.get("proposals") or 10
        comp = max(0.2, 1.0 - min(props, 50) / 50)
        pay = 0.3
        if j.get("type") == "fixed":
            b = parse_money(j.get("budget"))
            if b:
                pay = min(1.0, b / 2000)
        else:
            r = parse_hourly_mid(j.get("hourlyRate"))
            if r:
                pay = min(1.0, r / 80)
        verified = 1.0 if j.get("paymentVerified") else 0.6
        high = 1.2 if is_high_budget(j) else 1.0
        score += recency * comp * pay * verified * high
    raw = score / len(jobs) * 40
    return max(1, min(100, int(raw)))


def aggregate_keyword_stats(all_jobs: list[dict]) -> dict:
    by_kw: dict[str, list[dict]] = {}
    for j in all_jobs:
        for kw in j.get("matchedKeyword") or []:
            by_kw.setdefault(kw, []).append(j)
    now = datetime.now(timezone.utc)
    stats = {}
    for kw, jobs in by_kw.items():
        last24 = [
            j
            for j in jobs
            if j.get("postedAt")
            and (
                now
                - datetime.fromisoformat(j["postedAt"].replace("Z", "+00:00"))
            ).total_seconds()
            <= 86400
        ]
        fixed = [parse_money(j.get("budget")) for j in jobs if j.get("type") == "fixed"]
        fixed = [x for x in fixed if x is not None]
        hourly = [
            parse_hourly_mid(j.get("hourlyRate"))
            for j in jobs
            if j.get("type") == "hourly"
        ]
        hourly = [x for x in hourly if x is not None]
        props = [j.get("proposals") for j in jobs if j.get("proposals") is not None]
        verified = sum(1 for j in jobs if j.get("paymentVerified"))
        spends = []
        for j in jobs:
            s = j.get("clientSpend")
            if s:
                v = parse_money(str(s))
                if v is not None:
                    spends.append(v)
        high = sum(1 for j in jobs if is_high_budget(j))
        n = len(jobs)
        stats[kw] = {
            "totalJobs": n,
            "jobsLast24h": len(last24),
            "avgBudgetFixed": round(statistics.mean(fixed), 2) if fixed else None,
            "avgRateHourly": round(statistics.mean(hourly), 2) if hourly else None,
            "medianProposals": int(statistics.median(props)) if props else None,
            "pctVerified": round(100 * verified / n, 1) if n else 0,
            "avgClientSpend": round(statistics.mean(spends), 2) if spends else None,
            "pctHighBudget": round(100 * high / n, 1) if n else 0,
            "opportunityScore": opportunity_score(jobs),
            "sampleConfidence": confidence_label(n),
        }
    return stats


def aggregate_group_stats(all_jobs: list[dict]) -> dict:
    by_group: dict[str, list[dict]] = {}
    for j in all_jobs:
        g = j.get("keywordGroup") or "UNKNOWN"
        by_group.setdefault(g, []).append(j)
    out = {}
    for g, jobs in by_group.items():
        out[g] = {
            "totalJobs": len(jobs),
            "jobsLast24h": sum(
                1
                for j in jobs
                if j.get("postedAt")
            ),
            "opportunityScore": opportunity_score(jobs),
            "sampleConfidence": confidence_label(len(jobs)),
        }
    return out


def aggregate_platform_stats(all_jobs: list[dict]) -> dict:
    out = {}
    for platform, needles in PLATFORM_KEYWORDS.items():
        matched = []
        for j in all_jobs:
            blob = " ".join(
                [
                    j.get("title") or "",
                    " ".join(j.get("matchedKeyword") or []),
                    " ".join(j.get("skills") or []),
                ]
            ).lower()
            if any(n in blob for n in needles):
                matched.append(j)
        fixed = [parse_money(j.get("budget")) for j in matched if j.get("type") == "fixed"]
        fixed = [x for x in fixed if x is not None]
        hourly = [
            parse_hourly_mid(j.get("hourlyRate"))
            for j in matched
            if j.get("type") == "hourly"
        ]
        hourly = [x for x in hourly if x is not None]
        props = [j.get("proposals") for j in matched if j.get("proposals") is not None]
        out[platform] = {
            "jobs": len(matched),
            "avgBudgetFixed": round(statistics.mean(fixed), 2) if fixed else None,
            "avgRateHourly": round(statistics.mean(hourly), 2) if hourly else None,
            "medianProposals": int(statistics.median(props)) if props else None,
            "opportunityScore": opportunity_score(matched),
            "sampleConfidence": confidence_label(len(matched)),
        }
    return out


def write_summary(
    run_number: int,
    attempted: int,
    completed: int,
    total_jobs: int,
    kw_stats: dict,
    group_stats: dict,
    platform_stats: dict,
) -> None:
    top_kw = sorted(
        kw_stats.items(),
        key=lambda x: (x[1]["opportunityScore"], x[1]["jobsLast24h"]),
        reverse=True,
    )[:10]
    top_groups = sorted(
        group_stats.items(),
        key=lambda x: (x[1]["opportunityScore"], x[1]["totalJobs"]),
        reverse=True,
    )
    lines = [
        "# Upwork Market Intelligence",
        "",
        f"Last updated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        f"Run: {run_number}",
        f"Total jobs tracked: {total_jobs}",
        f"Keywords attempted: {attempted}",
        f"Keywords completed: {completed}",
        "",
        "## Top Opportunities",
        "",
    ]
    for kw, s in top_kw:
        lines.append(
            f"- **{kw}** — score {s['opportunityScore']} ({s['sampleConfidence']}): "
            f"24h {s['jobsLast24h']}, total {s['totalJobs']}, "
            f"fixed avg {s['avgBudgetFixed']}, hourly avg {s['avgRateHourly']}, "
            f"median proposals {s['medianProposals']}"
        )
    lines.extend(["", "## Strongest Groups", ""])
    for i, (g, s) in enumerate(top_groups[:5], 1):
        lines.append(f"{i}. {g} — score {s['opportunityScore']} ({s['totalJobs']} jobs)")
    lines.extend(["", "## Platform Ranking", ""])
    plat_sorted = sorted(
        platform_stats.items(),
        key=lambda x: x[1]["opportunityScore"],
        reverse=True,
    )
    for i, (p, s) in enumerate(plat_sorted, 1):
        lines.append(f"{i}. {p} — score {s['opportunityScore']} ({s['jobs']} jobs)")
    primary = top_kw[0][0] if top_kw else "web development"
    secondary = top_kw[1][0] if len(top_kw) > 1 else "wordpress developer"
    best_plat = plat_sorted[0][0] if plat_sorted else "WordPress"
    lines.extend(
        [
            "",
            "## Positioning Recommendation",
            "",
            f"Primary keyword: {primary}",
            f"Secondary keyword: {secondary}",
            f"Best platform/service: {best_plat}",
            "Overview keywords: web development, WordPress, Next.js, Webflow",
            "Skill tags: WordPress, React, Next.js, Webflow, Framer, Shopify, SEO",
            "",
            "## Current Verdicts",
            "",
            "WordPress: Steady volume; mix of redesign, builds, and fixes.",
            "Webflow: Moderate; often bundled with general web design searches.",
            "Framer: Niche but visible in design-heavy queries.",
            "GoHighLevel: Lower volume than CMS dev; CRM/automation posts stand out.",
            "AI/Vibe Coding: Growing in full-stack and product posts; Claude Code appears in eng listings.",
            "Ecommerce: Shopify and WooCommerce both active today.",
            "Maintenance: Retainer posts exist but are noisier in broad queries.",
            "",
            "## Important Changes",
            "",
            "Initial baseline run (first capture).",
            "",
        ]
    )
    SUMMARY_PATH.write_text("\n".join(lines))


def process_batches(
    window_hours: float,
    attempted_keywords: list[str],
    completed_keywords: list[str],
    failed_keywords: list[str],
    errors: list[str],
) -> dict:
    state = load_state()
    run_number = int(state.get("runNumber") or 0) + 1
    known = set(state.get("knownJobUrls") or [])
    jobs_index = load_jobs_index()
    known |= set(jobs_index.keys())

    cutoff = datetime.now(timezone.utc) - timedelta(hours=window_hours)
    new_jobs: list[dict] = []
    new_urls: list[str] = []

    entries: list[dict] = []
    for bf in sorted(ROOT.glob("search_batch_*.json")):
        entries.extend(json.loads(bf.read_text()))
    accum = ROOT / "search_accum.json"
    if accum.exists():
        entries.extend(json.loads(accum.read_text()))
    log_path = ROOT / "search_log.jsonl"
    if log_path.exists():
        with log_path.open() as lf:
            for line in lf:
                line = line.strip()
                if line:
                    entries.append(json.loads(line))
    for entry in entries:
            keyword = entry["keyword"]
            group = entry["group"]
            resp = entry.get("response") or {}
            if resp.get("status") == "error":
                continue
            for j in resp.get("jobs") or []:
                posted_raw = j.get("published_date") or j.get("created_date")
                if posted_raw:
                    try:
                        posted = datetime.fromisoformat(posted_raw.replace("Z", "+00:00"))
                        if posted < cutoff:
                            continue
                    except ValueError:
                        pass
                row = job_from_api(j, keyword, group)
                if not row:
                    continue
                url = row["url"]
                if url in known:
                    if url in jobs_index:
                        kws = jobs_index[url].setdefault("matchedKeyword", [])
                        if keyword not in kws:
                            kws.append(keyword)
                    continue
                known.add(url)
                jobs_index[url] = row
                new_jobs.append(row)
                new_urls.append(url)

    with JOBS_PATH.open("a") as f:
        for row in new_jobs:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    all_jobs = list(jobs_index.values())
    kw_stats = aggregate_keyword_stats(all_jobs)
    group_stats = aggregate_group_stats(all_jobs)
    platform_stats = aggregate_platform_stats(all_jobs)

    KEYWORD_STATS_PATH.write_text(json.dumps(kw_stats, indent=2))
    GROUP_STATS_PATH.write_text(json.dumps(group_stats, indent=2))
    PLATFORM_STATS_PATH.write_text(json.dumps(platform_stats, indent=2))

    top3 = sorted(
        kw_stats.items(),
        key=lambda x: x[1]["jobsLast24h"],
        reverse=True,
    )[:3]
    top3_names = [k for k, _ in top3]

    log = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "runNumber": run_number,
        "keywordsAttempted": len(attempted_keywords),
        "keywordsCompleted": len(completed_keywords),
        "newJobs": len(new_jobs),
        "totalJobs": len(all_jobs),
        "top3Keywords": top3_names,
        "errors": errors,
    }
    with RUN_LOG_PATH.open("a") as f:
        f.write(json.dumps(log) + "\n")

    state.update(
        {
            "lastRunAt": log["timestamp"],
            "runNumber": run_number,
            "totalJobs": len(all_jobs),
            "knownJobUrls": sorted(known),
            "firstRunComplete": True,
        }
    )
    STATE_PATH.write_text(json.dumps(state, indent=2))

    write_summary(
        run_number,
        len(attempted_keywords),
        len(completed_keywords),
        len(all_jobs),
        kw_stats,
        group_stats,
        platform_stats,
    )

    return {
        "runNumber": run_number,
        "newJobs": new_jobs,
        "kw_stats": kw_stats,
        "group_stats": group_stats,
        "platform_stats": platform_stats,
        "failed_keywords": failed_keywords,
        "log": log,
    }


if __name__ == "__main__":
    import sys

    window = float(sys.argv[1]) if len(sys.argv) > 1 else 2.0
    meta_path = ROOT / "run_meta.json"
    meta = json.loads(meta_path.read_text()) if meta_path.exists() else {}
    process_batches(
        window,
        meta.get("attempted", []),
        meta.get("completed", []),
        meta.get("failed", []),
        meta.get("errors", []),
    )
