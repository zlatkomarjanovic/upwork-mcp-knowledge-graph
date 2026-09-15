#!/usr/bin/env python3
"""One-time processor for Upwork keyword run results."""
import json, re, statistics, sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

BASE = Path(__file__).parent
RESULTS_PATH = BASE / "search-results-raw.json"
RUN_AT = datetime.now(timezone.utc)
_state_pre = BASE / "state.json"
_prev_run = 0
if _state_pre.exists():
    try:
        _prev_run = json.loads(_state_pre.read_text()).get("runNumber", 0)
    except json.JSONDecodeError:
        pass
WINDOW_HOURS = 2 if _prev_run == 0 else 1
CUTOFF = RUN_AT - timedelta(hours=WINDOW_HOURS)

KEYWORD_GROUPS = [
    ("CORE WEB DEVELOPMENT", [
        "web development", "website development", "web developer", "custom website",
        "frontend developer", "full stack developer",
    ]),
    ("WEB DESIGN", [
        "web design", "website design", "website redesign", "landing page design",
        "UI UX website", "responsive web design",
    ]),
    ("WORDPRESS", [
        "wordpress", "wordpress developer", "wordpress website", "wordpress development",
        "wordpress redesign", "wordpress customization", "wordpress migration",
        "wordpress speed optimization", "wordpress maintenance", "woocommerce",
        "elementor developer", "bricks builder",
    ]),
    ("WEBFLOW / FRAMER", [
        "webflow", "webflow developer", "webflow website", "webflow redesign",
        "figma to webflow", "framer", "framer developer", "framer website",
        "framer redesign", "figma to framer",
    ]),
    ("AI / VIBE CODING", [
        "AI web development", "AI web developer", "vibe coding", "claude code developer",
        "cursor AI developer", "lovable developer", "lovable app", "bolt developer",
        "bolt.new", "v0 developer", "v0 vercel", "replit developer", "supabase developer",
        "AI agent integration website",
    ]),
    ("GOHIGHLEVEL", [
        "gohighlevel", "go high level", "GHL", "gohighlevel developer",
        "gohighlevel website", "gohighlevel funnel", "gohighlevel automation", "gohighlevel CRM",
    ]),
    ("ADJACENT PLATFORMS", [
        "squarespace website", "wix website", "wix studio", "bubble developer",
    ]),
    ("MODERN STACK", [
        "nextjs developer", "next.js developer", "nextjs website", "react developer",
        "figma to nextjs", "tailwind developer", "astro developer", "sanity CMS",
    ]),
    ("ECOMMERCE", [
        "ecommerce website", "ecommerce developer", "shopify developer", "shopify website",
        "woocommerce developer", "shopware", "shopware developer", "shopware 6", "headless ecommerce",
    ]),
    ("MAINTENANCE / RETAINERS", [
        "website maintenance", "website maintenance monthly", "website support ongoing",
        "website management ongoing", "wordpress support retainer", "webflow maintenance",
        "shopify maintenance", "ongoing web developer", "web development retainer",
    ]),
    ("CONVERSION / PERFORMANCE", [
        "conversion rate optimization", "landing page optimization", "website audit",
        "core web vitals", "page speed optimization", "website speed optimization", "technical SEO website",
    ]),
]

SKIP_PATTERNS = re.compile(
    r"\b(alcohol|beer|wine|liquor|gambling|casino|betting|adult|porn|escort|"
    r"crypto trading|day trading|forex trading|dating app|dating site)\b",
    re.I,
)

PLATFORM_MAP = {
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


def parse_money(s):
    if not s:
        return None
    s = str(s).replace(",", "").replace("$", "")
    if "–" in s or "-" in s:
        parts = re.split(r"[–-]", s)
        nums = []
        for p in parts:
            p = p.strip().replace("/hr", "").replace("hr", "").strip()
            m = re.search(r"[\d.]+", p)
            if m:
                nums.append(float(m.group()))
        if nums:
            return sum(nums) / len(nums)
    m = re.search(r"[\d.]+", s.replace("/hr", ""))
    return float(m.group()) if m else None


def parse_spend(s):
    if not s:
        return None
    m = re.search(r"[\d,]+\.?\d*", str(s).replace("$", ""))
    if not m:
        return None
    return float(m.group().replace(",", ""))


def job_record(job, keyword, group):
    url = norm_url(job.get("url"))
    if not url:
        return None
    title = job.get("title") or ""
    desc = job.get("description_snippet") or ""
    if SKIP_PATTERNS.search(title + " " + desc):
        return None
    posted = job.get("published_date") or job.get("created_date")
    if posted:
        try:
            dt = datetime.fromisoformat(posted.replace("Z", "+00:00"))
            if dt < CUTOFF:
                return None
        except ValueError:
            pass
    client = job.get("client") or {}
    return {
        "url": url,
        "title": title,
        "matchedKeyword": [keyword],
        "keywordGroup": group,
        "postedAt": posted,
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
        "skills": job.get("skills"),
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
    score = 0
    for j in jobs:
        recency = 1
        if j.get("postedAt"):
            try:
                dt = datetime.fromisoformat(j["postedAt"].replace("Z", "+00:00"))
                age_h = (RUN_AT - dt).total_seconds() / 3600
                recency = max(0.2, 1 - age_h / 24)
            except ValueError:
                pass
        props = j.get("proposals") or 10
        comp = max(0.3, 1 - min(props, 50) / 50)
        budget = parse_money(j.get("budget"))
        pay = 0.5
        if j.get("type") == "fixed" and budget and budget >= 1000:
            pay = 1
        elif j.get("type") == "hourly" and budget and budget >= 40:
            pay = 1
        elif budget and budget >= 200:
            pay = 0.7
        verified = 1 if j.get("paymentVerified") else 0.6
        score += recency * comp * pay * verified * 10
    return min(100, int(score / max(len(jobs), 1) * 3))


def aggregate_jobs(all_jobs):
    by_kw = {}
    for j in all_jobs:
        for kw in j["matchedKeyword"]:
            by_kw.setdefault(kw, []).append(j)
    stats = {}
    now = RUN_AT
    for kw, jobs in by_kw.items():
        j24 = [x for x in jobs if x.get("postedAt") and (
            now - datetime.fromisoformat(x["postedAt"].replace("Z", "+00:00"))
        ).total_seconds() <= 86400]
        fixed = [parse_money(x["budget"]) for x in jobs if x.get("type") == "fixed"]
        fixed = [f for f in fixed if f is not None]
        hourly = [parse_money(x["budget"]) for x in jobs if x.get("type") == "hourly"]
        hourly = [h for h in hourly if h is not None]
        props = [x["proposals"] for x in jobs if x.get("proposals") is not None]
        verified = sum(1 for x in jobs if x.get("paymentVerified"))
        high = 0
        for x in jobs:
            b = parse_money(x.get("budget"))
            if x.get("type") == "fixed" and b and b >= 1000:
                high += 1
            elif x.get("type") == "hourly" and b and b >= 40:
                high += 1
        spends = [parse_spend(x.get("clientSpend")) for x in jobs]
        spends = [s for s in spends if s is not None]
        stats[kw] = {
            "totalJobs": len(jobs),
            "jobsLast24h": len(j24),
            "avgBudgetFixed": round(statistics.mean(fixed), 2) if fixed else None,
            "avgRateHourly": round(statistics.mean(hourly), 2) if hourly else None,
            "medianProposals": int(statistics.median(props)) if props else None,
            "pctVerified": round(100 * verified / len(jobs), 1) if jobs else 0,
            "avgClientSpend": round(statistics.mean(spends), 2) if spends else None,
            "pctHighBudget": round(100 * high / len(jobs), 1) if jobs else 0,
            "opportunityScore": opportunity_score(jobs),
            "sampleConfidence": confidence(len(jobs)),
        }
    return stats


def main():
    data = json.loads(RESULTS_PATH.read_text())
    searches = data.get("searches", [])
    errors = []
    jobs_map = {}
    keywords_attempted = sum(len(k[1]) for k in KEYWORD_GROUPS)
    keywords_completed = 0
    for item in searches:
        kw = item["keyword"]
        group = item["group"]
        if item.get("error"):
            errors.append(kw)
            continue
        keywords_completed += 1
        for job in item.get("jobs", []):
            rec = job_record(job, kw, group)
            if not rec:
                continue
            u = rec["url"]
            if u in jobs_map:
                existing = jobs_map[u]
                for mk in rec["matchedKeyword"]:
                    if mk not in existing["matchedKeyword"]:
                        existing["matchedKeyword"].append(mk)
            else:
                jobs_map[u] = rec

    all_jobs = list(jobs_map.values())
    jobs_path = BASE / "jobs.jsonl"
    if jobs_path.exists():
        merged = {j["url"]: j for j in all_jobs}
        for line in jobs_path.read_text().splitlines():
            if not line.strip():
                continue
            j = json.loads(line)
            u = j["url"]
            if u in merged:
                for mk in j.get("matchedKeyword", []):
                    if mk not in merged[u]["matchedKeyword"]:
                        merged[u]["matchedKeyword"].append(mk)
            else:
                merged[u] = j
        all_jobs = list(merged.values())
    run_number = 1
    state_path = BASE / "state.json"
    known = set()
    if state_path.exists():
        st = json.loads(state_path.read_text())
        run_number = st.get("runNumber", 0) + 1
        known = set(st.get("knownJobUrls", []))

    new_jobs = [j for j in all_jobs if j["url"] not in known]
    with (BASE / "jobs.jsonl").open("a") as f:
        for j in new_jobs:
            f.write(json.dumps(j, ensure_ascii=False) + "\n")

    all_known = known | {j["url"] for j in all_jobs}
    total_jobs = len(all_known)

    kw_stats = aggregate_jobs(all_jobs)
    group_stats = {}
    for gname, kws in KEYWORD_GROUPS:
        gj = []
        for j in all_jobs:
            if any(k in j["matchedKeyword"] for k in kws):
                gj.append(j)
        group_stats[gname] = {
            "totalJobs": len(gj),
            "jobsLast24h": sum(1 for x in gj if x.get("postedAt") and (
                RUN_AT - datetime.fromisoformat(x["postedAt"].replace("Z", "+00:00"))
            ).total_seconds() <= 86400),
            "opportunityScore": opportunity_score(gj),
            "sampleConfidence": confidence(len(gj)),
        }

    platform_stats = {}
    for pname, pat in PLATFORM_MAP.items():
        pj = [j for j in all_jobs if pat.search(j.get("title", "") + " " + " ".join(j.get("skills") or []))]
        fixed = [parse_money(x["budget"]) for x in pj if x.get("type") == "fixed"]
        fixed = [f for f in fixed if f is not None]
        hourly = [parse_money(x["budget"]) for x in pj if x.get("type") == "hourly"]
        hourly = [h for h in hourly if h is not None]
        props = [x["proposals"] for x in pj if x.get("proposals") is not None]
        platform_stats[pname] = {
            "jobs": len(pj),
            "avgBudgetFixed": round(statistics.mean(fixed), 2) if fixed else None,
            "avgRateHourly": round(statistics.mean(hourly), 2) if hourly else None,
            "medianProposals": int(statistics.median(props)) if props else None,
            "opportunityScore": opportunity_score(pj),
            "sampleConfidence": confidence(len(pj)),
        }

    (BASE / "keyword-stats.json").write_text(json.dumps(kw_stats, indent=2))
    (BASE / "group-stats.json").write_text(json.dumps(group_stats, indent=2))
    (BASE / "platform-stats.json").write_text(json.dumps(platform_stats, indent=2))

    top3 = sorted(kw_stats.items(), key=lambda x: x[1]["jobsLast24h"], reverse=True)[:3]
    log = {
        "timestamp": RUN_AT.isoformat(),
        "runNumber": run_number,
        "keywordsAttempted": keywords_attempted,
        "keywordsCompleted": keywords_completed,
        "newJobs": len(new_jobs),
        "totalJobs": total_jobs,
        "top3Keywords": [t[0] for t in top3],
        "errors": sorted(set(errors)),
    }
    errors = sorted(set(errors))
    with (BASE / "run-log.jsonl").open("a") as f:
        f.write(json.dumps(log) + "\n")

    state = {
        "lastRunAt": RUN_AT.isoformat(),
        "runNumber": run_number,
        "totalJobs": total_jobs,
        "knownJobUrls": sorted(all_known),
        "lastInsightRefresh": RUN_AT.isoformat(),
    }
    state_path.write_text(json.dumps(state, indent=2))

    top10 = sorted(kw_stats.items(), key=lambda x: (x[1]["opportunityScore"], x[1]["jobsLast24h"]), reverse=True)[:10]
    summary_lines = [
        "# Upwork Market Intelligence",
        "",
        f"Last updated: {RUN_AT.isoformat()}",
        f"Run: {run_number}",
        f"Total jobs tracked: {total_jobs}",
        f"Keywords attempted: {keywords_attempted}",
        f"Keywords completed: {keywords_completed}",
        "",
        "## Top Opportunities",
        "",
    ]
    for kw, st in top10:
        summary_lines.append(
            f"- **{kw}**: jobs24h={st['jobsLast24h']}, total={st['totalJobs']}, "
            f"fixed=${st['avgBudgetFixed']}, hourly=${st['avgRateHourly']}/hr, "
            f"median props={st['medianProposals']}, score={st['opportunityScore']}, {st['sampleConfidence']}"
        )
    summary_lines += ["", "## Strongest Groups", ""]
    for gname, gst in sorted(group_stats.items(), key=lambda x: x[1]["opportunityScore"], reverse=True)[:5]:
        summary_lines.append(
            f"- **{gname}**: jobs24h={gst['jobsLast24h']}, total={gst['totalJobs']}, score={gst['opportunityScore']}, {gst['sampleConfidence']}"
        )
    summary_lines += ["", "## Platform Ranking", ""]
    for pname, pst in sorted(platform_stats.items(), key=lambda x: x[1]["opportunityScore"], reverse=True):
        summary_lines.append(
            f"- **{pname}**: jobs={pst['jobs']}, score={pst['opportunityScore']}, {pst['sampleConfidence']}"
        )
    top_kw = top10[0][0] if top10 else "wordpress"
    summary_lines += [
        "",
        "## Positioning Recommendation",
        "",
        f"Primary keyword: {top_kw}",
        "Secondary keyword: webflow developer",
        "Best platform/service: WordPress + Elementor maintenance",
        "Overview keywords: WordPress, Webflow, Next.js, GoHighLevel, AI website builder",
        "Skill tags: WordPress, Elementor, Webflow, Next.js, Lovable, GoHighLevel, CRO",
        "",
        "## Current Verdicts",
        "",
        "WordPress: Strong hourly refresh + maintenance; malware/security spikes; budgets mixed.",
        "Webflow: Steady small fixes, SEO/AEO backend, and Figma implementation.",
        "Framer: Niche portfolio updates; lower volume than Webflow.",
        "GoHighLevel: Pipelines, webhooks, landing pages for Meta funnels.",
        "AI/Vibe Coding: Lovable site builds with high-spend clients; production handoff demand.",
        "Ecommerce: Shopify CRO and revamp; WooCommerce optimization at higher fixed budgets.",
        "Maintenance: Retainer-style WordPress manager roles; low hourly on some listings.",
        "",
        "## Important Changes",
        "",
        (
            f"Run {run_number}: {keywords_completed}/{keywords_attempted} keyword searches persisted. "
            + ("Full coverage." if keywords_completed >= keywords_attempted else "Retry failed/deferred keywords next hour.")
        ),
        "",
    ]
    (BASE / "current-summary.md").write_text("\n".join(summary_lines) + "\n")

    if run_number == 1:
        insights = """# Upwork Intelligence Insights

## Initial baseline (Run 1)

- Tracking started with full keyword sweep across web dev, WordPress, no-code platforms, AI builders, GHL, ecommerce, maintenance, and CRO terms.
- Opportunity scores will stabilize after several hourly runs; treat early scores as directional only.
"""
        (BASE / "insights.md").write_text(insights)

    out = {
        "runNumber": run_number,
        "keywordsAttempted": keywords_attempted,
        "keywordsCompleted": keywords_completed,
        "newJobs": new_jobs,
        "totalJobs": total_jobs,
        "kw_stats": kw_stats,
        "group_stats": group_stats,
        "platform_stats": platform_stats,
        "errors": errors,
        "top10": top10,
    }
    (BASE / "_run_output.json").write_text(json.dumps(out, default=str, indent=2))
    print(json.dumps({"run": run_number, "new": len(new_jobs), "total": total_jobs, "completed": keywords_completed}))


if __name__ == "__main__":
    main()
