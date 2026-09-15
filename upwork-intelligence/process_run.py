#!/usr/bin/env python3
"""Process MCP search batch file into intelligence store."""
import json
import re
import statistics
from datetime import datetime, timezone, timedelta
from pathlib import Path
from urllib.parse import urlparse, parse_qs

BASE = Path(__file__).resolve().parent

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
ALL_KEYWORDS = [k for kws in KEYWORD_GROUPS.values() for k in kws]

SKIP_PATTERNS = re.compile(
    r"alcohol|gambling|casino|adult|crypto trad|dating|onlyfans",
    re.I,
)

PLATFORMS = {
    "WordPress": re.compile(r"wordpress|elementor|woocommerce|divi|bricks", re.I),
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
    base = url.split("?")[0]
    return base


def parse_budget(budget_str, job_type):
    if not budget_str:
        return None, None
    s = str(budget_str).replace(",", "")
    if job_type == "hourly" or "/hr" in s or "hr" in s.lower():
        nums = re.findall(r"[\d.]+", s)
        if nums:
            return None, float(nums[-1]) if len(nums) == 1 else (float(nums[0]) + float(nums[1])) / 2
        return None, None
    nums = re.findall(r"[\d.]+", s)
    if nums:
        return float(nums[0]), None
    return None, None


def parse_spend(spent):
    if not spent:
        return None
    m = re.search(r"[\d,]+\.?\d*", str(spent).replace("$", ""))
    if m:
        return float(m.group(0).replace(",", ""))
    return None


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
    for j in jobs:
        recency = 1.0
        posted = j.get("postedAt")
        if posted:
            try:
                dt = datetime.fromisoformat(posted.replace("Z", "+00:00"))
                age_h = (datetime.now(timezone.utc) - dt).total_seconds() / 3600
                recency = max(0.2, 1.0 - age_h / 48)
            except Exception:
                pass
        fixed, hourly = j.get("_fixed"), j.get("_hourly")
        budget_pts = 0
        if fixed and fixed >= 1000:
            budget_pts = 1.0
        elif fixed and fixed >= 500:
            budget_pts = 0.7
        elif fixed:
            budget_pts = 0.3
        if hourly and hourly >= 40:
            budget_pts = max(budget_pts, 1.0)
        elif hourly and hourly >= 25:
            budget_pts = max(budget_pts, 0.6)
        props = j.get("proposals") or 50
        comp = max(0.1, 1.0 - min(props, 50) / 50)
        ver = 0.15 if j.get("paymentVerified") else 0
        score += recency * (0.35 + budget_pts * 0.35 + comp * 0.3 + ver)
    return min(100, max(1, int(score / len(jobs) * 25)))


def job_from_raw(raw, keyword, group):
    url = norm_url(raw.get("url"))
    if not url:
        return None
    title = raw.get("title") or ""
    snippet = raw.get("description_snippet") or ""
    if SKIP_PATTERNS.search(title + snippet):
        return None
    client = raw.get("client") or {}
    fixed, hourly = parse_budget(raw.get("budget"), raw.get("job_type"))
    return {
        "url": url,
        "title": title,
        "matchedKeyword": [keyword],
        "keywordGroup": group,
        "postedAt": raw.get("published_date") or raw.get("created_date"),
        "type": raw.get("job_type"),
        "budget": raw.get("budget"),
        "duration": raw.get("duration"),
        "proposals": raw.get("proposal_count"),
        "clientCountry": client.get("country"),
        "paymentVerified": client.get("verification_status") == "VERIFIED",
        "clientSpend": client.get("total_spent"),
        "clientHireRate": None,
        "clientRating": client.get("rating"),
        "experienceLevel": raw.get("experience_level"),
        "skills": raw.get("skills") or [],
        "_fixed": fixed,
        "_hourly": hourly,
    }


def load_state():
    p = BASE / "state.json"
    if p.exists():
        return json.loads(p.read_text())
    return {"runNumber": 0, "totalJobs": 0, "knownJobUrls": [], "lastInsightRefresh": None}


def main():
    batch_path = BASE / "mcp_batch.json"
    if not batch_path.exists():
        print("No mcp_batch.json")
        return 1

    batch = json.loads(batch_path.read_text())
    now = datetime.now(timezone.utc)
    state = load_state()
    run_number = state.get("runNumber", 0) + 1
    first_run = state.get("runNumber", 0) == 0
    window_h = 2.0 if first_run else 1.0
    cutoff = now - timedelta(hours=window_h)

    known = set(state.get("knownJobUrls") or [])
    jobs_by_url = {}

    jobs_path = BASE / "jobs.jsonl"
    if jobs_path.exists() and known:
        pass
    elif jobs_path.exists() and not known:
        for line in jobs_path.read_text().splitlines():
            if not line.strip():
                continue
            try:
                j = json.loads(line)
                u = norm_url(j.get("url"))
                if u:
                    known.add(u)
                    jobs_by_url[u] = j
            except json.JSONDecodeError:
                continue

    keywords_attempted = len(ALL_KEYWORDS)
    keywords_completed = 0
    errors = []
    keyword_hits = {k: [] for k in ALL_KEYWORDS}

    for entry in batch:
        kw = entry.get("keyword")
        group = entry.get("group") or KW_TO_GROUP.get(kw, "")
        if entry.get("error"):
            errors.append(kw)
            continue
        keywords_completed += 1
        for raw in entry.get("jobs") or []:
            j = job_from_raw(raw, kw, group)
            if not j:
                continue
            posted = j.get("postedAt")
            if posted:
                try:
                    dt = datetime.fromisoformat(posted.replace("Z", "+00:00"))
                    if dt < cutoff:
                        continue
                except Exception:
                    pass
            u = j["url"]
            keyword_hits.setdefault(kw, []).append(j)
            if u in jobs_by_url:
                existing = jobs_by_url[u]
                for mk in j["matchedKeyword"]:
                    if mk not in existing.get("matchedKeyword", []):
                        existing.setdefault("matchedKeyword", []).append(mk)
            else:
                jobs_by_url[u] = j

    new_jobs = [j for u, j in jobs_by_url.items() if u not in known]
    for j in new_jobs:
        rec = {k: v for k, v in j.items() if not k.startswith("_")}
        with jobs_path.open("a") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        known.add(j["url"])

    all_jobs = []
    for line in (jobs_path.read_text().splitlines() if jobs_path.exists() else []):
        if line.strip():
            try:
                all_jobs.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    for j in new_jobs:
        rec = {k: v for k, v in j.items() if not k.startswith("_")}
        if rec not in all_jobs:
            all_jobs.append(rec)

    total_jobs = len(all_jobs)
    now_iso = now.isoformat().replace("+00:00", "Z")

    kw_stats = {}
    for kw in ALL_KEYWORDS:
        kw_jobs = [j for j in all_jobs if kw in j.get("matchedKeyword", [])]
        recent = []
        for j in kw_jobs:
            p = j.get("postedAt")
            if p:
                try:
                    if datetime.fromisoformat(p.replace("Z", "+00:00")) >= now - timedelta(hours=24):
                        recent.append(j)
                except Exception:
                    pass
        fixed_vals = []
        hourly_vals = []
        props = []
        verified = 0
        high_b = 0
        spends = []
        for j in kw_jobs:
            f, h = parse_budget(j.get("budget"), j.get("type"))
            if f:
                fixed_vals.append(f)
            if h:
                hourly_vals.append(h)
            if j.get("proposals") is not None:
                props.append(j["proposals"])
            if j.get("paymentVerified"):
                verified += 1
            if (f and f >= 1000) or (h and h >= 40):
                high_b += 1
            sp = parse_spend(j.get("clientSpend"))
            if sp is not None:
                spends.append(sp)
        n = len(kw_jobs)
        kw_stats[kw] = {
            "totalJobs": n,
            "jobsLast24h": len(recent),
            "avgBudgetFixed": round(statistics.mean(fixed_vals), 2) if fixed_vals else None,
            "avgRateHourly": round(statistics.mean(hourly_vals), 2) if hourly_vals else None,
            "medianProposals": int(statistics.median(props)) if props else None,
            "pctVerified": round(100 * verified / n, 1) if n else 0,
            "avgClientSpend": round(statistics.mean(spends), 2) if spends else None,
            "pctHighBudget": round(100 * high_b / n, 1) if n else 0,
            "opportunityScore": opportunity_score(kw_jobs),
            "sampleConfidence": confidence_label(n),
        }

    group_stats = {}
    for g, kws in KEYWORD_GROUPS.items():
        gj = [j for j in all_jobs if j.get("keywordGroup") == g]
        group_stats[g] = {
            "totalJobs": len(gj),
            "jobsLast24h": sum(1 for j in gj if j.get("postedAt") and _within_24h(j, now)),
            "opportunityScore": opportunity_score(gj),
            "sampleConfidence": confidence_label(len(gj)),
        }

    platform_stats = {}
    for pname, pat in PLATFORMS.items():
        pj = [j for j in all_jobs if pat.search(j.get("title", "") + " ".join(j.get("skills") or []))]
        platform_stats[pname] = {
            "jobs": len(pj),
            "avgBudgetFixed": _avg_fixed(pj),
            "avgRateHourly": _avg_hourly(pj),
            "medianProposals": _med_props(pj),
            "opportunityScore": opportunity_score(pj),
            "sampleConfidence": confidence_label(len(pj)),
        }

    (BASE / "keyword-stats.json").write_text(json.dumps(kw_stats, indent=2))
    (BASE / "group-stats.json").write_text(json.dumps(group_stats, indent=2))
    (BASE / "platform-stats.json").write_text(json.dumps(platform_stats, indent=2))

    top3 = sorted(kw_stats.items(), key=lambda x: x[1]["jobsLast24h"], reverse=True)[:3]
    top3_kw = [t[0] for t in top3]

    log_rec = {
        "timestamp": now_iso,
        "runNumber": run_number,
        "keywordsAttempted": keywords_attempted,
        "keywordsCompleted": keywords_completed,
        "newJobs": len(new_jobs),
        "totalJobs": total_jobs,
        "top3Keywords": top3_kw,
        "errors": errors,
    }
    with (BASE / "run-log.jsonl").open("a") as f:
        f.write(json.dumps(log_rec) + "\n")

    state_out = {
        "lastRunAt": now_iso,
        "runNumber": run_number,
        "totalJobs": total_jobs,
        "knownJobUrls": list(known),
        "lastInsightRefresh": state.get("lastInsightRefresh"),
    }
    (BASE / "state.json").write_text(json.dumps(state_out, indent=2))

    write_summary(now_iso, run_number, keywords_attempted, keywords_completed, total_jobs, kw_stats, group_stats, platform_stats)
    write_chat_report(run_number, keywords_attempted, keywords_completed, len(new_jobs), total_jobs, kw_stats, group_stats, platform_stats, new_jobs, errors, first_run)
    return 0


def _within_24h(j, now):
    p = j.get("postedAt")
    if not p:
        return False
    try:
        return datetime.fromisoformat(p.replace("Z", "+00:00")) >= now - timedelta(hours=24)
    except Exception:
        return False


def _avg_fixed(jobs):
    vals = []
    for j in jobs:
        f, _ = parse_budget(j.get("budget"), j.get("type"))
        if f:
            vals.append(f)
    return round(statistics.mean(vals), 2) if vals else None


def _avg_hourly(jobs):
    vals = []
    for j in jobs:
        _, h = parse_budget(j.get("budget"), j.get("type"))
        if h:
            vals.append(h)
    return round(statistics.mean(vals), 2) if vals else None


def _med_props(jobs):
    props = [j["proposals"] for j in jobs if j.get("proposals") is not None]
    return int(statistics.median(props)) if props else None


def write_summary(now_iso, run, attempted, completed, total, kw_stats, group_stats, platform_stats):
    top10 = sorted(kw_stats.items(), key=lambda x: (-x[1]["jobsLast24h"], -x[1]["opportunityScore"]))[:10]
    groups_ranked = sorted(group_stats.items(), key=lambda x: -x[1]["opportunityScore"])
    plat_ranked = sorted(platform_stats.items(), key=lambda x: -x[1]["jobs"])

    lines = [
        "# Upwork Market Intelligence",
        "",
        f"Last updated: {now_iso}",
        f"Run: {run}",
        f"Total jobs tracked: {total}",
        f"Keywords attempted: {attempted}",
        f"Keywords completed: {completed}",
        "",
        "## Top Opportunities",
        "",
    ]
    for kw, st in top10:
        lines.append(f"- **{kw}** — jobs24h: {st['jobsLast24h']}, total: {st['totalJobs']}, "
                     f"avg fixed: {st['avgBudgetFixed']}, avg hourly: {st['avgRateHourly']}, "
                     f"median proposals: {st['medianProposals']}, score: {st['opportunityScore']}, "
                     f"confidence: {st['sampleConfidence']}")
    lines.extend(["", "## Strongest Groups", ""])
    for g, st in groups_ranked[:5]:
        lines.append(f"- {g}: score {st['opportunityScore']}, jobs24h {st['jobsLast24h']}, total {st['totalJobs']}")
    lines.extend(["", "## Platform Ranking", ""])
    for p, st in plat_ranked:
        lines.append(f"- {p}: {st['jobs']} jobs, score {st['opportunityScore']}")
    lines.extend([
        "",
        "## Positioning Recommendation",
        "",
        "Primary keyword: wordpress developer",
        "Secondary keyword: gohighlevel developer",
        "Best platform/service: WordPress + GoHighLevel",
        "Overview keywords: WordPress, Webflow, Next.js, GoHighLevel, AI web development",
        "Skill tags: WordPress, Elementor, Webflow, Next.js, Supabase, GoHighLevel",
        "",
        "## Current Verdicts",
        "",
        "WordPress: Steady volume; mixed budgets; competition high on large fixed builds.",
        "Webflow: Niche but quality leads (speed/CRO).",
        "Framer: Low volume; design-led marketing sites.",
        "GoHighLevel: Strong when GHL explicitly required; good US verified clients.",
        "AI/Vibe Coding: Lovable/Supabase appearing in web-adjacent posts.",
        "Ecommerce: Shopify maintenance and CRO steady.",
        "Maintenance: Retainer posts exist but keyword noise from SEO roles.",
        "",
        "## Important Changes",
        "",
        "Initial baseline run (no prior state).",
    ])
    (BASE / "current-summary.md").write_text("\n".join(lines) + "\n")


def write_chat_report(run, attempted, completed, new_count, total, kw_stats, group_stats, platform_stats, new_jobs, errors, first_run):
    report_path = BASE / "chat_report.md"
    top10 = sorted(kw_stats.items(), key=lambda x: (-x[1]["jobsLast24h"], -x[1]["opportunityScore"]))[:10]
    groups = sorted(group_stats.items(), key=lambda x: -x[1]["opportunityScore"])[:5]

    lines = [
        "UPWORK MARKET UPDATE",
        "",
        f"Run: {run}",
        f"Keywords attempted: {attempted}",
        f"Keywords completed: {completed}",
        f"New jobs: {new_count}",
        f"Total jobs tracked: {total}",
        "",
        "TOP 10 KEYWORDS",
        "",
    ]
    for i, (kw, st) in enumerate(top10, 1):
        lines.append(f"{i}. {kw} — score {st['opportunityScore']}")
        lines.append(f"   jobs24h: {st['jobsLast24h']}, total: {st['totalJobs']}, avg fixed: {st['avgBudgetFixed']}, "
                     f"avg hourly: {st['avgRateHourly']}, median proposals: {st['medianProposals']}, confidence: {st['sampleConfidence']}")
    lines.extend(["", "TOP GROUPS", ""])
    for g, st in groups:
        lines.append(f"- {g}: score {st['opportunityScore']}, total {st['totalJobs']}, jobs24h {st['jobsLast24h']}")
    lines.extend(["", "PLATFORM COMPARISON", ""])
    for pname in ["WordPress", "Webflow", "Framer", "GoHighLevel", "Shopify", "WooCommerce", "Shopware", "Lovable", "Bolt", "v0", "Next.js"]:
        st = platform_stats.get(pname, {})
        lines.append(f"- {pname}: jobs {st.get('jobs', 0)}, avg budget/rate {st.get('avgBudgetFixed') or st.get('avgRateHourly')}, "
                       f"median proposals {st.get('medianProposals')}, score {st.get('opportunityScore', 0)}, confidence {st.get('sampleConfidence', 'Very Low')}")
    lines.extend([
        "",
        "NEW JOBS THIS RUN",
        "",
    ])
    for j in new_jobs:
        lines.append(f"- {j.get('title')}")
        lines.append(f"  Keyword: {', '.join(j.get('matchedKeyword', []))}")
        lines.append(f"  Group: {j.get('keywordGroup')}")
        lines.append(f"  Type: {j.get('type')}")
        lines.append(f"  Budget/rate: {j.get('budget')}")
        lines.append(f"  Proposals: {j.get('proposals')}")
        lines.append(f"  Country: {j.get('clientCountry')}")
        lines.append(f"  Client spend: {j.get('clientSpend')}")
        lines.append(f"  Skills: {', '.join((j.get('skills') or [])[:8])}")
        lines.append(f"  URL: {j.get('url')}")
        lines.append("")
    if errors:
        lines.extend(["FAILED SEARCHES", ""] + [f"- {e}" for e in errors])
    else:
        lines.extend(["FAILED SEARCHES", "", "(none)"])
    if first_run:
        lines.extend(["", "IMPORTANT CHANGES", "", "First run: baseline established."])
    report_path.write_text("\n".join(lines))


if __name__ == "__main__":
    raise SystemExit(main())
