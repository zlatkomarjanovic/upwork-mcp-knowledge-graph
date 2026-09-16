#!/usr/bin/env python3
"""Process raw search batch results into intelligence files. One-time helper."""
import json, os, re, statistics
from datetime import datetime, timezone, timedelta
from pathlib import Path

BASE = Path(__file__).resolve().parent
RAW = BASE / "run-raw-batch.json"

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
    r"alcohol|gambling|casino|adult content|crypto trad|dating app|onlyfans",
    re.I,
)

PROPOSAL_MID = {
    "Fewer than 5": 2,
    "5 to 10": 7,
    "10 to 15": 12,
    "15 to 20": 17,
    "20 to 50": 35,
    "50+": 55,
}

PLATFORMS = {
    "WordPress": ["wordpress", "woocommerce", "elementor"],
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


def parse_money(s):
    if not s:
        return None
    s = str(s).replace(",", "")
    if "–" in s or "-" in s:
        parts = re.split(r"[–-]", s)
        nums = []
        for p in parts:
            m = re.search(r"(\d+(?:\.\d+)?)", p)
            if m:
                nums.append(float(m.group(1)))
        return statistics.mean(nums) if nums else None
    m = re.search(r"(\d+(?:\.\d+)?)", s)
    return float(m.group(1)) if m else None


def normalize_url(url):
    if not url:
        return None
    return url.split("?")[0]


def proposals_mid(tier):
    if tier is None:
        return None
    return PROPOSAL_MID.get(tier, None)


def is_high_budget(job_type, budget_val):
    if budget_val is None:
        return False
    if job_type == "fixed":
        return budget_val >= 1000
    if job_type == "hourly":
        return budget_val >= 40
    return False


def job_from_raw(j, keyword, group):
    url = normalize_url(j.get("url"))
    if not url:
        return None
    posted = j.get("published_date") or j.get("created_date")
    client = j.get("client") or {}
    budget_raw = j.get("budget")
    jt = j.get("job_type")
    spend = client.get("total_spent")
    if spend and isinstance(spend, str):
        spend_num = parse_money(spend)
    else:
        spend_num = spend
    return {
        "url": url,
        "title": j.get("title"),
        "matchedKeyword": [keyword],
        "keywordGroup": group,
        "postedAt": posted,
        "type": jt,
        "budget": budget_raw if jt == "fixed" else None,
        "hourlyRate": budget_raw if jt == "hourly" else None,
        "duration": j.get("duration"),
        "proposals": j.get("proposals_tier"),
        "clientCountry": client.get("country"),
        "paymentVerified": client.get("verification_status") == "VERIFIED",
        "clientSpend": spend if isinstance(spend, str) else spend,
        "clientHireRate": None,
        "clientRating": client.get("rating"),
        "experienceLevel": j.get("experience_level"),
        "skills": j.get("skills") or [],
        "_budgetNum": parse_money(budget_raw) if jt == "fixed" else None,
        "_rateNum": parse_money(budget_raw) if jt == "hourly" else None,
        "_proposalsMid": proposals_mid(j.get("proposals_tier")),
    }


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
        return 0
    now = datetime.now(timezone.utc)
    scores = []
    for j in jobs:
        s = 50.0
        try:
            pt = datetime.fromisoformat(j["postedAt"].replace("Z", "+00:00"))
            hours = (now - pt).total_seconds() / 3600
            s += max(0, 25 - hours * 2)
        except Exception:
            pass
        bn = j.get("_budgetNum") or j.get("_rateNum")
        if bn:
            s += min(20, bn / 100)
        pm = j.get("_proposalsMid")
        if pm is not None:
            s += max(0, 15 - pm / 3)
        if j.get("paymentVerified"):
            s += 5
        if is_high_budget(j.get("type"), bn):
            s += 10
        scores.append(min(100, max(1, s)))
    return round(statistics.mean(scores))


def main():
    data = json.loads(RAW.read_text())
    first_run = not (BASE / "state.json").exists()
    window_h = 2 if first_run else 1
    cutoff = datetime.now(timezone.utc) - timedelta(hours=window_h)

    state_path = BASE / "state.json"
    if state_path.exists():
        state = json.loads(state_path.read_text())
        known = set(state.get("knownJobUrls", []))
        run_number = state.get("runNumber", 0) + 1
    else:
        known = set()
        run_number = 1

    jobs_by_url = {}
    errors = data.get("errors", [])
    attempted = len(KEYWORDS)
    completed = data.get("keywordsCompleted", attempted - len(errors))

    for entry in data.get("results", []):
        kw = entry["keyword"]
        group = entry["group"]
        for j in entry.get("jobs", []):
            title = (j.get("title") or "") + " " + (j.get("description_snippet") or "")
            if SKIP_PATTERNS.search(title):
                continue
            posted = j.get("published_date") or j.get("created_date")
            try:
                pt = datetime.fromisoformat(posted.replace("Z", "+00:00"))
                if pt < cutoff:
                    continue
            except Exception:
                continue
            job = job_from_raw(j, kw, group)
            if not job:
                continue
            u = job["url"]
            if u in jobs_by_url:
                if kw not in jobs_by_url[u]["matchedKeyword"]:
                    jobs_by_url[u]["matchedKeyword"].append(kw)
            else:
                jobs_by_url[u] = job

    new_jobs = [j for u, j in jobs_by_url.items() if u not in known]

    # append jobs.jsonl
    jpath = BASE / "jobs.jsonl"
    with jpath.open("a") as f:
        for j in new_jobs:
            out = {k: v for k, v in j.items() if not k.startswith("_")}
            f.write(json.dumps(out, ensure_ascii=False) + "\n")

    all_jobs = []
    if jpath.exists():
        with jpath.open() as f:
            for line in f:
                line = line.strip()
                if line:
                    all_jobs.append(json.loads(line))

    now_iso = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    known.update(j["url"] for j in new_jobs)

    # keyword stats from all_jobs
    kw_stats = {}
    for kw, group in KEYWORDS:
        matched = [j for j in all_jobs if kw in j.get("matchedKeyword", [])]
        fixed = [parse_money(j.get("budget")) for j in matched if j.get("type") == "fixed"]
        fixed = [x for x in fixed if x is not None]
        hourly = [parse_money(j.get("hourlyRate")) for j in matched if j.get("type") == "hourly"]
        hourly = [x for x in hourly if x is not None]
        props = [proposals_mid(j.get("proposals")) for j in matched]
        props = [x for x in props if x is not None]
        verified = sum(1 for j in matched if j.get("paymentVerified"))
        high = sum(
            1
            for j in matched
            if is_high_budget(j.get("type"), parse_money(j.get("budget") or j.get("hourlyRate")))
        )
        last24 = cutoff24 = datetime.now(timezone.utc) - timedelta(hours=24)
        j24 = []
        for j in matched:
            try:
                if datetime.fromisoformat(j["postedAt"].replace("Z", "+00:00")) >= cutoff24:
                    j24.append(j)
            except Exception:
                pass
        spend_vals = []
        for j in matched:
            cs = j.get("clientSpend")
            if cs and isinstance(cs, str):
                v = parse_money(cs)
                if v:
                    spend_vals.append(v)
        n = len(matched)
        kw_stats[kw] = {
            "keywordGroup": group,
            "totalJobs": n,
            "jobsLast24h": len(j24),
            "avgBudgetFixed": round(statistics.mean(fixed), 2) if fixed else None,
            "avgRateHourly": round(statistics.mean(hourly), 2) if hourly else None,
            "medianProposals": int(statistics.median(props)) if props else None,
            "pctVerified": round(100 * verified / n, 1) if n else 0,
            "avgClientSpend": round(statistics.mean(spend_vals), 2) if spend_vals else None,
            "pctHighBudget": round(100 * high / n, 1) if n else 0,
            "opportunityScore": opportunity_score(
                [{**j, "_budgetNum": parse_money(j.get("budget")), "_rateNum": parse_money(j.get("hourlyRate")), "_proposalsMid": proposals_mid(j.get("proposals"))} for j in matched]
            ),
            "sampleConfidence": confidence(n),
        }

    (BASE / "keyword-stats.json").write_text(json.dumps(kw_stats, indent=2))

    groups = {}
    for kw, st in kw_stats.items():
        g = st["keywordGroup"]
        groups.setdefault(g, []).append(st)
    group_stats = {}
    for g, items in groups.items():
        n = sum(i["totalJobs"] for i in items)
        j24 = sum(i["jobsLast24h"] for i in items)
        scores = [i["opportunityScore"] for i in items if i["totalJobs"]]
        group_stats[g] = {
            "totalJobs": n,
            "jobsLast24h": j24,
            "avgOpportunityScore": round(statistics.mean(scores), 1) if scores else 0,
            "keywordCount": len(items),
        }
    (BASE / "group-stats.json").write_text(json.dumps(group_stats, indent=2))

    plat_stats = {}
    for pname, kws in PLATFORMS.items():
        matched = []
        for j in all_jobs:
            text = " ".join(j.get("matchedKeyword", [])).lower() + " " + " ".join(j.get("skills") or []).lower()
            if any(k in text for k in kws):
                matched.append(j)
        n = len(matched)
        fixed = [parse_money(j.get("budget")) for j in matched if j.get("type") == "fixed"]
        fixed = [x for x in fixed if x is not None]
        hourly = [parse_money(j.get("hourlyRate")) for j in matched if j.get("type") == "hourly"]
        hourly = [x for x in hourly if x is not None]
        props = [proposals_mid(j.get("proposals")) for j in matched]
        props = [x for x in props if x is not None]
        plat_stats[pname] = {
            "jobs": n,
            "avgBudgetFixed": round(statistics.mean(fixed), 2) if fixed else None,
            "avgRateHourly": round(statistics.mean(hourly), 2) if hourly else None,
            "medianProposals": int(statistics.median(props)) if props else None,
            "opportunityScore": opportunity_score(
                [{**j, "_budgetNum": parse_money(j.get("budget")), "_rateNum": parse_money(j.get("hourlyRate")), "_proposalsMid": proposals_mid(j.get("proposals"))} for j in matched]
            ),
            "sampleConfidence": confidence(n),
        }
    (BASE / "platform-stats.json").write_text(json.dumps(plat_stats, indent=2))

    top3 = sorted(kw_stats.items(), key=lambda x: x[1]["jobsLast24h"], reverse=True)[:3]
    top3k = [k for k, _ in top3]

    log = {
        "timestamp": now_iso,
        "runNumber": run_number,
        "keywordsAttempted": attempted,
        "keywordsCompleted": completed,
        "newJobs": len(new_jobs),
        "totalJobs": len(all_jobs),
        "top3Keywords": top3k,
        "errors": errors,
    }
    with (BASE / "run-log.jsonl").open("a") as f:
        f.write(json.dumps(log) + "\n")

    state = {
        "lastRunAt": now_iso,
        "runNumber": run_number,
        "totalJobs": len(all_jobs),
        "knownJobUrls": sorted(known),
        "lastInsightRefresh": now_iso if run_number == 1 else (json.loads(state_path.read_text()).get("lastInsightRefresh") if state_path.exists() else now_iso),
    }
    (BASE / "state.json").write_text(json.dumps(state, indent=2))

    # summary md
    top10 = sorted(kw_stats.items(), key=lambda x: (x[1]["opportunityScore"], x[1]["jobsLast24h"]), reverse=True)[:10]
    top_groups = sorted(group_stats.items(), key=lambda x: x[1]["avgOpportunityScore"], reverse=True)

    primary = top10[0][0] if top10 else "wordpress developer"
    secondary = top10[1][0] if len(top10) > 1 else "webflow developer"

    md = f"""# Upwork Market Intelligence

Last updated: {now_iso}
Run: {run_number}
Total jobs tracked: {len(all_jobs)}
Keywords attempted: {attempted}
Keywords completed: {completed}

## Top Opportunities

"""
    for kw, st in top10:
        md += f"- **{kw}** — score {st['opportunityScore']}, jobs24h {st['jobsLast24h']}, total {st['totalJobs']}, avg fixed {st['avgBudgetFixed']}, avg hourly {st['avgRateHourly']}, median proposals {st['medianProposals']}, {st['sampleConfidence']}\n"

    md += "\n## Strongest Groups\n\n"
    for g, st in top_groups:
        md += f"- {g}: score {st['avgOpportunityScore']}, jobs24h {st['jobsLast24h']}, total {st['totalJobs']}\n"

    md += "\n## Platform Ranking\n\n"
    for p, st in sorted(plat_stats.items(), key=lambda x: x[1]["opportunityScore"], reverse=True):
        md += f"- {p}: {st['jobs']} jobs, score {st['opportunityScore']}\n"

    md += f"""
## Positioning Recommendation

Primary keyword: {primary}
Secondary keyword: {secondary}
Best platform/service: WordPress / Elementor maintenance + redesign
Overview keywords: WordPress, Web Development, Elementor, Website Redesign
Skill tags: WordPress, Elementor, WooCommerce, Webflow, Next.js

## Current Verdicts

WordPress: Strong hourly and fixed volume; mixed budgets, solid retainer signals.
Webflow: Lower volume than WordPress; higher design-led budgets when present.
Framer: Niche; fewer posts but less crowded.
GoHighLevel: Sparse in title search; funnel/automation niche.
AI/Vibe Coding: Emerging; tool-specific keywords low volume.
Ecommerce: Shopify + WooCommerce steady; agency-style multi-site posts.
Maintenance: Ongoing WordPress and web developer posts align with retainer positioning.

## Important Changes

First baseline run — no prior comparison.
"""
    (BASE / "current-summary.md").write_text(md)

    if run_number == 1:
        (BASE / "insights.md").write_text(
            """# Durable Insights

- Baseline established on first hourly run. WordPress and core web keywords dominate raw volume.
- Retainer and ongoing developer keywords appear regularly; worth dedicated profile sections.
- AI/vibe coding keywords remain low sample size; track over 7+ days before shifting positioning.
"""
        )

    # chat output file
    out = {
        "runNumber": run_number,
        "attempted": attempted,
        "completed": completed,
        "newJobs": [ {k: v for k, v in j.items() if not k.startswith("_")} for j in new_jobs ],
        "top10": [(k, v) for k, v in top10],
        "top_groups": top_groups[:5],
        "plat_stats": plat_stats,
        "errors": errors,
        "totalJobs": len(all_jobs),
    }
    (BASE / "chat-out.json").write_text(json.dumps(out, indent=2, default=str))
    print(json.dumps({"ok": True, "new": len(new_jobs), "total": len(all_jobs), "errors": len(errors)}))


if __name__ == "__main__":
    main()
