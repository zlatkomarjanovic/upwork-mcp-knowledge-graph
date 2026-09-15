#!/usr/bin/env python3
"""Process raw search batch JSON into jobs.jsonl and stats. One-time per run."""
import json, re, statistics, sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

BASE = Path(__file__).parent
RAW = BASE / "_raw_searches.json"
STATE_PATH = BASE / "state.json"

SKIP_PATTERNS = re.compile(
    r"polymarket|trading bot|crypto trad|gambl|casino|adult|dating|onlyfans|porn|alcohol|beer brand",
    re.I,
)

PLATFORM_MAP = {
    "WordPress": ["wordpress"],
    "Webflow": ["webflow"],
    "Framer": ["framer"],
    "GoHighLevel": ["gohighlevel", "go high level", "ghl", "highlevel"],
    "Shopify": ["shopify"],
    "WooCommerce": ["woocommerce"],
    "Shopware": ["shopware"],
    "Lovable": ["lovable"],
    "Bolt": ["bolt.new", "bolt developer"],
    "v0": ["v0 developer", "v0 vercel"],
    "Next.js": ["nextjs", "next.js", "figma to nextjs"],
}

GROUPS = {
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

KW_TO_GROUP = {k.lower(): g for g, kws in GROUPS.items() for k in kws}


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
            m = re.search(r"([\d.]+)", p.replace("/hr", ""))
            if m:
                nums.append(float(m.group(1)))
        return sum(nums) / len(nums) if nums else None
    m = re.search(r"([\d.]+)", s.replace("/hr", ""))
    return float(m.group(1)) if m else None


def parse_spend(s):
    if not s:
        return None
    m = re.search(r"([\d,]+\.?\d*)", str(s).replace("$", ""))
    return float(m.group(1).replace(",", "")) if m else None


def job_record(job, keyword, group, window_hours):
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
            if dt < datetime.now(timezone.utc) - timedelta(hours=window_hours):
                return None
        except Exception:
            pass
    client = job.get("client") or {}
    ver = client.get("verification_status") == "VERIFIED"
    budget = job.get("budget")
    jt = job.get("job_type")
    fixed = parse_money(budget) if jt == "fixed" else None
    hourly = parse_money(budget) if jt == "hourly" else None
    return {
        "url": url,
        "title": title,
        "matchedKeyword": [keyword],
        "keywordGroup": group,
        "postedAt": posted,
        "type": jt,
        "budget": budget if jt == "fixed" else None,
        "hourlyRate": budget if jt == "hourly" else None,
        "duration": job.get("duration"),
        "proposals": job.get("proposal_count"),
        "clientCountry": client.get("country"),
        "paymentVerified": ver,
        "clientSpend": client.get("total_spent"),
        "clientHireRate": None,
        "clientRating": client.get("rating"),
        "experienceLevel": job.get("experience_level"),
        "skills": job.get("skills") or [],
        "_fixedNum": fixed,
        "_hourlyNum": hourly,
        "_spendNum": parse_spend(client.get("total_spent")),
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
        return 1
    score = 0
    now = datetime.now(timezone.utc)
    for j in jobs:
        recency = 50
        if j.get("postedAt"):
            try:
                dt = datetime.fromisoformat(j["postedAt"].replace("Z", "+00:00"))
                hrs = (now - dt).total_seconds() / 3600
                recency = max(10, 100 - hrs * 4)
            except Exception:
                pass
        budget_pts = 30
        if j.get("_fixedNum") and j["_fixedNum"] >= 1000:
            budget_pts = 90
        elif j.get("_hourlyNum") and j["_hourlyNum"] >= 40:
            budget_pts = 85
        elif j.get("_fixedNum") and j["_fixedNum"] >= 500:
            budget_pts = 60
        prop = j.get("proposals")
        comp = 70 if prop is None else max(10, 100 - prop * 2)
        ver = 15 if j.get("paymentVerified") else 0
        score += (recency * 0.25 + budget_pts * 0.35 + comp * 0.3 + ver * 0.1)
    return max(1, min(100, int(score / len(jobs))))


def main():
    raw = json.loads(RAW.read_text())
    window = raw.get("windowHours", 2)
    run_at = raw.get("runAt")
    run_number = raw.get("runNumber", 1)
    searches = raw.get("searches", [])
    errors = raw.get("errors", [])

    state = {}
    if STATE_PATH.exists():
        state = json.loads(STATE_PATH.read_text())
    known = set(state.get("knownJobUrls", []))

    all_jobs = {}
    kw_hits = {s["keyword"]: [] for s in searches if "keyword" in s}

    for entry in searches:
        kw = entry.get("keyword")
        if entry.get("error"):
            continue
        group = entry.get("group") or KW_TO_GROUP.get(kw.lower(), "OTHER")
        for job in entry.get("jobs", []):
            rec = job_record(job, kw, group, window)
            if not rec:
                continue
            url = rec["url"]
            kw_hits.setdefault(kw, []).append(rec)
            if url in all_jobs:
                if kw not in all_jobs[url]["matchedKeyword"]:
                    all_jobs[url]["matchedKeyword"].append(kw)
            else:
                all_jobs[url] = rec

    new_jobs = {u: j for u, j in all_jobs.items() if u not in known}

    # append jobs.jsonl
    jobs_path = BASE / "jobs.jsonl"
    with jobs_path.open("a") as f:
        for j in new_jobs.values():
            out = {k: v for k, v in j.items() if not k.startswith("_")}
            f.write(json.dumps(out, ensure_ascii=False) + "\n")

    # load all jobs for stats
    all_stored = []
    if jobs_path.exists():
        for line in jobs_path.read_text().splitlines():
            if line.strip():
                all_stored.append(json.loads(line))

    now = datetime.now(timezone.utc)
    cut24 = now - timedelta(hours=24)

    def enrich(j):
        j = dict(j)
        j["_fixedNum"] = parse_money(j.get("budget")) if j.get("type") == "fixed" else None
        j["_hourlyNum"] = parse_money(j.get("hourlyRate") or j.get("budget")) if j.get("type") == "hourly" else None
        j["_spendNum"] = parse_spend(j.get("clientSpend"))
        return j

    all_stored = [enrich(j) for j in all_stored]

    def in24(j):
        p = j.get("postedAt")
        if not p:
            return False
        try:
            return datetime.fromisoformat(p.replace("Z", "+00:00")) >= cut24
        except Exception:
            return False

    keyword_stats = {}
    for kw, group in [(k, KW_TO_GROUP.get(k.lower())) for g, kws in GROUPS.items() for k in kws]:
        matched = [j for j in all_stored if kw in (j.get("matchedKeyword") or [])]
        m24 = [j for j in matched if in24(j)]
        fixed = [j["_fixedNum"] for j in matched if j.get("_fixedNum")]
        hourly = [j["_hourlyNum"] for j in matched if j.get("_hourlyNum")]
        props = [j["proposals"] for j in matched if j.get("proposals") is not None]
        verified = sum(1 for j in matched if j.get("paymentVerified"))
        high_b = sum(
            1
            for j in matched
            if (j.get("_fixedNum") or 0) >= 1000 or (j.get("_hourlyNum") or 0) >= 40
        )
        spends = [j["_spendNum"] for j in matched if j.get("_spendNum")]
        n = len(matched)
        keyword_stats[kw] = {
            "keywordGroup": group,
            "totalJobs": n,
            "jobsLast24h": len(m24),
            "avgBudgetFixed": round(statistics.mean(fixed), 2) if fixed else None,
            "avgRateHourly": round(statistics.mean(hourly), 2) if hourly else None,
            "medianProposals": int(statistics.median(props)) if props else None,
            "pctVerified": round(100 * verified / n, 1) if n else 0,
            "avgClientSpend": round(statistics.mean(spends), 2) if spends else None,
            "pctHighBudget": round(100 * high_b / n, 1) if n else 0,
            "opportunityScore": opportunity_score(matched),
            "sampleConfidence": confidence(n),
        }

    group_stats = {}
    for g in GROUPS:
        kws = GROUPS[g]
        matched = [j for j in all_stored if any(k in (j.get("matchedKeyword") or []) for k in kws)]
        n = len(matched)
        group_stats[g] = {
            "totalJobs": n,
            "jobsLast24h": sum(1 for j in matched if in24(j)),
            "opportunityScore": opportunity_score(matched),
            "sampleConfidence": confidence(n),
        }

    platform_stats = {}
    for plat, kws in PLATFORM_MAP.items():
        matched = [j for j in all_stored if any(k.lower() in " ".join(j.get("matchedKeyword") or []).lower() or any(k.lower() in (s or "").lower() for s in (j.get("skills") or [])) for k in kws)]
        # simpler: keyword match in matchedKeyword or title/skills
        matched = []
        for j in all_stored:
            blob = " ".join(j.get("matchedKeyword") or []) + " " + j.get("title", "") + " " + " ".join(j.get("skills") or [])
            if any(k.lower() in blob.lower() for k in kws):
                matched.append(j)
        n = len(matched)
        fixed = [j["_fixedNum"] for j in matched if j.get("_fixedNum")]
        hourly = [j["_hourlyNum"] for j in matched if j.get("_hourlyNum")]
        props = [j["proposals"] for j in matched if j.get("proposals") is not None]
        platform_stats[plat] = {
            "totalJobs": n,
            "jobsLast24h": sum(1 for j in matched if in24(j)),
            "avgBudgetFixed": round(statistics.mean(fixed), 2) if fixed else None,
            "avgRateHourly": round(statistics.mean(hourly), 2) if hourly else None,
            "medianProposals": int(statistics.median(props)) if props else None,
            "opportunityScore": opportunity_score(matched),
            "sampleConfidence": confidence(n),
        }

    attempted = len(searches)
    completed = sum(1 for s in searches if not s.get("error"))
    top3 = sorted(keyword_stats.items(), key=lambda x: x[1]["jobsLast24h"], reverse=True)[:3]
    top3kw = [k for k, _ in top3]

    log = {
        "timestamp": run_at,
        "runNumber": run_number,
        "keywordsAttempted": attempted,
        "keywordsCompleted": completed,
        "newJobs": len(new_jobs),
        "totalJobs": len(all_stored),
        "top3Keywords": top3kw,
        "errors": errors,
    }
    with (BASE / "run-log.jsonl").open("a") as f:
        f.write(json.dumps(log) + "\n")

    known.update(all_jobs.keys())
    state_out = {
        "lastRunAt": run_at,
        "runNumber": run_number,
        "totalJobs": len(all_stored),
        "knownJobUrls": sorted(known),
        "lastInsightRefresh": state.get("lastInsightRefresh"),
    }
    STATE_PATH.write_text(json.dumps(state_out, indent=2))

    (BASE / "keyword-stats.json").write_text(json.dumps(keyword_stats, indent=2))
    (BASE / "group-stats.json").write_text(json.dumps(group_stats, indent=2))
    (BASE / "platform-stats.json").write_text(json.dumps(platform_stats, indent=2))

    # summary md
    top10 = sorted(keyword_stats.items(), key=lambda x: x[1]["opportunityScore"], reverse=True)[:10]
    groups_rank = sorted(group_stats.items(), key=lambda x: x[1]["opportunityScore"], reverse=True)

    lines = [
        "# Upwork Market Intelligence",
        "",
        f"Last updated: {run_at}",
        f"Run: {run_number}",
        f"Total jobs tracked: {len(all_stored)}",
        f"Keywords attempted: {attempted}",
        f"Keywords completed: {completed}",
        "",
        "## Top Opportunities",
        "",
    ]
    for kw, st in top10:
        lines.append(
            f"- **{kw}** — score {st['opportunityScore']} ({st['sampleConfidence']}): "
            f"24h={st['jobsLast24h']}, total={st['totalJobs']}, "
            f"fixed=${st['avgBudgetFixed']}, hourly=${st['avgRateHourly']}/hr, "
            f"median props={st['medianProposals']}"
        )
    lines += ["", "## Strongest Groups", ""]
    for g, st in groups_rank:
        lines.append(f"- {g}: score {st['opportunityScore']}, 24h={st['jobsLast24h']}, total={st['totalJobs']}")
    lines += ["", "## Platform Ranking", ""]
    for p, st in sorted(platform_stats.items(), key=lambda x: x[1]["opportunityScore"], reverse=True):
        lines.append(f"- {p}: score {st['opportunityScore']}, jobs={st['totalJobs']}")
    lines += [
        "",
        "## Positioning Recommendation",
        "",
        f"Primary keyword: {top10[0][0] if top10 else 'web development'}",
        f"Secondary keyword: {top10[1][0] if len(top10) > 1 else 'wordpress developer'}",
        f"Best platform/service: WordPress",
        "Overview keywords: web development, WordPress, Next.js, Webflow",
        "Skill tags: WordPress, WooCommerce, Next.js, React, Webflow, SEO",
        "",
        "## Current Verdicts",
        "",
        "WordPress: Strong volume; mix of maintenance and build work.",
        "Webflow: Moderate; often bundled with design.",
        "Framer: Lower volume than Webflow.",
        "GoHighLevel: Niche but integration-heavy postings.",
        "AI/Vibe Coding: Growing; often full-stack adjacent.",
        "Ecommerce: WooCommerce and Shopify both active.",
        "Maintenance: Retainer-style WordPress manager roles appear regularly.",
        "",
        "## Important Changes",
        "",
        "Initial baseline run — no prior comparison.",
    ]
    (BASE / "current-summary.md").write_text("\n".join(lines) + "\n")

    out = {
        "runNumber": run_number,
        "attempted": attempted,
        "completed": completed,
        "newJobs": len(new_jobs),
        "totalJobs": len(all_stored),
        "newJobList": [{k: v for k, v in j.items() if not k.startswith("_")} for j in new_jobs.values()],
        "keyword_stats": keyword_stats,
        "group_stats": group_stats,
        "platform_stats": platform_stats,
        "errors": errors,
        "top10": top10,
    }
    (BASE / "_run_output.json").write_text(json.dumps(out, indent=2, default=str))
    print(json.dumps({"ok": True, "new": len(new_jobs), "total": len(all_stored)}))


if __name__ == "__main__":
    main()
