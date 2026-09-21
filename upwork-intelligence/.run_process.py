#!/usr/bin/env python3
"""Process raw search batch JSON files into jobs.jsonl and stats. One-time processor for this run."""
import hashlib
import json, glob, re, statistics
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parent
ORG = "1472686528932380673"

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
    r"\b(crypto\s+trad|bitcoin\s+trad|forex\s+trad|gambling|casino|betting|adult\s+content|porn|escort|dating\s+app|alcohol)\b",
    re.I,
)

PLATFORM_KEYS = {
    "WordPress": re.compile(r"wordpress|woocommerce|elementor|bricks", re.I),
    "Webflow": re.compile(r"webflow", re.I),
    "Framer": re.compile(r"framer", re.I),
    "GoHighLevel": re.compile(r"gohighlevel|go high level|\bghl\b|highlevel", re.I),
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
    s = str(s).replace(",", "")
    if "–" in s or "-" in s and "/hr" in s:
        parts = re.split(r"[–-]", s.replace("/hr", "").strip())
        nums = []
        for p in parts:
            m = re.search(r"[\d.]+", p)
            if m:
                nums.append(float(m.group()))
        return sum(nums) / len(nums) if nums else None
    m = re.search(r"[\d.]+", s)
    return float(m.group()) if m else None


def parse_client_spend(s):
    if not s:
        return None
    s = str(s).replace(",", "").replace("$", "")
    m = re.search(r"[\d.]+", s)
    return float(m.group()) if m else None


def job_record(job, keyword, group):
    url = norm_url(job.get("url"))
    if not url:
        return None
    snippet = (job.get("description_snippet") or "") + " " + (job.get("title") or "")
    if SKIP_PATTERNS.search(snippet):
        return None
    client = job.get("client") or {}
    budget = job.get("budget")
    jt = job.get("job_type")
    return {
        "url": url,
        "title": job.get("title"),
        "matchedKeyword": [keyword],
        "keywordGroup": group,
        "postedAt": job.get("published_date") or job.get("created_date"),
        "type": jt,
        "budget": budget if jt == "fixed" else None,
        "hourlyRate": budget if jt == "hourly" else None,
        "duration": job.get("duration"),
        "proposals": job.get("proposal_count"),
        "clientCountry": client.get("country"),
        "paymentVerified": (client.get("verification_status") == "VERIFIED"),
        "clientSpend": parse_client_spend(client.get("total_spent")),
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


def is_high_budget(job):
    if job.get("type") == "fixed":
        b = parse_money(job.get("budget"))
        return b is not None and b >= 1000
    if job.get("type") == "hourly":
        r = parse_money(job.get("hourlyRate"))
        return r is not None and r >= 40
    return False


def opportunity_score(jobs):
    if not jobs:
        return 0
    now = datetime.now(timezone.utc)
    scores = []
    for j in jobs:
        s = 30.0
        posted = j.get("postedAt")
        if posted:
            try:
                dt = datetime.fromisoformat(posted.replace("Z", "+00:00"))
                age_h = (now - dt).total_seconds() / 3600
                if age_h <= 6:
                    s += 25
                elif age_h <= 24:
                    s += 15
                elif age_h <= 72:
                    s += 5
            except Exception:
                pass
        if j.get("paymentVerified"):
            s += 10
        if is_high_budget(j):
            s += 15
        prop = j.get("proposals")
        if prop is not None:
            if prop <= 5:
                s += 20
            elif prop <= 15:
                s += 10
            elif prop <= 30:
                s += 3
            else:
                s -= 5
        spend = j.get("clientSpend")
        if spend and spend >= 5000:
            s += 10
        elif spend and spend >= 1000:
            s += 5
        scores.append(max(1, min(100, s)))
    return round(sum(scores) / len(scores))


def main():
    raw_dir = BASE / "raw_batches"
    state_path = BASE / "state.json"
    state = json.loads(state_path.read_text()) if state_path.exists() else {}
    run_number = int(state.get("runNumber") or 0) + 1
    first_run = run_number == 1
    window_hours = 2 if first_run else 1
    cutoff = datetime.now(timezone.utc).timestamp() - window_hours * 3600

    known = set(state.get("knownJobUrls") or [])
    all_jobs_path = BASE / "jobs.jsonl"
    if all_jobs_path.exists():
        for line in all_jobs_path.read_text().splitlines():
            if line.strip():
                try:
                    known.add(json.loads(line)["url"])
                except (json.JSONDecodeError, KeyError):
                    pass
    jobs_by_url = {}
    keywords_attempted = 0
    keywords_completed = 0
    errors = []
    batch_files = sorted(raw_dir.glob("*.json")) if raw_dir.exists() else []
    all_jsonl = raw_dir / "all.jsonl"
    if all_jsonl.exists():
        for line in all_jsonl.read_text().splitlines():
            if line.strip():
                d = json.loads(line)
                bf = raw_dir / f"_ingest_{hashlib.md5(d['keyword'].encode()).hexdigest()[:8]}.json"
                if not bf.exists():
                    bf.write_text(json.dumps(d))
                batch_files.append(bf)
        batch_files = sorted(set(batch_files))

    kw_to_group = {}
    for g, kws in KEYWORD_GROUPS.items():
        for kw in kws:
            kw_to_group[kw] = g

    batch_by_kw = {}
    for bf in batch_files:
        if bf.name.startswith("_ingest_"):
            continue
        try:
            data = json.loads(bf.read_text())
        except json.JSONDecodeError:
            continue
        if not isinstance(data, dict):
            continue
        kw = data.get("keyword")
        if kw:
            batch_by_kw[kw] = data
    sr_path = BASE / "search_results.jsonl"
    if sr_path.exists():
        for line in sr_path.read_text().splitlines():
            if not line.strip():
                continue
            data = json.loads(line)
            kw = data.get("keyword")
            if kw:
                batch_by_kw[kw] = data

    queue_dir = BASE / "mcp_queue"
    if queue_dir.exists():
        for qf in queue_dir.glob("*.json"):
            if qf.name.startswith("_"):
                continue
            qd = json.loads(qf.read_text())
            kw = qd.get("keyword")
            if not kw:
                continue
            batch_by_kw[kw] = {
                "keyword": kw,
                "group": qd.get("group") or kw_to_group.get(kw, "UNKNOWN"),
                "response": qd.get("response") or qd,
            }

    for g, kws in KEYWORD_GROUPS.items():
        for keyword in kws:
            keywords_attempted += 1
            data = batch_by_kw.get(keyword)
            if not data:
                errors.append(keyword)
                continue
            group = data.get("group") or kw_to_group.get(keyword, "UNKNOWN")
            if data.get("error"):
                errors.append(keyword)
                continue
            keywords_completed += 1
            resp = data.get("response") or {}
            for job in resp.get("jobs") or []:
                posted = job.get("published_date") or job.get("created_date")
                if posted:
                    try:
                        ts = datetime.fromisoformat(posted.replace("Z", "+00:00")).timestamp()
                        if ts < cutoff:
                            continue
                    except Exception:
                        pass
                rec = job_record(job, keyword, group)
                if not rec:
                    continue
                u = rec["url"]
                if u in jobs_by_url:
                    if keyword not in jobs_by_url[u]["matchedKeyword"]:
                        jobs_by_url[u]["matchedKeyword"].append(keyword)
                else:
                    jobs_by_url[u] = rec

    new_jobs = [j for u, j in jobs_by_url.items() if u not in known]
    existing_jobs = []
    if all_jobs_path.exists():
        for line in all_jobs_path.read_text().splitlines():
            if line.strip():
                existing_jobs.append(json.loads(line))

    for j in new_jobs:
        with all_jobs_path.open("a") as f:
            f.write(json.dumps(j, ensure_ascii=False) + "\n")
        known.add(j["url"])

    all_jobs = existing_jobs + new_jobs
    now_iso = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    # keyword stats from all jobs
    kw_stats = {}
    for g, kws in KEYWORD_GROUPS.items():
        for kw in kws:
            kw_stats[kw] = {
                "keyword": kw, "group": g, "totalJobs": 0, "jobsLast24h": 0,
                "fixedBudgets": [], "hourlyRates": [], "proposals": [],
                "verified": 0, "clientSpends": [], "highBudget": 0, "jobs": [],
            }

    now = datetime.now(timezone.utc)
    for j in all_jobs:
        for kw in j.get("matchedKeyword") or []:
            if kw not in kw_stats:
                continue
            st = kw_stats[kw]
            st["totalJobs"] += 1
            st["jobs"].append(j)
            posted = j.get("postedAt")
            if posted:
                try:
                    if (now - datetime.fromisoformat(posted.replace("Z", "+00:00"))).total_seconds() <= 86400:
                        st["jobsLast24h"] += 1
                except Exception:
                    pass
            if j.get("paymentVerified"):
                st["verified"] += 1
            if j.get("clientSpend") is not None:
                st["clientSpends"].append(j["clientSpend"])
            if is_high_budget(j):
                st["highBudget"] += 1
            if j.get("type") == "fixed":
                b = parse_money(j.get("budget"))
                if b is not None:
                    st["fixedBudgets"].append(b)
            if j.get("type") == "hourly":
                r = parse_money(j.get("hourlyRate"))
                if r is not None:
                    st["hourlyRates"].append(r)
            if j.get("proposals") is not None:
                st["proposals"].append(j["proposals"])

    keyword_stats_out = {}
    for kw, st in kw_stats.items():
        n = st["totalJobs"]
        keyword_stats_out[kw] = {
            "keyword": kw,
            "group": st["group"],
            "totalJobs": n,
            "jobsLast24h": st["jobsLast24h"],
            "avgBudgetFixed": round(statistics.mean(st["fixedBudgets"]), 2) if st["fixedBudgets"] else None,
            "avgRateHourly": round(statistics.mean(st["hourlyRates"]), 2) if st["hourlyRates"] else None,
            "medianProposals": int(statistics.median(st["proposals"])) if st["proposals"] else None,
            "pctVerified": round(100 * st["verified"] / n, 1) if n else 0,
            "avgClientSpend": round(statistics.mean(st["clientSpends"]), 2) if st["clientSpends"] else None,
            "pctHighBudget": round(100 * st["highBudget"] / n, 1) if n else 0,
            "opportunityScore": opportunity_score(st["jobs"]),
            "sampleConfidence": confidence(n),
        }

    (BASE / "keyword-stats.json").write_text(json.dumps(keyword_stats_out, indent=2))

    group_stats = {}
    for g in KEYWORD_GROUPS:
        gjobs = [j for j in all_jobs if j.get("keywordGroup") == g]
        group_stats[g] = {
            "group": g,
            "totalJobs": len(gjobs),
            "jobsLast24h": sum(1 for j in gjobs if j.get("postedAt") and (now - datetime.fromisoformat(j["postedAt"].replace("Z", "+00:00"))).total_seconds() <= 86400),
            "opportunityScore": opportunity_score(gjobs),
            "sampleConfidence": confidence(len(gjobs)),
        }
    ranked_groups = sorted(group_stats.values(), key=lambda x: (-x["jobsLast24h"], -x["opportunityScore"]))
    (BASE / "group-stats.json").write_text(json.dumps({"groups": ranked_groups, "byName": group_stats}, indent=2))

    platform_stats = {}
    for pname, pat in PLATFORM_KEYS.items():
        pjobs = [j for j in all_jobs if pat.search(" ".join(j.get("matchedKeyword") or []) + " " + (j.get("title") or "") + " " + " ".join(j.get("skills") or []))]
        fixed_vals = [parse_money(j["budget"]) for j in pjobs if j.get("type") == "fixed" and parse_money(j.get("budget"))]
        hourly_vals = [parse_money(j.get("hourlyRate")) for j in pjobs if j.get("type") == "hourly" and parse_money(j.get("hourlyRate"))]
        platform_stats[pname] = {
            "platform": pname,
            "jobs": len(pjobs),
            "avgBudgetFixed": round(statistics.mean(fixed_vals), 2) if fixed_vals else None,
            "avgRateHourly": round(statistics.mean(hourly_vals), 2) if hourly_vals else None,
            "medianProposals": (
                int(statistics.median(pv))
                if (pv := [j["proposals"] for j in pjobs if j.get("proposals") is not None])
                else None
            ),
            "opportunityScore": opportunity_score(pjobs),
            "sampleConfidence": confidence(len(pjobs)),
        }
    (BASE / "platform-stats.json").write_text(json.dumps(platform_stats, indent=2))

    top3 = sorted(keyword_stats_out.values(), key=lambda x: (-x["jobsLast24h"], -x["opportunityScore"]))[:3]
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
    with (BASE / "run-log.jsonl").open("a") as f:
        f.write(json.dumps(log) + "\n")

    state.update({
        "lastRunAt": now_iso,
        "runNumber": run_number,
        "totalJobs": len(all_jobs),
        "knownJobUrls": list(known),
        "lastInsightRefresh": state.get("lastInsightRefresh"),
    })
    (BASE / "state.json").write_text(json.dumps(state, indent=2))

    # summary md
    top10 = sorted(keyword_stats_out.values(), key=lambda x: (-x["jobsLast24h"], -x["opportunityScore"]))[:10]
    primary = top10[0]["keyword"] if top10 else "web development"
    secondary = top10[1]["keyword"] if len(top10) > 1 else "wordpress developer"
    best_plat = max(platform_stats.items(), key=lambda x: (x[1]["jobs"], x[1]["opportunityScore"]))[0] if platform_stats else "WordPress"

    lines = [
        "# Upwork Market Intelligence",
        "",
        f"Last updated: {now_iso}",
        f"Run: {run_number}",
        f"Total jobs tracked: {len(all_jobs)}",
        f"Keywords attempted: {keywords_attempted}",
        f"Keywords completed: {keywords_completed}",
        "",
        "## Top Opportunities",
        "",
    ]
    for t in top10:
        lines.append(
            f"- **{t['keyword']}** — score {t['opportunityScore']}, jobs24h {t['jobsLast24h']}, total {t['totalJobs']}, "
            f"fixed avg ${t['avgBudgetFixed'] or 'n/a'}, hourly avg ${t['avgRateHourly'] or 'n/a'}, "
            f"median proposals {t['medianProposals']}, confidence {t['sampleConfidence']}"
        )
    lines += ["", "## Strongest Groups", ""]
    for g in ranked_groups[:5]:
        lines.append(f"- {g['group']}: jobs24h {g['jobsLast24h']}, score {g['opportunityScore']}, confidence {g['sampleConfidence']}")
    lines += ["", "## Platform Ranking", ""]
    for pname, ps in sorted(platform_stats.items(), key=lambda x: (-x[1]["jobs"], -x[1]["opportunityScore"])):
        lines.append(f"- {pname}: {ps['jobs']} jobs, score {ps['opportunityScore']}")
    lines += [
        "",
        "## Positioning Recommendation",
        f"Primary keyword: {primary}",
        f"Secondary keyword: {secondary}",
        f"Best platform/service: {best_plat}",
        "Overview keywords: web development, WordPress, Next.js, AI web development",
        "Skill tags: Next.js, React, TypeScript, WordPress, Supabase, Webflow",
        "",
        "## Current Verdicts",
        "WordPress: Steady volume, mixed budgets, strong for retainers and fixes.",
        "Webflow: Design-heavy posts, moderate competition.",
        "Framer: Lower volume than Webflow.",
        "GoHighLevel: Niche funnel/automation demand.",
        "AI/Vibe Coding: Growing Lovable/Supabase/Claude mentions.",
        "Ecommerce: Shopify and WooCommerce both active.",
        "Maintenance: Steady retainer-style posts.",
        "",
        "## Important Changes",
        "First run baseline established." if first_run else "See run log for deltas.",
    ]
    (BASE / "current-summary.md").write_text("\n".join(lines) + "\n")

    if first_run and not (BASE / "insights.md").exists():
        (BASE / "insights.md").write_text(
            "# Durable insights\n\n- Baseline tracking started.\n- WordPress and core web dev keywords show highest overlap in first window.\n"
        )

    out = {
        "runNumber": run_number,
        "keywordsAttempted": keywords_attempted,
        "keywordsCompleted": keywords_completed,
        "newJobs": new_jobs,
        "allJobsCount": len(all_jobs),
        "top10": top10,
        "ranked_groups": ranked_groups[:5],
        "platform_stats": platform_stats,
        "errors": errors,
        "primary": primary,
        "secondary": secondary,
        "best_plat": best_plat,
    }
    (BASE / ".last_output.json").write_text(json.dumps(out, default=str, indent=2))
    print(json.dumps({"ok": True, "new": len(new_jobs), "total": len(all_jobs), "errors": len(errors)}))


if __name__ == "__main__":
    main()
