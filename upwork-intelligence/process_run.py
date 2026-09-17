#!/usr/bin/env python3
"""Process raw search payloads into intelligence files."""
import json, re, statistics, hashlib
from datetime import datetime, timezone, timedelta
from pathlib import Path

BASE = Path(__file__).parent
KW_FILE = BASE / "keywords.json"
RAW_FILE = BASE / "raw-searches.jsonl"
BATCH_FILE = BASE / "_batch_results.jsonl"
JOBS_FILE = BASE / "jobs.jsonl"
STATE_FILE = BASE / "state.json"
RUN_LOG = BASE / "run-log.jsonl"
KW_STATS = BASE / "keyword-stats.json"
GROUP_STATS = BASE / "group-stats.json"
PLATFORM_STATS = BASE / "platform-stats.json"
SUMMARY = BASE / "current-summary.md"
INSIGHTS = BASE / "insights.md"

SKIP_TITLE = re.compile(r"crypto|gambling|casino|betting|porn|adult|escort|dating|onlyfans", re.I)

PLATFORM_MAP = {
    "WordPress": ["wordpress"],
    "Webflow": ["webflow"],
    "Framer": ["framer"],
    "GoHighLevel": ["gohighlevel", "go high level", "ghl", "highlevel"],
    "Shopify": ["shopify"],
    "WooCommerce": ["woocommerce"],
    "Shopware": ["shopware"],
    "Lovable": ["lovable"],
    "Bolt": ["bolt.new", "bolt developer", "bolt"],
    "v0": ["v0 developer", "v0 vercel", "v0"],
    "Next.js": ["nextjs", "next.js", "figma to nextjs"],
}

def norm_url(url):
    if not url:
        return None
    return url.split("?")[0]

def parse_money(s):
    if not s:
        return None
    s = str(s).replace(",", "").replace("$", "").strip()
    if "–" in s or "-" in s:
        parts = re.split(r"[–-]", s)
        nums = []
        for p in parts:
            p = p.replace("/hr", "").strip()
            try:
                nums.append(float(p))
            except ValueError:
                pass
        return statistics.mean(nums) if nums else None
    s = s.replace("/hr", "").strip()
    try:
        return float(s)
    except ValueError:
        return None

def parse_spend(s):
    if not s:
        return None
    s = str(s).replace(",", "").replace("$", "").strip()
    try:
        return float(s)
    except ValueError:
        return None

def proposal_mid(tier):
    if not tier:
        return None
    t = tier.lower()
    if "fewer than 5" in t:
        return 2
    if t.startswith("5 to 10"):
        return 7
    if t.startswith("10 to 15"):
        return 12
    if t.startswith("15 to 20"):
        return 17
    if t.startswith("20 to 50"):
        return 35
    if "50+" in t:
        return 55
    return None

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

def job_record(job, keyword, group):
    client = job.get("client") or {}
    verified = client.get("verification_status") == "VERIFIED"
    return {
        "url": norm_url(job.get("url")),
        "title": job.get("title"),
        "matchedKeyword": [keyword],
        "keywordGroup": group,
        "postedAt": job.get("published_date") or job.get("created_date"),
        "type": job.get("job_type"),
        "budget": job.get("budget"),
        "duration": job.get("duration"),
        "proposals": job.get("proposals_tier") or job.get("proposals"),
        "clientCountry": client.get("country"),
        "paymentVerified": verified if client else None,
        "clientSpend": client.get("total_spent"),
        "clientHireRate": None,
        "clientRating": client.get("rating"),
        "experienceLevel": job.get("experience_level"),
        "skills": job.get("skills"),
    }

def in_window(posted_at, hours):
    if not posted_at:
        return False
    try:
        dt = datetime.fromisoformat(posted_at.replace("Z", "+00:00"))
    except ValueError:
        return False
    return dt >= datetime.now(timezone.utc) - timedelta(hours=hours)

def opportunity_score(stats):
    # simple 1-100
    recency = min(stats.get("jobsLast24h", 0) * 8, 40)
    budget = min((stats.get("avgBudgetFixed") or 0) / 50, 25)
    rate = min((stats.get("avgRateHourly") or 0), 25)
    pay = max(budget, rate)
    props = stats.get("medianProposals")
    comp = 15 if props is not None and props <= 10 else (8 if props is not None and props <= 20 else 0)
    verified = min(stats.get("pctVerified", 0) / 4, 10)
    high = min(stats.get("pctHighBudget", 0) / 2, 10)
    return int(max(1, min(100, recency + pay + comp + verified + high)))

def main():
    keywords = json.loads(KW_FILE.read_text())
    kw_to_group = {k["keyword"]: k["group"] for k in keywords}

    state = {"runNumber": 0, "totalJobs": 0, "knownJobUrls": [], "lastRunAt": None, "lastInsightRefresh": None}
    if STATE_FILE.exists():
        state = json.loads(STATE_FILE.read_text())

    known = set(state.get("knownJobUrls") or [])
    existing_jobs = {}
    if JOBS_FILE.exists():
        for line in JOBS_FILE.read_text().splitlines():
            if not line.strip():
                continue
            j = json.loads(line)
            u = j.get("url")
            if u:
                existing_jobs[u] = j

    run_number = int(state.get("runNumber") or 0) + 1
    window_hours = 2 if run_number == 1 else 1

    raw_lines = []
    for p in (RAW_FILE, BATCH_FILE):
        if p.exists():
            raw_lines.extend(p.read_text().splitlines())
    if not raw_lines:
        print("No raw search files")
        return

    attempted = 0
    completed = 0
    errors = []
    new_jobs = []
    per_kw_hits = {k["keyword"]: [] for k in keywords}

    for line in raw_lines:
        if not line.strip():
            continue
        row = json.loads(line)
        kw = row.get("keyword")
        attempted += 1
        if row.get("error"):
            errors.append(kw)
            continue
        completed += 1
        payload = row.get("response") or {}
        for job in payload.get("jobs") or []:
            if not in_window(job.get("published_date") or job.get("created_date"), window_hours):
                continue
            title = job.get("title") or ""
            if SKIP_TITLE.search(title):
                continue
            url = norm_url(job.get("url"))
            if not url:
                continue
            group = kw_to_group.get(kw, "UNKNOWN")
            rec = job_record(job, kw, group)
            per_kw_hits[kw].append(rec)
            if url in existing_jobs:
                mk = existing_jobs[url].setdefault("matchedKeyword", [])
                if kw not in mk:
                    mk.append(kw)
            elif url not in known:
                new_jobs.append(rec)
                existing_jobs[url] = rec
                known.add(url)

    # append jobs
    with JOBS_FILE.open("w") as f:
        for j in existing_jobs.values():
            f.write(json.dumps(j, ensure_ascii=False) + "\n")

    all_jobs = list(existing_jobs.values())
    now = datetime.now(timezone.utc)

    def job_metrics(jobs):
        fixed = []
        hourly = []
        props = []
        verified = 0
        high = 0
        spend = []
        last24 = 0
        for j in jobs:
            b = parse_money(j.get("budget"))
            if j.get("type") == "fixed" and b is not None:
                fixed.append(b)
                if b >= 1000:
                    high += 1
            if j.get("type") == "hourly" and b is not None:
                hourly.append(b)
                if b >= 40:
                    high += 1
            pm = proposal_mid(j.get("proposals")) if isinstance(j.get("proposals"), str) else j.get("proposals")
            if pm is not None:
                props.append(pm)
            if j.get("paymentVerified"):
                verified += 1
            cs = parse_spend(j.get("clientSpend"))
            if cs is not None:
                spend.append(cs)
            pa = j.get("postedAt")
            if pa and in_window(pa, 24):
                last24 += 1
        n = len(jobs) or 1
        return {
            "totalJobs": len(jobs),
            "jobsLast24h": last24,
            "avgBudgetFixed": round(statistics.mean(fixed), 2) if fixed else None,
            "avgRateHourly": round(statistics.mean(hourly), 2) if hourly else None,
            "medianProposals": int(statistics.median(props)) if props else None,
            "pctVerified": round(100 * verified / n, 1),
            "avgClientSpend": round(statistics.mean(spend), 2) if spend else None,
            "pctHighBudget": round(100 * high / n, 1),
        }

    keyword_stats = {}
    for k in keywords:
        kw = k["keyword"]
        jobs = [existing_jobs[u] for u in existing_jobs if kw in (existing_jobs[u].get("matchedKeyword") or [])]
        # include fresh hits even if merged
        for j in per_kw_hits.get(kw, []):
            u = j["url"]
            if u in existing_jobs and existing_jobs[u] not in jobs:
                jobs.append(existing_jobs[u])
        m = job_metrics(jobs)
        m["sampleConfidence"] = confidence_label(m["totalJobs"])
        m["opportunityScore"] = opportunity_score(m)
        keyword_stats[kw] = m

    # groups
    groups = {}
    for k in keywords:
        g = k["group"]
        groups.setdefault(g, []).append(k["keyword"])
    group_stats = {}
    for g, kws in groups.items():
        jobs = []
        seen = set()
        for kw in kws:
            for j in per_kw_hits.get(kw, []):
                u = j["url"]
                if u and u not in seen and u in existing_jobs:
                    seen.add(u)
                    jobs.append(existing_jobs[u])
        # fallback all jobs in group from stored
        if not jobs:
            for j in existing_jobs.values():
                if j.get("keywordGroup") == g:
                    jobs.append(j)
        m = job_metrics(jobs)
        m["opportunityScore"] = opportunity_score(m)
        m["sampleConfidence"] = confidence_label(m["totalJobs"])
        group_stats[g] = m

    platform_stats = {}
    for pname, patterns in PLATFORM_MAP.items():
        jobs = []
        for j in existing_jobs.values():
            blob = " ".join([
                " ".join(j.get("matchedKeyword") or []),
                j.get("keywordGroup") or "",
                j.get("title") or "",
                " ".join(j.get("skills") or []),
            ]).lower()
            if any(p in blob for p in patterns):
                jobs.append(j)
        m = job_metrics(jobs)
        m["opportunityScore"] = opportunity_score(m)
        m["sampleConfidence"] = confidence_label(m["totalJobs"])
        platform_stats[pname] = m

    KW_STATS.write_text(json.dumps(keyword_stats, indent=2))
    GROUP_STATS.write_text(json.dumps(group_stats, indent=2))
    PLATFORM_STATS.write_text(json.dumps(platform_stats, indent=2))

    top_kw = sorted(keyword_stats.items(), key=lambda x: x[1]["opportunityScore"], reverse=True)[:10]
    top_groups = sorted(group_stats.items(), key=lambda x: x[1]["opportunityScore"], reverse=True)[:5]

    ts = now.isoformat()
    state.update({
        "lastRunAt": ts,
        "runNumber": run_number,
        "totalJobs": len(existing_jobs),
        "knownJobUrls": sorted(known),
    })
    STATE_FILE.write_text(json.dumps(state, indent=2))

    run_rec = {
        "timestamp": ts,
        "runNumber": run_number,
        "keywordsAttempted": attempted,
        "keywordsCompleted": completed,
        "newJobs": len(new_jobs),
        "totalJobs": len(existing_jobs),
        "top3Keywords": [k for k, _ in top_kw[:3]],
        "errors": errors,
    }
    with RUN_LOG.open("a") as f:
        f.write(json.dumps(run_rec) + "\n")

    # summary md
    lines = [
        "# Upwork Market Intelligence",
        "",
        f"Last updated: {ts}",
        f"Run: {run_number}",
        f"Total jobs tracked: {len(existing_jobs)}",
        f"Keywords attempted: {attempted}",
        f"Keywords completed: {completed}",
        "",
        "## Top Opportunities",
        "",
    ]
    for kw, st in top_kw:
        lines.append(f"- **{kw}** — score {st['opportunityScore']} ({st['sampleConfidence']}) | 24h: {st['jobsLast24h']} | total: {st['totalJobs']} | fixed avg: {st['avgBudgetFixed']} | hourly avg: {st['avgRateHourly']} | median proposals: {st['medianProposals']}")
    lines += ["", "## Strongest Groups", ""]
    for g, st in top_groups:
        lines.append(f"- **{g}** — score {st['opportunityScore']} | 24h: {st['jobsLast24h']} | total: {st['totalJobs']}")
    lines += ["", "## Platform Ranking", ""]
    for p, st in sorted(platform_stats.items(), key=lambda x: x[1]["opportunityScore"], reverse=True):
        lines.append(f"- **{p}** — score {st['opportunityScore']} | jobs: {st['totalJobs']} | 24h: {st['jobsLast24h']}")
    lines += [
        "",
        "## Positioning Recommendation",
        "",
        f"Primary keyword: {top_kw[0][0] if top_kw else 'wordpress developer'}",
        f"Secondary keyword: {top_kw[1][0] if len(top_kw) > 1 else 'webflow developer'}",
        f"Best platform/service: {max(platform_stats.items(), key=lambda x: x[1]['opportunityScore'])[0] if platform_stats else 'WordPress'}",
        "Overview keywords: WordPress, Webflow, Next.js, AI web development, website maintenance",
        "Skill tags: WordPress, Elementor, Webflow, React, Next.js, SEO, Shopify, Supabase, AI integrations",
        "",
        "## Current Verdicts",
        "",
        "WordPress: Steady volume; mix of maintenance, Elementor, speed, and security work.",
        "Webflow: Premium builds and migrations; strong when paired with SEO/CRO.",
        "Framer: Niche but active; design-heavy and migration projects.",
        "GoHighLevel: Automation and funnel ops; often bundled with ads/CRM.",
        "AI/Vibe Coding: Growing keyword noise; best leads mention production hardening.",
        "Ecommerce: Shopify migration and performance jobs stand out.",
        "Maintenance: Retainer-style WordPress and multi-site support recurring.",
        "",
        "## Important Changes",
        "",
        "First baseline run initialized." if run_number == 1 else "See chat update for deltas.",
    ]
    SUMMARY.write_text("\n".join(lines) + "\n")

    if run_number == 1 and not INSIGHTS.exists():
        INSIGHTS.write_text(
            "# Insights\n\n"
            "- WordPress + Elementor + maintenance appear frequently in the last 2 hours.\n"
            "- Webflow shows high-budget build work (e.g. $2.5k UK Webflow dev/design).\n"
            "- AI/vibe keywords surface production and automation roles more than pure site builds.\n"
            "- Performance/CWV and speed optimization jobs cluster around WordPress and Shopify.\n"
        )

    print(json.dumps({"run": run_number, "new": len(new_jobs), "total": len(existing_jobs), "attempted": attempted, "completed": completed, "errors": len(errors)}))

if __name__ == "__main__":
    main()
