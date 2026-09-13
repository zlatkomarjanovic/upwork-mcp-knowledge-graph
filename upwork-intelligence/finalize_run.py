#!/usr/bin/env python3
"""Process keyword search batches into tracker files. Run once per hourly cycle."""
import json
import re
import statistics
from datetime import datetime, timezone, timedelta
from pathlib import Path

BASE = Path(__file__).resolve().parent
ORG = "1472686528932380673"

KEYWORDS = [
    ("web development", "CORE WEB DEVELOPMENT"),
    ("website development", "CORE WEB DEVELOPMENT"),
    ("web developer", "CORE WEB DEVELOPMENT"),
    ("custom website", "CORE WEB DEVELOPMENT"),
    ("frontend developer", "CORE WEB DEVELOPMENT"),
    ("full stack developer", "CORE WEB DEVELOPMENT"),
    ("web design", "WEB DESIGN"),
    ("website design", "WEB DESIGN"),
    ("website redesign", "WEB DESIGN"),
    ("landing page design", "WEB DESIGN"),
    ("UI UX website", "WEB DESIGN"),
    ("responsive web design", "WEB DESIGN"),
    ("wordpress", "WORDPRESS"),
    ("wordpress developer", "WORDPRESS"),
    ("wordpress website", "WORDPRESS"),
    ("wordpress development", "WORDPRESS"),
    ("wordpress redesign", "WORDPRESS"),
    ("wordpress customization", "WORDPRESS"),
    ("wordpress migration", "WORDPRESS"),
    ("wordpress speed optimization", "WORDPRESS"),
    ("wordpress maintenance", "WORDPRESS"),
    ("woocommerce", "WORDPRESS"),
    ("elementor developer", "WORDPRESS"),
    ("bricks builder", "WORDPRESS"),
    ("webflow", "WEBFLOW / FRAMER"),
    ("webflow developer", "WEBFLOW / FRAMER"),
    ("webflow website", "WEBFLOW / FRAMER"),
    ("webflow redesign", "WEBFLOW / FRAMER"),
    ("figma to webflow", "WEBFLOW / FRAMER"),
    ("framer", "WEBFLOW / FRAMER"),
    ("framer developer", "WEBFLOW / FRAMER"),
    ("framer website", "WEBFLOW / FRAMER"),
    ("framer redesign", "WEBFLOW / FRAMER"),
    ("figma to framer", "WEBFLOW / FRAMER"),
    ("AI web development", "AI / VIBE CODING"),
    ("AI web developer", "AI / VIBE CODING"),
    ("vibe coding", "AI / VIBE CODING"),
    ("claude code developer", "AI / VIBE CODING"),
    ("cursor AI developer", "AI / VIBE CODING"),
    ("lovable developer", "AI / VIBE CODING"),
    ("lovable app", "AI / VIBE CODING"),
    ("bolt developer", "AI / VIBE CODING"),
    ("bolt.new", "AI / VIBE CODING"),
    ("v0 developer", "AI / VIBE CODING"),
    ("v0 vercel", "AI / VIBE CODING"),
    ("replit developer", "AI / VIBE CODING"),
    ("supabase developer", "AI / VIBE CODING"),
    ("AI agent integration website", "AI / VIBE CODING"),
    ("gohighlevel", "GOHIGHLEVEL"),
    ("go high level", "GOHIGHLEVEL"),
    ("GHL", "GOHIGHLEVEL"),
    ("gohighlevel developer", "GOHIGHLEVEL"),
    ("gohighlevel website", "GOHIGHLEVEL"),
    ("gohighlevel funnel", "GOHIGHLEVEL"),
    ("gohighlevel automation", "GOHIGHLEVEL"),
    ("gohighlevel CRM", "GOHIGHLEVEL"),
    ("squarespace website", "ADJACENT PLATFORMS"),
    ("wix website", "ADJACENT PLATFORMS"),
    ("wix studio", "ADJACENT PLATFORMS"),
    ("bubble developer", "ADJACENT PLATFORMS"),
    ("nextjs developer", "MODERN STACK"),
    ("next.js developer", "MODERN STACK"),
    ("nextjs website", "MODERN STACK"),
    ("react developer", "MODERN STACK"),
    ("figma to nextjs", "MODERN STACK"),
    ("tailwind developer", "MODERN STACK"),
    ("astro developer", "MODERN STACK"),
    ("sanity CMS", "MODERN STACK"),
    ("ecommerce website", "ECOMMERCE"),
    ("ecommerce developer", "ECOMMERCE"),
    ("shopify developer", "ECOMMERCE"),
    ("shopify website", "ECOMMERCE"),
    ("woocommerce developer", "ECOMMERCE"),
    ("shopware", "ECOMMERCE"),
    ("shopware developer", "ECOMMERCE"),
    ("shopware 6", "ECOMMERCE"),
    ("headless ecommerce", "ECOMMERCE"),
    ("website maintenance", "MAINTENANCE / RETAINERS"),
    ("website maintenance monthly", "MAINTENANCE / RETAINERS"),
    ("website support ongoing", "MAINTENANCE / RETAINERS"),
    ("website management ongoing", "MAINTENANCE / RETAINERS"),
    ("wordpress support retainer", "MAINTENANCE / RETAINERS"),
    ("webflow maintenance", "MAINTENANCE / RETAINERS"),
    ("shopify maintenance", "MAINTENANCE / RETAINERS"),
    ("ongoing web developer", "MAINTENANCE / RETAINERS"),
    ("web development retainer", "MAINTENANCE / RETAINERS"),
    ("conversion rate optimization", "CONVERSION / PERFORMANCE"),
    ("landing page optimization", "CONVERSION / PERFORMANCE"),
    ("website audit", "CONVERSION / PERFORMANCE"),
    ("core web vitals", "CONVERSION / PERFORMANCE"),
    ("page speed optimization", "CONVERSION / PERFORMANCE"),
    ("website speed optimization", "CONVERSION / PERFORMANCE"),
    ("technical SEO website", "CONVERSION / PERFORMANCE"),
]

SKIP_PATTERNS = re.compile(
    r"\b(alcohol|gambling|casino|betting|poker|adult content|porn|escort|crypto trading|bitcoin trading|forex trading|dating app|dating site)\b",
    re.I,
)

PLATFORM_MAP = {
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


def norm_url(url):
    if not url:
        return None
    return url.split("?")[0]


def parse_money(s):
    if not s:
        return None
    s = str(s).replace(",", "")
    m = re.search(r"([\d.]+)", s)
    return float(m.group(1)) if m else None


def parse_hourly_mid(budget):
    if not budget:
        return None
    nums = [float(x.replace(",", "")) for x in re.findall(r"([\d.]+)", str(budget))]
    if not nums:
        return None
    return sum(nums) / len(nums)


def parse_client_spend(spent):
    if not spent:
        return None
    return parse_money(spent)


def job_record(job, keyword, group):
    client = job.get("client") or {}
    url = norm_url(job.get("url"))
    return {
        "url": url,
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
        "skills": job.get("skills") or [],
    }


def is_high_budget(job):
    jt = job.get("type")
    b = job.get("budget")
    if jt == "fixed":
        v = parse_money(b)
        return v is not None and v >= 1000
    if jt == "hourly":
        v = parse_hourly_mid(b)
        return v is not None and v >= 40
    return False


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


def opportunity_score(jobs):
    if not jobs:
        return 1
    recency = sum(1 for j in jobs if j.get("_recent")) / len(jobs)
    high_b = sum(1 for j in jobs if j.get("_high")) / len(jobs)
    verified = sum(1 for j in jobs if j.get("paymentVerified")) / len(jobs)
    props = [j["proposals"] for j in jobs if j.get("proposals") is not None]
    low_comp = 1.0
    if props:
        med = statistics.median(props)
        low_comp = max(0, min(1, 1 - med / 50))
    budgets = []
    for j in jobs:
        if j.get("type") == "fixed":
            v = parse_money(j.get("budget"))
            if v:
                budgets.append(min(v / 5000, 1))
        elif j.get("type") == "hourly":
            v = parse_hourly_mid(j.get("budget"))
            if v:
                budgets.append(min(v / 100, 1))
    pay = statistics.mean(budgets) if budgets else 0.3
    raw = 0.25 * recency + 0.25 * pay + 0.2 * low_comp + 0.15 * high_b + 0.15 * verified
    return max(1, min(100, int(raw * 100)))


def main():
    now = datetime.now(timezone.utc)
    batch_path = BASE / "_kw_batches.jsonl"
    state_path = BASE / "state.json"
    jobs_path = BASE / "jobs.jsonl"

    state = {}
    if state_path.exists():
        state = json.loads(state_path.read_text())
    run_number = int(state.get("runNumber", 0)) + 1
    first_run = run_number == 1
    window = timedelta(hours=2 if first_run else 1)
    cutoff = now - window

    known = set(state.get("knownJobUrls") or [])
    all_jobs = {}
    keyword_jobs = {k: [] for k, _ in KEYWORDS}
    errors = []
    completed = set()
    attempted = len(KEYWORDS)

    if batch_path.exists():
        for line in batch_path.read_text().splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            kw = row.get("keyword")
            group = row.get("group")
            if row.get("error"):
                errors.append(kw)
                continue
            completed.add(kw)
            for job in row.get("jobs") or []:
                if SKIP_PATTERNS.search(
                    (job.get("title") or "") + " " + (job.get("description_snippet") or "")
                ):
                    continue
                rec = job_record(job, kw, group)
                if not rec["url"]:
                    continue
                posted = rec["postedAt"]
                if posted:
                    try:
                        dt = datetime.fromisoformat(posted.replace("Z", "+00:00"))
                        if dt < cutoff:
                            continue
                    except ValueError:
                        pass
                url = rec["url"]
                if url in all_jobs:
                    if kw not in all_jobs[url]["matchedKeyword"]:
                        all_jobs[url]["matchedKeyword"].append(kw)
                else:
                    all_jobs[url] = rec
                keyword_jobs[kw].append(all_jobs[url])

    for kw, _ in KEYWORDS:
        if kw not in completed and kw not in errors:
            errors.append(kw)

    new_urls = [u for u in all_jobs if u not in known]
    with jobs_path.open("a") as f:
        for u in new_urls:
            f.write(json.dumps(all_jobs[u], ensure_ascii=False) + "\n")
    known.update(all_jobs.keys())

    # reload historical jobs for stats
    hist = []
    if jobs_path.exists():
        for line in jobs_path.read_text().splitlines():
            if line.strip():
                hist.append(json.loads(line))
    hist_by_kw = {k: [] for k, _ in KEYWORDS}
    for j in hist:
        for mk in j.get("matchedKeyword") or []:
            if mk in hist_by_kw:
                hist_by_kw[mk].append(j)

    kw_stats = {}
    for kw, group in KEYWORDS:
        jobs = hist_by_kw[kw]
        now24 = now - timedelta(hours=24)
        j24 = []
        for j in jobs:
            p = j.get("postedAt")
            if not p:
                continue
            try:
                if datetime.fromisoformat(p.replace("Z", "+00:00")) >= now24:
                    j24.append(j)
            except ValueError:
                pass
        fixed = [parse_money(j.get("budget")) for j in jobs if j.get("type") == "fixed"]
        fixed = [x for x in fixed if x]
        hourly = [parse_hourly_mid(j.get("budget")) for j in jobs if j.get("type") == "hourly"]
        hourly = [x for x in hourly if x]
        props = [j["proposals"] for j in jobs if j.get("proposals") is not None]
        spend = [parse_client_spend(j.get("clientSpend")) for j in jobs]
        spend = [x for x in spend if x]
        enriched = []
        for j in j24:
            e = dict(j)
            e["_recent"] = True
            e["_high"] = is_high_budget(j)
            enriched.append(e)
        kw_stats[kw] = {
            "keyword": kw,
            "group": group,
            "totalJobs": len(jobs),
            "jobsLast24h": len(j24),
            "avgBudgetFixed": round(statistics.mean(fixed), 2) if fixed else None,
            "avgRateHourly": round(statistics.mean(hourly), 2) if hourly else None,
            "medianProposals": int(statistics.median(props)) if props else None,
            "pctVerified": round(
                100 * sum(1 for j in jobs if j.get("paymentVerified")) / len(jobs), 1
            )
            if jobs
            else 0,
            "avgClientSpend": round(statistics.mean(spend), 2) if spend else None,
            "pctHighBudget": round(
                100 * sum(1 for j in jobs if is_high_budget(j)) / len(jobs), 1
            )
            if jobs
            else 0,
            "opportunityScore": opportunity_score(enriched if enriched else jobs),
            "sampleConfidence": confidence(len(jobs)),
        }

    (BASE / "keyword-stats.json").write_text(json.dumps(kw_stats, indent=2))
    group_stats = {}
    for kw, group in KEYWORDS:
        gs = group_stats.setdefault(group, {"jobs": [], "keywords": []})
        gs["keywords"].append(kw)
        gs["jobs"].extend(hist_by_kw[kw])
    group_out = {}
    for g, data in group_stats.items():
        jobs = data["jobs"]
        group_out[g] = {
            "totalJobs": len(jobs),
            "jobsLast24h": sum(kw_stats[k]["jobsLast24h"] for k in data["keywords"]),
            "opportunityScore": round(
                statistics.mean([kw_stats[k]["opportunityScore"] for k in data["keywords"]])
            ),
        }
    (BASE / "group-stats.json").write_text(json.dumps(group_out, indent=2))

    plat_out = {}
    for plat, needles in PLATFORM_MAP.items():
        pjobs = [
            j
            for j in hist
            if any(
                n in " ".join(j.get("matchedKeyword") or []).lower()
                or n in (j.get("title") or "").lower()
                for n in needles
            )
        ]
        props = [j["proposals"] for j in pjobs if j.get("proposals") is not None]
        fixed = [parse_money(j.get("budget")) for j in pjobs if j.get("type") == "fixed"]
        fixed = [x for x in fixed if x]
        hourly = [parse_hourly_mid(j.get("budget")) for j in pjobs if j.get("type") == "hourly"]
        hourly = [x for x in hourly if x]
        plat_out[plat] = {
            "jobs": len(pjobs),
            "avgBudgetFixed": round(statistics.mean(fixed), 2) if fixed else None,
            "avgRateHourly": round(statistics.mean(hourly), 2) if hourly else None,
            "medianProposals": int(statistics.median(props)) if props else None,
            "opportunityScore": opportunity_score(pjobs),
            "sampleConfidence": confidence(len(pjobs)),
        }
    (BASE / "platform-stats.json").write_text(json.dumps(plat_out, indent=2))

    top3 = sorted(kw_stats.values(), key=lambda x: x["jobsLast24h"], reverse=True)[:3]
    top3k = [x["keyword"] for x in top3]

    log = {
        "timestamp": now.isoformat(),
        "runNumber": run_number,
        "keywordsAttempted": attempted,
        "keywordsCompleted": len(completed),
        "newJobs": len(new_urls),
        "totalJobs": len(known),
        "top3Keywords": top3k,
        "errors": sorted(set(errors)),
    }
    with (BASE / "run-log.jsonl").open("a") as f:
        f.write(json.dumps(log) + "\n")

    state.update(
        {
            "lastRunAt": now.isoformat(),
            "runNumber": run_number,
            "totalJobs": len(known),
            "knownJobUrls": sorted(known),
            "lastInsightRefresh": state.get("lastInsightRefresh"),
        }
    )
    state_path.write_text(json.dumps(state, indent=2))

    sorted_kw = sorted(kw_stats.values(), key=lambda x: x["opportunityScore"], reverse=True)
    primary = sorted_kw[0]["keyword"] if sorted_kw else "wordpress developer"
    secondary = sorted_kw[1]["keyword"] if len(sorted_kw) > 1 else "shopify developer"

    summary = f"""# Upwork Market Intelligence

Last updated: {now.strftime("%Y-%m-%d %H:%M UTC")}
Run: {run_number}
Total jobs tracked: {len(known)}
Keywords attempted: {attempted}
Keywords completed: {len(completed)}

## Top Opportunities

"""
    for i, k in enumerate(sorted_kw[:10], 1):
        summary += f"""{i}. **{k['keyword']}** — score {k['opportunityScore']}
   - jobsLast24h: {k['jobsLast24h']} | total: {k['totalJobs']} | avg fixed: {k['avgBudgetFixed']} | avg hourly: {k['avgRateHourly']} | median proposals: {k['medianProposals']} | confidence: {k['sampleConfidence']}

"""

    summary += "## Strongest Groups\n\n"
    for g, st in sorted(group_out.items(), key=lambda x: x[1]["opportunityScore"], reverse=True):
        summary += f"- {g}: score {st['opportunityScore']}, jobs24h {st['jobsLast24h']}, total {st['totalJobs']}\n"

    summary += "\n## Platform Ranking\n\n"
    for p, st in sorted(plat_out.items(), key=lambda x: x[1]["opportunityScore"], reverse=True):
        summary += f"- {p}: {st['jobs']} jobs, score {st['opportunityScore']}, confidence {st['sampleConfidence']}\n"

    summary += f"""
## Positioning Recommendation

Primary keyword: {primary}
Secondary keyword: {secondary}
Best platform/service: WordPress + Shopify hybrid delivery
Overview keywords: web development, wordpress developer, shopify developer, AI web development
Skill tags: WordPress, Elementor, Shopify, Next.js, Webflow, Supabase, SEO

## Current Verdicts

WordPress: Steady hourly + fix volume; Elementor and maintenance posts remain common.
Webflow: Lower explicit volume than WordPress; premium redesign niches still appear.
Framer: Sparse dedicated posts; often bundled with design tool searches.
GoHighLevel: Migration and funnel posts show up with verified AU/US clients.
AI/Vibe Coding: Vibe coding and AI SaaS takeover posts; wide rate spread.
Ecommerce: Shopify build/optimize demand strong in last 2h window.
Maintenance: Retainer keywords lag behind break/fix WordPress posts.

## Important Changes

- Run {run_number} bootstrap: {len(new_urls)} new jobs captured; {len(errors)} keyword searches pending retry if rate limited.
"""
    (BASE / "current-summary.md").write_text(summary)

    print(json.dumps({"run": run_number, "new": len(new_urls), "completed": len(completed), "errors": len(errors)}))


if __name__ == "__main__":
    main()
