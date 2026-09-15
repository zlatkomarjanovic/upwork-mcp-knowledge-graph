#!/usr/bin/env python3
"""Process search queue into jobs.jsonl, stats, summary. Run after keyword searches."""
import json, re, statistics, sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from urllib.parse import urlparse, parse_qs, urlunparse

BASE = Path(__file__).resolve().parent
QUEUE = BASE / "_search_queue.jsonl"
JOBS = BASE / "jobs.jsonl"
STATE = BASE / "state.json"
RUN_LOG = BASE / "run-log.jsonl"
KW_STATS = BASE / "keyword-stats.json"
GRP_STATS = BASE / "group-stats.json"
PLAT_STATS = BASE / "platform-stats.json"
SUMMARY = BASE / "current-summary.md"
INSIGHTS = BASE / "insights.md"

SKIP_TITLE = re.compile(
    r"\b(crypto|bitcoin|casino|gambling|betting|poker|adult|porn|escort|dating|hookup|onlyfans|alcohol|brewery|distillery)\b",
    re.I,
)

PLATFORMS = {
    "WordPress": re.compile(r"wordpress", re.I),
    "Webflow": re.compile(r"webflow", re.I),
    "Framer": re.compile(r"framer", re.I),
    "GoHighLevel": re.compile(r"gohighlevel|go high level|\bghl\b|highlevel", re.I),
    "Shopify": re.compile(r"shopify", re.I),
    "WooCommerce": re.compile(r"woocommerce|woo commerce", re.I),
    "Shopware": re.compile(r"shopware", re.I),
    "Lovable": re.compile(r"lovable", re.I),
    "Bolt": re.compile(r"\bbolt\.new\b|\bbolt developer\b", re.I),
    "v0": re.compile(r"\bv0\b|v0 vercel", re.I),
    "Next.js": re.compile(r"next\.?js", re.I),
}


def norm_url(url: str) -> str:
    if not url:
        return ""
    p = urlparse(url.split("?")[0])
    return urlunparse((p.scheme, p.netloc, p.path.rstrip("/"), "", "", ""))


def parse_money(s):
    if not s:
        return None
    s = str(s).replace(",", "")
    m = re.search(r"([\d.]+)", s)
    return float(m.group(1)) if m else None


def parse_hourly(budget_str):
    if not budget_str:
        return None
    nums = re.findall(r"([\d.]+)", str(budget_str).replace(",", ""))
    if not nums:
        return None
    vals = [float(x) for x in nums]
    return sum(vals) / len(vals)


def parse_client_spend(s):
    if not s:
        return None
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


def is_high_budget(job):
    if job.get("type") == "fixed":
        b = job.get("budgetFixed")
        return b is not None and b >= 1000
    if job.get("type") == "hourly":
        r = job.get("budgetHourly")
        return r is not None and r >= 40
    return False


def opportunity_score(jobs, now):
    if not jobs:
        return 1
    recency = 0
    budget = 0
    comp = 0
    verified = 0
    high = 0
    for j in jobs:
        try:
            pub = datetime.fromisoformat(j["postedAt"].replace("Z", "+00:00"))
            hours = (now - pub).total_seconds() / 3600
            recency += max(0, 24 - hours) / 24
        except Exception:
            recency += 0.3
        if j.get("type") == "fixed" and j.get("budgetFixed"):
            budget += min(j["budgetFixed"] / 5000, 1)
        elif j.get("type") == "hourly" and j.get("budgetHourly"):
            budget += min(j["budgetHourly"] / 80, 1)
        pc = j.get("proposals")
        if pc is not None:
            comp += max(0, 1 - pc / 50)
        else:
            comp += 0.5
        if j.get("paymentVerified"):
            verified += 1
        if is_high_budget(j):
            high += 1
    n = len(jobs)
    raw = (recency / n * 30) + (budget / n * 25) + (comp / n * 25) + (verified / n * 10) + (high / n * 10)
    return max(1, min(100, int(raw)))


def job_from_raw(raw, keyword, group):
    url = raw.get("url")
    if not url:
        return None
    title = raw.get("title") or ""
    if SKIP_TITLE.search(title):
        return None
    desc = raw.get("description_snippet") or ""
    if SKIP_TITLE.search(desc):
        return None
    client = raw.get("client") or {}
    jt = raw.get("job_type")
    budget = raw.get("budget")
    fixed = None
    hourly = None
    if jt == "fixed":
        fixed = parse_money(budget)
    elif jt == "hourly":
        hourly = parse_hourly(budget)
    return {
        "url": norm_url(url),
        "title": title,
        "matchedKeyword": [keyword],
        "keywordGroup": group,
        "postedAt": raw.get("published_date") or raw.get("created_date"),
        "type": jt,
        "budget": budget,
        "budgetFixed": fixed,
        "budgetHourly": hourly,
        "duration": raw.get("duration"),
        "proposals": raw.get("proposal_count"),
        "clientCountry": client.get("country"),
        "paymentVerified": client.get("verification_status") == "VERIFIED",
        "clientSpend": parse_client_spend(client.get("total_spent")),
        "clientHireRate": None,
        "clientRating": client.get("rating"),
        "experienceLevel": raw.get("experience_level"),
        "skills": raw.get("skills") or [],
    }


def load_state():
    if STATE.exists():
        return json.loads(STATE.read_text())
    return {"runNumber": 0, "totalJobs": 0, "knownJobUrls": [], "lastRunAt": None, "lastInsightRefresh": None}


def main():
    now = datetime.now(timezone.utc)
    state = load_state()
    run_number = state.get("runNumber", 0) + 1
    first_run = state.get("runNumber", 0) == 0
    window = timedelta(hours=2 if first_run else 1)
    cutoff = now - window

    known = set(state.get("knownJobUrls") or [])
    if not known and JOBS.exists():
        for line in JOBS.read_text().splitlines():
            if line.strip():
                try:
                    known.add(json.loads(line)["url"])
                except Exception:
                    pass

    keywords_attempted = 0
    keywords_completed = 0
    errors = []
    jobs_by_url = {}

    if not QUEUE.exists():
        print("No search queue", file=sys.stderr)
        sys.exit(1)

    for line in QUEUE.read_text().splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        kw = rec.get("keyword")
        group = rec.get("group")
        keywords_attempted += 1
        if rec.get("error"):
            errors.append(kw)
            continue
        if rec.get("status") == "error":
            errors.append(kw)
            continue
        keywords_completed += 1
        jobs = rec.get("jobs") or []
        for raw in jobs:
            j = job_from_raw(raw, kw, group)
            if not j:
                continue
            try:
                pub = datetime.fromisoformat(j["postedAt"].replace("Z", "+00:00"))
                if pub < cutoff:
                    continue
            except Exception:
                continue
            u = j["url"]
            if u in jobs_by_url:
                if kw not in jobs_by_url[u]["matchedKeyword"]:
                    jobs_by_url[u]["matchedKeyword"].append(kw)
            else:
                jobs_by_url[u] = j

    new_jobs = [j for u, j in jobs_by_url.items() if u not in known]
    with JOBS.open("a") as f:
        for j in new_jobs:
            f.write(json.dumps(j, ensure_ascii=False) + "\n")
            known.add(j["url"])

    all_jobs = []
    if JOBS.exists():
        for line in JOBS.read_text().splitlines():
            if line.strip():
                all_jobs.append(json.loads(line))

    now_iso = now.isoformat().replace("+00:00", "Z")
    kw_stats = {}
    for line in QUEUE.read_text().splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        kw = rec["keyword"]
        group = rec["group"]
        kw_jobs = []
        for raw in rec.get("jobs") or []:
            j = job_from_raw(raw, kw, group)
            if not j:
                continue
            try:
                pub = datetime.fromisoformat(j["postedAt"].replace("Z", "+00:00"))
                if pub >= now - timedelta(hours=24):
                    kw_jobs.append(j)
            except Exception:
                pass
        fixed = [j["budgetFixed"] for j in kw_jobs if j.get("budgetFixed")]
        hourly = [j["budgetHourly"] for j in kw_jobs if j.get("budgetHourly")]
        props = [j["proposals"] for j in kw_jobs if j.get("proposals") is not None]
        verified = [j for j in kw_jobs if j.get("paymentVerified")]
        spend = [j["clientSpend"] for j in kw_jobs if j.get("clientSpend")]
        high = [j for j in kw_jobs if is_high_budget(j)]
        total_kw = sum(1 for j in all_jobs if kw in j.get("matchedKeyword", []))
        kw_stats[kw] = {
            "keyword": kw,
            "group": group,
            "totalJobs": total_kw,
            "jobsLast24h": len(kw_jobs),
            "avgBudgetFixed": round(statistics.mean(fixed), 2) if fixed else None,
            "avgRateHourly": round(statistics.mean(hourly), 2) if hourly else None,
            "medianProposals": int(statistics.median(props)) if props else None,
            "pctVerified": round(100 * len(verified) / len(kw_jobs), 1) if kw_jobs else None,
            "avgClientSpend": round(statistics.mean(spend), 2) if spend else None,
            "pctHighBudget": round(100 * len(high) / len(kw_jobs), 1) if kw_jobs else None,
            "opportunityScore": opportunity_score(kw_jobs, now) if kw_jobs else 1,
            "sampleConfidence": confidence(total_kw),
        }

    KW_STATS.write_text(json.dumps(kw_stats, indent=2))

    groups = {}
    for ks in kw_stats.values():
        g = ks["group"]
        groups.setdefault(g, []).append(ks)
    group_stats = {}
    for g, items in groups.items():
        group_stats[g] = {
            "group": g,
            "keywords": len(items),
            "jobsLast24h": sum(i["jobsLast24h"] for i in items),
            "totalJobs": sum(i["totalJobs"] for i in items),
            "avgOpportunityScore": round(statistics.mean([i["opportunityScore"] for i in items]), 1),
        }
    GRP_STATS.write_text(json.dumps(group_stats, indent=2))

    plat_stats = {}
    for name, pat in PLATFORMS.items():
        matched = [j for j in all_jobs if pat.search(" ".join(j.get("matchedKeyword", [])) + " " + j.get("title", "") + " " + " ".join(j.get("skills") or []))]
        recent = []
        for j in matched:
            try:
                pub = datetime.fromisoformat(j["postedAt"].replace("Z", "+00:00"))
                if pub >= now - timedelta(hours=24):
                    recent.append(j)
            except Exception:
                pass
        fixed = [j["budgetFixed"] for j in recent if j.get("budgetFixed")]
        hourly = [j["budgetHourly"] for j in recent if j.get("budgetHourly")]
        props = [j["proposals"] for j in recent if j.get("proposals") is not None]
        plat_stats[name] = {
            "jobs": len(recent),
            "totalJobs": len(matched),
            "avgBudgetFixed": round(statistics.mean(fixed), 2) if fixed else None,
            "avgRateHourly": round(statistics.mean(hourly), 2) if hourly else None,
            "medianProposals": int(statistics.median(props)) if props else None,
            "opportunityScore": opportunity_score(recent, now) if recent else 1,
            "sampleConfidence": confidence(len(matched)),
        }
    PLAT_STATS.write_text(json.dumps(plat_stats, indent=2))

    top_kw = sorted(kw_stats.values(), key=lambda x: (-x["opportunityScore"], -x["jobsLast24h"]))[:10]
    top_groups = sorted(group_stats.values(), key=lambda x: -x["avgOpportunityScore"])[:5]

    primary = top_kw[0]["keyword"] if top_kw else "wordpress developer"
    secondary = top_kw[1]["keyword"] if len(top_kw) > 1 else "webflow developer"

    summary = f"""# Upwork Market Intelligence

Last updated: {now_iso}
Run: {run_number}
Total jobs tracked: {len(all_jobs)}
Keywords attempted: {keywords_attempted}
Keywords completed: {keywords_completed}

## Top Opportunities

"""
    for i, k in enumerate(top_kw, 1):
        summary += f"{i}. **{k['keyword']}** — score {k['opportunityScore']} ({k['sampleConfidence']})\n"
        summary += f"   - jobsLast24h: {k['jobsLast24h']} | total: {k['totalJobs']} | avg fixed: {k['avgBudgetFixed']} | avg hourly: {k['avgRateHourly']} | median proposals: {k['medianProposals']}\n"

    summary += "\n## Strongest Groups\n\n"
    for i, g in enumerate(top_groups, 1):
        summary += f"{i}. {g['group']} — avg score {g['avgOpportunityScore']} | jobs24h {g['jobsLast24h']}\n"

    summary += "\n## Platform Ranking\n\n"
    for i, (name, p) in enumerate(sorted(plat_stats.items(), key=lambda x: -x[1]["opportunityScore"]), 1):
        summary += f"{i}. {name} — score {p['opportunityScore']} | jobs24h {p['jobs']}\n"

    summary += f"""
## Positioning Recommendation

Primary keyword: {primary}
Secondary keyword: {secondary}
Best platform/service: WordPress + Next.js hybrid positioning
Overview keywords: WordPress Developer, Next.js Developer, Webflow Developer, AI Web Developer
Skill tags: WordPress, Elementor, Webflow, Next.js, React, Supabase, GoHighLevel, WooCommerce, Shopify

## Current Verdicts

WordPress: Steady volume, mixed budgets; strong retainer and maintenance overlap.
Webflow: Solid demand for dev + SEO/maintenance; Figma-to-Webflow still active.
Framer: Lower volume than Webflow but less crowded on some posts.
GoHighLevel: Niche but high-value agency/funnel work when it appears.
AI/Vibe Coding: Growing; Claude Code and Lovable show up in real posts.
Ecommerce: Shopify and WooCommerce both active; Shopware quieter.
Maintenance: Retainer-style WordPress and Webflow maintenance posts persist.

## Important Changes

Initial baseline run — tracking started {now_iso}.
"""
    SUMMARY.write_text(summary)

    if not INSIGHTS.exists():
        INSIGHTS.write_text(
            f"# Insights\n\n- Baseline established run {run_number} ({now_iso}).\n- WordPress and general web keywords show the highest overlapping job volume.\n- Webflow maintenance/SEO posts cluster with verified clients at mid budgets.\n"
        )

    top3 = sorted(kw_stats.values(), key=lambda x: -x["jobsLast24h"])[:3]
    log = {
        "timestamp": now_iso,
        "runNumber": run_number,
        "keywordsAttempted": keywords_attempted,
        "keywordsCompleted": keywords_completed,
        "newJobs": len(new_jobs),
        "totalJobs": len(all_jobs),
        "top3Keywords": [t["keyword"] for t in top3],
        "errors": errors,
    }
    with RUN_LOG.open("a") as f:
        f.write(json.dumps(log) + "\n")

    state.update(
        {
            "lastRunAt": now_iso,
            "runNumber": run_number,
            "totalJobs": len(all_jobs),
            "knownJobUrls": list(known)[-5000:],
            "lastInsightRefresh": state.get("lastInsightRefresh"),
        }
    )
    STATE.write_text(json.dumps(state, indent=2))

    # Chat report
    print("UPWORK MARKET UPDATE")
    print(f"Run: {run_number}")
    print(f"Keywords attempted: {keywords_attempted}")
    print(f"Keywords completed: {keywords_completed}")
    print(f"New jobs: {len(new_jobs)}")
    print(f"Total jobs tracked: {len(all_jobs)}")
    print("\nTOP 10 KEYWORDS\n")
    for i, k in enumerate(top_kw, 1):
        print(f"{i}. {k['keyword']} — score {k['opportunityScore']}")
        print(f"   jobs24h: {k['jobsLast24h']} | total: {k['totalJobs']} | avg fixed: {k['avgBudgetFixed']} | avg hourly: {k['avgRateHourly']} | median proposals: {k['medianProposals']} | confidence: {k['sampleConfidence']}")
    print("\nNEW JOBS THIS RUN\n")
    for j in new_jobs:
        print(f"- {j['title']}")
        print(f"  Keyword: {', '.join(j['matchedKeyword'])} | Group: {j['keywordGroup']} | Type: {j['type']} | Budget/rate: {j.get('budget')} | Proposals: {j.get('proposals')} | Country: {j.get('clientCountry')} | Client spend: {j.get('clientSpend')}")
        print(f"  Skills: {', '.join((j.get('skills') or [])[:8])}")
        print(f"  URL: {j['url']}")
    if errors:
        print("\nFAILED SEARCHES\n")
        for e in errors:
            print(f"- {e}")


if __name__ == "__main__":
    main()
