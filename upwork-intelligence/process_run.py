#!/usr/bin/env python3
"""Process raw search batches and update upwork-intelligence store."""
import json
import re
import statistics
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

BASE = Path(__file__).resolve().parent
WINDOW_HOURS_FIRST = 2
WINDOW_HOURS = 1

SKIP_PATTERNS = re.compile(
    r"casino|gambling|betting|poker|adult|xxx|porn|crypto trading|bitcoin trader|trading platform|real-time trading|dating app|hookup",
    re.I,
)

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

PLATFORM_KEYWORDS = {
    "WordPress": ["wordpress"],
    "Webflow": ["webflow"],
    "Framer": ["framer"],
    "GoHighLevel": ["gohighlevel", "go high level", "ghl"],
    "Shopify": ["shopify"],
    "WooCommerce": ["woocommerce"],
    "Shopware": ["shopware"],
    "Lovable": ["lovable"],
    "Bolt": ["bolt"],
    "v0": ["v0"],
    "Next.js": ["nextjs", "next.js"],
}


def norm_url(url: str) -> str:
    if not url:
        return ""
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
    try:
        return float(str(s).replace(",", "").replace("$", ""))
    except ValueError:
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
    budget = job.get("budget")
    jt = job.get("job_type")
    fixed = parse_money(budget) if jt == "fixed" else None
    hourly = parse_money(budget) if jt == "hourly" else None
    return {
        "url": norm_url(job.get("url") or ""),
        "title": job.get("title"),
        "matchedKeyword": [keyword],
        "keywordGroup": group,
        "postedAt": job.get("published_date") or job.get("created_date"),
        "type": jt,
        "budget": budget if jt == "fixed" else None,
        "hourlyRate": budget if jt == "hourly" else None,
        "duration": job.get("duration"),
        "proposals": job.get("proposal_count"),
        "clientCountry": client.get("country"),
        "paymentVerified": client.get("verification_status") == "VERIFIED",
        "clientSpend": client.get("total_spent"),
        "clientHireRate": None,
        "clientRating": client.get("rating"),
        "experienceLevel": job.get("experience_level"),
        "skills": job.get("skills"),
        "_fixedNum": fixed,
        "_hourlyNum": hourly,
        "_spendNum": parse_spend(client.get("total_spent")),
    }


def should_skip(job):
    if not job.get("url"):
        return True
    text = (job.get("title") or "") + " " + (job.get("description_snippet") or "")
    return bool(SKIP_PATTERNS.search(text))


def in_window(posted_at, now, hours):
    if not posted_at:
        return False
    try:
        dt = datetime.fromisoformat(posted_at.replace("Z", "+00:00"))
    except ValueError:
        return False
    return dt >= now - timedelta(hours=hours)


def opportunity_score(jobs_24h):
    if not jobs_24h:
        return 1
    recency = min(len(jobs_24h) * 8, 30)
    budgets = [j["_fixedNum"] for j in jobs_24h if j["_fixedNum"]]
    rates = [j["_hourlyNum"] for j in jobs_24h if j["_hourlyNum"]]
    avg_b = statistics.mean(budgets) if budgets else 0
    avg_r = statistics.mean(rates) if rates else 0
    budget_pts = min((avg_b / 1000) * 15 + (avg_r / 40) * 15, 30)
    props = [j["proposals"] for j in jobs_24h if j.get("proposals") is not None]
    med_p = statistics.median(props) if props else 50
    comp_pts = max(0, 25 - min(med_p, 25))
    high = sum(
        1
        for j in jobs_24h
        if (j["_fixedNum"] or 0) >= 1000 or (j["_hourlyNum"] or 0) >= 40
    )
    high_pts = min(high * 5, 10)
    verified = sum(1 for j in jobs_24h if j.get("paymentVerified"))
    ver_pts = min((verified / max(len(jobs_24h), 1)) * 10, 10)
    raw = recency + budget_pts + comp_pts + high_pts + ver_pts
    return max(1, min(100, int(raw)))


def load_search_data():
    all_keywords = list(KEYWORD_GROUPS.keys())
    mcp_dir = BASE / "mcp_raw"
    if mcp_dir.is_dir() and any(mcp_dir.glob("*.json")):
        by_kw = {}
        for f in mcp_dir.glob("*.json"):
            item = json.loads(f.read_text())
            by_kw[item["keyword"]] = item
        searches = []
        errors = []
        for kw in all_keywords:
            if kw not in by_kw:
                errors.append(kw)
                continue
            entry = by_kw[kw]
            searches.append(entry)
            resp = entry.get("response") or {}
            if resp.get("status") != "ok" and "jobs" not in resp:
                errors.append(kw)
        return {
            "keywordsAttempted": len(all_keywords),
            "keywordsCompleted": len(searches),
            "errors": errors,
            "searches": searches,
        }
    raw_path = Path(sys.argv[1]) if len(sys.argv) > 1 else BASE / "raw_batch.json"
    return json.loads(raw_path.read_text())


def main():
    data = load_search_data()
    now = datetime.now(timezone.utc)
    state_path = BASE / "state.json"
    if state_path.exists():
        state = json.loads(state_path.read_text())
        run_number = state.get("runNumber", 0) + 1
        known = set(state.get("knownJobUrls", []))
        first_run = False
    else:
        run_number = 1
        known = set()
        first_run = True

    window_h = WINDOW_HOURS_FIRST if first_run else WINDOW_HOURS
    all_keywords = list(KEYWORD_GROUPS.keys())
    keywords_attempted = data.get("keywordsAttempted", len(all_keywords))
    keywords_completed = data.get("keywordsCompleted", 0)
    errors = data.get("errors", [])
    searches = data.get("searches", [])

    jobs_by_url = {}
    for entry in searches:
        kw = entry["keyword"]
        group = KEYWORD_GROUPS.get(kw, "OTHER")
        resp = entry.get("response") or {}
        if resp.get("status") != "ok" and "jobs" not in resp:
            if kw not in errors:
                errors.append(kw)
            continue
        for job in resp.get("jobs") or []:
            if should_skip(job):
                continue
            if not in_window(job.get("published_date") or job.get("created_date"), now, window_h):
                continue
            url = norm_url(job.get("url") or "")
            if not url:
                continue
            rec = job_record(job, kw, group)
            if url in jobs_by_url:
                if kw not in jobs_by_url[url]["matchedKeyword"]:
                    jobs_by_url[url]["matchedKeyword"].append(kw)
            else:
                jobs_by_url[url] = rec

    new_jobs = [j for u, j in jobs_by_url.items() if u not in known]
    for j in new_jobs:
        known.add(j["url"])

    jobs_path = BASE / "jobs.jsonl"
    with jobs_path.open("a") as f:
        for j in new_jobs:
            out = {k: v for k, v in j.items() if not k.startswith("_")}
            f.write(json.dumps(out) + "\n")

    all_jobs = []
    if jobs_path.exists():
        for line in jobs_path.read_text().splitlines():
            if line.strip():
                all_jobs.append(json.loads(line))

    now_iso = now.isoformat().replace("+00:00", "Z")
    cutoff_24 = now - timedelta(hours=24)

    def jobs_for_keyword(kw):
        return [j for j in all_jobs if kw in j.get("matchedKeyword", [])]

    keyword_stats = {}
    for kw in all_keywords:
        kj = jobs_for_keyword(kw)
        j24 = [
            j
            for j in kj
            if j.get("postedAt")
            and datetime.fromisoformat(j["postedAt"].replace("Z", "+00:00")) >= cutoff_24
        ]
        fixed = [parse_money(j.get("budget")) for j in kj if j.get("type") == "fixed"]
        fixed = [x for x in fixed if x is not None]
        hourly = [parse_money(j.get("hourlyRate")) for j in kj if j.get("type") == "hourly"]
        hourly = [x for x in hourly if x is not None]
        props = [j["proposals"] for j in kj if j.get("proposals") is not None]
        verified = [j for j in kj if j.get("paymentVerified")]
        spends = [parse_spend(j.get("clientSpend")) for j in kj]
        spends = [x for x in spends if x is not None]
        high = sum(
            1
            for j in kj
            if (parse_money(j.get("budget")) or 0) >= 1000
            or (parse_money(j.get("hourlyRate")) or 0) >= 40
        )
        enriched = []
        for j in j24:
            enriched.append(
                {
                    **j,
                    "_fixedNum": parse_money(j.get("budget")),
                    "_hourlyNum": parse_money(j.get("hourlyRate")),
                }
            )
        keyword_stats[kw] = {
            "totalJobs": len(kj),
            "jobsLast24h": len(j24),
            "avgBudgetFixed": round(statistics.mean(fixed), 2) if fixed else None,
            "avgRateHourly": round(statistics.mean(hourly), 2) if hourly else None,
            "medianProposals": int(statistics.median(props)) if props else None,
            "pctVerified": round(100 * len(verified) / len(kj), 1) if kj else None,
            "avgClientSpend": round(statistics.mean(spends), 2) if spends else None,
            "pctHighBudget": round(100 * high / len(kj), 1) if kj else None,
            "opportunityScore": opportunity_score(enriched),
            "sampleConfidence": confidence_label(len(kj)),
        }

    (BASE / "keyword-stats.json").write_text(json.dumps(keyword_stats, indent=2))

    group_stats = {}
    for g in set(KEYWORD_GROUPS.values()):
        gk = [kw for kw, gg in KEYWORD_GROUPS.items() if gg == g]
        totals = sum(keyword_stats[k]["totalJobs"] for k in gk)
        j24 = sum(keyword_stats[k]["jobsLast24h"] for k in gk)
        scores = [keyword_stats[k]["opportunityScore"] for k in gk if keyword_stats[k]["totalJobs"]]
        group_stats[g] = {
            "totalJobs": totals,
            "jobsLast24h": j24,
            "avgOpportunityScore": round(statistics.mean(scores), 1) if scores else 0,
        }
    (BASE / "group-stats.json").write_text(json.dumps(group_stats, indent=2))

    platform_stats = {}
    for plat, needles in PLATFORM_KEYWORDS.items():
        matched = [
            j
            for j in all_jobs
            if any(
                n.lower() in " ".join(j.get("matchedKeyword", [])).lower()
                or n.lower() in (j.get("title") or "").lower()
                or any(n.lower() in (s or "").lower() for s in (j.get("skills") or []))
                for n in needles
            )
        ]
        fixed = [parse_money(j.get("budget")) for j in matched if j.get("type") == "fixed"]
        fixed = [x for x in fixed if x is not None]
        hourly = [parse_money(j.get("hourlyRate")) for j in matched if j.get("type") == "hourly"]
        hourly = [x for x in hourly if x is not None]
        props = [j["proposals"] for j in matched if j.get("proposals") is not None]
        enriched = []
        for j in matched:
            if j.get("postedAt") and datetime.fromisoformat(j["postedAt"].replace("Z", "+00:00")) >= cutoff_24:
                enriched.append(
                    {
                        **j,
                        "_fixedNum": parse_money(j.get("budget")),
                        "_hourlyNum": parse_money(j.get("hourlyRate")),
                    }
                )
        platform_stats[plat] = {
            "jobs": len(matched),
            "avgBudgetFixed": round(statistics.mean(fixed), 2) if fixed else None,
            "avgRateHourly": round(statistics.mean(hourly), 2) if hourly else None,
            "medianProposals": int(statistics.median(props)) if props else None,
            "opportunityScore": opportunity_score(enriched),
            "sampleConfidence": confidence_label(len(matched)),
        }
    (BASE / "platform-stats.json").write_text(json.dumps(platform_stats, indent=2))

    top3 = sorted(keyword_stats.items(), key=lambda x: x[1]["jobsLast24h"], reverse=True)[:3]
    top3_kw = [t[0] for t in top3]

    log = {
        "timestamp": now_iso,
        "runNumber": run_number,
        "keywordsAttempted": keywords_attempted,
        "keywordsCompleted": keywords_completed,
        "newJobs": len(new_jobs),
        "totalJobs": len(all_jobs),
        "top3Keywords": top3_kw,
        "errors": errors,
    }
    with (BASE / "run-log.jsonl").open("a") as f:
        f.write(json.dumps(log) + "\n")

    state_out = {
        "lastRunAt": now_iso,
        "runNumber": run_number,
        "totalJobs": len(all_jobs),
        "knownJobUrls": sorted(known),
        "lastInsightRefresh": None,
    }
    state_path.write_text(json.dumps(state_out, indent=2))

    top10 = sorted(keyword_stats.items(), key=lambda x: x[1]["opportunityScore"], reverse=True)[:10]
    groups_rank = sorted(group_stats.items(), key=lambda x: x[1]["avgOpportunityScore"], reverse=True)

    summary = f"""# Upwork Market Intelligence

Last updated: {now_iso}
Run: {run_number}
Total jobs tracked: {len(all_jobs)}
Keywords attempted: {keywords_attempted}
Keywords completed: {keywords_completed}

## Top Opportunities

"""
    for i, (kw, st) in enumerate(top10, 1):
        summary += f"""{i}. **{kw}** — score {st['opportunityScore']}
   - jobsLast24h: {st['jobsLast24h']} | totalJobs: {st['totalJobs']}
   - avg fixed: {st['avgBudgetFixed']} | avg hourly: {st['avgRateHourly']}
   - median proposals: {st['medianProposals']} | confidence: {st['sampleConfidence']}

"""

    summary += "## Strongest Groups\n\n"
    for i, (g, st) in enumerate(groups_rank[:5], 1):
        summary += f"{i}. {g} — jobs24h {st['jobsLast24h']}, score {st['avgOpportunityScore']}\n"

    summary += "\n## Platform Ranking\n\n"
    plat_rank = sorted(platform_stats.items(), key=lambda x: x[1]["opportunityScore"], reverse=True)
    for i, (p, st) in enumerate(plat_rank, 1):
        summary += f"{i}. {p} — jobs {st['jobs']}, score {st['opportunityScore']}\n"

    primary = top10[0][0] if top10 else "wordpress developer"
    secondary = top10[1][0] if len(top10) > 1 else "webflow developer"

    summary += f"""
## Positioning Recommendation

Primary keyword: {primary}
Secondary keyword: {secondary}
Best platform/service: WordPress + Elementor maintenance and builds
Overview keywords: WordPress, Web Development, Elementor, WooCommerce, Next.js
Skill tags: WordPress, Elementor, WooCommerce, Webflow, Next.js, Supabase, GoHighLevel

## Current Verdicts

WordPress: Steady hourly and fixed demand; Elementor fixes and agency subcontract work dominate fresh posts.
Webflow: Lower volume than WordPress; speed optimization and brochure builds appear in mixed searches.
Framer: Sparse direct keyword volume; often bundled with design tool searches.
GoHighLevel: Niche but visible (marketplace apps, funnel rebuilds); verify client history on low-rated posters.
AI/Vibe Coding: POD/Next.js/Supabase stacks show up under broader dev keywords more than pure "vibe coding".
Ecommerce: Shopify and WooCommerce both active; many sub-$500 fixed storefront jobs.
Maintenance: Retainer and monthly maintenance posts continue outside peak keyword overlap.

## Important Changes

First run baseline established.
"""
    (BASE / "current-summary.md").write_text(summary)

    insights_path = BASE / "insights.md"
    if not insights_path.exists():
        insights_path.write_text(
            """# Upwork Intelligence Insights

- Baseline run started Sep 15, 2026. WordPress and core web keywords show the highest overlapping job volume in the 2h seed window.
- GoHighLevel marketplace integration work appears alongside mobile skill tags; treat as specialized GHL dev, not generic web.
"""
        )

    report = {
        "runNumber": run_number,
        "keywordsAttempted": keywords_attempted,
        "keywordsCompleted": keywords_completed,
        "newJobs": len(new_jobs),
        "totalJobs": len(all_jobs),
        "newJobRecords": [{k: v for k, v in j.items() if not k.startswith("_")} for j in new_jobs],
        "keyword_stats": keyword_stats,
        "group_stats": group_stats,
        "platform_stats": platform_stats,
        "errors": errors,
        "top10": top10,
    }
    (BASE / "last_report.json").write_text(json.dumps(report, indent=2))
    print(json.dumps({"ok": True, "newJobs": len(new_jobs), "totalJobs": len(all_jobs)}))


if __name__ == "__main__":
    main()
