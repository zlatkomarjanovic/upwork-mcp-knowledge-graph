#!/usr/bin/env python3
"""Process search batch results into jobs.jsonl and stats."""
import json
import re
import statistics
from datetime import datetime, timezone, timedelta
from pathlib import Path

BASE = Path(__file__).resolve().parent
STATE_FILE = BASE / "state.json"
JOBS_FILE = BASE / "jobs.jsonl"
RUN_LOG = BASE / "run-log.jsonl"
BATCH_FILE = BASE / "_search_batches.jsonl"
KEYWORD_STATS = BASE / "keyword-stats.json"
GROUP_STATS = BASE / "group-stats.json"
PLATFORM_STATS = BASE / "platform-stats.json"
SUMMARY = BASE / "current-summary.md"
INSIGHTS = BASE / "insights.md"

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

ALL_KEYWORDS = list(KEYWORD_GROUPS.keys())

SKIP_PATTERNS = re.compile(
    r"\b(crypto|bitcoin|gambling|casino|poker|dating|adult|escort|alcohol|brewery|distillery)\b",
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
    s = str(s).replace(",", "")
    m = re.search(r"([\d.]+)", s)
    return float(m.group(1)) if m else None


def parse_hourly_rate(budget: str):
    if not budget or "hr" not in budget.lower():
        return None
    parts = re.findall(r"([\d.]+)", budget.replace(",", ""))
    if not parts:
        return None
    vals = [float(p) for p in parts]
    return sum(vals) / len(vals)


def parse_client_spend(spend: str):
    if not spend:
        return None
    return parse_money(spend)


def job_from_raw(j, keyword, group):
    url = j.get("url") or ""
    if not url:
        return None
    title = j.get("title") or ""
    desc = j.get("description_snippet") or ""
    if SKIP_PATTERNS.search(title + " " + desc):
        return None
    client = j.get("client") or {}
    budget = j.get("budget")
    return {
        "url": norm_url(url),
        "title": title,
        "matchedKeyword": [keyword],
        "keywordGroup": group,
        "postedAt": j.get("published_date") or j.get("created_date"),
        "type": j.get("job_type"),
        "budget": budget,
        "duration": j.get("duration"),
        "proposals": j.get("proposal_count")
        or {
            "Fewer than 5": 2,
            "5 to 10": 7,
            "10 to 15": 12,
            "15 to 20": 17,
            "20 to 50": 35,
            "50+": 55,
        }.get(j.get("proposals_tier")),
        "clientCountry": client.get("country"),
        "paymentVerified": client.get("verification_status") == "VERIFIED",
        "clientSpend": client.get("total_spent"),
        "clientHireRate": None,
        "clientRating": client.get("rating"),
        "experienceLevel": j.get("experience_level"),
        "skills": j.get("skills"),
    }


def load_jobs():
    jobs = {}
    if JOBS_FILE.exists():
        for line in JOBS_FILE.read_text().splitlines():
            if not line.strip():
                continue
            o = json.loads(line)
            jobs[o["url"]] = o
    return jobs


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


def is_high_budget(job):
    if job.get("type") == "fixed":
        b = parse_money(job.get("budget"))
        return b is not None and b >= 1000
    if job.get("type") == "hourly":
        r = parse_hourly_rate(job.get("budget") or "")
        return r is not None and r >= 40
    return False


def opportunity_score(jobs_list):
    if not jobs_list:
        return 1
    recency = sum(
        1 for j in jobs_list if j.get("_hours_old") is not None and j["_hours_old"] <= 24
    ) / len(jobs_list)
    props = [j.get("proposals") for j in jobs_list if j.get("proposals") is not None]
    med_p = statistics.median(props) if props else 50
    comp = max(0, 1 - min(med_p, 50) / 50)
    high_b = sum(1 for j in jobs_list if is_high_budget(j)) / len(jobs_list)
    verified = sum(1 for j in jobs_list if j.get("paymentVerified")) / len(jobs_list)
    raw = 0.35 * recency + 0.25 * comp + 0.2 * high_b + 0.2 * verified
    return max(1, min(100, int(raw * 100)))


def main():
    now = datetime.now(timezone.utc)
    state = {}
    if STATE_FILE.exists():
        state = json.loads(STATE_FILE.read_text())
    run_number = int(state.get("runNumber", 0)) + 1
    first_run = run_number == 1
    window = timedelta(hours=2 if first_run else 1)
    cutoff = now - window

    known = set(state.get("knownJobUrls", []))
    jobs = load_jobs()

    attempted = len(ALL_KEYWORDS)
    completed = []
    errors = []
    new_this_run = []

    sr_file = BASE / "search_responses.json"
    if (not BATCH_FILE.exists() or BATCH_FILE.stat().st_size == 0) and sr_file.exists():
        lines = []
        paired = json.loads(sr_file.read_text())
        for entry in paired:
            kw = entry.get("keyword")
            resp = entry.get("response") or {}
            job_list = resp.get("jobs") or []
            lines.append(json.dumps({"keyword": kw, "jobs": job_list}, ensure_ascii=False))
        if lines:
            BATCH_FILE.write_text("\n".join(lines) + "\n")

    if BATCH_FILE.exists():
        for line in BATCH_FILE.read_text().splitlines():
            if not line.strip():
                continue
            batch = json.loads(line)
            kw = batch.get("keyword")
            if batch.get("error"):
                errors.append(kw)
                continue
            completed.append(kw)
            group = KEYWORD_GROUPS.get(kw, "OTHER")
            for j in batch.get("jobs", []):
                job = job_from_raw(j, kw, group)
                if not job:
                    continue
                posted = job.get("postedAt")
                if posted:
                    try:
                        pd = datetime.fromisoformat(posted.replace("Z", "+00:00"))
                        if pd < cutoff:
                            continue
                        job["_hours_old"] = (now - pd).total_seconds() / 3600
                    except ValueError:
                        pass
                url = job["url"]
                if url in jobs:
                    mk = jobs[url].setdefault("matchedKeyword", [])
                    if kw not in mk:
                        mk.append(kw)
                else:
                    jobs[url] = job
                    if url not in known:
                        new_this_run.append(job)
                        known.add(url)

    with JOBS_FILE.open("w") as f:
        for o in jobs.values():
            o.pop("_hours_old", None)
            f.write(json.dumps(o, ensure_ascii=False) + "\n")

    all_jobs = list(jobs.values())
    cutoff24 = now - timedelta(hours=24)

    def jobs_for_keyword(kw):
        return [j for j in all_jobs if kw in j.get("matchedKeyword", [])]

    keyword_stats = {}
    for kw in ALL_KEYWORDS:
        jl = jobs_for_keyword(kw)
        fixed = [parse_money(j.get("budget")) for j in jl if j.get("type") == "fixed"]
        fixed = [x for x in fixed if x is not None]
        hourly = [parse_hourly_rate(j.get("budget") or "") for j in jl if j.get("type") == "hourly"]
        hourly = [x for x in hourly if x is not None]
        props = [j.get("proposals") for j in jl if j.get("proposals") is not None]
        spends = [parse_client_spend(j.get("clientSpend")) for j in jl]
        spends = [x for x in spends if x is not None]
        j24 = []
        for j in jl:
            p = j.get("postedAt")
            if not p:
                continue
            try:
                if datetime.fromisoformat(p.replace("Z", "+00:00")) >= cutoff24:
                    j24.append(j)
            except ValueError:
                pass
        for j in jl:
            if j.get("postedAt"):
                try:
                    j["_hours_old"] = (
                        now - datetime.fromisoformat(j["postedAt"].replace("Z", "+00:00"))
                    ).total_seconds() / 3600
                except ValueError:
                    j["_hours_old"] = 48
        keyword_stats[kw] = {
            "totalJobs": len(jl),
            "jobsLast24h": len(j24),
            "avgBudgetFixed": round(statistics.mean(fixed), 2) if fixed else None,
            "avgRateHourly": round(statistics.mean(hourly), 2) if hourly else None,
            "medianProposals": int(statistics.median(props)) if props else None,
            "pctVerified": round(100 * sum(1 for j in jl if j.get("paymentVerified")) / len(jl), 1)
            if jl
            else 0,
            "avgClientSpend": round(statistics.mean(spends), 2) if spends else None,
            "pctHighBudget": round(100 * sum(1 for j in jl if is_high_budget(j)) / len(jl), 1)
            if jl
            else 0,
            "opportunityScore": opportunity_score(jl),
            "sampleConfidence": confidence(len(jl)),
        }
        for j in jl:
            j.pop("_hours_old", None)

    group_stats = {}
    for g in set(KEYWORD_GROUPS.values()):
        kws = [k for k, v in KEYWORD_GROUPS.items() if v == g]
        jl = [j for j in all_jobs if any(k in j.get("matchedKeyword", []) for k in kws)]
        group_stats[g] = {
            "totalJobs": len(jl),
            "jobsLast24h": sum(keyword_stats[k]["jobsLast24h"] for k in kws),
            "opportunityScore": opportunity_score(jl) if jl else 1,
            "sampleConfidence": confidence(len(jl)),
        }

    platform_stats = {}
    for pname, patterns in PLATFORM_KEYWORDS.items():
        jl = [
            j
            for j in all_jobs
            if any(p.lower() in " ".join(j.get("matchedKeyword", [])).lower() for p in patterns)
            or any(
                (s or "").lower().find(p.replace(".", "")) >= 0
                for s in (j.get("skills") or [])
                for p in patterns
            )
        ]
        fixed = [parse_money(j.get("budget")) for j in jl if j.get("type") == "fixed"]
        fixed = [x for x in fixed if x is not None]
        hourly = [parse_hourly_rate(j.get("budget") or "") for j in jl if j.get("type") == "hourly"]
        hourly = [x for x in hourly if x is not None]
        props = [j.get("proposals") for j in jl if j.get("proposals") is not None]
        platform_stats[pname] = {
            "jobs": len(jl),
            "avgBudgetFixed": round(statistics.mean(fixed), 2) if fixed else None,
            "avgRateHourly": round(statistics.mean(hourly), 2) if hourly else None,
            "medianProposals": int(statistics.median(props)) if props else None,
            "opportunityScore": opportunity_score(jl) if jl else 1,
            "sampleConfidence": confidence(len(jl)),
        }

    KEYWORD_STATS.write_text(json.dumps(keyword_stats, indent=2))
    GROUP_STATS.write_text(json.dumps(group_stats, indent=2))
    PLATFORM_STATS.write_text(json.dumps(platform_stats, indent=2))

    top_kw = sorted(keyword_stats.items(), key=lambda x: x[1]["opportunityScore"], reverse=True)[:10]
    top3 = [k for k, _ in top_kw[:3]]

    log = {
        "timestamp": now.isoformat(),
        "runNumber": run_number,
        "keywordsAttempted": attempted,
        "keywordsCompleted": len(completed),
        "newJobs": len(new_this_run),
        "totalJobs": len(jobs),
        "top3Keywords": top3,
        "errors": errors,
    }
    with RUN_LOG.open("a") as f:
        f.write(json.dumps(log) + "\n")

    state = {
        "lastRunAt": now.isoformat(),
        "runNumber": run_number,
        "totalJobs": len(jobs),
        "knownJobUrls": sorted(known),
        "lastInsightRefresh": state.get("lastInsightRefresh"),
    }
    STATE_FILE.write_text(json.dumps(state, indent=2))

    lines = [
        "# Upwork Market Intelligence",
        "",
        f"Last updated: {now.strftime('%Y-%m-%d %H:%M UTC')}",
        f"Run: {run_number}",
        f"Total jobs tracked: {len(jobs)}",
        f"Keywords attempted: {attempted}",
        f"Keywords completed: {len(completed)}",
        "",
        "## Top Opportunities",
        "",
    ]
    for k, s in top_kw:
        lines.append(
            f"- **{k}** — score {s['opportunityScore']} ({s['sampleConfidence']}) | "
            f"24h: {s['jobsLast24h']} | total: {s['totalJobs']} | "
            f"avg fixed: {s['avgBudgetFixed']} | avg hourly: {s['avgRateHourly']} | "
            f"median proposals: {s['medianProposals']}"
        )
    lines.extend(["", "## Strongest Groups", ""])
    for g, s in sorted(group_stats.items(), key=lambda x: x[1]["opportunityScore"], reverse=True):
        lines.append(f"- {g}: score {s['opportunityScore']} ({s['sampleConfidence']}), jobs {s['totalJobs']}")
    lines.extend(["", "## Platform Ranking", ""])
    for p, s in sorted(platform_stats.items(), key=lambda x: x[1]["opportunityScore"], reverse=True):
        lines.append(f"- {p}: score {s['opportunityScore']}, jobs {s['jobs']}")
    primary = top_kw[0][0] if top_kw else "wordpress developer"
    secondary = top_kw[1][0] if len(top_kw) > 1 else "webflow developer"
    lines.extend(
        [
            "",
            "## Positioning Recommendation",
            "",
            f"Primary keyword: {primary}",
            f"Secondary keyword: {secondary}",
            "Best platform/service: WordPress + Elementor fixes / Next.js + Supabase SaaS",
            "Overview keywords: WordPress, Web Development, Next.js, Supabase, Webflow",
            "Skill tags: WordPress, Elementor, React, TypeScript, Supabase, Shopify, Webflow",
            "",
            "## Current Verdicts",
            "",
            "WordPress: High volume, mixed budgets; Elementor fix jobs posting hourly.",
            "Webflow: Steady expert CMS builds; Germany B2B launch active.",
            "Framer: Low volume but cleaner hourly builds.",
            "GoHighLevel: Niche; often paired with WordPress rebuilds.",
            "AI/Vibe Coding: Supabase/React SaaS and production-hardening roles.",
            "Ecommerce: Shopify brand launches and WooCommerce page fixes.",
            "Maintenance: Malware removal and Elementor optimization retainers.",
            "",
            "## Important Changes",
            "",
            "First baseline run." if first_run else "See run log for deltas.",
        ]
    )
    SUMMARY.write_text("\n".join(lines) + "\n")

    if first_run and not INSIGHTS.exists():
        INSIGHTS.write_text(
            "# Durable insights\n\n"
            "- WordPress + Elementor small fixes and upgrades dominate fresh postings in this window.\n"
            "- Full-stack Supabase/React contract roles show higher hourly bands than generic web dev.\n"
            "- Webflow senior CMS launches appear sporadically with expert hourly rates.\n"
        )

    print(json.dumps({"run": run_number, "new": len(new_this_run), "total": len(jobs), "completed": len(completed), "errors": len(errors)}))


if __name__ == "__main__":
    main()
