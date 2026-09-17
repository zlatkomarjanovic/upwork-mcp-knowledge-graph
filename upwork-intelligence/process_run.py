#!/usr/bin/env python3
"""Process keyword search batch results into jobs.jsonl and stats."""
import json
import re
import statistics
from datetime import datetime, timezone, timedelta
from pathlib import Path

BASE = Path(__file__).resolve().parent
STATE_PATH = BASE / "state.json"
JOBS_PATH = BASE / "jobs.jsonl"
RUN_LOG = BASE / "run-log.jsonl"
KW_STATS = BASE / "keyword-stats.json"
GROUP_STATS = BASE / "group-stats.json"
PLATFORM_STATS = BASE / "platform-stats.json"
SUMMARY = BASE / "current-summary.md"
INSIGHTS = BASE / "insights.md"
BATCH = BASE / "_batch_results.jsonl"

SKIP_TITLE = re.compile(
    r"\b(crypto|bitcoin|betting|casino|gambl|poker|onlyfans|adult|escort|dating|hookup)\b",
    re.I,
)

PLATFORM_MAP = {
    "wordpress": "WordPress",
    "woocommerce": "WooCommerce",
    "webflow": "Webflow",
    "framer": "Framer",
    "gohighlevel": "GoHighLevel",
    "go high level": "GoHighLevel",
    "ghl": "GoHighLevel",
    "highlevel": "GoHighLevel",
    "shopify": "Shopify",
    "shopware": "Shopware",
    "lovable": "Lovable",
    "bolt": "Bolt",
    "bolt.new": "Bolt",
    "v0": "v0",
    "next.js": "Next.js",
    "nextjs": "Next.js",
}

PROPOSAL_MID = {
    "Fewer than 5": 2,
    "5 to 10": 7,
    "10 to 15": 12,
    "15 to 20": 17,
    "20 to 50": 35,
    "50+": 55,
}


def norm_url(url: str) -> str:
    return url.split("?")[0] if url else ""


def parse_money(s):
    if not s:
        return None
    s = str(s).replace(",", "").replace("$", "").strip()
    if "–" in s or "-" in s:
        parts = re.split(r"[–-]", s)
        nums = []
        for p in parts:
            p = re.sub(r"[^\d.]", "", p.strip())
            if p:
                try:
                    nums.append(float(p))
                except ValueError:
                    pass
        return statistics.mean(nums) if nums else None
    m = re.search(r"[\d.]+", s)
    return float(m.group()) if m else None


def proposals_mid(tier):
    if not tier:
        return None
    return PROPOSAL_MID.get(tier)


def client_spend_num(spent):
    if not spent:
        return None
    m = re.search(r"[\d,]+\.?\d*", str(spent).replace(",", ""))
    return float(m.group()) if m else None


def detect_platform(job, keyword):
    text = " ".join(
        [
            keyword or "",
            job.get("title") or "",
            " ".join(job.get("skills") or []),
        ]
    ).lower()
    for needle, name in PLATFORM_MAP.items():
        if needle in text:
            return name
    return None


def job_record(job, keyword, group, window_start):
    pub = job.get("published_date") or job.get("created_date")
    if pub:
        try:
            dt = datetime.fromisoformat(pub.replace("Z", "+00:00"))
            if dt < window_start:
                return None
        except ValueError:
            pass
    url = job.get("url")
    if not url:
        return None
    title = job.get("title") or ""
    if SKIP_TITLE.search(title):
        return None
    client = job.get("client") or {}
    budget = job.get("budget")
    jtype = job.get("job_type")
    return {
        "url": norm_url(url),
        "title": title,
        "matchedKeyword": [keyword],
        "keywordGroup": group,
        "postedAt": pub,
        "type": jtype,
        "budget": budget if jtype == "fixed" else None,
        "hourlyRate": budget if jtype == "hourly" else None,
        "duration": job.get("duration"),
        "proposals": job.get("proposals_tier"),
        "clientCountry": client.get("country"),
        "paymentVerified": (client.get("verification_status") == "VERIFIED"),
        "clientSpend": client.get("total_spent"),
        "clientHireRate": None,
        "clientRating": client.get("rating"),
        "experienceLevel": job.get("experience_level"),
        "skills": job.get("skills") or [],
        "_platform": detect_platform(job, keyword),
    }


def confidence_label(n):
    if n >= 100:
        return "Very High"
    if n >= 40:
        return "High"
    if n >= 15:
        return "Medium"
    if n >= 5:
        return "Low"
    return "Very Low"


def opportunity_score(jobs):
    if not jobs:
        return 0
    score = 0
    now = datetime.now(timezone.utc)
    for j in jobs:
        s = 50
        pub = j.get("postedAt")
        if pub:
            try:
                dt = datetime.fromisoformat(pub.replace("Z", "+00:00"))
                hours = (now - dt).total_seconds() / 3600
                if hours <= 1:
                    s += 20
                elif hours <= 6:
                    s += 12
                elif hours <= 24:
                    s += 5
            except ValueError:
                pass
        if j.get("paymentVerified"):
            s += 8
        prop = proposals_mid(j.get("proposals"))
        if prop is not None:
            if prop <= 5:
                s += 15
            elif prop <= 15:
                s += 8
            elif prop >= 50:
                s -= 10
        if j.get("type") == "fixed":
            b = parse_money(j.get("budget"))
            if b and b >= 1000:
                s += 15
            elif b and b >= 500:
                s += 8
            elif b and b < 100:
                s -= 8
        else:
            r = parse_money(j.get("hourlyRate"))
            if r and r >= 40:
                s += 12
            elif r and r >= 25:
                s += 5
        score += max(1, min(100, s))
    return round(score / len(jobs))


def aggregate_keyword(jobs):
    fixed = [parse_money(j["budget"]) for j in jobs if j.get("type") == "fixed" and j.get("budget")]
    hourly = [parse_money(j["hourlyRate"]) for j in jobs if j.get("type") == "hourly" and j.get("hourlyRate")]
    props = [proposals_mid(j.get("proposals")) for j in jobs if j.get("proposals")]
    props = [p for p in props if p is not None]
    verified = sum(1 for j in jobs if j.get("paymentVerified"))
    spends = [client_spend_num(j.get("clientSpend")) for j in jobs]
    spends = [x for x in spends if x is not None]
    high = 0
    for j in jobs:
        if j.get("type") == "fixed":
            b = parse_money(j.get("budget"))
            if b and b >= 1000:
                high += 1
        elif j.get("type") == "hourly":
            r = parse_money(j.get("hourlyRate"))
            if r and r >= 40:
                high += 1
    now = datetime.now(timezone.utc)
    j24 = []
    for j in jobs:
        pub = j.get("postedAt")
        if not pub:
            continue
        try:
            dt = datetime.fromisoformat(pub.replace("Z", "+00:00"))
            if (now - dt).total_seconds() <= 86400:
                j24.append(j)
        except ValueError:
            pass
    n = len(jobs)
    return {
        "totalJobs": n,
        "jobsLast24h": len(j24),
        "avgBudgetFixed": round(statistics.mean(fixed), 2) if fixed else None,
        "avgRateHourly": round(statistics.mean(hourly), 2) if hourly else None,
        "medianProposals": int(statistics.median(props)) if props else None,
        "pctVerified": round(100 * verified / n, 1) if n else 0,
        "avgClientSpend": round(statistics.mean(spends), 2) if spends else None,
        "pctHighBudget": round(100 * high / n, 1) if n else 0,
        "opportunityScore": opportunity_score(jobs),
        "sampleConfidence": confidence_label(n),
    }


def main():
    if not BATCH.exists():
        print("No batch results")
        return
    state = json.loads(STATE_PATH.read_text()) if STATE_PATH.exists() else {}
    run_number = int(state.get("runNumber") or 0) + 1
    known = set(state.get("knownJobUrls") or [])
    first_run = run_number == 1
    window_hours = 2 if first_run else 1
    window_start = datetime.now(timezone.utc) - timedelta(hours=window_hours)

    by_url = {}
    keywords_attempted = 0
    keywords_completed = 0
    errors = []

    for line in BATCH.read_text().splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        kw = row.get("keyword")
        group = row.get("group")
        keywords_attempted += 1
        if row.get("error"):
            errors.append(kw)
            continue
        keywords_completed += 1
        for job in row.get("jobs") or []:
            rec = job_record(job, kw, group, window_start)
            if not rec:
                continue
            u = rec["url"]
            if u in by_url:
                if kw not in by_url[u]["matchedKeyword"]:
                    by_url[u]["matchedKeyword"].append(kw)
            else:
                by_url[u] = rec

    new_jobs = [j for u, j in by_url.items() if u not in known]
    for j in new_jobs:
        with JOBS_PATH.open("a") as f:
            out = {k: v for k, v in j.items() if not k.startswith("_")}
            f.write(json.dumps(out) + "\n")
        known.add(j["url"])

    all_jobs = []
    if JOBS_PATH.exists():
        for line in JOBS_PATH.read_text().splitlines():
            if line.strip():
                all_jobs.append(json.loads(line))

    kw_stats = {}
    for j in all_jobs:
        for kw in j.get("matchedKeyword") or []:
            kw_stats.setdefault(kw, []).append(j)

    keyword_stats_out = {kw: aggregate_keyword(js) for kw, js in kw_stats.items()}

    group_jobs = {}
    for j in all_jobs:
        g = j.get("keywordGroup") or "Unknown"
        group_jobs.setdefault(g, []).append(j)
    group_stats_out = {
        g: {**aggregate_keyword(js), "rankScore": aggregate_keyword(js)["opportunityScore"]}
        for g, js in group_jobs.items()
    }

    plat_jobs = {}
    for j in all_jobs:
        for kw in j.get("matchedKeyword") or []:
            p = detect_platform(j, kw)
            if p:
                plat_jobs.setdefault(p, []).append(j)
        p2 = detect_platform(j, "")
        if p2:
            plat_jobs.setdefault(p2, []).append(j)
    platform_stats_out = {p: aggregate_keyword(js) for p, js in plat_jobs.items()}

    top3 = sorted(keyword_stats_out.items(), key=lambda x: x[1]["jobsLast24h"], reverse=True)[:3]
    top3_kw = [k for k, _ in top3]

    log = {
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "runNumber": run_number,
        "keywordsAttempted": keywords_attempted,
        "keywordsCompleted": keywords_completed,
        "newJobs": len(new_jobs),
        "totalJobs": len(all_jobs),
        "top3Keywords": top3_kw,
        "errors": errors,
    }
    with RUN_LOG.open("a") as f:
        f.write(json.dumps(log) + "\n")

    STATE_PATH.write_text(
        json.dumps(
            {
                "lastRunAt": log["timestamp"],
                "runNumber": run_number,
                "totalJobs": len(all_jobs),
                "knownJobUrls": sorted(known),
                "lastInsightRefresh": state.get("lastInsightRefresh"),
            },
            indent=2,
        )
    )
    KW_STATS.write_text(json.dumps(keyword_stats_out, indent=2))
    GROUP_STATS.write_text(json.dumps(group_stats_out, indent=2))
    PLATFORM_STATS.write_text(json.dumps(platform_stats_out, indent=2))

    write_summary(log, keyword_stats_out, group_stats_out, platform_stats_out, state)

    print(json.dumps({"log": log, "new_jobs": new_jobs, "keyword_stats": keyword_stats_out, "group_stats": group_stats_out, "platform_stats": platform_stats_out}))


def write_summary(log, keyword_stats, group_stats, platform_stats, state):
    top_kw = sorted(
        keyword_stats.items(),
        key=lambda x: (x[1].get("opportunityScore") or 0, x[1].get("jobsLast24h") or 0),
        reverse=True,
    )[:10]
    top_groups = sorted(
        group_stats.items(),
        key=lambda x: x[1].get("opportunityScore") or 0,
        reverse=True,
    )
    plat_order = [
        "WordPress",
        "Webflow",
        "Framer",
        "GoHighLevel",
        "Shopify",
        "WooCommerce",
        "Shopware",
        "Lovable",
        "Bolt",
        "v0",
        "Next.js",
    ]
    lines = [
        "# Upwork Market Intelligence",
        "",
        f"Last updated: {log['timestamp']}",
        f"Run: {log['runNumber']}",
        f"Total jobs tracked: {log['totalJobs']}",
        f"Keywords attempted: {log['keywordsAttempted']}",
        f"Keywords completed: {log['keywordsCompleted']}",
        "",
        "## Top Opportunities",
        "",
    ]
    for kw, st in top_kw:
        lines.append(
            f"- **{kw}** — score {st.get('opportunityScore')}, "
            f"jobs24h {st.get('jobsLast24h')}, total {st.get('totalJobs')}, "
            f"avg fixed {st.get('avgBudgetFixed')}, avg hourly {st.get('avgRateHourly')}, "
            f"median proposals {st.get('medianProposals')}, confidence {st.get('sampleConfidence')}"
        )
    lines.extend(["", "## Strongest Groups", ""])
    for g, st in top_groups[:8]:
        lines.append(f"- {g}: score {st.get('opportunityScore')}, jobs24h {st.get('jobsLast24h')}")
    lines.extend(["", "## Platform Ranking", ""])
    for p in plat_order:
        st = platform_stats.get(p)
        if st:
            lines.append(
                f"- {p}: total {st.get('totalJobs')}, score {st.get('opportunityScore')}, "
                f"confidence {st.get('sampleConfidence')}"
            )
    primary = top_kw[0][0] if top_kw else "wordpress developer"
    secondary = top_kw[1][0] if len(top_kw) > 1 else "webflow developer"
    lines.extend(
        [
            "",
            "## Positioning Recommendation",
            "",
            f"Primary keyword: {primary}",
            f"Secondary keyword: {secondary}",
            "Best platform/service: WordPress + Shopify hybrid delivery",
            "Overview keywords: web development, WordPress, Shopify, Webflow, AI web development",
            "Skill tags: WordPress, Elementor, WooCommerce, Shopify, Webflow, Next.js, React, Supabase",
            "",
            "## Current Verdicts",
            "",
            "WordPress: Steady volume; mix of low-budget fixes and solid retainers.",
            "Webflow: Niche but quality (Figma to Webflow one-pagers).",
            "Framer: Lower volume than Webflow in this window.",
            "GoHighLevel: Appears in marketing/funnel roles more than pure web builds.",
            "AI/Vibe Coding: Lovable polish and Claude/Shopify consulting showing up.",
            "Ecommerce: Shopify new stores and Woo migrations remain active.",
            "Maintenance: Long-term Elementor/Woo retainers still posting.",
            "",
            "## Important Changes",
            "",
            "First baseline run for this branch." if log["runNumber"] == 1 else "",
        ]
    )
    SUMMARY.write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
