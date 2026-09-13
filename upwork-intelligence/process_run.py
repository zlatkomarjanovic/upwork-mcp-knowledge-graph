#!/usr/bin/env python3
"""One-shot stats builder for hourly tracker runs."""
import json, math, re, statistics
from datetime import datetime, timezone, timedelta
from pathlib import Path

BASE = Path(__file__).parent
RUN_AT = datetime(2026, 9, 13, 12, 32, 43, tzinfo=timezone.utc)
WINDOW_HOURS = 2  # first run
CUTOFF = RUN_AT - timedelta(hours=WINDOW_HOURS)

KEYWORD_GROUPS = {
    "CORE WEB DEVELOPMENT": ["web development", "website development", "web developer", "custom website", "frontend developer", "full stack developer"],
    "WEB DESIGN": ["web design", "website design", "website redesign", "landing page design", "UI UX website", "responsive web design"],
    "WORDPRESS": ["wordpress", "wordpress developer", "wordpress website", "wordpress development", "wordpress redesign", "wordpress customization", "wordpress migration", "wordpress speed optimization", "wordpress maintenance", "woocommerce", "elementor developer", "bricks builder"],
    "WEBFLOW / FRAMER": ["webflow", "webflow developer", "webflow website", "webflow redesign", "figma to webflow", "framer", "framer developer", "framer website", "framer redesign", "figma to framer"],
    "AI / VIBE CODING": ["AI web development", "AI web developer", "vibe coding", "claude code developer", "cursor AI developer", "lovable developer", "lovable app", "bolt developer", "bolt.new", "v0 developer", "v0 vercel", "replit developer", "supabase developer", "AI agent integration website"],
    "GOHIGHLEVEL": ["gohighlevel", "go high level", "GHL", "gohighlevel developer", "gohighlevel website", "gohighlevel funnel", "gohighlevel automation", "gohighlevel CRM"],
    "ADJACENT PLATFORMS": ["squarespace website", "wix website", "wix studio", "bubble developer"],
    "MODERN STACK": ["nextjs developer", "next.js developer", "nextjs website", "react developer", "figma to nextjs", "tailwind developer", "astro developer", "sanity CMS"],
    "ECOMMERCE": ["ecommerce website", "ecommerce developer", "shopify developer", "shopify website", "woocommerce developer", "shopware", "shopware developer", "shopware 6", "headless ecommerce"],
    "MAINTENANCE / RETAINERS": ["website maintenance", "website maintenance monthly", "website support ongoing", "website management ongoing", "wordpress support retainer", "webflow maintenance", "shopify maintenance", "ongoing web developer", "web development retainer"],
    "CONVERSION / PERFORMANCE": ["conversion rate optimization", "landing page optimization", "website audit", "core web vitals", "page speed optimization", "website speed optimization", "technical SEO website"],
}
ALL_KEYWORDS = [k for ks in KEYWORD_GROUPS.values() for k in ks]

PLATFORM_MAP = {
    "WordPress": ["wordpress"],
    "Webflow": ["webflow"],
    "Framer": ["framer"],
    "GoHighLevel": ["gohighlevel", "go high level", "GHL", "highlevel"],
    "Shopify": ["shopify"],
    "WooCommerce": ["woocommerce"],
    "Shopware": ["shopware"],
    "Lovable": ["lovable"],
    "Bolt": ["bolt"],
    "v0": ["v0"],
    "Next.js": ["nextjs", "next.js"],
}

SKIP_PAT = re.compile(r"alcohol|gambling|adult content|crypto trading|dating", re.I)


def norm_url(u):
    if not u:
        return None
    return u.split("?")[0]


def parse_money(budget_str):
    if not budget_str:
        return None, None
    s = budget_str.replace(",", "")
    if "/hr" in s.lower() or "hr" in s.lower():
        nums = re.findall(r"[\d.]+", s)
        if nums:
            vals = [float(x) for x in nums]
            return None, sum(vals) / len(vals)
        return None, None
    m = re.search(r"([\d.]+)", s)
    if m:
        return float(m.group(1)), None
    return None, None


def parse_spend(s):
    if not s:
        return None
    m = re.search(r"([\d,]+\.?\d*)", str(s).replace("$", ""))
    return float(m.group(1).replace(",", "")) if m else None


def confidence(n):
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
    now = RUN_AT
    for j in jobs:
        posted = j.get("postedAt")
        if posted:
            try:
                dt = datetime.fromisoformat(posted.replace("Z", "+00:00"))
                age_h = max(0.1, (now - dt).total_seconds() / 3600)
                recency = min(30, 30 / age_h)
            except Exception:
                recency = 5
        else:
            recency = 5
        fb, hr = parse_money(j.get("budget") or "")
        pay = 0
        if fb and fb >= 1000:
            pay += 25
        elif fb and fb >= 500:
            pay += 15
        elif fb and fb >= 200:
            pay += 8
        if hr and hr >= 40:
            pay += 25
        elif hr and hr >= 25:
            pay += 12
        props = j.get("proposals") or 50
        comp = max(5, 25 - min(props, 25))
        if j.get("paymentVerified"):
            pay += 5
        score += recency + pay + comp
    return min(100, int(score / len(jobs) * 2))


def load_jobs():
    jobs = {}
    p = BASE / "jobs.jsonl"
    if p.exists():
        for line in p.read_text().splitlines():
            if line.strip():
                j = json.loads(line)
                u = norm_url(j.get("url"))
                if u:
                    jobs[u] = j
    return jobs


def main():
    jobs = load_jobs()
    jobs_list = list(jobs.values())

    kw_stats = {}
    for kw in ALL_KEYWORDS:
        matched = [j for j in jobs_list if kw in j.get("matchedKeyword", [])]
        fixed = [parse_money(j.get("budget") or "")[0] for j in matched]
        fixed = [x for x in fixed if x]
        hourly = [parse_money(j.get("budget") or "")[1] for j in matched]
        hourly = [x for x in hourly if x]
        props = [j["proposals"] for j in matched if j.get("proposals") is not None]
        verified = sum(1 for j in matched if j.get("paymentVerified")) / len(matched) if matched else 0
        high = sum(
            1
            for j in matched
            if (parse_money(j.get("budget") or "")[0] or 0) >= 1000
            or (parse_money(j.get("budget") or "")[1] or 0) >= 40
        )
        j24 = sum(
            1
            for j in matched
            if j.get("postedAt")
            and datetime.fromisoformat(j["postedAt"].replace("Z", "+00:00")) >= RUN_AT - timedelta(hours=24)
        )
        kw_stats[kw] = {
            "totalJobs": len(matched),
            "jobsLast24h": j24,
            "avgBudgetFixed": round(statistics.mean(fixed), 2) if fixed else None,
            "avgRateHourly": round(statistics.mean(hourly), 2) if hourly else None,
            "medianProposals": int(statistics.median(props)) if props else None,
            "pctVerified": round(verified * 100, 1),
            "avgClientSpend": None,
            "pctHighBudget": round(high / len(matched) * 100, 1) if matched else 0,
            "opportunityScore": opportunity_score(matched),
            "sampleConfidence": confidence(len(matched)),
        }

    group_stats = {}
    for g, kws in KEYWORD_GROUPS.items():
        gj = [j for j in jobs_list if any(k in j.get("matchedKeyword", []) for k in kws)]
        group_stats[g] = {
            "totalJobs": len(gj),
            "jobsLast24h": sum(
                1
                for j in gj
                if j.get("postedAt")
                and datetime.fromisoformat(j["postedAt"].replace("Z", "+00:00")) >= RUN_AT - timedelta(hours=24)
            ),
            "opportunityScore": opportunity_score(gj),
            "sampleConfidence": confidence(len(gj)),
        }

    plat_stats = {}
    for plat, needles in PLATFORM_MAP.items():
        pj = [
            j
            for j in jobs_list
            if any(n.lower() in " ".join(j.get("matchedKeyword", [])).lower() for n in needles)
            or any(n.lower() in (j.get("title") or "").lower() for n in needles)
            or any(n.lower() in " ".join(j.get("skills") or []).lower() for n in needles)
        ]
        fixed = [parse_money(j.get("budget") or "")[0] for j in pj]
        fixed = [x for x in fixed if x]
        hourly = [parse_money(j.get("budget") or "")[1] for j in pj]
        hourly = [x for x in hourly if x]
        props = [j["proposals"] for j in pj if j.get("proposals") is not None]
        plat_stats[plat] = {
            "jobs": len(pj),
            "avgBudgetFixed": round(statistics.mean(fixed), 2) if fixed else None,
            "avgRateHourly": round(statistics.mean(hourly), 2) if hourly else None,
            "medianProposals": int(statistics.median(props)) if props else None,
            "opportunityScore": opportunity_score(pj),
            "confidence": confidence(len(pj)),
        }

    (BASE / "keyword-stats.json").write_text(json.dumps(kw_stats, indent=2))
    (BASE / "group-stats.json").write_text(json.dumps(group_stats, indent=2))
    (BASE / "platform-stats.json").write_text(json.dumps(plat_stats, indent=2))

    state = {
        "lastRunAt": RUN_AT.isoformat(),
        "runNumber": 1,
        "totalJobs": len(jobs_list),
        "knownJobUrls": list(jobs.keys())[:5000],
        "lastInsightRefresh": RUN_AT.isoformat(),
    }
    (BASE / "state.json").write_text(json.dumps(state, indent=2))
    print(json.dumps({"jobs": len(jobs_list), "keywords": len(kw_stats)}))


if __name__ == "__main__":
    main()
