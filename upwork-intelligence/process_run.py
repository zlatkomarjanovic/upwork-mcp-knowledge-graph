#!/usr/bin/env python3
"""Process Upwork keyword search batches into intelligence store."""
import json
import os
import re
import statistics
from datetime import datetime, timezone, timedelta
from pathlib import Path
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

BASE = Path(__file__).resolve().parent
MCP_RAW = BASE / "mcp_raw"
STATE_FILE = BASE / "state.json"
JOBS_FILE = BASE / "jobs.jsonl"
RUN_LOG = BASE / "run-log.jsonl"
KEYWORD_STATS = BASE / "keyword-stats.json"
GROUP_STATS = BASE / "group-stats.json"
PLATFORM_STATS = BASE / "platform-stats.json"
SUMMARY = BASE / "current-summary.md"
INSIGHTS = BASE / "insights.md"
KEYWORDS_FILE = BASE / "keywords.json"

SKIP_PATTERNS = re.compile(
    r"\b(casino|gambling|betting|poker|alcohol|beer|wine|liquor|adult content|porn|escort|crypto trading|bitcoin trading|forex trading|dating app|dating site)\b",
    re.I,
)

PLATFORM_KEYWORDS = {
    "WordPress": ["wordpress"],
    "Webflow": ["webflow"],
    "Framer": ["framer"],
    "GoHighLevel": ["gohighlevel", "go high level", "ghl", "highlevel"],
    "Shopify": ["shopify"],
    "WooCommerce": ["woocommerce"],
    "Shopware": ["shopware"],
    "Lovable": ["lovable"],
    "Bolt": ["bolt.new", "bolt developer", "bolt"],
    "v0": ["v0 developer", "v0 vercel", "v0"],
    "Next.js": ["nextjs", "next.js", "next.js developer", "nextjs developer"],
}


def normalize_url(url: str) -> str:
    if not url:
        return ""
    p = urlparse(url.split("?")[0])
    return urlunparse((p.scheme, p.netloc, p.path.rstrip("/"), "", "", ""))


def parse_budget(budget_str, job_type):
    if not budget_str:
        return None, None
    s = budget_str.replace(",", "").replace("$", "")
    if "–" in s or "-" in s:
        parts = re.split(r"[–-]", s)
        nums = []
        for p in parts:
            p = p.strip().replace("/hr", "").replace("hr", "").strip()
            try:
                nums.append(float(re.sub(r"[^\d.]", "", p) or 0))
            except ValueError:
                pass
        if job_type == "hourly" and nums:
            return None, sum(nums) / len(nums)
        if nums:
            return sum(nums) / len(nums), None
    s = s.replace("/hr", "").strip()
    try:
        val = float(re.sub(r"[^\d.]", "", s) or 0)
    except ValueError:
        return None, None
    if job_type == "hourly":
        return None, val
    return val, None


def parse_spend(spend_str):
    if not spend_str:
        return None
    try:
        return float(re.sub(r"[^\d.]", "", spend_str.replace(",", "")))
    except ValueError:
        return None


def confidence_label(n):
    if n >= 100:
        return "Very High"
    if n >= 40:
        return "High"
    if n >= 15:
        return "Medium"
    if n >= 5:
        return "Low"
    return "Very Low"


def is_high_budget(fixed, hourly):
    if fixed is not None and fixed >= 1000:
        return True
    if hourly is not None and hourly >= 40:
        return True
    return False


def opportunity_score(jobs):
    if not jobs:
        return 1
    now = datetime.now(timezone.utc)
    score = 0.0
    for j in jobs:
        age_h = 24
        if j.get("postedAt"):
            try:
                posted = datetime.fromisoformat(j["postedAt"].replace("Z", "+00:00"))
                age_h = max(0.5, (now - posted).total_seconds() / 3600)
            except ValueError:
                pass
        recency = max(0, 100 - age_h * 8)
        fixed, hourly = j.get("_fixed"), j.get("_hourly")
        budget_pts = 0
        if fixed and fixed >= 1000:
            budget_pts = min(30, fixed / 200)
        elif hourly and hourly >= 40:
            budget_pts = min(30, hourly)
        elif fixed:
            budget_pts = min(15, fixed / 100)
        props = j.get("proposals") or 10
        comp = max(5, 100 - min(props, 50) * 1.8)
        ver = 10 if j.get("paymentVerified") else 0
        hi = 15 if is_high_budget(fixed, hourly) else 0
        score += (recency * 0.25 + budget_pts + comp * 0.35 + ver + hi) / len(jobs) * (100 / 80)
    return max(1, min(100, int(score)))


def job_from_api(job, keyword, group):
    title = job.get("title") or ""
    desc = job.get("description_snippet") or ""
    if SKIP_PATTERNS.search(title + " " + desc):
        return None
    url = job.get("url")
    if not url:
        return None
    url = normalize_url(url)
    client = job.get("client") or {}
    fixed, hourly = parse_budget(job.get("budget"), job.get("job_type"))
    posted = job.get("published_date") or job.get("created_date")
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
        "skills": job.get("skills") or [],
        "_fixed": fixed,
        "_hourly": hourly,
    }


def load_keywords():
    with open(KEYWORDS_FILE) as f:
        return json.load(f)


def load_state():
    if STATE_FILE.exists():
        with open(STATE_FILE) as f:
            return json.load(f)
    return {"lastRunAt": None, "runNumber": 0, "totalJobs": 0, "knownJobUrls": [], "lastInsightRefresh": None}


def load_all_jobs():
    jobs_by_url = {}
    if JOBS_FILE.exists():
        with open(JOBS_FILE) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                j = json.loads(line)
                u = j.get("url")
                if u:
                    jobs_by_url[u] = j
    return jobs_by_url


def _load_saved_responses():
    """keyword -> response from mcp_raw/*.json and search_responses.jsonl"""
    saved = {}
    if MCP_RAW.exists():
        for path in MCP_RAW.glob("*.json"):
            try:
                data = json.loads(path.read_text())
            except json.JSONDecodeError:
                continue
            kw = data.get("keyword")
            if not kw:
                continue
            saved[kw] = data.get("response") or data
    jsonl = BASE / "search_responses.jsonl"
    if jsonl.exists():
        with open(jsonl) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    continue
                kw = row.get("keyword")
                if kw:
                    saved[kw] = row.get("response") or row
    return saved


def ingest_mcp_raw(keyword_to_group, first_run):
    window = timedelta(hours=2 if first_run else 1)
    cutoff = datetime.now(timezone.utc) - window
    errors = []
    attempted = 0
    completed = 0
    new_in_run = {}
    saved = _load_saved_responses()

    for group, keywords in keyword_to_group.items():
        for kw in keywords:
            attempted += 1
            resp = saved.get(kw)
            if resp is None:
                errors.append(kw)
                continue
            if resp.get("status") == "error" or resp.get("error_code"):
                errors.append(kw)
                continue
            completed += 1
            for job in resp.get("jobs") or []:
                rec = job_from_api(job, kw, group)
                if not rec:
                    continue
                if rec.get("postedAt"):
                    try:
                        posted = datetime.fromisoformat(rec["postedAt"].replace("Z", "+00:00"))
                        if posted < cutoff:
                            continue
                    except ValueError:
                        pass
                u = rec["url"]
                if u in new_in_run:
                    if kw not in new_in_run[u]["matchedKeyword"]:
                        new_in_run[u]["matchedKeyword"].append(kw)
                else:
                    new_in_run[u] = rec
    return attempted, completed, errors, new_in_run


def merge_jobs(existing, new_in_run):
    new_urls = []
    for url, rec in new_in_run.items():
        clean = {k: v for k, v in rec.items() if not k.startswith("_")}
        if url in existing:
            ex = existing[url]
            for mk in clean.get("matchedKeyword", []):
                if mk not in ex.get("matchedKeyword", []):
                    ex.setdefault("matchedKeyword", []).append(mk)
        else:
            existing[url] = clean
            new_urls.append(clean)
    return new_urls


def compute_keyword_stats(all_jobs, keyword_to_group):
    now = datetime.now(timezone.utc)
    cut24 = now - timedelta(hours=24)
    stats = {}
    kw_to_group = {}
    for g, kws in keyword_to_group.items():
        for kw in kws:
            kw_to_group[kw] = g

    for g, kws in keyword_to_group.items():
        for kw in kws:
            matched = [j for j in all_jobs.values() if kw in j.get("matchedKeyword", [])]
            jobs24 = []
            for j in matched:
                if j.get("postedAt"):
                    try:
                        if datetime.fromisoformat(j["postedAt"].replace("Z", "+00:00")) >= cut24:
                            jobs24.append(j)
                    except ValueError:
                        pass
            fixed_vals = []
            hourly_vals = []
            proposals = []
            verified = 0
            spend_vals = []
            high_b = 0
            for j in matched:
                f, h = parse_budget(j.get("budget"), j.get("type"))
                if f is not None:
                    fixed_vals.append(f)
                if h is not None:
                    hourly_vals.append(h)
                if j.get("proposals") is not None:
                    proposals.append(j["proposals"])
                if j.get("paymentVerified"):
                    verified += 1
                sp = parse_spend(j.get("clientSpend"))
                if sp is not None:
                    spend_vals.append(sp)
                if is_high_budget(f, h):
                    high_b += 1
            enriched = []
            for j in matched:
                f, h = parse_budget(j.get("budget"), j.get("type"))
                enriched.append({**j, "_fixed": f, "_hourly": h})
            n = len(matched)
            stats[kw] = {
                "keywordGroup": g,
                "totalJobs": n,
                "jobsLast24h": len(jobs24),
                "avgBudgetFixed": round(statistics.mean(fixed_vals), 2) if fixed_vals else None,
                "avgRateHourly": round(statistics.mean(hourly_vals), 2) if hourly_vals else None,
                "medianProposals": int(statistics.median(proposals)) if proposals else None,
                "pctVerified": round(100 * verified / n, 1) if n else 0,
                "avgClientSpend": round(statistics.mean(spend_vals), 2) if spend_vals else None,
                "pctHighBudget": round(100 * high_b / n, 1) if n else 0,
                "opportunityScore": opportunity_score(enriched),
                "sampleConfidence": confidence_label(n),
            }
    return stats


def compute_group_stats(keyword_stats, keyword_to_group):
    groups = {}
    for g in keyword_to_group:
        kws = [s for k, s in keyword_stats.items() if s["keywordGroup"] == g]
        if not kws:
            groups[g] = {"totalJobs": 0, "jobsLast24h": 0, "opportunityScore": 1, "sampleConfidence": "Very Low"}
            continue
        groups[g] = {
            "totalJobs": sum(x["totalJobs"] for x in kws),
            "jobsLast24h": sum(x["jobsLast24h"] for x in kws),
            "opportunityScore": int(statistics.mean([x["opportunityScore"] for x in kws])),
            "sampleConfidence": confidence_label(sum(x["totalJobs"] for x in kws)),
        }
    return groups


def compute_platform_stats(all_jobs):
    stats = {}
    for platform, patterns in PLATFORM_KEYWORDS.items():
        matched = []
        for j in all_jobs.values():
            text = " ".join(
                [
                    j.get("title") or "",
                    " ".join(j.get("skills") or []),
                    " ".join(j.get("matchedKeyword") or []),
                ]
            ).lower()
            if any(p in text for p in patterns):
                matched.append(j)
        fixed_vals, hourly_vals, proposals = [], [], []
        enriched = []
        for j in matched:
            f, h = parse_budget(j.get("budget"), j.get("type"))
            if f is not None:
                fixed_vals.append(f)
            if h is not None:
                hourly_vals.append(h)
            if j.get("proposals") is not None:
                proposals.append(j["proposals"])
            enriched.append({**j, "_fixed": f, "_hourly": h})
        n = len(matched)
        now = datetime.now(timezone.utc)
        cut24 = now - timedelta(hours=24)
        j24 = sum(
            1
            for j in matched
            if j.get("postedAt")
            and datetime.fromisoformat(j["postedAt"].replace("Z", "+00:00")) >= cut24
        )
        stats[platform] = {
            "jobs": n,
            "jobsLast24h": j24,
            "avgBudgetFixed": round(statistics.mean(fixed_vals), 2) if fixed_vals else None,
            "avgRateHourly": round(statistics.mean(hourly_vals), 2) if hourly_vals else None,
            "medianProposals": int(statistics.median(proposals)) if proposals else None,
            "score": opportunity_score(enriched) if enriched else 1,
            "confidence": confidence_label(n),
        }
    return stats


def write_summary(run_num, attempted, completed, total_jobs, kw_stats, group_stats, plat_stats):
    top_kw = sorted(kw_stats.values(), key=lambda x: (-x["opportunityScore"], -x["jobsLast24h"]))[:10]
    top_groups = sorted(group_stats.items(), key=lambda x: -x[1]["opportunityScore"])[:5]

    lines = [
        "# Upwork Market Intelligence",
        "",
        f"Last updated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        f"Run: {run_num}",
        f"Total jobs tracked: {total_jobs}",
        f"Keywords attempted: {attempted}",
        f"Keywords completed: {completed}",
        "",
        "## Top Opportunities",
        "",
    ]
    for i, s in enumerate(top_kw, 1):
        kw = [k for k, v in kw_stats.items() if v is s][0]
        lines.append(f"{i}. **{kw}** — score {s['opportunityScore']} ({s['sampleConfidence']})")
        lines.append(
            f"   jobs24h: {s['jobsLast24h']} | total: {s['totalJobs']} | avg fixed: {s['avgBudgetFixed']} | avg hourly: {s['avgRateHourly']} | median proposals: {s['medianProposals']}"
        )
    lines.extend(["", "## Strongest Groups", ""])
    for g, s in top_groups:
        lines.append(f"- **{g}**: score {s['opportunityScore']}, jobs24h {s['jobsLast24h']}, total {s['totalJobs']}")
    lines.extend(["", "## Platform Ranking", ""])
    for p, s in sorted(plat_stats.items(), key=lambda x: -x[1]["score"]):
        lines.append(f"- **{p}**: jobs {s['jobs']}, score {s['score']}, confidence {s['confidence']}")
    lines.extend(
        [
            "",
            "## Positioning Recommendation",
            "",
            "Primary keyword: full stack developer",
            "Secondary keyword: WordPress developer",
            "Best platform/service: WordPress + AI production fixes",
            "Overview keywords: Next.js, WordPress, AI web development, Webflow",
            "Skill tags: Next.js, WordPress, WooCommerce, Supabase, Webflow, Framer",
            "",
            "## Current Verdicts",
            "",
            "WordPress: Strong volume; mixed budgets; Elementor and WooCommerce common.",
            "Webflow: Lower volume than WordPress; speed/CRO niches pay better.",
            "Framer: Niche; often paired with React for custom integrations.",
            "GoHighLevel: Steady CRM/automation demand; expert-level posts.",
            "AI/Vibe Coding: Growing; many low-budget posts, some strong SaaS audits.",
            "Ecommerce: Shopify and WooCommerce lead; headless is sparse hourly.",
            "Maintenance: Retainer posts exist but titles are noisy; filter carefully.",
            "",
            "## Important Changes",
            "",
            "First run: baseline established.",
            "",
        ]
    )
    SUMMARY.write_text("\n".join(lines))


def main():
    MCP_RAW.mkdir(parents=True, exist_ok=True)
    keyword_to_group = load_keywords()
    state = load_state()
    first_run = state.get("runNumber", 0) == 0 or state.get("totalJobs", 0) == 0
    run_num = state.get("runNumber", 0) + 1

    attempted, completed, errors, new_in_run = ingest_mcp_raw(keyword_to_group, first_run)
    existing = load_all_jobs()
    new_jobs = merge_jobs(existing, new_in_run)

    with open(JOBS_FILE, "a") as f:
        for j in new_jobs:
            f.write(json.dumps(j, ensure_ascii=False) + "\n")

    all_jobs = load_all_jobs()
    kw_stats = compute_keyword_stats(all_jobs, keyword_to_group)
    group_stats = compute_group_stats(kw_stats, keyword_to_group)
    plat_stats = compute_platform_stats(all_jobs)

    with open(KEYWORD_STATS, "w") as f:
        json.dump(kw_stats, f, indent=2)
    with open(GROUP_STATS, "w") as f:
        json.dump(group_stats, f, indent=2)
    with open(PLATFORM_STATS, "w") as f:
        json.dump(plat_stats, f, indent=2)

    known = list(all_jobs.keys())
    state.update(
        {
            "lastRunAt": datetime.now(timezone.utc).isoformat(),
            "runNumber": run_num,
            "totalJobs": len(all_jobs),
            "knownJobUrls": known[-5000:],
        }
    )
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

    top3 = sorted(kw_stats.items(), key=lambda x: -x[1]["jobsLast24h"])[:3]
    top3_names = [t[0] for t in top3]
    with open(RUN_LOG, "a") as f:
        f.write(
            json.dumps(
                {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "runNumber": run_num,
                    "keywordsAttempted": attempted,
                    "keywordsCompleted": completed,
                    "newJobs": len(new_jobs),
                    "totalJobs": len(all_jobs),
                    "top3Keywords": top3_names,
                    "errors": errors,
                }
            )
            + "\n"
        )

    write_summary(run_num, attempted, completed, len(all_jobs), kw_stats, group_stats, plat_stats)

    if not INSIGHTS.exists():
        INSIGHTS.write_text(
            "# Upwork Intelligence Insights\n\n"
            "- Baseline run: WordPress and core web dev keywords show the highest posting volume.\n"
            "- GoHighLevel and Next.js posts tend toward higher complexity and rates when verified clients post.\n"
            "- AI/vibe coding keywords surface many low fixed budgets; filter for SaaS and production audits.\n"
        )

    print(json.dumps({"run": run_num, "attempted": attempted, "completed": completed, "newJobs": len(new_jobs), "total": len(all_jobs), "errors": len(errors)}))


if __name__ == "__main__":
    main()
