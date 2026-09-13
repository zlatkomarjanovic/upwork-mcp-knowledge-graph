#!/usr/bin/env python3
"""Update keyword/group/platform stats and state from jobs.jsonl."""
import json
import math
import os
import re
import statistics
from datetime import datetime, timezone, timedelta
from pathlib import Path

BASE = Path(__file__).resolve().parent
JOBS_PATH = BASE / "jobs.jsonl"
STATE_PATH = BASE / "state.json"
KW_STATS = BASE / "keyword-stats.json"
GROUP_STATS = BASE / "group-stats.json"
PLATFORM_STATS = BASE / "platform-stats.json"

KEYWORD_GROUPS = {
    "web development": "CORE WEB DEVELOPMENT",
    "website development": "CORE WEB DEVELOPMENT",
    "web developer": "CORE WEB DEVELOPMENT",
    "custom website": "CORE WEB DEVELOPMENT",
    "frontend developer": "CORE WEB DEVELOPMENT",
    "full stack developer": "CORE WEB DEVELOPMENT",
    "web design": "WEB DESIGN",
    "website design": "WEB DESIGN",
    "website redesign": "WEB DESIGN",
    "landing page design": "WEB DESIGN",
    "UI UX website": "WEB DESIGN",
    "responsive web design": "WEB DESIGN",
    "wordpress": "WORDPRESS",
    "wordpress developer": "WORDPRESS",
    "wordpress website": "WORDPRESS",
    "wordpress development": "WORDPRESS",
    "wordpress redesign": "WORDPRESS",
    "wordpress customization": "WORDPRESS",
    "wordpress migration": "WORDPRESS",
    "wordpress speed optimization": "WORDPRESS",
    "wordpress maintenance": "WORDPRESS",
    "woocommerce": "WORDPRESS",
    "elementor developer": "WORDPRESS",
    "bricks builder": "WORDPRESS",
    "webflow": "WEBFLOW / FRAMER",
    "webflow developer": "WEBFLOW / FRAMER",
    "webflow website": "WEBFLOW / FRAMER",
    "webflow redesign": "WEBFLOW / FRAMER",
    "figma to webflow": "WEBFLOW / FRAMER",
    "framer": "WEBFLOW / FRAMER",
    "framer developer": "WEBFLOW / FRAMER",
    "framer website": "WEBFLOW / FRAMER",
    "framer redesign": "WEBFLOW / FRAMER",
    "figma to framer": "WEBFLOW / FRAMER",
    "AI web development": "AI / VIBE CODING",
    "AI web developer": "AI / VIBE CODING",
    "vibe coding": "AI / VIBE CODING",
    "claude code developer": "AI / VIBE CODING",
    "cursor AI developer": "AI / VIBE CODING",
    "lovable developer": "AI / VIBE CODING",
    "lovable app": "AI / VIBE CODING",
    "bolt developer": "AI / VIBE CODING",
    "bolt.new": "AI / VIBE CODING",
    "v0 developer": "AI / VIBE CODING",
    "v0 vercel": "AI / VIBE CODING",
    "replit developer": "AI / VIBE CODING",
    "supabase developer": "AI / VIBE CODING",
    "AI agent integration website": "AI / VIBE CODING",
    "gohighlevel": "GOHIGHLEVEL",
    "go high level": "GOHIGHLEVEL",
    "GHL": "GOHIGHLEVEL",
    "gohighlevel developer": "GOHIGHLEVEL",
    "gohighlevel website": "GOHIGHLEVEL",
    "gohighlevel funnel": "GOHIGHLEVEL",
    "gohighlevel automation": "GOHIGHLEVEL",
    "gohighlevel CRM": "GOHIGHLEVEL",
    "squarespace website": "ADJACENT PLATFORMS",
    "wix website": "ADJACENT PLATFORMS",
    "wix studio": "ADJACENT PLATFORMS",
    "bubble developer": "ADJACENT PLATFORMS",
    "nextjs developer": "MODERN STACK",
    "next.js developer": "MODERN STACK",
    "nextjs website": "MODERN STACK",
    "react developer": "MODERN STACK",
    "figma to nextjs": "MODERN STACK",
    "tailwind developer": "MODERN STACK",
    "astro developer": "MODERN STACK",
    "sanity CMS": "MODERN STACK",
    "ecommerce website": "ECOMMERCE",
    "ecommerce developer": "ECOMMERCE",
    "shopify developer": "ECOMMERCE",
    "shopify website": "ECOMMERCE",
    "woocommerce developer": "ECOMMERCE",
    "shopware": "ECOMMERCE",
    "shopware developer": "ECOMMERCE",
    "shopware 6": "ECOMMERCE",
    "headless ecommerce": "ECOMMERCE",
    "website maintenance": "MAINTENANCE / RETAINERS",
    "website maintenance monthly": "MAINTENANCE / RETAINERS",
    "website support ongoing": "MAINTENANCE / RETAINERS",
    "website management ongoing": "MAINTENANCE / RETAINERS",
    "wordpress support retainer": "MAINTENANCE / RETAINERS",
    "webflow maintenance": "MAINTENANCE / RETAINERS",
    "shopify maintenance": "MAINTENANCE / RETAINERS",
    "ongoing web developer": "MAINTENANCE / RETAINERS",
    "web development retainer": "MAINTENANCE / RETAINERS",
    "conversion rate optimization": "CONVERSION / PERFORMANCE",
    "landing page optimization": "CONVERSION / PERFORMANCE",
    "website audit": "CONVERSION / PERFORMANCE",
    "core web vitals": "CONVERSION / PERFORMANCE",
    "page speed optimization": "CONVERSION / PERFORMANCE",
    "website speed optimization": "CONVERSION / PERFORMANCE",
    "technical SEO website": "CONVERSION / PERFORMANCE",
}

PLATFORMS = {
    "WordPress": re.compile(r"wordpress|elementor|woocommerce|bricks", re.I),
    "Webflow": re.compile(r"webflow", re.I),
    "Framer": re.compile(r"framer", re.I),
    "GoHighLevel": re.compile(r"gohighlevel|go high level|\bghl\b|highlevel", re.I),
    "Shopify": re.compile(r"shopify", re.I),
    "WooCommerce": re.compile(r"woocommerce", re.I),
    "Shopware": re.compile(r"shopware", re.I),
    "Lovable": re.compile(r"lovable", re.I),
    "Bolt": re.compile(r"bolt\.new|\bbolt\b", re.I),
    "v0": re.compile(r"\bv0\b|v0 vercel", re.I),
    "Next.js": re.compile(r"next\.?js", re.I),
}


def parse_money(s):
    if not s:
        return None
    s = str(s).replace(",", "").replace("$", "").strip()
    if "–" in s or "-" in s:
        parts = re.split(r"[–-]", s)
        nums = []
        for p in parts:
            p = re.sub(r"[^\d.]", "", p)
            if p:
                nums.append(float(p))
        return sum(nums) / len(nums) if nums else None
    m = re.search(r"[\d.]+", s)
    return float(m.group()) if m else None


def parse_hourly(s):
    if not s:
        return None
    s = str(s).lower()
    if "/hr" not in s and "hr" not in s and "–" in s:
        pass
    return parse_money(s)


def confidence(n):
    if n <= 4:
        return "Very Low"
    if n <= 14:
        return "Low"
    if n <= 39:
        return "Medium"
    if n <= 99:
        return "High"
    return "Very High"


def high_budget(job):
    if job.get("type") == "fixed":
        b = parse_money(job.get("budget"))
        return b is not None and b >= 1000
    if job.get("type") == "hourly":
        r = parse_hourly(job.get("budget"))
        return r is not None and r >= 40
    return False


def opportunity_score(jobs):
    if not jobs:
        return 1
    now = datetime.now(timezone.utc)
    recency = 0
    budget = 0
    comp = 0
    verified = 0
    high = 0
    for j in jobs:
        try:
            posted = datetime.fromisoformat(j["postedAt"].replace("Z", "+00:00"))
            hours = (now - posted).total_seconds() / 3600
            recency += max(0, 24 - hours) / 24
        except Exception:
            recency += 0.3
        if j.get("type") == "fixed":
            b = parse_money(j.get("budget"))
            if b:
                budget += min(b / 2000, 1.5)
        else:
            r = parse_hourly(j.get("budget"))
            if r:
                budget += min(r / 80, 1.5)
        p = j.get("proposals")
        if p is not None:
            comp += max(0, 1 - min(p, 50) / 50)
        if j.get("paymentVerified"):
            verified += 1
        if high_budget(j):
            high += 1
    n = len(jobs)
    raw = (recency / n * 25) + (budget / n * 25) + (comp / n * 25) + (verified / n * 15) + (high / n * 10)
    return max(1, min(100, int(raw)))


def load_jobs():
    jobs = []
    if JOBS_PATH.exists():
        with open(JOBS_PATH) as f:
            for line in f:
                line = line.strip()
                if line:
                    jobs.append(json.loads(line))
    return jobs


def jobs_for_keyword(all_jobs, keyword):
    return [j for j in all_jobs if keyword in j.get("matchedKeyword", [])]


def compute_keyword_stats(all_jobs):
    out = {}
    for kw in KEYWORD_GROUPS:
        subset = jobs_for_keyword(all_jobs, kw)
        now = datetime.now(timezone.utc)
        last24 = [j for j in subset if j.get("postedAt") and (now - datetime.fromisoformat(j["postedAt"].replace("Z", "+00:00"))).total_seconds() <= 86400]
        fixed = [parse_money(j["budget"]) for j in subset if j.get("type") == "fixed" and j.get("budget")]
        hourly = [parse_hourly(j["budget"]) for j in subset if j.get("type") == "hourly" and j.get("budget")]
        props = [j["proposals"] for j in subset if j.get("proposals") is not None]
        verified = [j for j in subset if j.get("paymentVerified")]
        high = [j for j in subset if high_budget(j)]
        out[kw] = {
            "totalJobs": len(subset),
            "jobsLast24h": len(last24),
            "avgBudgetFixed": round(statistics.mean(fixed), 2) if fixed else None,
            "avgRateHourly": round(statistics.mean(hourly), 2) if hourly else None,
            "medianProposals": int(statistics.median(props)) if props else None,
            "pctVerified": round(100 * len(verified) / len(subset), 1) if subset else 0,
            "avgClientSpend": None,
            "pctHighBudget": round(100 * len(high) / len(subset), 1) if subset else 0,
            "opportunityScore": opportunity_score(subset),
            "sampleConfidence": confidence(len(subset)),
        }
    return out


def compute_group_stats(kw_stats):
    groups = {}
    for kw, g in KEYWORD_GROUPS.items():
        groups.setdefault(g, []).append(kw_stats[kw])
    out = {}
    for g, rows in groups.items():
        total = sum(r["totalJobs"] for r in rows)
        j24 = sum(r["jobsLast24h"] for r in rows)
        scores = [r["opportunityScore"] for r in rows if r["totalJobs"]]
        out[g] = {
            "totalJobs": total,
            "jobsLast24h": j24,
            "avgOpportunityScore": round(statistics.mean(scores), 1) if scores else 0,
            "keywordCount": len(rows),
        }
    return dict(sorted(out.items(), key=lambda x: -x[1]["jobsLast24h"]))


def job_matches_platform(job, name, pattern):
    text = " ".join(
        [
            job.get("title") or "",
            " ".join(job.get("skills") or []),
            " ".join(job.get("matchedKeyword") or []),
        ]
    )
    return bool(pattern.search(text))


def compute_platform_stats(all_jobs):
    out = {}
    for name, pat in PLATFORMS.items():
        subset = [j for j in all_jobs if job_matches_platform(j, name, pat)]
        fixed = [parse_money(j["budget"]) for j in subset if j.get("type") == "fixed" and j.get("budget")]
        hourly = [parse_hourly(j["budget"]) for j in subset if j.get("type") == "hourly" and j.get("budget")]
        props = [j["proposals"] for j in subset if j.get("proposals") is not None]
        out[name] = {
            "jobs": len(subset),
            "avgBudgetFixed": round(statistics.mean(fixed), 2) if fixed else None,
            "avgRateHourly": round(statistics.mean(hourly), 2) if hourly else None,
            "medianProposals": int(statistics.median(props)) if props else None,
            "opportunityScore": opportunity_score(subset),
            "sampleConfidence": confidence(len(subset)),
        }
    return out


def main():
    jobs = load_jobs()
    kw_stats = compute_keyword_stats(jobs)
    with open(KW_STATS, "w") as f:
        json.dump(kw_stats, f, indent=2)
    with open(GROUP_STATS, "w") as f:
        json.dump(compute_group_stats(kw_stats), f, indent=2)
    with open(PLATFORM_STATS, "w") as f:
        json.dump(compute_platform_stats(jobs), f, indent=2)
    print(f"Updated stats from {len(jobs)} jobs")


if __name__ == "__main__":
    main()
