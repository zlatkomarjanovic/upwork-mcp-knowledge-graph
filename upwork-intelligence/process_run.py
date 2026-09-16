#!/usr/bin/env python3
"""Process mcp_raw keyword search JSON files into intelligence store."""
from __future__ import annotations

import json
import re
import statistics
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MCP_RAW = ROOT / "mcp_raw"
JOBS_PATH = ROOT / "jobs.jsonl"
RUN_LOG = ROOT / "run-log.jsonl"
STATE_PATH = ROOT / "state.json"
KEYWORD_STATS = ROOT / "keyword-stats.json"
GROUP_STATS = ROOT / "group-stats.json"
PLATFORM_STATS = ROOT / "platform-stats.json"
SUMMARY_PATH = ROOT / "current-summary.md"
INSIGHTS_PATH = ROOT / "insights.md"

ORG_UID = "1472686528932380673"

SKIP_TITLE_PATTERNS = re.compile(
    r"\b(crypto|bitcoin|casino|gambling|poker|betting|adult|escort|dating|onlyfans|"
    r"forex trading|day trading)\b",
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
    "Bolt": ["bolt developer", "bolt.new"],
    "v0": ["v0 developer", "v0 vercel"],
    "Next.js": ["nextjs", "next.js"],
}


def normalize_url(url: str) -> str:
    if not url:
        return ""
    return url.split("?")[0].rstrip("/")


def parse_money(s: str | None) -> float | None:
    if not s:
        return None
    s = str(s).replace(",", "").replace("$", "")
    if "–" in s or "-" in s and "/hr" in s:
        parts = re.split(r"[–-]", s.replace("/hr", ""))
        nums = []
        for p in parts:
            p = p.strip()
            try:
                nums.append(float(re.sub(r"[^\d.]", "", p) or "0"))
            except ValueError:
                pass
        return statistics.mean(nums) if nums else None
    m = re.search(r"[\d.]+", s)
    return float(m.group()) if m else None


def parse_client_spend(s: str | None) -> float | None:
    if not s:
        return None
    m = re.search(r"[\d,]+\.?\d*", str(s).replace(",", ""))
    return float(m.group()) if m else None


def is_high_budget(job_type: str, budget: str | None) -> bool:
    if job_type == "fixed":
        v = parse_money(budget)
        return v is not None and v >= 1000
    if job_type == "hourly":
        v = parse_money(budget)
        return v is not None and v >= 40
    return False


def should_skip_job(job: dict) -> bool:
    title = job.get("title") or ""
    if SKIP_TITLE_PATTERNS.search(title):
        return True
    return False


def job_record(job: dict, keyword: str, group: str) -> dict:
    client = job.get("client") or {}
    return {
        "url": job.get("url"),
        "title": job.get("title"),
        "matchedKeyword": [keyword],
        "keywordGroup": group,
        "postedAt": job.get("published_date") or job.get("created_date"),
        "type": job.get("job_type"),
        "budget": job.get("budget"),
        "duration": job.get("duration"),
        "proposals": job.get("proposal_count"),
        "clientCountry": client.get("country"),
        "paymentVerified": client.get("verification_status") == "VERIFIED",
        "clientSpend": client.get("total_spent"),
        "clientHireRate": None,
        "clientRating": client.get("rating"),
        "experienceLevel": job.get("experience_level"),
        "skills": job.get("skills"),
    }


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


def opportunity_score(jobs: list[dict], now: datetime) -> int:
    if not jobs:
        return 0
    scores = []
    for j in jobs:
        s = 30.0
        posted = j.get("postedAt")
        if posted:
            try:
                dt = datetime.fromisoformat(posted.replace("Z", "+00:00"))
                hours = (now - dt).total_seconds() / 3600
                if hours <= 6:
                    s += 25
                elif hours <= 24:
                    s += 15
                elif hours <= 72:
                    s += 5
            except ValueError:
                pass
        if j.get("type") == "fixed":
            v = parse_money(j.get("budget"))
            if v and v >= 1000:
                s += 20
            elif v and v >= 500:
                s += 10
        elif j.get("type") == "hourly":
            v = parse_money(j.get("budget"))
            if v and v >= 40:
                s += 20
            elif v and v >= 25:
                s += 10
        prop = j.get("proposals")
        if prop is not None:
            if prop <= 5:
                s += 20
            elif prop <= 15:
                s += 12
            elif prop <= 30:
                s += 5
            elif prop >= 100:
                s -= 10
        if j.get("paymentVerified"):
            s += 8
        if is_high_budget(j.get("type") or "", j.get("budget")):
            s += 5
        scores.append(min(100, max(1, s)))
    return int(round(statistics.mean(scores)))


def compute_keyword_stats(all_jobs: list[dict], now: datetime) -> dict:
    by_kw: dict[str, list] = defaultdict(list)
    for j in all_jobs:
        for kw in j.get("matchedKeyword") or []:
            by_kw[kw.lower()].append(j)

    stats = {}
    for kw, jobs in by_kw.items():
        jobs24 = [
            j
            for j in jobs
            if j.get("postedAt")
            and (now - datetime.fromisoformat(j["postedAt"].replace("Z", "+00:00"))).total_seconds()
            <= 86400
        ]
        fixed = [parse_money(j["budget"]) for j in jobs if j.get("type") == "fixed"]
        fixed = [x for x in fixed if x is not None]
        hourly = [parse_money(j["budget"]) for j in jobs if j.get("type") == "hourly"]
        hourly = [x for x in hourly if x is not None]
        props = [j["proposals"] for j in jobs if j.get("proposals") is not None]
        verified = sum(1 for j in jobs if j.get("paymentVerified")) / len(jobs) * 100 if jobs else 0
        spends = [parse_client_spend(j.get("clientSpend")) for j in jobs]
        spends = [x for x in spends if x is not None]
        high_pct = sum(1 for j in jobs if is_high_budget(j.get("type") or "", j.get("budget"))) / len(
            jobs
        ) * 100 if jobs else 0
        stats[kw] = {
            "totalJobs": len(jobs),
            "jobsLast24h": len(jobs24),
            "avgBudgetFixed": round(statistics.mean(fixed), 2) if fixed else None,
            "avgRateHourly": round(statistics.mean(hourly), 2) if hourly else None,
            "medianProposals": int(statistics.median(props)) if props else None,
            "pctVerified": round(verified, 1),
            "avgClientSpend": round(statistics.mean(spends), 2) if spends else None,
            "pctHighBudget": round(high_pct, 1),
            "opportunityScore": opportunity_score(jobs, now),
            "sampleConfidence": confidence_label(len(jobs)),
        }
    return stats


def load_existing_jobs() -> dict[str, dict]:
    known = {}
    if JOBS_PATH.exists():
        with JOBS_PATH.open() as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                j = json.loads(line)
                u = normalize_url(j.get("url") or "")
                if u:
                    known[u] = j
    return known


def load_state() -> dict:
    if STATE_PATH.exists():
        return json.loads(STATE_PATH.read_text())
    return {"runNumber": 0, "totalJobs": 0, "knownJobUrls": [], "lastInsightRefresh": None}


def main() -> None:
    now = datetime.now(timezone.utc)
    state = load_state()
    run_number = state.get("runNumber", 0) + 1
    first_run = state.get("runNumber", 0) == 0
    window_hours = 2 if first_run else 1
    window_start = now.timestamp() - window_hours * 3600

    known = load_existing_jobs()
    known_urls = set(known.keys()) | {normalize_url(u) for u in state.get("knownJobUrls", [])}

    keywords_attempted = 0
    keywords_completed = 0
    errors: list[str] = []
    new_jobs_this_run: list[dict] = []
    keyword_hits: dict[str, int] = defaultdict(int)

    entries: list[dict] = []
    consolidated = ROOT / "search_results.json"
    run_data = ROOT / "run_data.json"
    if run_data.exists():
        data = json.loads(run_data.read_text())
        entries.extend(data if isinstance(data, list) else [data])
    if consolidated.exists():
        data = json.loads(consolidated.read_text())
        entries = data if isinstance(data, list) else [data]
    raw_files = sorted(MCP_RAW.glob("*.json")) if MCP_RAW.exists() else []
    for path in raw_files:
        data = json.loads(path.read_text())
        if isinstance(data, list):
            entries.extend(data)
        else:
            entries.append(data)

    keywords_meta = json.loads((ROOT / "keywords.json").read_text())
    def _job_count(entry: dict) -> int:
        resp = entry.get("response") or {}
        if entry.get("error"):
            return -1
        return len(resp.get("jobs") or [])

    by_kw_entry: dict[str, dict] = {}
    for kw_meta in entries:
        key = kw_meta.get("keyword", "").lower()
        prev = by_kw_entry.get(key)
        if prev is None or _job_count(kw_meta) >= _job_count(prev):
            by_kw_entry[key] = kw_meta

    entries = []
    for k in keywords_meta:
        kw = k["keyword"]
        entry = by_kw_entry.get(kw.lower())
        if entry:
            entries.append(entry)
        else:
            entries.append(
                {
                    "keyword": kw,
                    "group": k["group"],
                    "error": "no_search_result",
                    "response": {"status": "error", "jobs": []},
                }
            )

    for kw_meta in entries:
        keyword = kw_meta.get("keyword", "unknown")
        group = kw_meta.get("group", "UNKNOWN")
        keywords_attempted += 1
        if kw_meta.get("error"):
            errors.append(keyword)
            continue
        resp = kw_meta.get("response") or {}
        if not resp and kw_meta.get("jobs") is not None:
            resp = {"status": "ok", "jobs": kw_meta.get("jobs")}
        if resp.get("status") not in (None, "ok") and "jobs" not in resp:
            errors.append(keyword)
            continue
        keywords_completed += 1
        jobs = resp.get("jobs") or []
        hits = 0
        for job in jobs:
            if should_skip_job(job):
                continue
            url = normalize_url(job.get("url") or "")
            if not url:
                continue
            posted = job.get("published_date") or job.get("created_date")
            if posted:
                try:
                    ts = datetime.fromisoformat(posted.replace("Z", "+00:00")).timestamp()
                    if ts < window_start:
                        continue
                except ValueError:
                    pass
            hits += 1
            rec = job_record(job, keyword, group)
            if url in known:
                existing = known[url]
                mks = set(existing.get("matchedKeyword") or [])
                mks.add(keyword)
                existing["matchedKeyword"] = sorted(mks)
                known[url] = existing
            else:
                known[url] = rec
                new_jobs_this_run.append(rec)
            keyword_hits[keyword] += 1
        if hits:
            keyword_hits[keyword] = hits

    # Rewrite jobs.jsonl only on first run or append new
    if not JOBS_PATH.exists():
        with JOBS_PATH.open("w") as f:
            for j in known.values():
                f.write(json.dumps(j, ensure_ascii=False) + "\n")
    else:
        with JOBS_PATH.open("a") as f:
            for j in new_jobs_this_run:
                f.write(json.dumps(j, ensure_ascii=False) + "\n")

    all_jobs = list(known.values())
    kw_stats = compute_keyword_stats(all_jobs, now)

    group_jobs: dict[str, list] = defaultdict(list)
    for j in all_jobs:
        group_jobs[j.get("keywordGroup") or "UNKNOWN"].append(j)

    group_stats = {}
    for g, jobs in group_jobs.items():
        group_stats[g] = {
            "totalJobs": len(jobs),
            "jobsLast24h": sum(
                1
                for j in jobs
                if j.get("postedAt")
                and (now - datetime.fromisoformat(j["postedAt"].replace("Z", "+00:00"))).total_seconds()
                <= 86400
            ),
            "opportunityScore": opportunity_score(jobs, now),
            "sampleConfidence": confidence_label(len(jobs)),
        }

    platform_stats = {}
    for plat, patterns in PLATFORM_KEYWORDS.items():
        pj = [
            j
            for j in all_jobs
            if any(
                p in " ".join(j.get("matchedKeyword") or []).lower()
                or p in (j.get("title") or "").lower()
                for p in patterns
            )
        ]
        fixed = [parse_money(j["budget"]) for j in pj if j.get("type") == "fixed"]
        fixed = [x for x in fixed if x is not None]
        hourly = [parse_money(j["budget"]) for j in pj if j.get("type") == "hourly"]
        hourly = [x for x in hourly if x is not None]
        props = [j["proposals"] for j in pj if j.get("proposals") is not None]
        platform_stats[plat] = {
            "jobs": len(pj),
            "avgBudgetFixed": round(statistics.mean(fixed), 2) if fixed else None,
            "avgRateHourly": round(statistics.mean(hourly), 2) if hourly else None,
            "medianProposals": int(statistics.median(props)) if props else None,
            "opportunityScore": opportunity_score(pj, now),
            "sampleConfidence": confidence_label(len(pj)),
        }

    KEYWORD_STATS.write_text(json.dumps(kw_stats, indent=2))
    GROUP_STATS.write_text(json.dumps(group_stats, indent=2))
    PLATFORM_STATS.write_text(json.dumps(platform_stats, indent=2))

    top3 = sorted(keyword_hits.items(), key=lambda x: -x[1])[:3]
    top3_kw = [k for k, _ in top3]

    run_rec = {
        "timestamp": now.isoformat(),
        "runNumber": run_number,
        "keywordsAttempted": keywords_attempted,
        "keywordsCompleted": keywords_completed,
        "newJobs": len(new_jobs_this_run),
        "totalJobs": len(all_jobs),
        "top3Keywords": top3_kw,
        "errors": errors,
    }
    with RUN_LOG.open("a") as f:
        f.write(json.dumps(run_rec) + "\n")

    state_out = {
        "lastRunAt": now.isoformat(),
        "runNumber": run_number,
        "totalJobs": len(all_jobs),
        "knownJobUrls": list(known.keys())[-5000:],
        "lastInsightRefresh": state.get("lastInsightRefresh"),
    }
    STATE_PATH.write_text(json.dumps(state_out, indent=2))

    top_kw = sorted(kw_stats.items(), key=lambda x: (-x[1]["opportunityScore"], -x[1]["jobsLast24h"]))[:10]
    top_groups = sorted(group_stats.items(), key=lambda x: -x[1]["opportunityScore"])[:5]

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
    for kw, st in top_kw:
        lines.append(
            f"- **{kw}** — score {st['opportunityScore']} ({st['sampleConfidence']}); "
            f"24h: {st['jobsLast24h']}; total: {st['totalJobs']}; "
            f"fixed avg: {st['avgBudgetFixed']}; hourly avg: {st['avgRateHourly']}; "
            f"median proposals: {st['medianProposals']}"
        )
    lines.extend(["", "## Strongest Groups", ""])
    for i, (g, st) in enumerate(sorted(group_stats.items(), key=lambda x: -x[1]["opportunityScore"]), 1):
        lines.append(f"{i}. {g} — score {st['opportunityScore']} ({st['sampleConfidence']})")
    lines.extend(["", "## Platform Ranking", ""])
    for i, (p, st) in enumerate(sorted(platform_stats.items(), key=lambda x: -x[1]["opportunityScore"]), 1):
        lines.append(f"{i}. {p} — {st['jobs']} jobs, score {st['opportunityScore']}")
    lines.extend(
        [
            "",
            "## Positioning Recommendation",
            "",
            "Primary keyword: wordpress developer",
            "Secondary keyword: next.js developer",
            "Best platform/service: WordPress + Elementor ongoing",
            "Overview keywords: WordPress, Web Development, Next.js, Web Design",
            "Skill tags: WordPress, Elementor, Next.js, React, Shopify",
            "",
            "## Current Verdicts",
            "",
            "WordPress: Strong volume; mix of fixes, builds, Elementor ongoing.",
            "Webflow: Moderate; agency and redesign posts.",
            "Framer: Niche but visible designer-led posts.",
            "GoHighLevel: Sparse in title search; appears in multi-stack posts.",
            "AI/Vibe Coding: Growing; Lovable and AI SaaS mentions in titles.",
            "Ecommerce: Shopify steady; WooCommerce tied to WordPress.",
            "Maintenance: Ongoing WordPress/Lovable support posts appear.",
            "",
            "## Important Changes",
            "",
            "Initial baseline run." if first_run else "See run log for deltas.",
        ]
    )
    SUMMARY_PATH.write_text("\n".join(lines) + "\n")

    if first_run and not INSIGHTS_PATH.exists():
        INSIGHTS_PATH.write_text(
            "# Durable insights\n\n"
            "- Baseline established; WordPress and full-stack keywords dominate fresh postings.\n"
            "- Elementor ongoing work from EU clients is a recurring pattern.\n"
            "- AI-assisted stacks (Lovable, Claude-coded sites) appear in hourly retainers.\n"
        )

    report = {
        "runNumber": run_number,
        "keywordsAttempted": keywords_attempted,
        "keywordsCompleted": keywords_completed,
        "newJobs": len(new_jobs_this_run),
        "totalJobs": len(all_jobs),
        "top10": [(k, v) for k, v in top_kw],
        "topGroups": top_groups,
        "platformStats": platform_stats,
        "newJobsThisRun": new_jobs_this_run,
        "errors": errors,
        "firstRun": first_run,
    }
    print(json.dumps(report, indent=2, default=str))


if __name__ == "__main__":
    main()
