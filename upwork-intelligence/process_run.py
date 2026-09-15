#!/usr/bin/env python3
"""Process MCP raw searches into jobs, stats, and summaries."""
from __future__ import annotations

import json
import re
import statistics
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse, parse_qs

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "mcp_raw"
KEYWORDS = json.loads((ROOT / "keywords.json").read_text(encoding="utf-8"))
ALL_KEYWORDS = list(KEYWORDS.keys())

SKIP_PATTERNS = re.compile(
    r"\b(crypto\s*trading|bitcoin\s*trading|gambling|casino|betting|adult\s*content|"
    r"escort|porn|dating\s*app|alcohol\s*brand)\b",
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
    "Bolt": ["bolt.new", "bolt developer", "bolt"],
    "v0": ["v0 vercel", "v0 developer", "v0"],
    "Next.js": ["nextjs", "next.js"],
}


def norm_url(url: str | None) -> str | None:
    if not url:
        return None
    base = url.split("?")[0]
    return base.rstrip("/")


def parse_budget(budget: str | None, job_type: str | None) -> tuple[float | None, float | None]:
    if not budget:
        return None, None
    s = budget.replace(",", "").replace("$", "").strip()
    if "–" in s or "-" in s:
        parts = re.split(r"[–-]", s)
        nums = []
        for p in parts:
            p = p.replace("/hr", "").strip()
            try:
                nums.append(float(p))
            except ValueError:
                pass
        if not nums:
            return None, None
        if job_type == "hourly" or "/hr" in budget.lower():
            return None, sum(nums) / len(nums)
        return sum(nums) / len(nums), None
    s = s.replace("/hr", "").strip()
    try:
        v = float(s)
    except ValueError:
        return None, None
    if job_type == "hourly":
        return None, v
    return v, None


def parse_spend(spent: str | None) -> float | None:
    if not spent:
        return None
    s = spent.replace(",", "").replace("$", "").strip()
    try:
        return float(s)
    except ValueError:
        return None


def is_excluded(job: dict) -> bool:
    text = (job.get("title") or "") + " " + (job.get("description_snippet") or "")
    return bool(SKIP_PATTERNS.search(text))


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
    now = datetime.now(timezone.utc)
    recency = 0
    budget_pts = 0
    prop_pts = 0
    verify_pts = 0
    high_budget = 0
    for j in jobs:
        posted = j.get("postedAt")
        if posted:
            try:
                dt = datetime.fromisoformat(posted.replace("Z", "+00:00"))
                hours = (now - dt).total_seconds() / 3600
                if hours <= 24:
                    recency += 3
                elif hours <= 72:
                    recency += 1
            except ValueError:
                pass
        fixed, hourly = parse_budget(j.get("budget"), j.get("type"))
        if fixed and fixed >= 1000:
            high_budget += 2
            budget_pts += 2
        elif fixed and fixed >= 500:
            budget_pts += 1
        if hourly and hourly >= 40:
            high_budget += 2
            budget_pts += 2
        elif hourly and hourly >= 25:
            budget_pts += 1
        p = j.get("proposals")
        if p is not None:
            if p <= 5:
                prop_pts += 3
            elif p <= 15:
                prop_pts += 2
            elif p <= 30:
                prop_pts += 1
        if j.get("paymentVerified"):
            verify_pts += 1
    raw = recency + budget_pts + prop_pts + verify_pts + high_budget
    return max(1, min(100, int(raw * 100 / max(len(jobs) * 8, 1))))


def job_record(raw: dict, keyword: str, group: str) -> dict | None:
    url = norm_url(raw.get("url"))
    if not url:
        return None
    if is_excluded(raw):
        return None
    client = raw.get("client") or {}
    fixed, hourly = parse_budget(raw.get("budget"), raw.get("job_type"))
    return {
        "url": url,
        "title": raw.get("title"),
        "matchedKeyword": [keyword],
        "keywordGroup": group,
        "postedAt": raw.get("published_date") or raw.get("created_date"),
        "type": raw.get("job_type"),
        "budget": raw.get("budget"),
        "duration": raw.get("duration"),
        "proposals": raw.get("proposal_count"),
        "clientCountry": client.get("country"),
        "paymentVerified": client.get("verification_status") == "VERIFIED",
        "clientSpend": client.get("total_spent"),
        "clientHireRate": None,
        "clientRating": client.get("rating"),
        "experienceLevel": raw.get("experience_level"),
        "skills": raw.get("skills") or [],
        "_fixed": fixed,
        "_hourly": hourly,
    }


def load_state() -> dict:
    p = ROOT / "state.json"
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return {"runNumber": 0, "totalJobs": 0, "knownJobUrls": []}


def within_window(posted: str | None, hours: float) -> bool:
    if not posted:
        return False
    try:
        dt = datetime.fromisoformat(posted.replace("Z", "+00:00"))
    except ValueError:
        return False
    now = datetime.now(timezone.utc)
    return (now - dt).total_seconds() <= hours * 3600


def aggregate_jobs(all_jobs: list[dict]) -> tuple[dict, dict, dict]:
    kw_stats = {}
    for kw in ALL_KEYWORDS:
        kw_stats[kw] = {
            "totalJobs": 0,
            "jobsLast24h": 0,
            "avgBudgetFixed": None,
            "avgRateHourly": None,
            "medianProposals": None,
            "pctVerified": None,
            "avgClientSpend": None,
            "pctHighBudget": None,
            "opportunityScore": 0,
            "sampleConfidence": "Very Low",
        }
    group_stats = {}
    for g in set(KEYWORDS.values()):
        group_stats[g] = {"totalJobs": 0, "jobsLast24h": 0, "opportunityScore": 0, "sampleConfidence": "Very Low"}

    now = datetime.now(timezone.utc)
    for job in all_jobs:
        for kw in job.get("matchedKeyword") or []:
            if kw not in kw_stats:
                continue
            ks = kw_stats[kw]
            ks["totalJobs"] += 1
            posted = job.get("postedAt")
            if posted:
                try:
                    dt = datetime.fromisoformat(posted.replace("Z", "+00:00"))
                    if (now - dt).total_seconds() <= 86400:
                        ks["jobsLast24h"] += 1
                except ValueError:
                    pass
            g = KEYWORDS.get(kw)
            if g:
                group_stats[g]["totalJobs"] += 1
                if posted:
                    try:
                        dt = datetime.fromisoformat(posted.replace("Z", "+00:00"))
                        if (now - dt).total_seconds() <= 86400:
                            group_stats[g]["jobsLast24h"] += 1
                    except ValueError:
                        pass

    def enrich_stats(jobs_for_kw: list[dict], stats: dict):
        if not jobs_for_kw:
            return
        fixed = [j["_fixed"] for j in jobs_for_kw if j.get("_fixed")]
        hourly = [j["_hourly"] for j in jobs_for_kw if j.get("_hourly")]
        props = [j["proposals"] for j in jobs_for_kw if j.get("proposals") is not None]
        spends = [parse_spend(j.get("clientSpend")) for j in jobs_for_kw]
        spends = [s for s in spends if s is not None]
        verified = sum(1 for j in jobs_for_kw if j.get("paymentVerified"))
        high = 0
        for j in jobs_for_kw:
            if j.get("_fixed") and j["_fixed"] >= 1000:
                high += 1
            if j.get("_hourly") and j["_hourly"] >= 40:
                high += 1
        stats["avgBudgetFixed"] = round(statistics.mean(fixed), 2) if fixed else None
        stats["avgRateHourly"] = round(statistics.mean(hourly), 2) if hourly else None
        stats["medianProposals"] = int(statistics.median(props)) if props else None
        stats["pctVerified"] = round(100 * verified / len(jobs_for_kw), 1) if jobs_for_kw else None
        stats["avgClientSpend"] = round(statistics.mean(spends), 2) if spends else None
        stats["pctHighBudget"] = round(100 * high / len(jobs_for_kw), 1) if jobs_for_kw else None
        stats["opportunityScore"] = opportunity_score(jobs_for_kw)
        stats["sampleConfidence"] = confidence_label(len(jobs_for_kw))

    for kw, stats in kw_stats.items():
        jobs_for = [j for j in all_jobs if kw in (j.get("matchedKeyword") or [])]
        enrich_stats(jobs_for, stats)

    for g, stats in group_stats.items():
        jobs_for = [j for j in all_jobs if j.get("keywordGroup") == g]
        enrich_stats(jobs_for, stats)

    platform_stats = {}
    for plat, kws in PLATFORM_KEYWORDS.items():
        jobs_for = []
        for j in all_jobs:
            text = " ".join(j.get("matchedKeyword") or []).lower() + " " + (j.get("title") or "").lower()
            if any(k.lower() in text for k in kws):
                jobs_for.append(j)
        ps = {
            "totalJobs": len(jobs_for),
            "jobsLast24h": 0,
            "avgBudgetFixed": None,
            "avgRateHourly": None,
            "medianProposals": None,
            "opportunityScore": 0,
            "sampleConfidence": "Very Low",
        }
        now2 = datetime.now(timezone.utc)
        for j in jobs_for:
            posted = j.get("postedAt")
            if posted:
                try:
                    dt = datetime.fromisoformat(posted.replace("Z", "+00:00"))
                    if (now2 - dt).total_seconds() <= 86400:
                        ps["jobsLast24h"] += 1
                except ValueError:
                    pass
        enrich_stats(jobs_for, ps)
        platform_stats[plat] = ps

    return kw_stats, group_stats, platform_stats


def strip_internal(job: dict) -> dict:
    out = {k: v for k, v in job.items() if not k.startswith("_")}
    return out


def write_summary(run: int, kw_stats, group_stats, platform_stats, total, attempted, completed, new_count, errors):
    top_kw = sorted(kw_stats.items(), key=lambda x: (-x[1]["opportunityScore"], -x[1]["jobsLast24h"]))[:10]
    top_groups = sorted(group_stats.items(), key=lambda x: (-x[1]["opportunityScore"], -x[1]["jobsLast24h"]))[:5]
    lines = [
        "# Upwork Market Intelligence",
        "",
        f"Last updated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        f"Run: {run}",
        f"Total jobs tracked: {total}",
        f"Keywords attempted: {attempted}",
        f"Keywords completed: {completed}",
        "",
        "## Top Opportunities",
        "",
    ]
    for kw, s in top_kw:
        lines.append(
            f"- **{kw}**: score {s['opportunityScore']}, jobs24h {s['jobsLast24h']}, total {s['totalJobs']}, "
            f"avg fixed {s['avgBudgetFixed']}, avg hourly {s['avgRateHourly']}, median proposals {s['medianProposals']}, "
            f"confidence {s['sampleConfidence']}"
        )
    lines.extend(["", "## Strongest Groups", ""])
    for g, s in sorted(top_groups, key=lambda x: -x[1]["opportunityScore"]):
        lines.append(f"- **{g}**: score {s['opportunityScore']}, jobs24h {s['jobsLast24h']}, total {s['totalJobs']}")
    lines.extend(["", "## Platform Ranking", ""])
    for p, s in sorted(platform_stats.items(), key=lambda x: -x[1]["opportunityScore"]):
        lines.append(f"- **{p}**: jobs {s['totalJobs']}, score {s['opportunityScore']}, confidence {s['sampleConfidence']}")
    primary = top_kw[0][0] if top_kw else "wordpress developer"
    secondary = top_kw[1][0] if len(top_kw) > 1 else "webflow developer"
    lines.extend(
        [
            "",
            "## Positioning Recommendation",
            "",
            f"Primary keyword: {primary}",
            f"Secondary keyword: {secondary}",
            "Best platform/service: WordPress + Elementor maintenance and production fixes",
            "Overview keywords: WordPress, Web Development, Elementor, Website Maintenance",
            "Skill tags: WordPress, Elementor, WooCommerce, Page Speed Optimization, Technical SEO",
            "",
            "## Current Verdicts",
            "",
            "WordPress: Steady hourly and fixed volume; Elementor/Divi edits and emergency fixes dominate last 2h.",
            "Webflow: Lower post volume than WordPress; speed optimization niche shows higher budgets.",
            "Framer: Sparse in this window.",
            "GoHighLevel: Figma-to-GHL landing builds appear with verified spenders.",
            "AI/Vibe Coding: Lovable code review and Supabase/Next fixes; mixed with heavy full-stack AI roles.",
            "Ecommerce: Shopify automation and WooCommerce maintenance both active.",
            "Maintenance: Retainer and monthly WordPress support posts continue outside strict 2h window.",
            "",
            "## Important Changes",
            "",
            f"First run bootstrap: {new_count} new jobs captured; {len(errors)} keyword gaps." if run == 1 else "See chat for material deltas.",
            "",
        ]
    )
    (ROOT / "current-summary.md").write_text("\n".join(lines), encoding="utf-8")


def main():
    state = load_state()
    run = state.get("runNumber", 0) + 1
    known = set(state.get("knownJobUrls") or [])
    first_run = state.get("totalJobs", 0) == 0 and not (ROOT / "jobs.jsonl").exists()
    window_h = 2.0 if first_run else 1.0

    attempted = len(ALL_KEYWORDS)
    completed = 0
    errors = []
    new_jobs_run: list[dict] = []
    jobs_by_url: dict[str, dict] = {}

    jobs_path = ROOT / "jobs.jsonl"
    if jobs_path.exists():
        for line in jobs_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            j = json.loads(line)
            u = j.get("url")
            if u:
                jobs_by_url[u] = j

    if RAW.exists():
        for f in RAW.glob("*.json"):
            item = json.loads(f.read_text(encoding="utf-8"))
            kw = item.get("keyword")
            group = item.get("group") or KEYWORDS.get(kw, "UNKNOWN")
            resp = item.get("response") or item
            if resp.get("status") == "error" or resp.get("error"):
                errors.append(kw)
                continue
            if kw not in KEYWORDS:
                continue
            if not (resp.get("jobs") or []):
                errors.append(kw)
                continue
            completed += 1
            for raw in resp.get("jobs") or []:
                rec = job_record(raw, kw, group)
                if not rec:
                    continue
                if not within_window(rec.get("postedAt"), window_h):
                    continue
                url = rec["url"]
                if url in jobs_by_url:
                    existing = jobs_by_url[url]
                    mks = set(existing.get("matchedKeyword") or [])
                    mks.update(rec["matchedKeyword"])
                    existing["matchedKeyword"] = sorted(mks)
                else:
                    jobs_by_url[url] = rec
                    if url not in known:
                        new_jobs_run.append(rec)
                        known.add(url)

    for kw in ALL_KEYWORDS:
        safe = "".join(c if c.isalnum() else "_" for c in kw)[:80]
        if not (RAW / f"{safe}.json").exists():
            errors.append(kw)

    with jobs_path.open("a", encoding="utf-8") as fp:
        for j in new_jobs_run:
            fp.write(json.dumps(strip_internal(j), ensure_ascii=False) + "\n")

    all_jobs = list(jobs_by_url.values())
    kw_stats, group_stats, platform_stats = aggregate_jobs(all_jobs)

    (ROOT / "keyword-stats.json").write_text(json.dumps(kw_stats, indent=2), encoding="utf-8")
    (ROOT / "group-stats.json").write_text(json.dumps(group_stats, indent=2), encoding="utf-8")
    (ROOT / "platform-stats.json").write_text(json.dumps(platform_stats, indent=2), encoding="utf-8")

    log = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "runNumber": run,
        "keywordsAttempted": attempted,
        "keywordsCompleted": completed,
        "newJobs": len(new_jobs_run),
        "totalJobs": len(all_jobs),
        "top3Keywords": [k for k, _ in sorted(kw_stats.items(), key=lambda x: -x[1]["opportunityScore"])[:3]],
        "errors": sorted(set(errors)),
    }
    with (ROOT / "run-log.jsonl").open("a", encoding="utf-8") as fp:
        fp.write(json.dumps(log) + "\n")

    state_out = {
        "lastRunAt": log["timestamp"],
        "runNumber": run,
        "totalJobs": len(all_jobs),
        "knownJobUrls": sorted(known),
        "lastInsightRefresh": state.get("lastInsightRefresh"),
    }
    (ROOT / "state.json").write_text(json.dumps(state_out, indent=2), encoding="utf-8")
    write_summary(run, kw_stats, group_stats, platform_stats, len(all_jobs), attempted, completed, len(new_jobs_run), errors)

    out = {
        "run": run,
        "newJobs": len(new_jobs_run),
        "totalJobs": len(all_jobs),
        "completed": completed,
        "errors": sorted(set(errors)),
        "new_jobs": [strip_internal(j) for j in new_jobs_run],
        "kw_stats": kw_stats,
        "group_stats": group_stats,
        "platform_stats": platform_stats,
    }
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
