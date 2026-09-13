#!/usr/bin/env python3
"""Ingest search batches, append jobs, update stats, summary, run-log."""
import json
import re
import statistics
from datetime import datetime, timezone, timedelta
from pathlib import Path

BASE = Path(__file__).parent
RUN_AT = datetime(2026, 9, 13, 12, 32, 43, tzinfo=timezone.utc)
WINDOW_HOURS = 2
CUTOFF = RUN_AT - timedelta(hours=WINDOW_HOURS)

KEYWORD_GROUPS = {
    "CORE WEB DEVELOPMENT": ["web development", "website development", "web developer", "custom website", "frontend developer", "full stack developer"],
    "WEB DESIGN": ["web design", "website design", "website redesign", "landing page design", "UI UX website", "responsive web design"],
    "WORDPRESS": ["wordpress", "wordpress developer", "wordpress website", "wordpress development", "wordpress redesign", "wordpress customization", "wordpress migration", "wordpress speed optimization", "wordpress maintenance", "woocommerce", "elementor developer", "bricks builder"],
    "WEBFLOW / FRAMER": ["webflow", "webflow developer", "webflow website", "webflow redesign", "figma to webflow", "framer", "framer developer", "framer website", "framer redesign", "figma to framer"],
    "AI / VIBE CODING": ["AI web development", "AI web developer", "vibe coding", "claude code developer", "cursor AI developer", "lovable developer", "lovable app", "bolt developer", "bolt.new", "v0 developer", "v0 vercel", "replit developer", "supabase developer", "AI agent integration website"],
    "GOHIGHLEVEL": ["gohighlevel", "go high level", "GHL", "gohighlevel developer", "gohighlevel website", "gohighlevel funnel", "gohighlevel automation", "gohighlevel CRM"],
    "ADJACENT PLATFORMS": ["squarespace website", "wix website", "wix studio", "bubble developer"],
    "MODERN STACK": ["nextjs developer", "next.js developer", "nextjs website", "react developer", "figma to nextjs", "tailwind developer", "astro developer", "sanity CMS"],
    "ECOMMERCE": ["ecommerce website", "ecommerce developer", "shopify developer", "shopify website", "woocommerce developer", "shopware", "shopware developer", "shopware 6", "headless ecommerce"],
    "MAINTENANCE / RETAINERS": ["website maintenance", "website maintenance monthly", "website support ongoing", "website management ongoing", "wordpress support retainer", "webflow maintenance", "shopify maintenance", "ongoing web developer", "web development retainer"],
    "CONVERSION / PERFORMANCE": ["conversion rate optimization", "landing page optimization", "website audit", "core web vitals", "page speed optimization", "website speed optimization", "technical SEO website"],
}
KW_TO_GROUP = {k: g for g, ks in KEYWORD_GROUPS.items() for k in ks}
ALL_KEYWORDS = [k for ks in KEYWORD_GROUPS.values() for k in ks]

PLATFORM_MAP = {
    "WordPress": ["wordpress"],
    "Webflow": ["webflow"],
    "Framer": ["framer"],
    "GoHighLevel": ["gohighlevel", "go high level", "GHL", "highlevel"],
    "Shopify": ["shopify"],
    "WooCommerce": ["woocommerce"],
    "Shopware": ["shopware"],
    "Lovable": ["lovable"],
    "Bolt": ["bolt"],
    "v0": ["v0"],
    "Next.js": ["nextjs", "next.js"],
}

SKIP_PAT = re.compile(r"alcohol|gambling|adult content|crypto trading|\bdating\b", re.I)


def norm_url(u):
    if not u:
        return None
    return u.split("?")[0]


def kw_for_title(title):
    t = (title or "").lower()
    for kw in ALL_KEYWORDS:
        parts = kw.lower().split()
        if all(p in t for p in parts):
            return kw
    return None


def parse_money(budget_str):
    if not budget_str:
        return None, None
    s = str(budget_str).replace(",", "")
    if "hr" in s.lower():
        nums = re.findall(r"[\d.]+", s)
        if nums:
            vals = [float(x) for x in nums]
            return None, sum(vals) / len(vals)
        return None, None
    m = re.search(r"([\d.]+)", s)
    if m:
        return float(m.group(1)), None
    return None, None


def parse_spend(s):
    if not s:
        return None
    m = re.search(r"([\d,]+\.?\d*)", str(s).replace("$", ""))
    return float(m.group(1).replace(",", "")) if m else None


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
    now = RUN_AT
    for j in jobs:
        posted = j.get("postedAt")
        if posted:
            try:
                dt = datetime.fromisoformat(posted.replace("Z", "+00:00"))
                age_h = max(0.1, (now - dt).total_seconds() / 3600)
                recency = min(30, 30 / age_h)
            except Exception:
                recency = 5
        else:
            recency = 5
        fb, hr = parse_money(j.get("budget") or "")
        pay = 0
        if fb and fb >= 1000:
            pay += 25
        elif fb and fb >= 500:
            pay += 15
        elif fb and fb >= 200:
            pay += 8
        if hr and hr >= 40:
            pay += 25
        elif hr and hr >= 25:
            pay += 12
        props = j.get("proposals") if j.get("proposals") is not None else 50
        comp = max(5, 25 - min(props, 25))
        if j.get("paymentVerified"):
            pay += 5
        score += recency + pay + comp
    return min(100, int(score / len(jobs) * 2))


def job_from_api(j, keyword):
    url = norm_url(j.get("url"))
    if not url:
        return None
    title = j.get("title") or ""
    snippet = j.get("description_snippet") or ""
    if SKIP_PAT.search(title + " " + snippet):
        return None
    posted = j.get("published_date") or j.get("created_date")
    if posted:
        try:
            dt = datetime.fromisoformat(posted.replace("Z", "+00:00"))
            if dt < CUTOFF:
                return None
        except Exception:
            pass
    client = j.get("client") or {}
    verified = client.get("verification_status") == "VERIFIED"
    group = KW_TO_GROUP.get(keyword, "OTHER")
    return {
        "url": url,
        "title": title,
        "matchedKeyword": [keyword],
        "keywordGroup": group,
        "postedAt": posted,
        "type": j.get("job_type"),
        "budget": j.get("budget"),
        "duration": j.get("duration"),
        "proposals": j.get("proposal_count"),
        "clientCountry": client.get("country"),
        "paymentVerified": verified,
        "clientSpend": client.get("total_spent"),
        "clientHireRate": None,
        "clientRating": client.get("rating"),
        "experienceLevel": j.get("experience_level"),
        "skills": j.get("skills") or [],
    }


def load_jobs():
    jobs = {}
    p = BASE / "jobs.jsonl"
    if p.exists():
        for line in p.read_text().splitlines():
            if line.strip():
                j = json.loads(line)
                u = norm_url(j.get("url"))
                if u:
                    jobs[u] = j
    return jobs


def ingest_batch(batch_path):
    """batch: list of {keyword, status, jobs?}"""
    data = json.loads(Path(batch_path).read_text())
    existing = load_jobs()
    new_urls = set()
    for entry in data:
        if entry.get("status") != "ok":
            continue
        kw = entry["keyword"]
        for raw in entry.get("jobs") or []:
            rec = job_from_api(raw, kw)
            if not rec:
                continue
            u = rec["url"]
            if u in existing:
                mk = existing[u].setdefault("matchedKeyword", [])
                if kw not in mk:
                    mk.append(kw)
            else:
                existing[u] = rec
                new_urls.add(u)
    with (BASE / "jobs.jsonl").open("w") as f:
        for j in existing.values():
            f.write(json.dumps(j, ensure_ascii=False) + "\n")
    return existing, new_urls, data


def update_stats(jobs_list):
    kw_stats = {}
    for kw in ALL_KEYWORDS:
        matched = [j for j in jobs_list if kw in j.get("matchedKeyword", [])]
        fixed = [parse_money(j.get("budget") or "")[0] for j in matched]
        fixed = [x for x in fixed if x]
        hourly = [parse_money(j.get("budget") or "")[1] for j in matched]
        hourly = [x for x in hourly if x]
        props = [j["proposals"] for j in matched if j.get("proposals") is not None]
        verified = sum(1 for j in matched if j.get("paymentVerified")) / len(matched) if matched else 0
        high = sum(
            1
            for j in matched
            if (parse_money(j.get("budget") or "")[0] or 0) >= 1000
            or (parse_money(j.get("budget") or "")[1] or 0) >= 40
        )
        j24 = sum(
            1
            for j in matched
            if j.get("postedAt")
            and datetime.fromisoformat(j["postedAt"].replace("Z", "+00:00")) >= RUN_AT - timedelta(hours=24)
        )
        kw_stats[kw] = {
            "totalJobs": len(matched),
            "jobsLast24h": j24,
            "avgBudgetFixed": round(statistics.mean(fixed), 2) if fixed else None,
            "avgRateHourly": round(statistics.mean(hourly), 2) if hourly else None,
            "medianProposals": int(statistics.median(props)) if props else None,
            "pctVerified": round(verified * 100, 1),
            "avgClientSpend": None,
            "pctHighBudget": round(high / len(matched) * 100, 1) if matched else 0,
            "opportunityScore": opportunity_score(matched),
            "sampleConfidence": confidence(len(matched)),
        }

    group_stats = {}
    for g, kws in KEYWORD_GROUPS.items():
        gj = [j for j in jobs_list if any(k in j.get("matchedKeyword", []) for k in kws)]
        group_stats[g] = {
            "totalJobs": len(gj),
            "jobsLast24h": sum(
                1
                for j in gj
                if j.get("postedAt")
                and datetime.fromisoformat(j["postedAt"].replace("Z", "+00:00")) >= RUN_AT - timedelta(hours=24)
            ),
            "opportunityScore": opportunity_score(gj),
            "sampleConfidence": confidence(len(gj)),
        }

    plat_stats = {}
    for plat, needles in PLATFORM_MAP.items():
        pj = [
            j
            for j in jobs_list
            if any(n.lower() in " ".join(j.get("matchedKeyword", [])).lower() for n in needles)
            or any(n.lower() in (j.get("title") or "").lower() for n in needles)
            or any(n.lower() in " ".join(j.get("skills") or []).lower() for n in needles)
        ]
        fixed = [parse_money(j.get("budget") or "")[0] for j in pj]
        fixed = [x for x in fixed if x]
        hourly = [parse_money(j.get("budget") or "")[1] for j in pj]
        hourly = [x for x in hourly if x]
        props = [j["proposals"] for j in pj if j.get("proposals") is not None]
        plat_stats[plat] = {
            "jobs": len(pj),
            "avgBudgetFixed": round(statistics.mean(fixed), 2) if fixed else None,
            "avgRateHourly": round(statistics.mean(hourly), 2) if hourly else None,
            "medianProposals": int(statistics.median(props)) if props else None,
            "opportunityScore": opportunity_score(pj),
            "confidence": confidence(len(pj)),
        }

    (BASE / "keyword-stats.json").write_text(json.dumps(kw_stats, indent=2))
    (BASE / "group-stats.json").write_text(json.dumps(group_stats, indent=2))
    (BASE / "platform-stats.json").write_text(json.dumps(plat_stats, indent=2))
    return kw_stats, group_stats, plat_stats


def write_summary(kw_stats, group_stats, plat_stats, jobs_list, attempted, completed, errors, run_num):
    top_kw = sorted(kw_stats.items(), key=lambda x: (-x[1]["opportunityScore"], -x[1]["jobsLast24h"]))[:10]
    top_groups = sorted(group_stats.items(), key=lambda x: -x[1]["opportunityScore"])[:5]
    lines = [
        "# Upwork Market Intelligence",
        "",
        f"Last updated: {RUN_AT.isoformat()}",
        f"Run: {run_num}",
        f"Total jobs tracked: {len(jobs_list)}",
        f"Keywords attempted: {attempted}",
        f"Keywords completed: {completed}",
        "",
        "## Top Opportunities",
        "",
    ]
    for kw, s in top_kw:
        lines.append(
            f"- **{kw}**: jobs24h={s['jobsLast24h']}, total={s['totalJobs']}, "
            f"fixed={s['avgBudgetFixed']}, hourly={s['avgRateHourly']}, "
            f"median props={s['medianProposals']}, score={s['opportunityScore']}, {s['sampleConfidence']}"
        )
    lines.extend(["", "## Strongest Groups", ""])
    for i, (g, s) in enumerate(sorted(group_stats.items(), key=lambda x: -x[1]["opportunityScore"]), 1):
        lines.append(f"{i}. {g} (score {s['opportunityScore']}, jobs24h {s['jobsLast24h']})")
    lines.extend(["", "## Platform Ranking", ""])
    for i, (p, s) in enumerate(sorted(plat_stats.items(), key=lambda x: -x[1]["opportunityScore"]), 1):
        lines.append(f"{i}. {p} (jobs {s['jobs']}, score {s['opportunityScore']})")
    primary = top_kw[0][0] if top_kw else "full stack developer"
    secondary = top_kw[1][0] if len(top_kw) > 1 else "wordpress developer"
    best_plat = max(plat_stats.items(), key=lambda x: x[1]["opportunityScore"])[0] if plat_stats else "WordPress"
    lines.extend([
        "",
        "## Positioning Recommendation",
        "",
        f"Primary keyword: {primary}",
        f"Secondary keyword: {secondary}",
        f"Best platform/service: {best_plat}",
        "Overview keywords: WordPress, Webflow, Next.js, AI web development",
        "Skill tags: WordPress, React, Next.js, Webflow, Shopify, Supabase",
        "",
        "## Current Verdicts",
        "",
        "WordPress: Steady volume; mix of low-budget builds and premium real estate/ecom.",
        "Webflow: Niche but quality leads when titles match.",
        "Framer: Smaller sample; repair/redesign tasks appear.",
        "GoHighLevel: Funnel fixes and automation; often small fixed budgets.",
        "AI/Vibe Coding: Claude Code and AI ecommerce posts emerging this window.",
        "Ecommerce: Shopify + headless Astro roles; some high fixed budgets.",
        "Maintenance: Retainer posts less frequent in 2h window; watch UK membership WP.",
        "",
        "## Important Changes",
        "",
        "First run baseline established." if run_num == 1 else "See run log for deltas.",
    ])
    if errors:
        lines.append(f"Failed keywords this run: {', '.join(errors)}")
    (BASE / "current-summary.md").write_text("\n".join(lines) + "\n")


def main():
    import sys

    batch = BASE / "search_batch.json"
    if not batch.exists():
        print("missing search_batch.json")
        sys.exit(1)
    meta_path = BASE / "run_meta.json"
    meta = json.loads(meta_path.read_text()) if meta_path.exists() else {"runNumber": 1, "attempted": 93, "completed": 0, "errors": []}

    existing_before = load_jobs()
    before_count = len(existing_before)
    jobs_map, new_urls, batch_data = ingest_batch(batch)
    jobs_list = list(jobs_map.values())

    kw_stats, group_stats, plat_stats = update_stats(jobs_list)
    run_num = meta.get("runNumber", 1)
    attempted = meta.get("attempted", len(ALL_KEYWORDS))
    completed = meta.get("completed", len(ALL_KEYWORDS))
    errors = meta.get("errors", [])

    top3 = sorted(kw_stats.items(), key=lambda x: -x[1]["jobsLast24h"])[:3]
    top3_names = [t[0] for t in top3]

    log_rec = {
        "timestamp": RUN_AT.isoformat(),
        "runNumber": run_num,
        "keywordsAttempted": attempted,
        "keywordsCompleted": completed,
        "newJobs": len(new_urls),
        "totalJobs": len(jobs_list),
        "top3Keywords": top3_names,
        "errors": errors,
    }
    with (BASE / "run-log.jsonl").open("a") as f:
        f.write(json.dumps(log_rec) + "\n")

    state = {
        "lastRunAt": RUN_AT.isoformat(),
        "runNumber": run_num,
        "totalJobs": len(jobs_list),
        "knownJobUrls": list(jobs_map.keys())[:5000],
        "lastInsightRefresh": RUN_AT.isoformat(),
    }
    (BASE / "state.json").write_text(json.dumps(state, indent=2))
    write_summary(kw_stats, group_stats, plat_stats, jobs_list, attempted, completed, errors, run_num)

    out = {
        "newJobs": len(new_urls),
        "totalJobs": len(jobs_list),
        "new_urls": list(new_urls),
        "kw_stats": kw_stats,
        "group_stats": group_stats,
        "plat_stats": plat_stats,
        "jobs_list": jobs_list,
        "errors": errors,
        "attempted": attempted,
        "completed": completed,
        "runNumber": run_num,
    }
    (BASE / "_run_output.json").write_text(json.dumps(out, default=str))
    print(json.dumps({"new": len(new_urls), "total": len(jobs_list)}))


if __name__ == "__main__":
    main()
