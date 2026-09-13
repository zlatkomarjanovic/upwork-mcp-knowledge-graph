#!/usr/bin/env python3
"""Process run-results.jsonl into jobs.jsonl and stats files."""
import json
import math
import re
import statistics
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).parent
RESULTS = BASE / "run-results.jsonl"
JOBS = BASE / "jobs.jsonl"
STATE = BASE / "state.json"
RUN_LOG = BASE / "run-log.jsonl"

SKIP_PATTERNS = re.compile(
    r"\b(crypto trading|bitcoin trading|forex trading|casino|gambling|poker|"
    r"adult content|escort|dating app|onlyfans|alcohol brand|liquor brand)\b",
    re.I,
)

KEYWORD_GROUPS = {
    "web development": "Core Web Development",
    "website development": "Core Web Development",
    "web developer": "Core Web Development",
    "custom website": "Core Web Development",
    "frontend developer": "Core Web Development",
    "full stack developer": "Core Web Development",
    "web design": "Web Design",
    "website design": "Web Design",
    "website redesign": "Web Design",
    "landing page design": "Web Design",
    "UI UX website": "Web Design",
    "responsive web design": "Web Design",
    "wordpress": "WordPress",
    "wordpress developer": "WordPress",
    "wordpress website": "WordPress",
    "wordpress development": "WordPress",
    "wordpress redesign": "WordPress",
    "wordpress customization": "WordPress",
    "wordpress migration": "WordPress",
    "wordpress speed optimization": "WordPress",
    "wordpress maintenance": "WordPress",
    "woocommerce": "WordPress",
    "elementor developer": "WordPress",
    "bricks builder": "WordPress",
    "webflow": "Webflow / Framer",
    "webflow developer": "Webflow / Framer",
    "webflow website": "Webflow / Framer",
    "webflow redesign": "Webflow / Framer",
    "figma to webflow": "Webflow / Framer",
    "framer": "Webflow / Framer",
    "framer developer": "Webflow / Framer",
    "framer website": "Webflow / Framer",
    "framer redesign": "Webflow / Framer",
    "figma to framer": "Webflow / Framer",
    "AI web development": "AI / Vibe Coding",
    "AI web developer": "AI / Vibe Coding",
    "vibe coding": "AI / Vibe Coding",
    "claude code developer": "AI / Vibe Coding",
    "cursor AI developer": "AI / Vibe Coding",
    "lovable developer": "AI / Vibe Coding",
    "lovable app": "AI / Vibe Coding",
    "bolt developer": "AI / Vibe Coding",
    "bolt.new": "AI / Vibe Coding",
    "v0 developer": "AI / Vibe Coding",
    "v0 vercel": "AI / Vibe Coding",
    "replit developer": "AI / Vibe Coding",
    "supabase developer": "AI / Vibe Coding",
    "AI agent integration website": "AI / Vibe Coding",
    "gohighlevel": "GoHighLevel",
    "go high level": "GoHighLevel",
    "GHL": "GoHighLevel",
    "gohighlevel developer": "GoHighLevel",
    "gohighlevel website": "GoHighLevel",
    "gohighlevel funnel": "GoHighLevel",
    "gohighlevel automation": "GoHighLevel",
    "gohighlevel CRM": "GoHighLevel",
    "squarespace website": "Adjacent Platforms",
    "wix website": "Adjacent Platforms",
    "wix studio": "Adjacent Platforms",
    "bubble developer": "Adjacent Platforms",
    "nextjs developer": "Modern Stack",
    "next.js developer": "Modern Stack",
    "nextjs website": "Modern Stack",
    "react developer": "Modern Stack",
    "figma to nextjs": "Modern Stack",
    "tailwind developer": "Modern Stack",
    "astro developer": "Modern Stack",
    "sanity CMS": "Modern Stack",
    "ecommerce website": "Ecommerce",
    "ecommerce developer": "Ecommerce",
    "shopify developer": "Ecommerce",
    "shopify website": "Ecommerce",
    "woocommerce developer": "Ecommerce",
    "shopware": "Ecommerce",
    "shopware developer": "Ecommerce",
    "shopware 6": "Ecommerce",
    "headless ecommerce": "Ecommerce",
    "website maintenance": "Maintenance / Retainers",
    "website maintenance monthly": "Maintenance / Retainers",
    "website support ongoing": "Maintenance / Retainers",
    "website management ongoing": "Maintenance / Retainers",
    "wordpress support retainer": "Maintenance / Retainers",
    "webflow maintenance": "Maintenance / Retainers",
    "shopify maintenance": "Maintenance / Retainers",
    "ongoing web developer": "Maintenance / Retainers",
    "web development retainer": "Maintenance / Retainers",
    "conversion rate optimization": "Conversion / Performance",
    "landing page optimization": "Conversion / Performance",
    "website audit": "Conversion / Performance",
    "core web vitals": "Conversion / Performance",
    "page speed optimization": "Conversion / Performance",
    "website speed optimization": "Conversion / Performance",
    "technical SEO website": "Conversion / Performance",
}

ALL_KEYWORDS = list(KEYWORD_GROUPS.keys())

PLATFORM_MAP = {
    "WordPress": "WordPress",
    "Webflow / Framer": ["Webflow", "Framer"],
    "GoHighLevel": "GoHighLevel",
    "Ecommerce": ["Shopify", "WooCommerce", "Shopware"],
    "AI / Vibe Coding": ["Lovable", "Bolt", "v0", "Next.js"],
}


def norm_url(url: str) -> str:
    if not url:
        return ""
    return url.split("?")[0]


def parse_budget(budget_str, job_type):
    if not budget_str:
        return None, None
    s = budget_str.replace(",", "")
    if job_type == "hourly" and "/hr" in s:
        nums = re.findall(r"[\d.]+", s)
        if len(nums) >= 2:
            return None, (float(nums[0]) + float(nums[1])) / 2
        if nums:
            return None, float(nums[0])
    if job_type == "fixed":
        nums = re.findall(r"[\d.]+", s)
        if nums:
            return float(nums[0]), None
    return None, None


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


def is_high_budget(job_type, fixed_val, hourly_val):
    if job_type == "fixed" and fixed_val is not None and fixed_val >= 1000:
        return True
    if job_type == "hourly" and hourly_val is not None and hourly_val >= 40:
        return True
    return False


def job_record(job, keyword, group):
    client = job.get("client") or {}
    url = norm_url(job.get("url") or "")
    posted = job.get("published_date") or job.get("created_date")
    jt = job.get("job_type")
    fixed, hourly = parse_budget(job.get("budget"), jt)
    text = (job.get("title") or "") + " " + (job.get("description_snippet") or "")
    if SKIP_PATTERNS.search(text):
        return None
    return {
        "url": url,
        "title": job.get("title"),
        "matchedKeyword": [keyword],
        "keywordGroup": group,
        "postedAt": posted,
        "type": jt,
        "budget": job.get("budget"),
        "fixedValue": fixed,
        "hourlyValue": hourly,
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


def opportunity_score(jobs):
    if not jobs:
        return 0
    now = datetime.now(timezone.utc)
    scores = []
    for j in jobs:
        s = 30.0
        posted = j.get("postedAt")
        if posted:
            try:
                dt = datetime.fromisoformat(posted.replace("Z", "+00:00"))
                hours = (now - dt).total_seconds() / 3600
                if hours <= 2:
                    s += 25
                elif hours <= 24:
                    s += 15
                elif hours <= 72:
                    s += 5
            except ValueError:
                pass
        if j.get("fixedValue") and j["fixedValue"] >= 1000:
            s += 15
        elif j.get("hourlyValue") and j["hourlyValue"] >= 40:
            s += 12
        p = j.get("proposals")
        if p is not None:
            if p <= 5:
                s += 15
            elif p <= 15:
                s += 8
            elif p > 40:
                s -= 10
        if j.get("paymentVerified"):
            s += 8
        scores.append(max(0, min(100, s)))
    return round(sum(scores) / len(scores))


def aggregate_keyword_stats(all_jobs_by_kw):
    out = {}
    now = datetime.now(timezone.utc)
    for kw, jobs in all_jobs_by_kw.items():
        fixed_vals = [j["fixedValue"] for j in jobs if j.get("fixedValue")]
        hourly_vals = [j["hourlyValue"] for j in jobs if j.get("hourlyValue")]
        props = [j["proposals"] for j in jobs if j.get("proposals") is not None]
        verified = sum(1 for j in jobs if j.get("paymentVerified"))
        high_b = sum(
            1
            for j in jobs
            if is_high_budget(j.get("type"), j.get("fixedValue"), j.get("hourlyValue"))
        )
        j24 = 0
        for j in jobs:
            if not j.get("postedAt"):
                continue
            try:
                dt = datetime.fromisoformat(j["postedAt"].replace("Z", "+00:00"))
                if (now - dt).total_seconds() <= 86400:
                    j24 += 1
            except ValueError:
                pass
        spends = []
        for j in jobs:
            sp = j.get("clientSpend")
            if sp and isinstance(sp, str):
                m = re.search(r"[\d,.]+", sp.replace(",", ""))
                if m:
                    spends.append(float(m.group().replace(",", "")))
        out[kw] = {
            "totalJobs": len(jobs),
            "jobsLast24h": j24,
            "avgBudgetFixed": round(statistics.mean(fixed_vals), 2) if fixed_vals else None,
            "avgRateHourly": round(statistics.mean(hourly_vals), 2) if hourly_vals else None,
            "medianProposals": int(statistics.median(props)) if props else None,
            "pctVerified": round(100 * verified / len(jobs), 1) if jobs else 0,
            "avgClientSpend": round(statistics.mean(spends), 2) if spends else None,
            "pctHighBudget": round(100 * high_b / len(jobs), 1) if jobs else 0,
            "opportunityScore": opportunity_score(jobs),
            "sampleConfidence": confidence_label(len(jobs)),
        }
    return out


def main():
    import sys

    window_hours = float(sys.argv[1]) if len(sys.argv) > 1 else 2.0
    run_number = int(sys.argv[2]) if len(sys.argv) > 2 else 1

    state = json.loads(STATE.read_text()) if STATE.exists() else {}
    known = set(state.get("knownJobUrls") or [])
    existing_jobs = {}
    if JOBS.exists():
        for line in JOBS.read_text().splitlines():
            if line.strip():
                j = json.loads(line)
                u = norm_url(j.get("url", ""))
                if u:
                    existing_jobs[u] = j
                    known.add(u)

    now = datetime.now(timezone.utc)
    cutoff = now.timestamp() - window_hours * 3600

    keywords_attempted = len(ALL_KEYWORDS)
    keywords_completed = 0
    errors = []
    new_this_run = {}
    kw_hits = defaultdict(list)

    if RESULTS.exists():
        for line in RESULTS.read_text().splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            kw = row.get("keyword")
            if row.get("error"):
                errors.append(kw)
                continue
            resp = row.get("response") or {}
            if resp.get("status") not in (None, "ok") and "jobs" not in resp:
                errors.append(kw)
                continue
            keywords_completed += 1
            group = KEYWORD_GROUPS.get(kw, "Other")
            for job in resp.get("jobs") or []:
                rec = job_record(job, kw, group)
                if not rec or not rec["url"]:
                    continue
                posted = rec.get("postedAt")
                if posted:
                    try:
                        ts = datetime.fromisoformat(posted.replace("Z", "+00:00")).timestamp()
                        if ts < cutoff:
                            continue
                    except ValueError:
                        pass
                kw_hits[kw].append(rec)
                u = rec["url"]
                if u in new_this_run:
                    if kw not in new_this_run[u]["matchedKeyword"]:
                        new_this_run[u]["matchedKeyword"].append(kw)
                    continue
                if u in existing_jobs:
                    ej = existing_jobs[u]
                    if kw not in ej.get("matchedKeyword", []):
                        ej.setdefault("matchedKeyword", []).append(kw)
                    continue
                new_this_run[u] = rec

    with JOBS.open("a") as f:
        for j in new_this_run.values():
            f.write(json.dumps(j, ensure_ascii=False) + "\n")
            existing_jobs[j["url"]] = j
            known.add(j["url"])

    all_jobs = list(existing_jobs.values())
    all_jobs_by_kw = defaultdict(list)
    for j in all_jobs:
        for mk in j.get("matchedKeyword") or []:
            all_jobs_by_kw[mk].append(j)
    for kw in ALL_KEYWORDS:
        all_jobs_by_kw.setdefault(kw, [])

    keyword_stats = aggregate_keyword_stats(all_jobs_by_kw)
    (BASE / "keyword-stats.json").write_text(json.dumps(keyword_stats, indent=2))

    group_jobs = defaultdict(list)
    for kw, jobs in all_jobs_by_kw.items():
        g = KEYWORD_GROUPS[kw]
        group_jobs[g].extend(jobs)
    group_stats = {}
    for g, jobs in group_jobs.items():
        seen = {}
        for j in jobs:
            seen[j["url"]] = j
        group_stats[g] = aggregate_keyword_stats({g: list(seen.values())})[g]
    (BASE / "group-stats.json").write_text(json.dumps(group_stats, indent=2))

    platform_stats = {}
    platforms = {
        "WordPress": lambda j: any(
            "wordpress" in (s or "").lower() for s in (j.get("skills") or [])
        )
        or "wordpress" in (j.get("title") or "").lower(),
        "Webflow": lambda j: "webflow" in (j.get("title") or "").lower()
        or any("webflow" in (s or "").lower() for s in (j.get("skills") or [])),
        "Framer": lambda j: "framer" in (j.get("title") or "").lower()
        or any("framer" in (s or "").lower() for s in (j.get("skills") or [])),
        "GoHighLevel": lambda j: "highlevel" in (j.get("title") or "").lower()
        or any("highlevel" in (s or "").lower() for s in (j.get("skills") or [])),
        "Shopify": lambda j: "shopify" in (j.get("title") or "").lower()
        or any("shopify" in (s or "").lower() for s in (j.get("skills") or [])),
        "WooCommerce": lambda j: "woocommerce" in (j.get("title") or "").lower()
        or any("woocommerce" in (s or "").lower() for s in (j.get("skills") or [])),
        "Shopware": lambda j: "shopware" in (j.get("title") or "").lower(),
        "Lovable": lambda j: "lovable" in (j.get("title") or "").lower(),
        "Bolt": lambda j: "bolt" in (j.get("title") or "").lower(),
        "v0": lambda j: "v0" in (j.get("title") or "").lower(),
        "Next.js": lambda j: "next" in (j.get("title") or "").lower()
        or any("next" in (s or "").lower() for s in (j.get("skills") or [])),
    }
    for name, pred in platforms.items():
        pj = [j for j in all_jobs if pred(j)]
        platform_stats[name] = aggregate_keyword_stats({name: pj})[name] if pj else {
            "totalJobs": 0,
            "jobsLast24h": 0,
            "avgBudgetFixed": None,
            "avgRateHourly": None,
            "medianProposals": None,
            "pctVerified": 0,
            "avgClientSpend": None,
            "pctHighBudget": 0,
            "opportunityScore": 0,
            "sampleConfidence": "Very Low",
        }
    (BASE / "platform-stats.json").write_text(json.dumps(platform_stats, indent=2))

    top3 = sorted(keyword_stats.items(), key=lambda x: x[1]["jobsLast24h"], reverse=True)[:3]
    top3_kw = [k for k, _ in top3]

    log = {
        "timestamp": now.isoformat(),
        "runNumber": run_number,
        "keywordsAttempted": keywords_attempted,
        "keywordsCompleted": keywords_completed,
        "newJobs": len(new_this_run),
        "totalJobs": len(existing_jobs),
        "top3Keywords": top3_kw,
        "errors": errors,
    }
    with RUN_LOG.open("a") as f:
        f.write(json.dumps(log) + "\n")

    state.update(
        {
            "lastRunAt": now.isoformat(),
            "runNumber": run_number,
            "totalJobs": len(existing_jobs),
            "knownJobUrls": sorted(known),
            "lastInsightRefresh": state.get("lastInsightRefresh"),
        }
    )
    STATE.write_text(json.dumps(state, indent=2))

    print(json.dumps({"log": log, "new_jobs": list(new_this_run.values()), "keyword_stats": keyword_stats, "group_stats": group_stats, "platform_stats": platform_stats}))


if __name__ == "__main__":
    main()
