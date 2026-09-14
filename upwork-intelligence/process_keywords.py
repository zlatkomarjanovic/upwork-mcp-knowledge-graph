#!/usr/bin/env python3
"""Process raw search batches into jobs.jsonl and stats. Run after searches."""
import json, re, statistics, sys
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).parent
RAW = BASE / "raw-searches.json"
STATE_FILE = BASE / "state.json"
JOBS_FILE = BASE / "jobs.jsonl"
RUN_LOG = BASE / "run-log.jsonl"
KW_STATS = BASE / "keyword-stats.json"
GRP_STATS = BASE / "group-stats.json"
PLAT_STATS = BASE / "platform-stats.json"
SUMMARY = BASE / "current-summary.md"
INSIGHTS = BASE / "insights.md"

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
        "gohighlevel website", "gohighlevel funnel", "gohighlevel automation", "gohighlevel CRM",
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
        "woocommerce developer", "shopware", "shopware developer", "shopware 6", "headless ecommerce",
    ],
    "MAINTENANCE / RETAINERS": [
        "website maintenance", "website maintenance monthly", "website support ongoing",
        "website management ongoing", "wordpress support retainer", "webflow maintenance",
        "shopify maintenance", "ongoing web developer", "web development retainer",
    ],
    "CONVERSION / PERFORMANCE": [
        "conversion rate optimization", "landing page optimization", "website audit",
        "core web vitals", "page speed optimization", "website speed optimization", "technical SEO website",
    ],
}

KW_TO_GROUP = {k: g for g, kws in KEYWORD_GROUPS.items() for k in kws}

SKIP_PATTERNS = re.compile(
    r"crypto\s+exchange|cryptocurrency\s+exchange|bitcoin\s+lightning|dating|gambling|casino|adult\s+content|porn|escort",
    re.I,
)

PLATFORMS = {
    "WordPress": re.compile(r"wordpress|elementor|woocommerce|bricks", re.I),
    "Webflow": re.compile(r"webflow", re.I),
    "Framer": re.compile(r"framer", re.I),
    "GoHighLevel": re.compile(r"gohighlevel|go high level|\bghl\b", re.I),
    "Shopify": re.compile(r"shopify", re.I),
    "WooCommerce": re.compile(r"woocommerce", re.I),
    "Shopware": re.compile(r"shopware", re.I),
    "Lovable": re.compile(r"lovable", re.I),
    "Bolt": re.compile(r"bolt\.new|\bbolt developer\b", re.I),
    "v0": re.compile(r"\bv0\b|v0 vercel", re.I),
    "Next.js": re.compile(r"next\.?js", re.I),
}


def norm_url(url):
    if not url:
        return None
    return url.split("?")[0]


def parse_budget(budget_str, job_type):
    if not budget_str:
        return None, None
    s = budget_str.replace(",", "")
    if job_type == "fixed":
        m = re.search(r"([\d.]+)", s)
        return (float(m.group(1)) if m else None, None)
    m = re.findall(r"([\d.]+)", s)
    if len(m) >= 2:
        return None, (float(m[0]) + float(m[1])) / 2
    if len(m) == 1:
        return None, float(m[0])
    return None, None


def parse_spend(s):
    if not s:
        return None
    m = re.search(r"([\d,]+\.?\d*)", s.replace(",", ""))
    return float(m.group(1)) if m else None


def job_from_raw(j, keyword, group, cutoff):
    url = norm_url(j.get("url"))
    if not url:
        return None
    pub = j.get("published_date") or j.get("created_date")
    if pub:
        try:
            dt = datetime.fromisoformat(pub.replace("Z", "+00:00"))
            if dt < cutoff:
                return None
        except ValueError:
            pass
    title = j.get("title") or ""
    desc = j.get("description_snippet") or ""
    if SKIP_PATTERNS.search(title + " " + desc):
        return None
    client = j.get("client") or {}
    fixed, hourly = parse_budget(j.get("budget"), j.get("job_type"))
    return {
        "url": url,
        "title": title,
        "matchedKeyword": [keyword],
        "keywordGroup": group,
        "postedAt": pub,
        "type": j.get("job_type"),
        "budget": j.get("budget"),
        "budgetFixed": fixed,
        "rateHourly": hourly,
        "duration": j.get("duration"),
        "proposals": j.get("proposal_count"),
        "clientCountry": client.get("country"),
        "paymentVerified": client.get("verification_status") == "VERIFIED",
        "clientSpend": client.get("total_spent"),
        "clientSpendNum": parse_spend(client.get("total_spent")),
        "clientHireRate": None,
        "clientRating": client.get("rating"),
        "experienceLevel": j.get("experience_level"),
        "skills": j.get("skills") or [],
    }


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
    now = datetime.now(timezone.utc)
    scores = []
    for j in jobs:
        s = 40.0
        pub = j.get("postedAt")
        if pub:
            try:
                dt = datetime.fromisoformat(pub.replace("Z", "+00:00"))
                hours = (now - dt).total_seconds() / 3600
                s += max(0, 25 - hours * 2)
            except ValueError:
                pass
        if j.get("budgetFixed") and j["budgetFixed"] >= 1000:
            s += 15
        if j.get("rateHourly") and j["rateHourly"] >= 40:
            s += 15
        p = j.get("proposals")
        if p is not None:
            s += max(0, 20 - min(p, 20))
        if j.get("paymentVerified"):
            s += 5
        scores.append(min(100, s))
    return round(statistics.mean(scores))


def median_proposals(jobs):
    ps = [j["proposals"] for j in jobs if j.get("proposals") is not None]
    return statistics.median(ps) if ps else None


def jobs_last_24h(jobs):
    now = datetime.now(timezone.utc)
    c = 0
    for j in jobs:
        pub = j.get("postedAt")
        if not pub:
            continue
        try:
            dt = datetime.fromisoformat(pub.replace("Z", "+00:00"))
            if (now - dt).total_seconds() <= 86400:
                c += 1
        except ValueError:
            pass
    return c


def main():
    if not RAW.exists():
        print("Missing raw-searches.json", file=sys.stderr)
        sys.exit(1)
    data = json.loads(RAW.read_text())
    run_at = data.get("runAt") or datetime.now(timezone.utc).isoformat()
    hours = data.get("windowHours", 2)
    cutoff = datetime.fromisoformat(run_at.replace("Z", "+00:00")) - __import__("datetime").timedelta(hours=hours)

    state = {}
    if STATE_FILE.exists():
        state = json.loads(STATE_FILE.read_text())
    run_number = state.get("runNumber", 0) + 1
    known = set(state.get("knownJobUrls", []))

    existing_jobs = {}
    if JOBS_FILE.exists():
        for line in JOBS_FILE.read_text().splitlines():
            if not line.strip():
                continue
            o = json.loads(line)
            existing_jobs[o["url"]] = o

    new_jobs = []
    errors = data.get("errors", [])
    keywords_attempted = len(data.get("searches", []))
    keywords_completed = sum(1 for s in data.get("searches", []) if s.get("status") == "ok")

    for search in data.get("searches", []):
        kw = search.get("keyword")
        group = KW_TO_GROUP.get(kw, "OTHER")
        if search.get("status") != "ok":
            continue
        for j in search.get("jobs", []):
            rec = job_from_raw(j, kw, group, cutoff)
            if not rec:
                continue
            url = rec["url"]
            if url in existing_jobs:
                ek = existing_jobs[url]
                mks = set(ek.get("matchedKeyword", []))
                mks.update(rec["matchedKeyword"])
                ek["matchedKeyword"] = sorted(mks)
                continue
            if url in {x["url"] for x in new_jobs}:
                for nj in new_jobs:
                    if nj["url"] == url:
                        nj["matchedKeyword"] = sorted(set(nj["matchedKeyword"] + [kw]))
                continue
            new_jobs.append(rec)

    with JOBS_FILE.open("a") as f:
        for j in new_jobs:
            out = {k: v for k, v in j.items() if k not in ("budgetFixed", "rateHourly", "clientSpendNum")}
            f.write(json.dumps(out) + "\n")
            existing_jobs[j["url"]] = out

    all_jobs = list(existing_jobs.values())
    known.update(existing_jobs.keys())

    kw_stats = {}
    for kw, group in KW_TO_GROUP.items():
        kj = [j for j in all_jobs if kw in j.get("matchedKeyword", [])]
        fixed = [j["budgetFixed"] for j in kj if j.get("budgetFixed")]
        hourly = [j["rateHourly"] for j in kj if j.get("rateHourly")]
        verified = sum(1 for j in kj if j.get("paymentVerified"))
        high_b = sum(
            1
            for j in kj
            if (j.get("budgetFixed") and j["budgetFixed"] >= 1000)
            or (j.get("rateHourly") and j["rateHourly"] >= 40)
        )
        spends = []
        for j in kj:
            sn = parse_spend(j.get("clientSpend"))
            if sn:
                spends.append(sn)
        kw_stats[kw] = {
            "keywordGroup": group,
            "totalJobs": len(kj),
            "jobsLast24h": jobs_last_24h(kj),
            "avgBudgetFixed": round(statistics.mean(fixed), 2) if fixed else None,
            "avgRateHourly": round(statistics.mean(hourly), 2) if hourly else None,
            "medianProposals": median_proposals(kj),
            "pctVerified": round(100 * verified / len(kj), 1) if kj else 0,
            "avgClientSpend": round(statistics.mean(spends), 2) if spends else None,
            "pctHighBudget": round(100 * high_b / len(kj), 1) if kj else 0,
            "opportunityScore": opportunity_score(kj),
            "sampleConfidence": confidence(len(kj)),
        }

    grp_stats = {}
    for group in KEYWORD_GROUPS:
        gj = [j for j in all_jobs if j.get("keywordGroup") == group]
        grp_stats[group] = {
            "totalJobs": len(gj),
            "jobsLast24h": jobs_last_24h(gj),
            "opportunityScore": opportunity_score(gj),
            "sampleConfidence": confidence(len(gj)),
        }

    plat_stats = {}
    for name, pat in PLATFORMS.items():
        pj = [j for j in all_jobs if pat.search(j.get("title", "") + " " + " ".join(j.get("skills") or []))]
        plat_stats[name] = {
            "jobs": len(pj),
            "avgBudgetFixed": round(statistics.mean([x["budgetFixed"] for x in pj if x.get("budgetFixed")]), 2)
            if any(x.get("budgetFixed") for x in pj)
            else None,
            "avgRateHourly": round(statistics.mean([x["rateHourly"] for x in pj if x.get("rateHourly")]), 2)
            if any(x.get("rateHourly") for x in pj)
            else None,
            "medianProposals": median_proposals(pj),
            "opportunityScore": opportunity_score(pj),
            "sampleConfidence": confidence(len(pj)),
        }

    KW_STATS.write_text(json.dumps(kw_stats, indent=2))
    GRP_STATS.write_text(json.dumps(grp_stats, indent=2))
    PLAT_STATS.write_text(json.dumps(plat_stats, indent=2))

    top3 = sorted(kw_stats.items(), key=lambda x: x[1]["jobsLast24h"], reverse=True)[:3]
    top3k = [k for k, _ in top3]

    log = {
        "timestamp": run_at,
        "runNumber": run_number,
        "keywordsAttempted": keywords_attempted,
        "keywordsCompleted": keywords_completed,
        "newJobs": len(new_jobs),
        "totalJobs": len(all_jobs),
        "top3Keywords": top3k,
        "errors": errors,
    }
    with RUN_LOG.open("a") as f:
        f.write(json.dumps(log) + "\n")

    state_out = {
        "lastRunAt": run_at,
        "runNumber": run_number,
        "totalJobs": len(all_jobs),
        "knownJobUrls": sorted(known),
        "lastInsightRefresh": state.get("lastInsightRefresh"),
    }
    STATE_FILE.write_text(json.dumps(state_out, indent=2))

    top_kw = sorted(kw_stats.items(), key=lambda x: x[1]["opportunityScore"], reverse=True)[:10]
    top_groups = sorted(grp_stats.items(), key=lambda x: x[1]["opportunityScore"], reverse=True)

    lines = [
        "# Upwork Market Intelligence",
        "",
        f"Last updated: {run_at}",
        f"Run: {run_number}",
        f"Total jobs tracked: {len(all_jobs)}",
        f"Keywords attempted: {keywords_attempted}",
        f"Keywords completed: {keywords_completed}",
        "",
        "## Top Opportunities",
        "",
    ]
    for i, (k, st) in enumerate(top_kw, 1):
        lines.append(
            f"{i}. **{k}** — score {st['opportunityScore']} ({st['sampleConfidence']}) | "
            f"24h: {st['jobsLast24h']} | total: {st['totalJobs']} | "
            f"fixed avg: {st['avgBudgetFixed']} | hourly avg: {st['avgRateHourly']} | "
            f"median proposals: {st['medianProposals']}"
        )
    lines += ["", "## Strongest Groups", ""]
    for i, (g, st) in enumerate(top_groups[:5], 1):
        lines.append(f"{i}. **{g}** — score {st['opportunityScore']} | 24h: {st['jobsLast24h']} | total: {st['totalJobs']}")
    lines += ["", "## Platform Ranking", ""]
    for i, (p, st) in enumerate(sorted(plat_stats.items(), key=lambda x: x[1]["jobs"], reverse=True), 1):
        lines.append(f"{i}. **{p}** — {st['jobs']} jobs | score {st['opportunityScore']}")
    primary = top_kw[0][0] if top_kw else "web development"
    secondary = top_kw[1][0] if len(top_kw) > 1 else "wordpress developer"
    best_plat = max(plat_stats.items(), key=lambda x: x[1]["opportunityScore"])[0] if plat_stats else "WordPress"
    lines += [
        "",
        "## Positioning Recommendation",
        "",
        f"Primary keyword: {primary}",
        f"Secondary keyword: {secondary}",
        f"Best platform/service: {best_plat}",
        "Overview keywords: Next.js, WordPress, Shopify, Webflow, AI SaaS MVP",
        "Skill tags: React, TypeScript, Supabase, Stripe, CRO, Elementor",
        "",
        "## Current Verdicts",
        "",
        "WordPress: Steady volume; maintenance and Elementor builds common.",
        "Webflow: Lower volume than WordPress; niche premium builds.",
        "Framer: Sparse but design-led.",
        "GoHighLevel: Niche agency funnel work.",
        "AI/Vibe Coding: Growing MVP and production SaaS posts.",
        "Ecommerce: Shopify dominates hourly CRO + build posts.",
        "Maintenance: Retainer-style Shopify/WordPress manager roles appear.",
        "",
        "## Important Changes",
        "",
        "Initial baseline run — no prior comparison." if run_number == 1 else "See run log for deltas.",
    ]
    SUMMARY.write_text("\n".join(lines) + "\n")

    if run_number == 1 and not INSIGHTS.exists():
        INSIGHTS.write_text(
            "# Upwork Intelligence Insights\n\n"
            "- Baseline established on first hourly run.\n"
            "- Shopify + WordPress remain highest-volume platforms in tracked keywords.\n"
        )

    print(json.dumps({"runNumber": run_number, "newJobs": len(new_jobs), "totalJobs": len(all_jobs), "top3": top3k}))


if __name__ == "__main__":
    main()
