#!/usr/bin/env python3
"""Process Upwork keyword search responses into jobs.jsonl and stats."""
from __future__ import annotations

import json
import re
import statistics
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
_KEYWORD_FILE = json.loads((ROOT / "keywords.json").read_text())
KEYWORDS = [{"keyword": k, "group": g} for k, g in _KEYWORD_FILE["keywords"].items()]
ORG_UID = _KEYWORD_FILE.get("org_uid")
SEARCH_FILE = ROOT / "search_responses.json"
STATE_FILE = ROOT / "state.json"
JOBS_FILE = ROOT / "jobs.jsonl"
RUN_LOG = ROOT / "run-log.jsonl"
KEYWORD_STATS = ROOT / "keyword-stats.json"
GROUP_STATS = ROOT / "group-stats.json"
PLATFORM_STATS = ROOT / "platform-stats.json"
SUMMARY_FILE = ROOT / "current-summary.md"
INSIGHTS_FILE = ROOT / "insights.md"

SKIP_TITLE_PATTERNS = re.compile(
    r"\b(crypto|bitcoin|trading|casino|gambling|poker|dating|adult|escort|porn|onlyfans|alcohol|brewery|distillery)\b",
    re.I,
)

PLATFORMS = {
    "WordPress": re.compile(r"wordpress|woocommerce|elementor|bricks", re.I),
    "Webflow": re.compile(r"webflow", re.I),
    "Framer": re.compile(r"framer", re.I),
    "GoHighLevel": re.compile(r"gohighlevel|go high level|\bghl\b|highlevel", re.I),
    "Shopify": re.compile(r"shopify", re.I),
    "WooCommerce": re.compile(r"woocommerce", re.I),
    "Shopware": re.compile(r"shopware", re.I),
    "Lovable": re.compile(r"lovable", re.I),
    "Bolt": re.compile(r"bolt\.new|\bbolt developer\b", re.I),
    "v0": re.compile(r"\bv0\b|v0 vercel", re.I),
    "Next.js": re.compile(r"next\.?js", re.I),
}


def parse_money(s: str | None) -> float | None:
    if not s:
        return None
    s = s.replace(",", "").strip()
    if "–" in s or "-" in s:
        parts = re.split(r"[–-]", s)
        nums = []
        for p in parts:
            p = re.sub(r"[^\d.]", "", p)
            if p:
                nums.append(float(p))
        return statistics.mean(nums) if nums else None
    m = re.search(r"[\d.]+", s)
    return float(m.group()) if m else None


def parse_proposals_tier(tier: str | None) -> int | None:
    if not tier:
        return None
    t = tier.lower()
    if "fewer than 5" in t:
        return 3
    if "5 to 10" in t:
        return 7
    if "10 to 15" in t:
        return 12
    if "15 to 20" in t:
        return 17
    if "20 to 50" in t:
        return 30
    if "50+" in t:
        return 50
    return None


def parse_client_spend(s: str | None) -> float | None:
    if not s:
        return None
    s = s.replace(",", "").replace("$", "").strip()
    m = re.search(r"[\d.]+", s)
    return float(m.group()) if m else None


def norm_url(url: str) -> str:
    return url.split("?")[0].rstrip("/") if url else ""


def load_state() -> dict:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {"runNumber": 0, "totalJobs": 0, "knownJobUrls": [], "lastRunAt": None, "lastInsightRefresh": None}


def load_jobs_index() -> dict[str, dict]:
    jobs = {}
    if JOBS_FILE.exists():
        for line in JOBS_FILE.read_text().splitlines():
            if line.strip():
                j = json.loads(line)
                jobs[norm_url(j["url"])] = j
    return jobs


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
    now = datetime.now(timezone.utc)
    for j in jobs:
        recency = 0.5
        if j.get("postedAt"):
            try:
                posted = datetime.fromisoformat(j["postedAt"].replace("Z", "+00:00"))
                hours = (now - posted).total_seconds() / 3600
                recency = max(0.2, 1.0 - hours / 48)
            except ValueError:
                pass
        budget_boost = 0.0
        if j.get("type") == "fixed" and j.get("budgetFixed") and j["budgetFixed"] >= 1000:
            budget_boost = 1.0
        elif j.get("type") == "hourly" and j.get("rateHourlyMid") and j["rateHourlyMid"] >= 40:
            budget_boost = 0.8
        elif j.get("budgetFixed") and j["budgetFixed"] >= 1000:
            budget_boost = 0.6
        props = j.get("proposals") or 20
        comp = max(0.1, 1.0 - min(props, 50) / 50)
        verified = 0.15 if j.get("paymentVerified") else 0
        score += recency * (1 + budget_boost + verified) * (0.5 + comp)
    raw = score / len(jobs) * 25
    return max(1, min(100, int(raw)))


def job_from_api(raw: dict, keyword: str, group: str) -> dict | None:
    url = raw.get("url")
    if not url:
        return None
    title = raw.get("title") or ""
    if SKIP_TITLE_PATTERNS.search(title):
        return None
    client = raw.get("client") or {}
    budget = raw.get("budget")
    jtype = raw.get("job_type")
    fixed = None
    rate_mid = None
    budget_display = budget
    if jtype == "fixed":
        fixed = parse_money(budget)
    elif jtype == "hourly":
        rate_mid = parse_money(budget)
    posted = raw.get("published_date") or raw.get("created_date")
    return {
        "url": norm_url(url),
        "title": title,
        "matchedKeyword": [keyword],
        "keywordGroup": group,
        "postedAt": posted,
        "type": jtype,
        "budget": budget_display,
        "budgetFixed": fixed,
        "rateHourlyMid": rate_mid,
        "duration": raw.get("duration"),
        "proposals": raw.get("proposal_count") or parse_proposals_tier(raw.get("proposals_tier")),
        "clientCountry": client.get("country"),
        "paymentVerified": client.get("verification_status") == "VERIFIED",
        "clientSpend": client.get("total_spent"),
        "clientSpendNum": parse_client_spend(client.get("total_spent")),
        "clientHireRate": None,
        "clientRating": client.get("rating"),
        "experienceLevel": raw.get("experience_level"),
        "skills": raw.get("skills") or [],
    }


def in_window(posted: str | None, hours: float) -> bool:
    if not posted:
        return False
    try:
        dt = datetime.fromisoformat(posted.replace("Z", "+00:00"))
        anchor = datetime.now(timezone.utc)
        age = (anchor - dt).total_seconds()
        return 0 <= age <= hours * 3600
    except ValueError:
        return False


def detect_platforms(job: dict) -> list[str]:
    text = " ".join(
        [job.get("title") or "", " ".join(job.get("skills") or []), " ".join(job.get("matchedKeyword") or [])]
    )
    found = []
    for name, pat in PLATFORMS.items():
        if pat.search(text):
            found.append(name)
    return found


def main() -> None:
    if not SEARCH_FILE.exists():
        print("Missing search_responses.json", flush=True)
        return

    paired = json.loads(SEARCH_FILE.read_text())
    state = load_state()
    run_number = state.get("runNumber", 0) + 1
    first_run = state.get("runNumber", 0) == 0
    jobs_index = load_jobs_index()
    window_hours = float(__import__("os").environ.get("WINDOW_HOURS", "") or (2.0 if first_run else 1.0))
    if first_run and not jobs_index and "WINDOW_HOURS" not in __import__("os").environ:
        window_hours = 6.0

    known = set(state.get("knownJobUrls") or [])
    if not known and jobs_index:
        known = set(jobs_index.keys())
    new_this_run: list[dict] = []
    errors: list[str] = []
    keywords_attempted = len(KEYWORDS)
    keywords_completed = 0

    for entry in paired:
        kw = entry["keyword"]
        group = entry["group"]
        resp = entry.get("response") or {}
        if resp.get("status") == "error" or resp.get("error_code"):
            errors.append(kw)
            continue
        keywords_completed += 1
        for raw in resp.get("jobs") or []:
            j = job_from_api(raw, kw, group)
            if not j or not in_window(j.get("postedAt"), window_hours):
                continue
            u = j["url"]
            if u in jobs_index:
                existing = jobs_index[u]
                if kw not in existing["matchedKeyword"]:
                    existing["matchedKeyword"].append(kw)
            else:
                jobs_index[u] = j
                if u not in known:
                    new_this_run.append(j)
                    known.add(u)

    with JOBS_FILE.open("a") as f:
        for j in new_this_run:
            f.write(json.dumps(j) + "\n")

    all_jobs = list(jobs_index.values())
    now_iso = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    # Keyword stats from all tracked jobs
    kw_stats: dict[str, dict] = {}
    for spec in KEYWORDS:
        kw = spec["keyword"]
        matched = [j for j in all_jobs if kw in j.get("matchedKeyword", [])]
        jobs24 = [j for j in matched if in_window(j.get("postedAt"), 24)]
        fixed_vals = [j["budgetFixed"] for j in matched if j.get("budgetFixed")]
        rate_vals = [j["rateHourlyMid"] for j in matched if j.get("rateHourlyMid")]
        props = [j["proposals"] for j in matched if j.get("proposals") is not None]
        verified = sum(1 for j in matched if j.get("paymentVerified"))
        spend_vals = [j["clientSpendNum"] for j in matched if j.get("clientSpendNum")]
        high_budget = sum(
            1
            for j in matched
            if (j.get("budgetFixed") or 0) >= 1000 or (j.get("rateHourlyMid") or 0) >= 40
        )
        total = len(matched)
        pct_high = (high_budget / total * 100) if total else 0
        kw_stats[kw] = {
            "keyword": kw,
            "group": spec["group"],
            "totalJobs": total,
            "jobsLast24h": len(jobs24),
            "avgBudgetFixed": round(statistics.mean(fixed_vals), 2) if fixed_vals else None,
            "avgRateHourly": round(statistics.mean(rate_vals), 2) if rate_vals else None,
            "medianProposals": int(statistics.median(props)) if props else None,
            "pctVerified": round(verified / total * 100, 1) if total else 0,
            "avgClientSpend": round(statistics.mean(spend_vals), 2) if spend_vals else None,
            "pctHighBudget": round(pct_high, 1),
            "opportunityScore": opportunity_score(matched),
            "sampleConfidence": confidence_label(total),
        }

    KEYWORD_STATS.write_text(json.dumps(kw_stats, indent=2))

    # Group stats
    groups: dict[str, list] = {}
    for s in kw_stats.values():
        groups.setdefault(s["group"], []).append(s)
    group_stats = {}
    for g, items in groups.items():
        total = sum(x["totalJobs"] for x in items)
        j24 = sum(x["jobsLast24h"] for x in items)
        scores = [x["opportunityScore"] for x in items if x["totalJobs"]]
        group_stats[g] = {
            "group": g,
            "totalJobs": total,
            "jobsLast24h": j24,
            "avgOpportunityScore": round(statistics.mean(scores), 1) if scores else 0,
            "keywordCount": len(items),
        }
    GROUP_STATS.write_text(json.dumps(group_stats, indent=2))

    # Platform stats
    plat_stats = {}
    for pname in PLATFORMS:
        matched = []
        for j in all_jobs:
            if pname in detect_platforms(j):
                matched.append(j)
        fixed_vals = [j["budgetFixed"] for j in matched if j.get("budgetFixed")]
        rate_vals = [j["rateHourlyMid"] for j in matched if j.get("rateHourlyMid")]
        props = [j["proposals"] for j in matched if j.get("proposals") is not None]
        plat_stats[pname] = {
            "platform": pname,
            "jobs": len(matched),
            "avgBudgetFixed": round(statistics.mean(fixed_vals), 2) if fixed_vals else None,
            "avgRateHourly": round(statistics.mean(rate_vals), 2) if rate_vals else None,
            "medianProposals": int(statistics.median(props)) if props else None,
            "opportunityScore": opportunity_score(matched),
            "sampleConfidence": confidence_label(len(matched)),
        }
    PLATFORM_STATS.write_text(json.dumps(plat_stats, indent=2))

    top3 = sorted(kw_stats.values(), key=lambda x: (x["jobsLast24h"], x["opportunityScore"]), reverse=True)[:3]
    top3_names = [t["keyword"] for t in top3]

    run_log = {
        "timestamp": now_iso,
        "runNumber": run_number,
        "keywordsAttempted": keywords_attempted,
        "keywordsCompleted": keywords_completed,
        "newJobs": len(new_this_run),
        "totalJobs": len(all_jobs),
        "top3Keywords": top3_names,
        "errors": errors,
    }
    with RUN_LOG.open("a") as f:
        f.write(json.dumps(run_log) + "\n")

    state.update(
        {
            "lastRunAt": now_iso,
            "runNumber": run_number,
            "totalJobs": len(all_jobs),
            "knownJobUrls": sorted(known),
        }
    )
    STATE_FILE.write_text(json.dumps(state, indent=2))

    top10 = sorted(kw_stats.values(), key=lambda x: (x["opportunityScore"], x["jobsLast24h"]), reverse=True)[:10]
    ranked_groups = sorted(group_stats.values(), key=lambda x: x["avgOpportunityScore"], reverse=True)

    # Positioning heuristics
    primary = top10[0]["keyword"] if top10 else "wordpress developer"
    secondary = top10[1]["keyword"] if len(top10) > 1 else "shopify developer"
    best_plat = max(plat_stats.values(), key=lambda x: (x["jobs"], x["opportunityScore"]), default={"platform": "WordPress"})
    overview_kw = ", ".join([t["keyword"] for t in top10[:5]])
    skill_tags = "WordPress, Shopify, Next.js, Webflow, SEO, Supabase, AI integration"

    summary_lines = [
        "# Upwork Market Intelligence",
        "",
        f"Last updated: {now_iso}",
        f"Run: {run_number}",
        f"Total jobs tracked: {len(all_jobs)}",
        f"Keywords attempted: {keywords_attempted}",
        f"Keywords completed: {keywords_completed}",
        "",
        "## Top Opportunities",
        "",
    ]
    for t in top10:
        summary_lines.append(
            f"- **{t['keyword']}** — score {t['opportunityScore']}, jobs24h {t['jobsLast24h']}, "
            f"total {t['totalJobs']}, avg fixed ${t['avgBudgetFixed'] or 'n/a'}, "
            f"avg hourly ${t['avgRateHourly'] or 'n/a'}, median proposals {t['medianProposals']}, "
            f"confidence {t['sampleConfidence']}"
        )
    summary_lines.extend(["", "## Strongest Groups", ""])
    for g in ranked_groups[:5]:
        summary_lines.append(
            f"- {g['group']}: jobs24h {g['jobsLast24h']}, total {g['totalJobs']}, avg score {g['avgOpportunityScore']}"
        )
    summary_lines.extend(["", "## Platform Ranking", ""])
    for p in sorted(plat_stats.values(), key=lambda x: x["opportunityScore"], reverse=True):
        summary_lines.append(
            f"- {p['platform']}: {p['jobs']} jobs, score {p['opportunityScore']}, confidence {p['sampleConfidence']}"
        )
    summary_lines.extend(
        [
            "",
            "## Positioning Recommendation",
            "",
            f"Primary keyword: {primary}",
            f"Secondary keyword: {secondary}",
            f"Best platform/service: {best_plat['platform']}",
            f"Overview keywords: {overview_kw}",
            f"Skill tags: {skill_tags}",
            "",
            "## Current Verdicts",
            "",
            f"WordPress: Strong volume; mix of fixes and builds.",
            f"Webflow: Steady premium hourly demand.",
            f"Framer: Lower volume in window.",
            f"GoHighLevel: Funnel/page builder demand present.",
            f"AI/Vibe Coding: Production takeover and Supabase/AI stack jobs.",
            f"Ecommerce: Shopify and WooCommerce both active.",
            f"Maintenance: Retainer-style WordPress support posts.",
            "",
            "## Important Changes",
            "",
            "First baseline run." if run_number == 1 else "See run log for deltas.",
        ]
    )
    SUMMARY_FILE.write_text("\n".join(summary_lines) + "\n")

    if run_number == 1 and not INSIGHTS_FILE.exists():
        INSIGHTS_FILE.write_text(
            "# Durable insights\n\n"
            "- WordPress dominates hourly volume in the 2h bootstrap window.\n"
            "- GoHighLevel appears via HubSpot migration and page-builder roles.\n"
            "- Next.js/Supabase production takeover jobs skew expert and higher rate.\n"
        )

    # stdout for agent
    print(json.dumps({"run_log": run_log, "new_jobs": new_this_run, "top10": top10, "group_stats": ranked_groups[:5], "platform_stats": plat_stats}))


if __name__ == "__main__":
    main()
