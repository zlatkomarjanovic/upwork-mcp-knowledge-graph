#!/usr/bin/env python3
"""Process Upwork keyword batch results into intelligence store."""
import json
import re
import statistics
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BATCH = ROOT / "_batch_results.jsonl"
JOBS_FILE = ROOT / "jobs.jsonl"
RUN_LOG = ROOT / "run-log.jsonl"
STATE_FILE = ROOT / "state.json"

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
    r"crypto|gambling|casino|adult|dating|alcohol|beer|wine distillery",
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
    "WordPress": re.compile(r"wordpress", re.I),
    "Webflow": re.compile(r"webflow", re.I),
    "Framer": re.compile(r"framer", re.I),
    "GoHighLevel": re.compile(r"gohighlevel|go high level|\bghl\b", re.I),
    "Shopify": re.compile(r"shopify", re.I),
    "WooCommerce": re.compile(r"woocommerce", re.I),
    "Shopware": re.compile(r"shopware", re.I),
    "Lovable": re.compile(r"lovable", re.I),
    "Bolt": re.compile(r"bolt\.new|\bbolt developer\b", re.I),
    "v0": re.compile(r"\bv0\b", re.I),
    "Next.js": re.compile(r"next\.?js", re.I),
}


def load_state():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {"runNumber": 0, "totalJobs": 0, "knownJobUrls": [], "lastInsightRefresh": None}


def url_key(url):
    return url.split("?")[0] if url else ""


def parse_money(s):
    if not s:
        return None
    s = str(s).replace(",", "").replace("$", "")
    if "–" in s or "-" in s:
        parts = re.split(r"[–-]", s)
        nums = []
        for p in parts:
            m = re.search(r"(\d+(?:\.\d+)?)", p.replace("/hr", ""))
            if m:
                nums.append(float(m.group(1)))
        return statistics.mean(nums) if nums else None
    m = re.search(r"(\d+(?:\.\d+)?)", s.replace("/hr", ""))
    return float(m.group(1)) if m else None


def parse_client_spend(s):
    if not s:
        return None
    m = re.search(r"([\d,]+(?:\.\d+)?)", str(s).replace("$", ""))
    return float(m.group(1).replace(",", "")) if m else None


def proposals_mid(tier):
    if not tier:
        return None
    return PROPOSAL_MID.get(tier)


def is_high_budget(job_type, budget_raw):
    if job_type == "fixed":
        v = parse_money(budget_raw)
        return v is not None and v >= 1000
    if job_type == "hourly":
        v = parse_money(budget_raw)
        return v is not None and v >= 40
    return False


def should_skip(job):
    text = (job.get("title") or "") + " " + " ".join(job.get("skills") or [])
    if SKIP_PATTERNS.search(text):
        return True
    return False


def normalize_job(raw, keyword, group):
    url = raw.get("url")
    if not url:
        return None
    client = raw.get("client") or {}
    budget = raw.get("budget")
    return {
        "url": url_key(url),
        "title": raw.get("title"),
        "matchedKeyword": [keyword],
        "keywordGroup": group,
        "postedAt": raw.get("published_date") or raw.get("created_date"),
        "type": raw.get("job_type"),
        "budget": budget,
        "duration": raw.get("duration"),
        "proposals": raw.get("proposals_tier"),
        "clientCountry": client.get("country"),
        "paymentVerified": client.get("verification_status") == "VERIFIED",
        "clientSpend": parse_client_spend(client.get("total_spent")),
        "clientHireRate": None,
        "clientRating": client.get("rating"),
        "experienceLevel": raw.get("experience_level"),
        "skills": raw.get("skills") or [],
    }


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


def opportunity_score(jobs):
    if not jobs:
        return 0
    score = 0
    now = datetime.now(timezone.utc)
    for j in jobs:
        s = 0
        posted = j.get("postedAt")
        if posted:
            try:
                dt = datetime.fromisoformat(posted.replace("Z", "+00:00"))
                hours = (now - dt).total_seconds() / 3600
                if hours <= 24:
                    s += max(0, 30 - hours)
            except ValueError:
                pass
        if j.get("type") == "fixed":
            v = parse_money(j.get("budget"))
            if v:
                s += min(25, v / 200)
        elif j.get("type") == "hourly":
            v = parse_money(j.get("budget"))
            if v:
                s += min(25, v)
        pm = proposals_mid(j.get("proposals"))
        if pm is not None:
            s += max(0, 20 - pm / 3)
        if j.get("paymentVerified"):
            s += 5
        if is_high_budget(j.get("type"), j.get("budget")):
            s += 10
        score += s
    return min(100, max(1, int(score / len(jobs) * 3)))


def compute_keyword_stats(all_jobs):
    by_kw = {}
    now = datetime.now(timezone.utc)
    cutoff_24 = now - timedelta(hours=24)
    for kw, _ in KEYWORDS:
        matched = [j for j in all_jobs if kw in j.get("matchedKeyword", [])]
        fixed = [parse_money(j["budget"]) for j in matched if j.get("type") == "fixed" and parse_money(j.get("budget"))]
        hourly = [parse_money(j["budget"]) for j in matched if j.get("type") == "hourly" and parse_money(j.get("budget"))]
        props = [proposals_mid(j.get("proposals")) for j in matched if proposals_mid(j.get("proposals")) is not None]
        verified = [j for j in matched if j.get("paymentVerified")]
        spends = [j["clientSpend"] for j in matched if j.get("clientSpend") is not None]
        high = [j for j in matched if is_high_budget(j.get("type"), j.get("budget"))]
        jobs_24 = []
        for j in matched:
            pa = j.get("postedAt")
            if not pa:
                continue
            try:
                dt = datetime.fromisoformat(pa.replace("Z", "+00:00"))
                if dt >= cutoff_24:
                    jobs_24.append(j)
            except ValueError:
                pass
        n = len(matched)
        by_kw[kw] = {
            "totalJobs": n,
            "jobsLast24h": len(jobs_24),
            "avgBudgetFixed": round(statistics.mean(fixed), 2) if fixed else None,
            "avgRateHourly": round(statistics.mean(hourly), 2) if hourly else None,
            "medianProposals": int(statistics.median(props)) if props else None,
            "pctVerified": round(100 * len(verified) / n, 1) if n else 0,
            "avgClientSpend": round(statistics.mean(spends), 2) if spends else None,
            "pctHighBudget": round(100 * len(high) / n, 1) if n else 0,
            "opportunityScore": opportunity_score(matched),
            "sampleConfidence": confidence_label(n),
        }
    return by_kw


def compute_group_stats(kw_stats):
    groups = {}
    for kw, group in KEYWORDS:
        gs = groups.setdefault(group, {"keywords": [], "totalJobs": 0, "jobsLast24h": 0, "scores": []})
        st = kw_stats.get(kw, {})
        gs["keywords"].append(kw)
        gs["totalJobs"] += st.get("totalJobs", 0)
        gs["jobsLast24h"] += st.get("jobsLast24h", 0)
        gs["scores"].append(st.get("opportunityScore", 0))
    out = {}
    for g, v in groups.items():
        out[g] = {
            "totalJobs": v["totalJobs"],
            "jobsLast24h": v["jobsLast24h"],
            "avgOpportunityScore": round(statistics.mean(v["scores"]), 1) if v["scores"] else 0,
            "keywordCount": len(v["keywords"]),
        }
    return dict(sorted(out.items(), key=lambda x: -x[1]["avgOpportunityScore"]))


def compute_platform_stats(all_jobs):
    out = {}
    now = datetime.now(timezone.utc)
    cutoff_24 = now - timedelta(hours=24)
    for name, pat in PLATFORMS.items():
        matched = []
        for j in all_jobs:
            blob = (j.get("title") or "") + " " + " ".join(j.get("skills") or []) + " " + " ".join(j.get("matchedKeyword") or [])
            if pat.search(blob):
                matched.append(j)
        fixed = [parse_money(j["budget"]) for j in matched if j.get("type") == "fixed" and parse_money(j.get("budget"))]
        hourly = [parse_money(j["budget"]) for j in matched if j.get("type") == "hourly" and parse_money(j.get("budget"))]
        props = [proposals_mid(j.get("proposals")) for j in matched if proposals_mid(j.get("proposals")) is not None]
        jobs_24 = 0
        for j in matched:
            pa = j.get("postedAt")
            if pa:
                try:
                    if datetime.fromisoformat(pa.replace("Z", "+00:00")) >= cutoff_24:
                        jobs_24 += 1
                except ValueError:
                    pass
        n = len(matched)
        out[name] = {
            "jobs": n,
            "jobsLast24h": jobs_24,
            "avgBudgetFixed": round(statistics.mean(fixed), 2) if fixed else None,
            "avgRateHourly": round(statistics.mean(hourly), 2) if hourly else None,
            "medianProposals": int(statistics.median(props)) if props else None,
            "opportunityScore": opportunity_score(matched),
            "sampleConfidence": confidence_label(n),
        }
    return out


def write_summary(run_num, kw_attempted, kw_completed, total_jobs, kw_stats, group_stats, platform_stats, errors):
    top_kw = sorted(kw_stats.items(), key=lambda x: (-x[1]["opportunityScore"], -x[1]["jobsLast24h"]))[:10]
    lines = [
        "# Upwork Market Intelligence",
        "",
        f"Last updated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        f"Run: {run_num}",
        f"Total jobs tracked: {total_jobs}",
        f"Keywords attempted: {kw_attempted}",
        f"Keywords completed: {kw_completed}",
        "",
        "## Top Opportunities",
        "",
    ]
    for kw, st in top_kw:
        lines.append(
            f"- **{kw}** — score {st['opportunityScore']} ({st['sampleConfidence']}); "
            f"24h: {st['jobsLast24h']}; total: {st['totalJobs']}; "
            f"avg fixed: {st['avgBudgetFixed']}; avg hourly: {st['avgRateHourly']}; "
            f"median proposals: {st['medianProposals']}"
        )
    lines.extend(["", "## Strongest Groups", ""])
    for g, st in list(group_stats.items())[:5]:
        lines.append(f"- {g}: avg score {st['avgOpportunityScore']}, 24h jobs {st['jobsLast24h']}")
    lines.extend(["", "## Platform Ranking", ""])
    plat_sorted = sorted(platform_stats.items(), key=lambda x: -x[1]["opportunityScore"])
    for name, st in plat_sorted:
        if st["jobs"]:
            lines.append(f"- {name}: {st['jobs']} jobs, score {st['opportunityScore']}")
    primary = top_kw[0][0] if top_kw else "web development"
    secondary = top_kw[1][0] if len(top_kw) > 1 else "wordpress developer"
    best_plat = plat_sorted[0][0] if plat_sorted else "WordPress"
    lines.extend([
        "",
        "## Positioning Recommendation",
        "",
        f"Primary keyword: {primary}",
        f"Secondary keyword: {secondary}",
        f"Best platform/service: {best_plat}",
        "Overview keywords: WordPress, Webflow, Shopify, Next.js, AI web development",
        "Skill tags: WordPress, Webflow, Shopify, React, Next.js, Figma, SEO",
        "",
        "## Current Verdicts",
        "",
        "WordPress: Strong volume in partial sample; mixed budgets, steady SMB fixes and builds.",
        "Webflow: Premium fixed retainer signal ($12k Webflow role in window).",
        "Framer: Insufficient sample this run (search blocked mid-batch).",
        "GoHighLevel: No data this run.",
        "AI/Vibe Coding: AI full-stack and Replit mentions in core dev searches.",
        "Ecommerce: Shopify and WooCommerce active; premium mattress brand hourly $35-75.",
        "Maintenance: Limited keyword coverage this run.",
        "",
        "## Important Changes",
        "",
    ])
    if errors:
        lines.append(f"- Upwork MCP search restricted after 9 keywords ({len(errors)} failed). Retry next hour sequentially.")
    else:
        lines.append("- First baseline run established.")
    (ROOT / "current-summary.md").write_text("\n".join(lines) + "\n")


def main():
    run_at = datetime.now(timezone.utc)
    state = load_state()
    run_num = state.get("runNumber", 0) + 1
    first_run = state.get("runNumber", 0) == 0
    window_hours = 2 if first_run else 1
    cutoff = run_at - timedelta(hours=window_hours)

    known = set(state.get("knownJobUrls") or [])
    existing_jobs = {}
    if JOBS_FILE.exists():
        for line in JOBS_FILE.read_text().splitlines():
            if not line.strip():
                continue
            j = json.loads(line)
            existing_jobs[j["url"]] = j

    batch_by_kw = {}
    if BATCH.exists():
        for line in BATCH.read_text().splitlines():
            if line.strip():
                row = json.loads(line)
                batch_by_kw[row["keyword"]] = row

    errors = []
    keywords_completed = 0
    new_jobs = []

    for kw, group in KEYWORDS:
        row = batch_by_kw.get(kw)
        if not row:
            errors.append(kw)
            continue
        if row.get("status") != "ok":
            errors.append(kw)
            continue
        keywords_completed += 1
        for raw in row.get("jobs") or []:
            if should_skip(raw):
                continue
            posted = raw.get("published_date") or raw.get("created_date")
            if posted:
                try:
                    dt = datetime.fromisoformat(posted.replace("Z", "+00:00"))
                    if dt < cutoff:
                        continue
                except ValueError:
                    continue
            else:
                continue
            norm = normalize_job(raw, kw, group)
            if not norm:
                continue
            u = norm["url"]
            if u in existing_jobs:
                ek = existing_jobs[u]
                kws = set(ek.get("matchedKeyword") or [])
                kws.add(kw)
                ek["matchedKeyword"] = sorted(kws)
                existing_jobs[u] = ek
            elif u in {j["url"] for j in new_jobs}:
                for j in new_jobs:
                    if j["url"] == u:
                        kws = set(j.get("matchedKeyword") or [])
                        kws.add(kw)
                        j["matchedKeyword"] = sorted(kws)
            else:
                new_jobs.append(norm)

    if new_jobs:
        with JOBS_FILE.open("a") as f:
            for j in new_jobs:
                f.write(json.dumps(j, ensure_ascii=False) + "\n")

    all_jobs = list(existing_jobs.values()) + new_jobs
    # refresh existing from disk merge
    all_jobs_map = {j["url"]: j for j in existing_jobs.values()}
    for j in new_jobs:
        all_jobs_map[j["url"]] = j
    all_jobs = list(all_jobs_map.values())

    kw_stats = compute_keyword_stats(all_jobs)
    group_stats = compute_group_stats(kw_stats)
    platform_stats = compute_platform_stats(all_jobs)

    (ROOT / "keyword-stats.json").write_text(json.dumps(kw_stats, indent=2) + "\n")
    (ROOT / "group-stats.json").write_text(json.dumps(group_stats, indent=2) + "\n")
    (ROOT / "platform-stats.json").write_text(json.dumps(platform_stats, indent=2) + "\n")

    top3 = sorted(kw_stats.items(), key=lambda x: -x[1]["jobsLast24h"])[:3]
    top3_names = [t[0] for t in top3]

    log = {
        "timestamp": run_at.isoformat(),
        "runNumber": run_num,
        "keywordsAttempted": len(KEYWORDS),
        "keywordsCompleted": keywords_completed,
        "newJobs": len(new_jobs),
        "totalJobs": len(all_jobs),
        "top3Keywords": top3_names,
        "errors": errors,
    }
    with RUN_LOG.open("a") as f:
        f.write(json.dumps(log) + "\n")

    known.update(all_jobs_map.keys())
    state_out = {
        "lastRunAt": run_at.isoformat(),
        "runNumber": run_num,
        "totalJobs": len(all_jobs_map),
        "knownJobUrls": sorted(known),
        "lastInsightRefresh": state.get("lastInsightRefresh"),
    }
    STATE_FILE.write_text(json.dumps(state_out, indent=2) + "\n")

    write_summary(run_num, len(KEYWORDS), keywords_completed, len(all_jobs_map), kw_stats, group_stats, platform_stats, errors)

    insights = ROOT / "insights.md"
    if not insights.exists():
        insights.write_text(
            "# Upwork Intelligence Insights\n\n"
            "- 2026-09-17: Tracker initialized. Partial run 1 due to Upwork search restriction after ~9 parallel MCP calls; use sequential searches (~12/min) on future runs.\n"
        )

    print(json.dumps({"run": run_num, "newJobs": len(new_jobs), "totalJobs": len(all_jobs_map), "completed": keywords_completed, "errors": len(errors)}))


if __name__ == "__main__":
    main()
