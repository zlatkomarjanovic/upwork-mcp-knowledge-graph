#!/usr/bin/env python3
"""Process search batch file and update upwork-intelligence store."""
import json
import re
import statistics
from datetime import datetime, timezone, timedelta
from pathlib import Path
from urllib.parse import urlparse, urlunparse

ROOT = Path(__file__).parent
BATCH = ROOT / "_search_batches.jsonl"

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

SKIP_PATTERNS = re.compile(
    r"alcohol|gambling|casino|adult content|porn|crypto trading|dating app|onlyfans",
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


def norm_url(url: str) -> str:
    if not url:
        return ""
    u = urlparse(url.split("?")[0])
    return urlunparse((u.scheme, u.netloc, u.path.rstrip("/"), "", "", ""))


def parse_budget(budget_str, job_type):
    if not budget_str:
        return None, None
    s = str(budget_str).replace(",", "")
    if job_type == "fixed":
        m = re.search(r"([\d.]+)", s)
        return (float(m.group(1)) if m else None), None
    m = re.findall(r"([\d.]+)", s)
    if len(m) >= 2:
        return None, (float(m[0]) + float(m[1])) / 2
    if len(m) == 1:
        return None, float(m[0])
    return None, None


def parse_spend(sp):
    if not sp:
        return None
    m = re.search(r"([\d,]+\.?\d*)", str(sp).replace("$", ""))
    return float(m.group(1).replace(",", "")) if m else None


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
    score = 0
    now = datetime.now(timezone.utc)
    for j in jobs:
        recency = 50
        pa = j.get("postedAt")
        if pa:
            try:
                dt = datetime.fromisoformat(pa.replace("Z", "+00:00"))
                hours = (now - dt).total_seconds() / 3600
                recency = max(10, 100 - hours * 4)
            except Exception:
                pass
        prop = j.get("proposals") or 20
        comp = max(10, 100 - prop * 2)
        fixed, hourly = parse_budget(j.get("budget"), j.get("type"))
        pay = 30
        if fixed and fixed >= 1000:
            pay = 90
        elif fixed and fixed >= 500:
            pay = 70
        elif hourly and hourly >= 40:
            pay = 85
        elif hourly and hourly >= 25:
            pay = 55
        ver = 15 if j.get("paymentVerified") else 0
        score += (recency * 0.25 + comp * 0.25 + pay * 0.35 + ver * 0.15)
    raw = score / len(jobs)
    return max(1, min(100, int(raw)))


def job_from_api(j, keyword, group):
    url = norm_url(j.get("url") or "")
    if not url:
        return None
    title = j.get("title") or ""
    desc = (j.get("description_snippet") or "") + title
    if SKIP_PATTERNS.search(desc):
        return None
    if "crypto card" in title.lower() or "trading bot" in title.lower():
        return None
    client = j.get("client") or {}
    fixed, hourly = parse_budget(j.get("budget"), j.get("job_type"))
    return {
        "url": url,
        "title": title,
        "matchedKeyword": [keyword],
        "keywordGroup": group,
        "postedAt": j.get("published_date") or j.get("created_date"),
        "type": j.get("job_type"),
        "budget": j.get("budget"),
        "duration": j.get("duration"),
        "proposals": j.get("proposal_count"),
        "clientCountry": client.get("country"),
        "paymentVerified": client.get("verification_status") == "VERIFIED",
        "clientSpend": client.get("total_spent"),
        "clientHireRate": None,
        "clientRating": client.get("rating"),
        "experienceLevel": j.get("experience_level"),
        "skills": j.get("skills") or [],
        "_fixed": fixed,
        "_hourly": hourly,
        "_spend": parse_spend(client.get("total_spent")),
    }


def load_state():
    p = ROOT / "state.json"
    if p.exists():
        return json.loads(p.read_text())
    return {"runNumber": 0, "totalJobs": 0, "knownJobUrls": [], "lastInsightRefresh": None}


def main():
    if not BATCH.exists():
        print("No batch file")
        return
    state = load_state()
    run_number = state.get("runNumber", 0) + 1
    first_run = run_number == 1
    window_h = 2.0 if first_run else 1.0
    cutoff = datetime.now(timezone.utc) - timedelta(hours=window_h)

    known = set(state.get("knownJobUrls") or [])
    jobs_path = ROOT / "jobs.jsonl"
    all_jobs = {}
    if jobs_path.exists():
        for line in jobs_path.read_text().splitlines():
            if not line.strip():
                continue
            o = json.loads(line)
            all_jobs[o["url"]] = o

    keywords_attempted = 0
    keywords_completed = 0
    errors = []
    new_this_run = []

    for line in BATCH.read_text().splitlines():
        if not line.strip():
            continue
        batch = json.loads(line)
        kw = batch["keyword"]
        keywords_attempted += 1
        if batch.get("error"):
            errors.append(kw)
            continue
        keywords_completed += 1
        group = KEYWORD_GROUPS.get(kw, batch.get("group", "OTHER"))
        for j in batch.get("jobs") or []:
            rec = job_from_api(j, kw, group)
            if not rec:
                continue
            pa = rec.get("postedAt")
            if pa:
                try:
                    dt = datetime.fromisoformat(pa.replace("Z", "+00:00"))
                    if dt < cutoff:
                        continue
                except Exception:
                    pass
            url = rec["url"]
            if url in all_jobs:
                existing = all_jobs[url]
                mk = set(existing.get("matchedKeyword") or [])
                mk.update(rec["matchedKeyword"])
                existing["matchedKeyword"] = sorted(mk)
                continue
            if url in known:
                continue
            clean = {k: v for k, v in rec.items() if not k.startswith("_")}
            all_jobs[url] = clean
            new_this_run.append(clean)
            known.add(url)

    with jobs_path.open("w") as f:
        for o in all_jobs.values():
            f.write(json.dumps(o, ensure_ascii=False) + "\n")

    now_iso = datetime.now(timezone.utc).isoformat()
    state.update(
        {
            "lastRunAt": now_iso,
            "runNumber": run_number,
            "totalJobs": len(all_jobs),
            "knownJobUrls": sorted(known),
        }
    )
    (ROOT / "state.json").write_text(json.dumps(state, indent=2))

    now = datetime.now(timezone.utc)
    cut24 = now - timedelta(hours=24)

    def jobs_for_keyword(kw):
        return [j for j in all_jobs.values() if kw in (j.get("matchedKeyword") or [])]

    kw_stats = {}
    for kw in KEYWORD_GROUPS:
        jl = jobs_for_keyword(kw)
        j24 = [
            j
            for j in jl
            if j.get("postedAt")
            and datetime.fromisoformat(j["postedAt"].replace("Z", "+00:00")) >= cut24
        ]
        fixed_vals = []
        hourly_vals = []
        props = []
        verified = 0
        spends = []
        high_b = 0
        for j in jl:
            ft, hr = parse_budget(j.get("budget"), j.get("type"))
            if ft:
                fixed_vals.append(ft)
            if hr:
                hourly_vals.append(hr)
            if j.get("proposals") is not None:
                props.append(j["proposals"])
            if j.get("paymentVerified"):
                verified += 1
            sp = parse_spend(j.get("clientSpend"))
            if sp:
                spends.append(sp)
            if (ft and ft >= 1000) or (hr and hr >= 40):
                high_b += 1
        n = len(jl)
        kw_stats[kw] = {
            "keywordGroup": KEYWORD_GROUPS[kw],
            "totalJobs": n,
            "jobsLast24h": len(j24),
            "avgBudgetFixed": round(statistics.mean(fixed_vals), 2) if fixed_vals else None,
            "avgRateHourly": round(statistics.mean(hourly_vals), 2) if hourly_vals else None,
            "medianProposals": int(statistics.median(props)) if props else None,
            "pctVerified": round(100 * verified / n, 1) if n else 0,
            "avgClientSpend": round(statistics.mean(spends), 2) if spends else None,
            "pctHighBudget": round(100 * high_b / n, 1) if n else 0,
            "opportunityScore": opportunity_score(jl),
            "sampleConfidence": confidence(n),
        }
    (ROOT / "keyword-stats.json").write_text(json.dumps(kw_stats, indent=2))

    group_stats = {}
    for g in set(KEYWORD_GROUPS.values()):
        jl = [j for j in all_jobs.values() if j.get("keywordGroup") == g]
        j24 = [
            j
            for j in jl
            if j.get("postedAt")
            and datetime.fromisoformat(j["postedAt"].replace("Z", "+00:00")) >= cut24
        ]
        group_stats[g] = {
            "totalJobs": len(jl),
            "jobsLast24h": len(j24),
            "opportunityScore": opportunity_score(jl),
            "sampleConfidence": confidence(len(jl)),
        }
    (ROOT / "group-stats.json").write_text(json.dumps(group_stats, indent=2))

    plat_stats = {}
    for plat, kws in PLATFORM_MAP.items():
        jl = []
        for j in all_jobs.values():
            text = " ".join(j.get("matchedKeyword") or []).lower() + " " + " ".join(
                j.get("skills") or []
            ).lower()
            if any(k in text for k in kws):
                jl.append(j)
        plat_stats[plat] = {
            "totalJobs": len(jl),
            "opportunityScore": opportunity_score(jl),
            "sampleConfidence": confidence(len(jl)),
        }
    (ROOT / "platform-stats.json").write_text(json.dumps(plat_stats, indent=2))

    top3 = sorted(kw_stats.items(), key=lambda x: x[1]["jobsLast24h"], reverse=True)[:3]
    log = {
        "timestamp": now_iso,
        "runNumber": run_number,
        "keywordsAttempted": keywords_attempted,
        "keywordsCompleted": keywords_completed,
        "newJobs": len(new_this_run),
        "totalJobs": len(all_jobs),
        "top3Keywords": [t[0] for t in top3],
        "errors": errors,
    }
    with (ROOT / "run-log.jsonl").open("a") as f:
        f.write(json.dumps(log) + "\n")

    top_kw = sorted(kw_stats.items(), key=lambda x: x[1]["opportunityScore"], reverse=True)[:10]
    top_groups = sorted(group_stats.items(), key=lambda x: x[1]["opportunityScore"], reverse=True)

    summary = f"""# Upwork Market Intelligence

Last updated: {now_iso}
Run: {run_number}
Total jobs tracked: {len(all_jobs)}
Keywords attempted: {keywords_attempted}
Keywords completed: {keywords_completed}

## Top Opportunities

"""
    for i, (kw, st) in enumerate(top_kw, 1):
        summary += f"{i}. **{kw}** — score {st['opportunityScore']} ({st['sampleConfidence']})\n"
        summary += f"   - jobsLast24h: {st['jobsLast24h']}, total: {st['totalJobs']}, avg fixed: {st['avgBudgetFixed']}, avg hourly: {st['avgRateHourly']}, median proposals: {st['medianProposals']}\n"

    summary += "\n## Strongest Groups\n\n"
    for i, (g, st) in enumerate(top_groups[:8], 1):
        summary += f"{i}. {g} — score {st['opportunityScore']} (24h: {st['jobsLast24h']}, total: {st['totalJobs']})\n"

    summary += "\n## Platform Ranking\n\n"
    for i, (p, st) in enumerate(
        sorted(plat_stats.items(), key=lambda x: x[1]["opportunityScore"], reverse=True), 1
    ):
        summary += f"{i}. {p} — score {st['opportunityScore']} (n={st['totalJobs']})\n"

    primary = top_kw[0][0] if top_kw else "wordpress developer"
    secondary = top_kw[1][0] if len(top_kw) > 1 else "webflow developer"
    summary += f"""
## Positioning Recommendation

Primary keyword: {primary}
Secondary keyword: {secondary}
Best platform/service: WordPress / Webflow hybrid builds
Overview keywords: {primary}, {secondary}, website redesign, ongoing web developer
Skill tags: WordPress, Webflow, Next.js, Elementor, SEO, CRO

## Current Verdicts

WordPress: Steady volume; mix of low fixed AI-to-WP conversions and agency retainers.
Webflow: Smaller but cleaner small-scope expert jobs.
Framer: Low sample; niche.
GoHighLevel: Integration/automation spikes; verify scope fit.
AI/Vibe Coding: Claude/Elementor conversion jobs emerging.
Ecommerce: Shopify CRO/revamp posts strong competition.
Maintenance: Long-term partnership posts recurring.

## Important Changes

First baseline run — establishing keyword and platform stats.
"""
    (ROOT / "current-summary.md").write_text(summary)

    insights = ROOT / "insights.md"
    if not insights.exists():
        insights.write_text(
            "# Durable insights\n\n- 2026-09-15: Baseline tracker started. WordPress + Shopify dominate visible hourly/fixed mix in first 2h window.\n"
        )

    print(json.dumps({"run": run_number, "new": len(new_this_run), "total": len(all_jobs), "errors": errors}))


if __name__ == "__main__":
    main()
