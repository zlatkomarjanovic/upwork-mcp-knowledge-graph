#!/usr/bin/env python3
"""Post-process raw keyword search batches into jobs.jsonl and stats."""
import json
import math
import os
import re
import statistics
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parent
RAW = BASE / "raw_batches"
WINDOW_HOURS_FIRST = 2.0
WINDOW_HOURS = 1.0
SKIP_RE = re.compile(
    r"\b(alcohol|gambling|adult|crypto trading|dating|casino|porn)\b", re.I
)

KEYWORD_GROUPS = {
    "CORE WEB DEVELOPMENT": [
        "web development", "website development", "web developer", "custom website",
        "frontend developer", "full stack developer",
    ],
    "WEB DESIGN": [
        "web design", "website design", "website redesign", "landing page design",
        "UI UX website", "responsive web design",
    ],
    "WORDPRESS": [
        "wordpress", "wordpress developer", "wordpress website", "wordpress development",
        "wordpress redesign", "wordpress customization", "wordpress migration",
        "wordpress speed optimization", "wordpress maintenance", "woocommerce",
        "elementor developer", "bricks builder",
    ],
    "WEBFLOW / FRAMER": [
        "webflow", "webflow developer", "webflow website", "webflow redesign",
        "figma to webflow", "framer", "framer developer", "framer website",
        "framer redesign", "figma to framer",
    ],
    "AI / VIBE CODING": [
        "AI web development", "AI web developer", "vibe coding", "claude code developer",
        "cursor AI developer", "lovable developer", "lovable app", "bolt developer",
        "bolt.new", "v0 developer", "v0 vercel", "replit developer", "supabase developer",
        "AI agent integration website",
    ],
    "GOHIGHLEVEL": [
        "gohighlevel", "go high level", "GHL", "gohighlevel developer",
        "gohighlevel website", "gohighlevel funnel", "gohighlevel automation",
        "gohighlevel CRM",
    ],
    "ADJACENT PLATFORMS": [
        "squarespace website", "wix website", "wix studio", "bubble developer",
    ],
    "MODERN STACK": [
        "nextjs developer", "next.js developer", "nextjs website", "react developer",
        "figma to nextjs", "tailwind developer", "astro developer", "sanity CMS",
    ],
    "ECOMMERCE": [
        "ecommerce website", "ecommerce developer", "shopify developer", "shopify website",
        "woocommerce developer", "shopware", "shopware developer", "shopware 6",
        "headless ecommerce",
    ],
    "MAINTENANCE / RETAINERS": [
        "website maintenance", "website maintenance monthly", "website support ongoing",
        "website management ongoing", "wordpress support retainer", "webflow maintenance",
        "shopify maintenance", "ongoing web developer", "web development retainer",
    ],
    "CONVERSION / PERFORMANCE": [
        "conversion rate optimization", "landing page optimization", "website audit",
        "core web vitals", "page speed optimization", "website speed optimization",
        "technical SEO website",
    ],
}

ALL_KEYWORDS = []
KW_TO_GROUP = {}
for g, kws in KEYWORD_GROUPS.items():
    for k in kws:
        ALL_KEYWORDS.append(k)
        KW_TO_GROUP[k] = g

PLATFORM_MAP = {
    "wordpress": "WordPress", "woocommerce": "WooCommerce", "shopify": "Shopify",
    "webflow": "Webflow", "framer": "Framer", "gohighlevel": "GoHighLevel",
    "go high level": "GoHighLevel", "ghl": "GoHighLevel", "lovable": "Lovable",
    "bolt": "Bolt", "v0": "v0", "nextjs": "Next.js", "next.js": "Next.js",
    "shopware": "Shopware",
}

PROPOSAL_MID = {
    "Fewer than 5": 2, "5 to 10": 7, "10 to 15": 12, "15 to 20": 17,
    "20 to 50": 35, "50+": 55,
}


def norm_url(u):
    if not u:
        return None
    return u.split("?")[0]


def parse_money(s):
    if not s:
        return None
    s = str(s).replace(",", "")
    if "–" in s or "-" in s and "/hr" in s:
        parts = re.split(r"[–-]", s.replace("/hr", ""))
        try:
            return (float(parts[0].strip()) + float(parts[-1].strip())) / 2
        except ValueError:
            return None
    m = re.search(r"([\d.]+)", s)
    return float(m.group(1)) if m else None


def proposal_mid(tier):
    if not tier:
        return None
    return PROPOSAL_MID.get(tier)


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


def is_high_budget(job):
    if job.get("type") == "fixed":
        b = job.get("_budget_num")
        return b is not None and b >= 1000
    if job.get("type") == "hourly":
        r = job.get("_rate_num")
        return r is not None and r >= 40
    return False


def opportunity_score(stats):
    recent = stats.get("jobsLast24h", 0)
    total = stats.get("totalJobs", 0)
    med_p = stats.get("medianProposals") or 25
    avg_f = stats.get("avgBudgetFixed") or 0
    avg_h = stats.get("avgRateHourly") or 0
    pct_v = stats.get("pctVerified") or 0
    pct_hb = stats.get("pctHighBudget") or 0
    pay = max(avg_f / 2000, avg_h / 80, 0.2)
    comp = max(0.15, 1 - (med_p / 50))
    raw = (
        math.log1p(recent) * 22
        + math.log1p(total) * 8
        + pay * 25
        + comp * 25
        + (pct_v / 100) * 10
        + (pct_hb / 100) * 10
    )
    return max(1, min(100, int(raw)))


def job_from_api(j, keyword, group, run_at):
    url = norm_url(j.get("url"))
    if not url:
        return None
    title = j.get("title") or ""
    desc = j.get("description_snippet") or ""
    if SKIP_RE.search(title + " " + desc):
        return None
    pub = j.get("published_date") or j.get("created_date")
    client = j.get("client") or {}
    budget_raw = j.get("budget")
    jtype = j.get("job_type")
    rate_num = None
    budget_num = None
    if jtype == "hourly" and budget_raw:
        rate_num = parse_money(budget_raw)
    elif jtype == "fixed" and budget_raw:
        budget_num = parse_money(budget_raw)
    return {
        "url": url,
        "title": title,
        "matchedKeyword": [keyword],
        "keywordGroup": group,
        "postedAt": pub,
        "type": jtype,
        "budget": budget_raw if jtype == "fixed" else None,
        "hourlyRate": budget_raw if jtype == "hourly" else None,
        "duration": j.get("duration"),
        "proposals": j.get("proposals_tier"),
        "clientCountry": client.get("country"),
        "paymentVerified": client.get("verification_status") == "VERIFIED",
        "clientSpend": client.get("total_spent"),
        "clientHireRate": None,
        "clientRating": client.get("rating"),
        "experienceLevel": j.get("experience_level"),
        "skills": j.get("skills") or [],
        "_budget_num": budget_num,
        "_rate_num": rate_num,
        "_firstSeenRun": run_at,
    }


def load_state():
    p = BASE / "state.json"
    if p.exists():
        return json.loads(p.read_text())
    return {"runNumber": 0, "totalJobs": 0, "knownJobUrls": [], "lastInsightRefresh": None}


def main(run_at_iso, keywords_completed, keywords_attempted, errors, first_run=False):
    run_at = datetime.fromisoformat(run_at_iso.replace("Z", "+00:00"))
    state = load_state()
    run_number = state.get("runNumber", 0) + 1
    known = set(state.get("knownJobUrls") or [])
    window_h = WINDOW_HOURS_FIRST if first_run or not known else WINDOW_HOURS
    cutoff = run_at.timestamp() - window_h * 3600

    jobs_by_url = {}
    jobs_path = BASE / "jobs.jsonl"
    if jobs_path.exists():
        for line in jobs_path.read_text().splitlines():
            if not line.strip():
                continue
            o = json.loads(line)
            u = o.get("url")
            if u:
                jobs_by_url[u] = o

    new_this_run = []
    if RAW.exists():
        for fp in sorted(RAW.glob("*.json")):
            batch = json.loads(fp.read_text())
            kw = batch.get("keyword")
            group = batch.get("group") or KW_TO_GROUP.get(kw, "OTHER")
            if batch.get("error"):
                continue
            for j in batch.get("jobs") or []:
                rec = job_from_api(j, kw, group, run_at_iso)
                if not rec:
                    continue
                pub = rec.get("postedAt")
                if pub:
                    try:
                        ts = datetime.fromisoformat(pub.replace("Z", "+00:00")).timestamp()
                        if ts < cutoff:
                            continue
                    except ValueError:
                        pass
                u = rec["url"]
                if u in jobs_by_url:
                    mk = jobs_by_url[u].setdefault("matchedKeyword", [])
                    if kw not in mk:
                        mk.append(kw)
                else:
                    jobs_by_url[u] = rec
                    new_this_run.append(rec)

    with jobs_path.open("a") as f:
        for rec in new_this_run:
            out = {k: v for k, v in rec.items() if not k.startswith("_")}
            f.write(json.dumps(out, ensure_ascii=False) + "\n")

    all_jobs = list(jobs_by_url.values())
    now = run_at.timestamp()
    day_ago = now - 86400

    kw_stats = {}
    for kw in ALL_KEYWORDS:
        matched = [j for j in all_jobs if kw in (j.get("matchedKeyword") or [])]
        if not matched:
            kw_stats[kw] = {
                "totalJobs": 0, "jobsLast24h": 0, "avgBudgetFixed": None,
                "avgRateHourly": None, "medianProposals": None, "pctVerified": None,
                "avgClientSpend": None, "pctHighBudget": None, "opportunityScore": 1,
                "sampleConfidence": "Very Low",
            }
            continue
        fixed = [j["_budget_num"] for j in matched if j.get("_budget_num")]
        hourly = [j["_rate_num"] for j in matched if j.get("_rate_num")]
        props = [proposal_mid(j.get("proposals")) for j in matched]
        props = [p for p in props if p is not None]
        verified = sum(1 for j in matched if j.get("paymentVerified"))
        high_b = sum(1 for j in matched if is_high_budget(j))
        j24 = 0
        for j in matched:
            pub = j.get("postedAt")
            if not pub:
                continue
            try:
                if datetime.fromisoformat(pub.replace("Z", "+00:00")).timestamp() >= day_ago:
                    j24 += 1
            except ValueError:
                pass
        st = {
            "totalJobs": len(matched),
            "jobsLast24h": j24,
            "avgBudgetFixed": round(statistics.mean(fixed), 2) if fixed else None,
            "avgRateHourly": round(statistics.mean(hourly), 2) if hourly else None,
            "medianProposals": int(statistics.median(props)) if props else None,
            "pctVerified": round(100 * verified / len(matched), 1) if matched else None,
            "avgClientSpend": None,
            "pctHighBudget": round(100 * high_b / len(matched), 1) if matched else None,
            "sampleConfidence": confidence(len(matched)),
        }
        st["opportunityScore"] = opportunity_score(st)
        kw_stats[kw] = st

    (BASE / "keyword-stats.json").write_text(json.dumps(kw_stats, indent=2))

    group_stats = {}
    for g, kws in KEYWORD_GROUPS.items():
        totals = [kw_stats[k]["totalJobs"] for k in kws]
        j24s = [kw_stats[k]["jobsLast24h"] for k in kws]
        scores = [kw_stats[k]["opportunityScore"] for k in kws if kw_stats[k]["totalJobs"]]
        group_stats[g] = {
            "totalJobs": sum(totals),
            "jobsLast24h": sum(j24s),
            "avgOpportunityScore": int(statistics.mean(scores)) if scores else 0,
            "keywordCount": len(kws),
        }
    (BASE / "group-stats.json").write_text(json.dumps(group_stats, indent=2))

    plat_stats = {}
    for pk in ["WordPress", "Webflow", "Framer", "GoHighLevel", "Shopify", "WooCommerce",
               "Shopware", "Lovable", "Bolt", "v0", "Next.js"]:
        plat_jobs = []
        for j in all_jobs:
            blob = " ".join(
                [j.get("title") or ""]
                + (j.get("matchedKeyword") or [])
                + (j.get("skills") or [])
            ).lower()
            key = pk.lower().replace(".", "")
            if key in blob or pk.lower() in blob:
                plat_jobs.append(j)
        if not plat_jobs:
            plat_stats[pk] = {"jobs": 0, "avgBudgetRate": None, "medianProposals": None,
                              "score": 0, "confidence": "Very Low"}
            continue
        fixed = [j["_budget_num"] for j in plat_jobs if j.get("_budget_num")]
        hourly = [j["_rate_num"] for j in plat_jobs if j.get("_rate_num")]
        props = [proposal_mid(j.get("proposals")) for j in plat_jobs]
        props = [p for p in props if p is not None]
        avg_br = None
        if fixed:
            avg_br = statistics.mean(fixed)
        elif hourly:
            avg_br = statistics.mean(hourly)
        plat_stats[pk] = {
            "jobs": len(plat_jobs),
            "avgBudgetRate": round(avg_br, 2) if avg_br else None,
            "medianProposals": int(statistics.median(props)) if props else None,
            "score": opportunity_score({"jobsLast24h": len(plat_jobs), "totalJobs": len(plat_jobs),
                                        "medianProposals": statistics.median(props) if props else 20,
                                        "avgBudgetFixed": avg_br or 0, "avgRateHourly": avg_br or 0,
                                        "pctVerified": 70, "pctHighBudget": 20}),
            "confidence": confidence(len(plat_jobs)),
        }
    (BASE / "platform-stats.json").write_text(json.dumps(plat_stats, indent=2))

    state.update({
        "lastRunAt": run_at_iso,
        "runNumber": run_number,
        "totalJobs": len(all_jobs),
        "knownJobUrls": list(jobs_by_url.keys()),
        "lastInsightRefresh": state.get("lastInsightRefresh"),
    })
    (BASE / "state.json").write_text(json.dumps(state, indent=2))

    log = {
        "timestamp": run_at_iso,
        "runNumber": run_number,
        "keywordsAttempted": keywords_attempted,
        "keywordsCompleted": keywords_completed,
        "newJobs": len(new_this_run),
        "totalJobs": len(all_jobs),
        "top3Keywords": sorted(kw_stats.items(), key=lambda x: x[1]["opportunityScore"], reverse=True)[:3],
        "errors": errors,
    }
    with (BASE / "run-log.jsonl").open("a") as f:
        f.write(json.dumps(log) + "\n")

    top_kw = sorted(
        [(k, v) for k, v in kw_stats.items() if v["totalJobs"] > 0],
        key=lambda x: x[1]["opportunityScore"],
        reverse=True,
    )[:10]
    primary = top_kw[0][0] if top_kw else "wordpress developer"
    secondary = top_kw[1][0] if len(top_kw) > 1 else "webflow developer"

    summary = f"""# Upwork Market Intelligence

Last updated: {run_at_iso}
Run: {run_number}
Total jobs tracked: {len(all_jobs)}
Keywords attempted: {keywords_attempted}
Keywords completed: {keywords_completed}

## Top Opportunities

"""
    for k, v in top_kw:
        summary += (
            f"- **{k}** — score {v['opportunityScore']} | jobs24h {v['jobsLast24h']} | "
            f"total {v['totalJobs']} | avg fixed {v['avgBudgetFixed']} | avg hourly {v['avgRateHourly']} | "
            f"median proposals {v['medianProposals']} | {v['sampleConfidence']}\n"
        )

    grp_rank = sorted(group_stats.items(), key=lambda x: x[1]["jobsLast24h"], reverse=True)
    summary += "\n## Strongest Groups\n\n"
    for g, s in grp_rank[:5]:
        summary += f"- {g}: jobs24h {s['jobsLast24h']}, total {s['totalJobs']}, avg score {s['avgOpportunityScore']}\n"

    summary += "\n## Platform Ranking\n\n"
    for p, s in sorted(plat_stats.items(), key=lambda x: x[1]["score"], reverse=True):
        summary += f"- {p}: jobs {s['jobs']}, score {s['score']}, {s['confidence']}\n"

    summary += f"""
## Positioning Recommendation

Primary keyword: {primary}
Secondary keyword: {secondary}
Best platform/service: WordPress + Next.js hybrid delivery
Overview keywords: {primary}, {secondary}, website development, AI web development
Skill tags: Next.js, WordPress, Webflow, Supabase, conversion optimization

## Current Verdicts

WordPress: Steady migration, redesign, and WooCommerce volume; competition rises on broad queries.
Webflow: Niche but qualified Figma-to-Webflow builds; budgets often modest.
Framer: Lower volume than Webflow; good for design-led marketing sites.
GoHighLevel: Funnel/LP design and automation integrations; not pure dev-heavy.
AI/Vibe Coding: Lovable/Cursor/vibe roles growing; many are VA/production, filter for production engineering.
Ecommerce: Shopify + WooCommerce maintenance and rebuilds remain active.
Maintenance: Hosting emergencies and WP support retainers show up hourly.

## Important Changes

First baseline run initialized tracking store.
"""
    (BASE / "current-summary.md").write_text(summary)

    out = {
        "runNumber": run_number,
        "newJobs": len(new_this_run),
        "totalJobs": len(all_jobs),
        "topKw": top_kw,
        "group_stats": group_stats,
        "plat_stats": plat_stats,
        "new_jobs": new_this_run,
    }
    (BASE / ".last_output.json").write_text(json.dumps(out, default=str, indent=2))
    print(json.dumps({"runNumber": run_number, "newJobs": len(new_this_run), "total": len(all_jobs)}))


if __name__ == "__main__":
    import sys
    run_at = sys.argv[1] if len(sys.argv) > 1 else datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    attempted = int(sys.argv[2]) if len(sys.argv) > 2 else len(ALL_KEYWORDS)
    completed = int(sys.argv[3]) if len(sys.argv) > 3 else attempted
    errs = json.loads(sys.argv[4]) if len(sys.argv) > 4 else []
    first = sys.argv[5] == "1" if len(sys.argv) > 5 else True
    main(run_at, completed, attempted, errs, first_run=first)
