#!/usr/bin/env python3
"""One-shot processor for hourly Upwork keyword run."""
import json
import re
import statistics
from datetime import datetime, timezone, timedelta
from pathlib import Path

BASE = Path(__file__).resolve().parent
SKIP_TITLE = re.compile(
    r"\b(alcohol|gambling|casino|adult|porn|crypto trading|dating)\b", re.I
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
    "GoHighLevel": ["gohighlevel", "go high level", "GHL", "highlevel"],
    "Shopify": ["shopify"],
    "WooCommerce": ["woocommerce"],
    "Shopware": ["shopware"],
    "Lovable": ["lovable"],
    "Bolt": ["bolt"],
    "v0": ["v0"],
    "Next.js": ["nextjs", "next.js"],
}


def norm_url(url):
    if not url:
        return None
    return url.split("?")[0]


def parse_budget(budget_str, job_type):
    if not budget_str:
        return None, None
    s = budget_str.replace(",", "")
    if job_type == "hourly" or "/hr" in s.lower():
        nums = re.findall(r"[\d.]+", s)
        if len(nums) >= 2:
            return None, (float(nums[0]) + float(nums[1])) / 2
        if len(nums) == 1:
            return None, float(nums[0])
        return None, None
    nums = re.findall(r"[\d.]+", s)
    if nums:
        return float(nums[0]), None
    return None, None


def parse_client_spend(spent):
    if not spent:
        return None
    nums = re.findall(r"[\d.]+", str(spent).replace(",", ""))
    return float(nums[0]) if nums else None


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


def is_high_budget(fixed, hourly):
    if fixed is not None and fixed >= 1000:
        return True
    if hourly is not None and hourly >= 40:
        return True
    return False


def job_record(job, keyword, group, window_start):
    pub = job.get("published_date") or job.get("created_date")
    if pub:
        try:
            dt = datetime.fromisoformat(pub.replace("Z", "+00:00"))
            if dt < window_start:
                return None
        except ValueError:
            pass
    url = norm_url(job.get("url"))
    if not url:
        return None
    title = job.get("title") or ""
    if SKIP_TITLE.search(title):
        return None
    client = job.get("client") or {}
    fixed, hourly = parse_budget(job.get("budget"), job.get("job_type"))
    vs = client.get("verification_status")
    return {
        "url": url,
        "title": title,
        "matchedKeyword": [keyword],
        "keywordGroup": group,
        "postedAt": pub,
        "type": job.get("job_type"),
        "budget": job.get("budget"),
        "budgetFixed": fixed,
        "budgetHourly": hourly,
        "duration": job.get("duration"),
        "proposals": job.get("proposal_count"),
        "clientCountry": client.get("country"),
        "paymentVerified": vs == "VERIFIED" if vs else None,
        "clientSpend": client.get("total_spent"),
        "clientSpendNum": parse_client_spend(client.get("total_spent")),
        "clientHireRate": None,
        "clientRating": client.get("rating"),
        "experienceLevel": job.get("experience_level"),
        "skills": job.get("skills"),
        "_fixed": fixed,
        "_hourly": hourly,
    }


def opportunity_score(jobs):
    if not jobs:
        return 0
    score = 0
    now = datetime.now(timezone.utc)
    for j in jobs:
        s = 10
        pub = j.get("postedAt")
        if pub:
            try:
                dt = datetime.fromisoformat(pub.replace("Z", "+00:00"))
                hours = (now - dt).total_seconds() / 3600
                if hours <= 1:
                    s += 25
                elif hours <= 6:
                    s += 15
                elif hours <= 24:
                    s += 8
            except ValueError:
                pass
        if j.get("_fixed") and j["_fixed"] >= 1000:
            s += 20
        elif j.get("_fixed") and j["_fixed"] >= 500:
            s += 10
        if j.get("_hourly") and j["_hourly"] >= 40:
            s += 15
        p = j.get("proposals")
        if p is not None:
            if p <= 5:
                s += 15
            elif p <= 15:
                s += 8
            elif p > 50:
                s -= 5
        if j.get("paymentVerified"):
            s += 5
        score += s
    return min(100, max(1, int(score / len(jobs))))


def keyword_stats(all_jobs):
    stats = {}
    now = datetime.now(timezone.utc)
    day_ago = now - timedelta(hours=24)
    for kw, group in KEYWORD_GROUPS.items():
        matched = [j for j in all_jobs if kw in j.get("matchedKeyword", [])]
        stats[kw] = aggregate_kw(kw, group, matched, day_ago)
    return stats


def aggregate_kw(kw, group, jobs, day_ago):
    j24 = []
    for j in jobs:
        pub = j.get("postedAt")
        if pub:
            try:
                if datetime.fromisoformat(pub.replace("Z", "+00:00")) >= day_ago:
                    j24.append(j)
            except ValueError:
                pass
    fixed_vals = [j["_fixed"] for j in jobs if j.get("_fixed")]
    hourly_vals = [j["_hourly"] for j in jobs if j.get("_hourly")]
    props = [j["proposals"] for j in jobs if j.get("proposals") is not None]
    verified = [j for j in jobs if j.get("paymentVerified")]
    spends = [j["clientSpendNum"] for j in jobs if j.get("clientSpendNum")]
    high = sum(1 for j in jobs if is_high_budget(j.get("_fixed"), j.get("_hourly")))
    n = len(jobs)
    return {
        "keyword": kw,
        "group": group,
        "totalJobs": n,
        "jobsLast24h": len(j24),
        "avgBudgetFixed": round(statistics.mean(fixed_vals), 2) if fixed_vals else None,
        "avgRateHourly": round(statistics.mean(hourly_vals), 2) if hourly_vals else None,
        "medianProposals": int(statistics.median(props)) if props else None,
        "pctVerified": round(100 * len(verified) / n, 1) if n else 0,
        "avgClientSpend": round(statistics.mean(spends), 2) if spends else None,
        "pctHighBudget": round(100 * high / n, 1) if n else 0,
        "opportunityScore": opportunity_score(jobs),
        "sampleConfidence": confidence_label(n),
    }


def group_stats(kw_stats):
    groups = {}
    for s in kw_stats.values():
        g = s["group"]
        groups.setdefault(g, []).append(s)
    out = {}
    for g, items in groups.items():
        total = sum(x["totalJobs"] for x in items)
        j24 = sum(x["jobsLast24h"] for x in items)
        scores = [x["opportunityScore"] for x in items if x["totalJobs"]]
        out[g] = {
            "group": g,
            "totalJobs": total,
            "jobsLast24h": j24,
            "avgOpportunityScore": round(statistics.mean(scores), 1) if scores else 0,
            "keywordCount": len(items),
        }
    return dict(sorted(out.items(), key=lambda x: -x[1]["jobsLast24h"]))


def platform_stats(all_jobs):
    out = {}
    for plat, patterns in PLATFORM_KEYWORDS.items():
        matched = []
        for j in all_jobs:
            text = " ".join(
                [
                    j.get("title") or "",
                    " ".join(j.get("skills") or []),
                    " ".join(j.get("matchedKeyword") or []),
                ]
            ).lower()
            if any(p.lower() in text for p in patterns):
                matched.append(j)
        fixed_vals = [j["_fixed"] for j in matched if j.get("_fixed")]
        hourly_vals = [j["_hourly"] for j in matched if j.get("_hourly")]
        props = [j["proposals"] for j in matched if j.get("proposals") is not None]
        n = len(matched)
        out[plat] = {
            "platform": plat,
            "jobs": n,
            "avgBudgetFixed": round(statistics.mean(fixed_vals), 2) if fixed_vals else None,
            "avgRateHourly": round(statistics.mean(hourly_vals), 2) if hourly_vals else None,
            "medianProposals": int(statistics.median(props)) if props else None,
            "opportunityScore": opportunity_score(matched),
            "sampleConfidence": confidence_label(n),
        }
    return out


def strip_internal(j):
    o = {k: v for k, v in j.items() if not k.startswith("_")}
    return o


def main():
    raw_path = BASE / "_raw_run.json"
    data = json.loads(raw_path.read_text())
    run_meta = data["meta"]
    window_hours = run_meta.get("windowHours", 2)
    window_start = datetime.now(timezone.utc) - timedelta(hours=window_hours)

    state_path = BASE / "state.json"
    if state_path.exists():
        state = json.loads(state_path.read_text())
        run_number = state.get("runNumber", 0) + 1
        known = set(state.get("knownJobUrls", []))
    else:
        run_number = 1
        known = set()

    jobs_by_url = {}
    keywords_attempted = len(KEYWORD_GROUPS)
    searched_ok = set()
    errors = []

    for entry in data.get("searches", []):
        kw = entry["keyword"]
        group = KEYWORD_GROUPS.get(kw, "OTHER")
        resp = entry.get("response") or {}
        if resp.get("status") == "error" or resp.get("error_code"):
            if kw not in errors:
                errors.append(kw)
            continue
        searched_ok.add(kw)
        for job in resp.get("jobs") or []:
            rec = job_record(job, kw, group, window_start)
            if not rec:
                continue
            u = rec["url"]
            if u in jobs_by_url:
                if kw not in jobs_by_url[u]["matchedKeyword"]:
                    jobs_by_url[u]["matchedKeyword"].append(kw)
            else:
                jobs_by_url[u] = rec

    for kw in KEYWORD_GROUPS:
        if kw not in searched_ok and kw not in errors:
            errors.append(kw)

    keywords_completed = len(searched_ok)

    all_jobs = list(jobs_by_url.values())
    new_jobs = [j for j in all_jobs if j["url"] not in known]

    jobs_path = BASE / "jobs.jsonl"
    with jobs_path.open("a") as f:
        for j in new_jobs:
            f.write(json.dumps(strip_internal(j)) + "\n")

    # reload all jobs for stats from file + new
    all_stored = []
    if jobs_path.exists():
        for line in jobs_path.read_text().splitlines():
            if line.strip():
                o = json.loads(line)
                o["_fixed"] = o.get("budgetFixed")
                o["_hourly"] = o.get("budgetHourly")
                if o["_fixed"] is None and o.get("budget"):
                    o["_fixed"], o["_hourly"] = parse_budget(o["budget"], o.get("type"))
                all_stored.append(o)

    kw_s = keyword_stats(all_stored)
    g_s = group_stats(kw_s)
    p_s = platform_stats(all_stored)

    (BASE / "keyword-stats.json").write_text(json.dumps(kw_s, indent=2))
    (BASE / "group-stats.json").write_text(json.dumps(g_s, indent=2))
    (BASE / "platform-stats.json").write_text(json.dumps(p_s, indent=2))

    total_jobs = len(all_stored)
    known.update(j["url"] for j in new_jobs)
    last_run = datetime.now(timezone.utc).isoformat()
    state_out = {
        "lastRunAt": last_run,
        "runNumber": run_number,
        "totalJobs": total_jobs,
        "knownJobUrls": sorted(known),
        "lastInsightRefresh": last_run if run_number == 1 else (
            json.loads(state_path.read_text()).get("lastInsightRefresh") if state_path.exists() else last_run
        ),
    }
    (BASE / "state.json").write_text(json.dumps(state_out, indent=2))

    top3 = sorted(kw_s.values(), key=lambda x: -x["jobsLast24h"])[:3]
    log = {
        "timestamp": last_run,
        "runNumber": run_number,
        "keywordsAttempted": keywords_attempted,
        "keywordsCompleted": keywords_completed,
        "newJobs": len(new_jobs),
        "totalJobs": total_jobs,
        "top3Keywords": [t["keyword"] for t in top3],
        "errors": errors,
    }
    with (BASE / "run-log.jsonl").open("a") as f:
        f.write(json.dumps(log) + "\n")

    top10 = sorted(kw_s.values(), key=lambda x: -x["opportunityScore"])[:10]
    summary = build_summary(run_number, keywords_attempted, keywords_completed, total_jobs, top10, g_s, p_s)
    (BASE / "current-summary.md").write_text(summary)

    if run_number == 1:
        insights = """# Upwork Intelligence Insights

## Initial baseline (Run 1)

- Tracking started with full keyword sweep across web dev, WordPress, Webflow/Framer, AI/vibe coding, GHL, ecommerce, maintenance, and CRO terms.
- Opportunity scores will stabilize after several runs as sample sizes grow.
"""
        (BASE / "insights.md").write_text(insights)

    out = {
        "runNumber": run_number,
        "keywordsAttempted": keywords_attempted,
        "keywordsCompleted": keywords_completed,
        "newJobs": [strip_internal(j) for j in new_jobs],
        "totalJobs": total_jobs,
        "top10": top10,
        "groups": list(g_s.values())[:5],
        "platforms": p_s,
        "errors": errors,
        "all_new_count": len(new_jobs),
    }
    (BASE / "_run_output.json").write_text(json.dumps(out, indent=2, default=str))
    print(json.dumps({"ok": True, "run": run_number, "new": len(new_jobs), "total": total_jobs}))


def build_summary(run_number, attempted, completed, total, top10, groups, platforms):
    lines = [
        "# Upwork Market Intelligence",
        "",
        f"Last updated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        f"Run: {run_number}",
        f"Total jobs tracked: {total}",
        f"Keywords attempted: {attempted}",
        f"Keywords completed: {completed}",
        "",
        "## Top Opportunities",
        "",
    ]
    for t in top10:
        lines.append(
            f"- **{t['keyword']}** — score {t['opportunityScore']} ({t['sampleConfidence']}); "
            f"24h: {t['jobsLast24h']}; total: {t['totalJobs']}; "
            f"avg fixed: {t['avgBudgetFixed']}; avg hourly: {t['avgRateHourly']}; "
            f"median proposals: {t['medianProposals']}"
        )
    lines.extend(["", "## Strongest Groups", ""])
    for g in list(groups.values())[:5]:
        lines.append(f"- {g['group']}: {g['jobsLast24h']} jobs (24h), score avg {g['avgOpportunityScore']}")
    lines.extend(["", "## Platform Ranking", ""])
    plat_sorted = sorted(platforms.values(), key=lambda x: -x["jobs"])
    for p in plat_sorted:
        lines.append(f"- {p['platform']}: {p['jobs']} jobs, score {p['opportunityScore']}")
    lines.extend(
        [
            "",
            "## Positioning Recommendation",
            "",
            "Primary keyword: (see top opportunities)",
            "Secondary keyword: full stack developer",
            "Best platform/service: WordPress + Next.js hybrid positioning",
            "Overview keywords: WordPress, Webflow, Next.js, AI-assisted development",
            "Skill tags: WordPress, Elementor, Webflow, React, Next.js, Claude Code",
            "",
            "## Current Verdicts",
            "",
            "WordPress: Steady volume; mix of low and premium budgets.",
            "Webflow: Maintenance and landing-page builds recurring.",
            "Framer: Smaller but specialized demand.",
            "GoHighLevel: Agency funnel/stack integrations.",
            "AI/Vibe Coding: Growing Claude Code and AI builder mentions.",
            "Ecommerce: Shopify and WooCommerce both active.",
            "Maintenance: Retainer-style Webflow/WordPress support posts appear regularly.",
            "",
            "## Important Changes",
            "",
            "First run: baseline established.",
        ]
    )
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    main()
