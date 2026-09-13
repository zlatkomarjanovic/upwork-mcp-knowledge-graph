#!/usr/bin/env python3
"""One-shot processor for hourly Upwork tracker run. Reads raw MCP batch file."""
import json, re, statistics, os
from datetime import datetime, timezone, timedelta
from pathlib import Path

BASE = Path(__file__).parent
RAW = BASE / "_raw_searches.json"
STATE_FILE = BASE / "state.json"
JOBS_FILE = BASE / "jobs.jsonl"
RUN_LOG = BASE / "run-log.jsonl"

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

SKIP_PATTERNS = re.compile(
    r"\b(alcohol|gambling|adult content|crypto trading|dating)\b", re.I
)

PLATFORM_MAP = {
    "WordPress": ["wordpress"],
    "Webflow": ["webflow"],
    "Framer": ["framer"],
    "GoHighLevel": ["gohighlevel", "highlevel", "go high level", "ghl"],
    "Shopify": ["shopify"],
    "WooCommerce": ["woocommerce"],
    "Shopware": ["shopware"],
    "Lovable": ["lovable"],
    "Bolt": ["bolt.new", "bolt developer", "bolt"],
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
    s = str(s).replace(",", "").replace("$", "")
    if "–" in s or "-" in s:
        parts = re.split(r"[–-]", s)
        nums = []
        for p in parts:
            m = re.search(r"([\d.]+)", p)
            if m:
                nums.append(float(m.group(1)))
        return sum(nums) / len(nums) if nums else None
    m = re.search(r"([\d.]+)", s)
    return float(m.group(1)) if m else None


def parse_hourly_rate(budget, job_type):
    if job_type != "hourly" or not budget:
        return None
    return parse_money(budget)


def parse_fixed(budget, job_type):
    if job_type != "fixed" or not budget:
        return None
    return parse_money(budget)


def is_high_budget(job):
    if job.get("type") == "fixed":
        b = job.get("budgetFixed")
        return b is not None and b >= 1000
    if job.get("type") == "hourly":
        r = job.get("budgetHourly")
        return r is not None and r >= 40
    return False


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


def job_from_api(j, keyword, group, window_start):
    url = norm_url(j.get("url"))
    if not url:
        return None
    pub = j.get("published_date") or j.get("created_date")
    if pub:
        try:
            dt = datetime.fromisoformat(pub.replace("Z", "+00:00"))
            if dt < window_start:
                return None
        except ValueError:
            pass
    title = j.get("title") or ""
    snippet = j.get("description_snippet") or ""
    if SKIP_PATTERNS.search(title + " " + snippet):
        return None
    client = j.get("client") or {}
    jt = j.get("job_type")
    budget = j.get("budget")
    return {
        "url": url,
        "title": title,
        "matchedKeyword": [keyword],
        "keywordGroup": group,
        "postedAt": pub,
        "type": jt,
        "budget": budget,
        "budgetFixed": parse_fixed(budget, jt),
        "budgetHourly": parse_hourly_rate(budget, jt),
        "duration": j.get("duration"),
        "proposals": j.get("proposal_count"),
        "clientCountry": client.get("country"),
        "paymentVerified": client.get("verification_status") == "VERIFIED",
        "clientSpend": client.get("total_spent"),
        "clientHireRate": None,
        "clientRating": client.get("rating"),
        "experienceLevel": j.get("experience_level"),
        "skills": j.get("skills"),
    }


def opportunity_score(stats):
    recent = stats.get("jobsLast24h", 0)
    total = stats.get("totalJobs", 0)
    med_prop = stats.get("medianProposals")
    avg_fixed = stats.get("avgBudgetFixed") or 0
    avg_hourly = stats.get("avgRateHourly") or 0
    pct_v = stats.get("pctVerified") or 0
    pct_hb = stats.get("pctHighBudget") or 0
    prop_factor = 50 - min(med_prop or 25, 50)
    pay = min(avg_fixed / 50, 40) + min(avg_hourly, 40)
    score = (
        min(recent * 8, 40)
        + min(total, 20)
        + prop_factor * 0.4
        + pay * 0.3
        + pct_v * 0.15
        + pct_hb * 0.25
    )
    return max(1, min(100, int(round(score))))


def compute_keyword_stats(all_jobs, keyword):
    jobs = [j for j in all_jobs if keyword in j.get("matchedKeyword", [])]
    now = datetime.now(timezone.utc)
    d24 = now - timedelta(hours=24)
    recent = []
    for j in jobs:
        try:
            dt = datetime.fromisoformat((j.get("postedAt") or "").replace("Z", "+00:00"))
            if dt >= d24:
                recent.append(j)
        except (ValueError, TypeError):
            pass
    fixed = [j["budgetFixed"] for j in jobs if j.get("budgetFixed")]
    hourly = [j["budgetHourly"] for j in jobs if j.get("budgetHourly")]
    props = [j["proposals"] for j in jobs if j.get("proposals") is not None]
    verified = [j for j in jobs if j.get("paymentVerified")]
    spends = []
    for j in jobs:
        sp = j.get("clientSpend")
        if sp:
            m = re.search(r"([\d,.]+)", str(sp))
            if m:
                spends.append(float(m.group(1).replace(",", "")))
    hb = sum(1 for j in jobs if is_high_budget(j))
    st = {
        "totalJobs": len(jobs),
        "jobsLast24h": len(recent),
        "avgBudgetFixed": round(statistics.mean(fixed), 2) if fixed else None,
        "avgRateHourly": round(statistics.mean(hourly), 2) if hourly else None,
        "medianProposals": int(statistics.median(props)) if props else None,
        "pctVerified": round(100 * len(verified) / len(jobs), 1) if jobs else 0,
        "avgClientSpend": round(statistics.mean(spends), 2) if spends else None,
        "pctHighBudget": round(100 * hb / len(jobs), 1) if jobs else 0,
    }
    st["sampleConfidence"] = confidence_label(st["totalJobs"])
    st["opportunityScore"] = opportunity_score(st)
    return st


def main():
    raw = json.loads(RAW.read_text())
    run_at = datetime.fromisoformat(raw["runAt"].replace("Z", "+00:00"))
    first_run = not STATE_FILE.exists()
    window_hours = 2 if first_run else 1
    window_start = run_at - timedelta(hours=window_hours)

    state = {}
    known = set()
    if STATE_FILE.exists():
        state = json.loads(STATE_FILE.read_text())
        known = set(state.get("knownJobUrls", []))
        run_number = state.get("runNumber", 0) + 1
    else:
        run_number = 1
        if JOBS_FILE.exists():
            for line in JOBS_FILE.read_text().splitlines():
                if line.strip():
                    known.add(json.loads(line).get("url"))

    merged = {}
    errors = raw.get("errors", [])
    keywords_attempted = raw.get("keywordsAttempted", 0)
    keywords_completed = raw.get("keywordsCompleted", 0)

    for entry in raw.get("searches", []):
        kw = entry["keyword"]
        group = entry["group"]
        if entry.get("error"):
            errors.append(kw)
            continue
        for j in entry.get("jobs", []):
            job = job_from_api(j, kw, group, window_start)
            if not job:
                continue
            u = job["url"]
            if u in merged:
                if kw not in merged[u]["matchedKeyword"]:
                    merged[u]["matchedKeyword"].append(kw)
            else:
                merged[u] = job

    new_jobs = [j for u, j in merged.items() if u not in known]
    with JOBS_FILE.open("a") as f:
        for j in new_jobs:
            f.write(json.dumps(j, ensure_ascii=False) + "\n")
            known.add(j["url"])

    all_jobs = []
    if JOBS_FILE.exists():
        for line in JOBS_FILE.read_text().splitlines():
            if line.strip():
                all_jobs.append(json.loads(line))

    kw_stats = {}
    for group, kws in KEYWORD_GROUPS.items():
        for kw in kws:
            kw_stats[kw] = {**compute_keyword_stats(all_jobs, kw), "keywordGroup": group}

    group_stats = {}
    for group, kws in KEYWORD_GROUPS.items():
        gj = [j for j in all_jobs if j.get("keywordGroup") == group or any(k in j.get("matchedKeyword", []) for k in kws)]
        st = compute_keyword_stats(gj, "__dummy__") if False else None
        # aggregate by group membership via matched keywords
        gj = [j for j in all_jobs if any(k in j.get("matchedKeyword", []) for k in kws)]
        fixed = [j["budgetFixed"] for j in gj if j.get("budgetFixed")]
        hourly = [j["budgetHourly"] for j in gj if j.get("budgetHourly")]
        props = [j["proposals"] for j in gj if j.get("proposals") is not None]
        now = datetime.now(timezone.utc)
        d24 = now - timedelta(hours=24)
        recent_n = 0
        for j in gj:
            try:
                dt = datetime.fromisoformat((j.get("postedAt") or "").replace("Z", "+00:00"))
                if dt >= d24:
                    recent_n += 1
            except (ValueError, TypeError):
                pass
        verified = [j for j in gj if j.get("paymentVerified")]
        hb = sum(1 for j in gj if is_high_budget(j))
        gs = {
            "totalJobs": len(gj),
            "jobsLast24h": recent_n,
            "avgBudgetFixed": round(statistics.mean(fixed), 2) if fixed else None,
            "avgRateHourly": round(statistics.mean(hourly), 2) if hourly else None,
            "medianProposals": int(statistics.median(props)) if props else None,
            "pctVerified": round(100 * len(verified) / len(gj), 1) if gj else 0,
            "pctHighBudget": round(100 * hb / len(gj), 1) if gj else 0,
        }
        gs["sampleConfidence"] = confidence_label(gs["totalJobs"])
        gs["opportunityScore"] = opportunity_score(gs)
        group_stats[group] = gs

    platform_stats = {}
    for plat, needles in PLATFORM_MAP.items():
        pj = [
            j for j in all_jobs
            if any(n.lower() in " ".join(j.get("matchedKeyword", [])).lower() for n in needles)
            or any(n.lower() in " ".join(j.get("skills") or []).lower() for n in needles)
            or any(n.lower() in (j.get("title") or "").lower() for n in needles)
        ]
        fixed = [j["budgetFixed"] for j in pj if j.get("budgetFixed")]
        hourly = [j["budgetHourly"] for j in pj if j.get("budgetHourly")]
        props = [j["proposals"] for j in pj if j.get("proposals") is not None]
        ps = {
            "jobs": len(pj),
            "avgBudgetFixed": round(statistics.mean(fixed), 2) if fixed else None,
            "avgRateHourly": round(statistics.mean(hourly), 2) if hourly else None,
            "medianProposals": int(statistics.median(props)) if props else None,
        }
        ps["sampleConfidence"] = confidence_label(ps["jobs"])
        ps["opportunityScore"] = opportunity_score({"totalJobs": ps["jobs"], "jobsLast24h": ps["jobs"], **ps})
        platform_stats[plat] = ps

    top3 = sorted(kw_stats.items(), key=lambda x: x[1]["jobsLast24h"], reverse=True)[:3]
    top3_kw = [k for k, _ in top3]

    log = {
        "timestamp": run_at.isoformat().replace("+00:00", "Z"),
        "runNumber": run_number,
        "keywordsAttempted": keywords_attempted,
        "keywordsCompleted": keywords_completed,
        "newJobs": len(new_jobs),
        "totalJobs": len(all_jobs),
        "top3Keywords": top3_kw,
        "errors": list(dict.fromkeys(errors)),
    }
    with RUN_LOG.open("a") as f:
        f.write(json.dumps(log) + "\n")

    state_out = {
        "lastRunAt": run_at.isoformat().replace("+00:00", "Z"),
        "runNumber": run_number,
        "totalJobs": len(all_jobs),
        "knownJobUrls": sorted(known),
        "lastInsightRefresh": state.get("lastInsightRefresh"),
    }
    STATE_FILE.write_text(json.dumps(state_out, indent=2))
    (BASE / "keyword-stats.json").write_text(json.dumps(kw_stats, indent=2))
    (BASE / "group-stats.json").write_text(json.dumps(group_stats, indent=2))
    (BASE / "platform-stats.json").write_text(json.dumps(platform_stats, indent=2))

    summary_path = BASE / "current-summary.md"
    top10 = sorted(kw_stats.items(), key=lambda x: x[1]["opportunityScore"], reverse=True)[:10]
    top_groups = sorted(group_stats.items(), key=lambda x: x[1]["opportunityScore"], reverse=True)

    lines = [
        "# Upwork Market Intelligence",
        "",
        f"Last updated: {run_at.isoformat().replace('+00:00', 'Z')}",
        f"Run: {run_number}",
        f"Total jobs tracked: {len(all_jobs)}",
        f"Keywords attempted: {keywords_attempted}",
        f"Keywords completed: {keywords_completed}",
        "",
        "## Top Opportunities",
        "",
    ]
    for kw, st in top10:
        lines.append(
            f"- **{kw}** — score {st['opportunityScore']} ({st['sampleConfidence']}): "
            f"24h={st['jobsLast24h']}, total={st['totalJobs']}, "
            f"fixed=${st['avgBudgetFixed']}, hourly=${st['avgRateHourly']}/hr, "
            f"median proposals={st['medianProposals']}"
        )
    lines += ["", "## Strongest Groups", ""]
    for g, st in top_groups[:5]:
        lines.append(f"- **{g}** — score {st['opportunityScore']}, 24h={st['jobsLast24h']}, total={st['totalJobs']}")
    lines += ["", "## Platform Ranking", ""]
    for p, st in sorted(platform_stats.items(), key=lambda x: x[1]["opportunityScore"], reverse=True):
        lines.append(f"- **{p}** — score {st['opportunityScore']}, jobs={st['jobs']}")

    primary = top10[0][0] if top10 else "web development"
    secondary = top10[1][0] if len(top10) > 1 else "wordpress developer"
    lines += [
        "",
        "## Positioning Recommendation",
        "",
        f"Primary keyword: {primary}",
        f"Secondary keyword: {secondary}",
        f"Best platform/service: WordPress / Next.js hybrid",
        f"Overview keywords: {primary}, {secondary}, full stack developer",
        "Skill tags: Next.js, WordPress, Webflow, Supabase, Shopify",
        "",
        "## Current Verdicts",
        "",
        "WordPress: Steady volume, mixed budgets.",
        "Webflow: Niche but qualified leads.",
        "Framer: Lower volume than Webflow.",
        "GoHighLevel: Funnel/fix demand spikes.",
        "AI/Vibe Coding: Lovable/Supabase finish-work posts.",
        "Ecommerce: Shopify + WooCommerce active.",
        "Maintenance: Retainer keywords slower but less competition.",
        "",
        "## Important Changes",
        "",
        "Initial baseline run." if run_number == 1 else "See chat for deltas.",
    ]
    summary_path.write_text("\n".join(lines) + "\n")

    out = {
        "runNumber": run_number,
        "keywordsAttempted": keywords_attempted,
        "keywordsCompleted": keywords_completed,
        "newJobs": new_jobs,
        "totalJobs": len(all_jobs),
        "kw_stats": kw_stats,
        "group_stats": group_stats,
        "platform_stats": platform_stats,
        "errors": list(dict.fromkeys(errors)),
        "top10": top10,
    }
    (BASE / "_run_output.json").write_text(json.dumps(out, default=str))


if __name__ == "__main__":
    main()
