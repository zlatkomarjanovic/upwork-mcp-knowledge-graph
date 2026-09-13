#!/usr/bin/env python3
"""Process search results into knowledge tree files."""
import json
import re
import statistics
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).parent
WINDOW_HOURS = 2  # first run (1h after state exists)
RUN_AT = datetime.now(timezone.utc)


def norm_url(url: str) -> str:
    if not url:
        return ""
    return url.split("?")[0]


def parse_budget(budget: str | None, job_type: str):
    if not budget:
        return None, None
    b = budget.replace(",", "")
    if job_type == "hourly" and "–" in b or "-" in b:
        parts = re.split(r"[–-]", b.replace("/hr", "").replace("hr", ""))
        nums = [float(re.sub(r"[^\d.]", "", p)) for p in parts if re.search(r"\d", p)]
        if nums:
            return None, sum(nums) / len(nums)
    m = re.search(r"([\d.]+)", b)
    if m:
        val = float(m.group(1))
        if job_type == "hourly":
            return None, val
        return val, None
    return None, None


def parse_spend(s: str | None):
    if not s:
        return None
    m = re.search(r"([\d,.]+)", s.replace(",", ""))
    return float(m.group(1)) if m else None


SKIP_PATTERNS = re.compile(
    r"\b(alcohol|gambling|casino|adult content|porn|crypto trading|dating app|dating site)\b",
    re.I,
)


def is_high_budget(fixed, hourly):
    if fixed is not None and fixed >= 1000:
        return True
    if hourly is not None and hourly >= 40:
        return True
    return False


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


def opportunity_score(jobs):
    if not jobs:
        return 0
    score = 0.0
    now = RUN_AT
    for j in jobs:
        posted = datetime.fromisoformat(j["postedAt"].replace("Z", "+00:00"))
        hours_ago = max(0, (now - posted).total_seconds() / 3600)
        recency = max(0, 1 - hours_ago / 24)
        fixed, hourly = j.get("_fixed"), j.get("_hourly")
        budget_part = 0
        if fixed and fixed >= 1000:
            budget_part = min(1, fixed / 5000)
        elif hourly and hourly >= 40:
            budget_part = min(1, hourly / 100)
        elif fixed:
            budget_part = min(0.5, fixed / 1000)
        props = j.get("proposals") or 20
        comp = max(0, 1 - props / 50)
        verified = 1 if j.get("paymentVerified") else 0.3
        high = 1 if is_high_budget(fixed, hourly) else 0
        score += (recency * 25 + budget_part * 25 + comp * 25 + verified * 15 + high * 10)
    return min(100, int(score / len(jobs)))


def job_from_raw(raw, keyword, group):
    url = raw.get("url")
    if not url:
        return None
    title = raw.get("title") or ""
    snippet = raw.get("description_snippet") or ""
    if SKIP_PATTERNS.search(title + " " + snippet):
        return None
    posted = raw.get("published_date") or raw.get("created_date")
    if not posted:
        return None
    posted_dt = datetime.fromisoformat(posted.replace("Z", "+00:00"))
    if (RUN_AT - posted_dt).total_seconds() > WINDOW_HOURS * 3600:
        return None
    client = raw.get("client") or {}
    fixed, hourly = parse_budget(raw.get("budget"), raw.get("job_type", ""))
    hire_rate = None
    return {
        "url": norm_url(url),
        "title": title,
        "matchedKeyword": [keyword],
        "keywordGroup": group,
        "postedAt": posted,
        "type": raw.get("job_type"),
        "budget": raw.get("budget"),
        "duration": raw.get("duration"),
        "proposals": raw.get("proposal_count"),
        "clientCountry": client.get("country"),
        "paymentVerified": client.get("verification_status") == "VERIFIED",
        "clientSpend": client.get("total_spent"),
        "clientHireRate": hire_rate,
        "clientRating": client.get("rating"),
        "experienceLevel": raw.get("experience_level"),
        "skills": raw.get("skills") or [],
        "_fixed": fixed,
        "_hourly": hourly,
        "_spend_num": parse_spend(client.get("total_spent")),
    }


def load_search_file(path):
    with open(path) as f:
        return json.load(f)


def main():
    import sys

    responses_path = BASE / "search_responses.json"
    if not responses_path.exists():
        print("No search_responses.json", file=sys.stderr)
        sys.exit(1)

    data = load_search_file(responses_path)
    keywords_meta = json.loads((BASE / "keywords.json").read_text())

    state_path = BASE / "state.json"
    global WINDOW_HOURS
    if state_path.exists():
        state = json.loads(state_path.read_text())
        run_number = state.get("runNumber", 0) + 1
        known = set(state.get("knownJobUrls", []))
        WINDOW_HOURS = 1
    else:
        run_number = 1
        known = set()

    jobs_by_url = {}
    errors = data.get("errors", [])
    attempted = len(keywords_meta)
    completed = 0

    for entry in data.get("searches", []):
        kw = entry.get("keyword")
        group = entry.get("group")
        if entry.get("error"):
            errors.append(kw)
            continue
        completed += 1
        for raw in entry.get("jobs", []):
            j = job_from_raw(raw, kw, group)
            if not j:
                continue
            u = j["url"]
            if u in jobs_by_url:
                if kw not in jobs_by_url[u]["matchedKeyword"]:
                    jobs_by_url[u]["matchedKeyword"].append(kw)
            else:
                jobs_by_url[u] = j

    new_jobs = [j for u, j in jobs_by_url.items() if u not in known]
    for j in new_jobs:
        out = {k: v for k, v in j.items() if not k.startswith("_")}
        with open(BASE / "jobs.jsonl", "a") as f:
            f.write(json.dumps(out) + "\n")

    all_urls = known | set(jobs_by_url.keys())
    total_jobs = len(all_urls)

    # Load all jobs for stats from jobs.jsonl + new
    all_jobs = []
    jp = BASE / "jobs.jsonl"
    if jp.exists():
        for line in jp.read_text().splitlines():
            if line.strip():
                all_jobs.append(json.loads(line))

    now = RUN_AT
    kw_stats = {}
    for meta in keywords_meta:
        kw = meta["keyword"]
        kw_jobs = [j for j in all_jobs if kw in j.get("matchedKeyword", [])]
        jobs_24h = [
            j
            for j in kw_jobs
            if (now - datetime.fromisoformat(j["postedAt"].replace("Z", "+00:00"))).total_seconds()
            <= 86400
        ]
        fixed_vals = []
        hourly_vals = []
        props = []
        verified = 0
        spends = []
        high_pct = 0
        for j in kw_jobs:
            f, h = parse_budget(j.get("budget"), j.get("type") or "")
            if f:
                fixed_vals.append(f)
            if h:
                hourly_vals.append(h)
            if j.get("proposals") is not None:
                props.append(j["proposals"])
            if j.get("paymentVerified"):
                verified += 1
            s = parse_spend(j.get("clientSpend"))
            if s:
                spends.append(s)
            if is_high_budget(f, h):
                high_pct += 1
        n = len(kw_jobs)
        kw_stats[kw] = {
            "keywordGroup": meta["group"],
            "totalJobs": n,
            "jobsLast24h": len(jobs_24h),
            "avgBudgetFixed": round(statistics.mean(fixed_vals), 2) if fixed_vals else None,
            "avgRateHourly": round(statistics.mean(hourly_vals), 2) if hourly_vals else None,
            "medianProposals": int(statistics.median(props)) if props else None,
            "pctVerified": round(100 * verified / n, 1) if n else 0,
            "avgClientSpend": round(statistics.mean(spends), 2) if spends else None,
            "pctHighBudget": round(100 * high_pct / n, 1) if n else 0,
            "opportunityScore": opportunity_score(
                [{**j, "_fixed": parse_budget(j.get("budget"), j.get("type") or "")[0], "_hourly": parse_budget(j.get("budget"), j.get("type") or "")[1]} for j in kw_jobs]
            ),
            "sampleConfidence": confidence(n),
        }

    (BASE / "keyword-stats.json").write_text(json.dumps(kw_stats, indent=2))

    group_stats = {}
    for g in {m["group"] for m in keywords_meta}:
        gkws = [k for k, v in kw_stats.items() if v["keywordGroup"] == g]
        scores = [kw_stats[k]["opportunityScore"] for k in gkws]
        jobs24 = sum(kw_stats[k]["jobsLast24h"] for k in gkws)
        group_stats[g] = {
            "totalJobs": sum(kw_stats[k]["totalJobs"] for k in gkws),
            "jobsLast24h": jobs24,
            "avgOpportunityScore": int(statistics.mean(scores)) if scores else 0,
            "keywordCount": len(gkws),
        }
    (BASE / "group-stats.json").write_text(json.dumps(group_stats, indent=2))

    platforms = {
        "WordPress": ["wordpress", "elementor", "woocommerce"],
        "Webflow": ["webflow"],
        "Framer": ["framer"],
        "GoHighLevel": ["gohighlevel", "go high level", "ghl"],
        "Shopify": ["shopify"],
        "WooCommerce": ["woocommerce"],
        "Shopware": ["shopware"],
        "Lovable": ["lovable"],
        "Bolt": ["bolt"],
        "v0": ["v0"],
        "Next.js": ["nextjs", "next.js"],
    }
    platform_stats = {}
    for pname, terms in platforms.items():
        pj = [
            j
            for j in all_jobs
            if any(
                t in " ".join(j.get("matchedKeyword", [])).lower()
                or any(t in (s or "").lower() for s in j.get("skills", []))
                or t in (j.get("title") or "").lower()
                for t in terms
            )
        ]
        fixed_vals, hourly_vals, props = [], [], []
        for j in pj:
            f, h = parse_budget(j.get("budget"), j.get("type") or "")
            if f:
                fixed_vals.append(f)
            if h:
                hourly_vals.append(h)
            if j.get("proposals") is not None:
                props.append(j["proposals"])
        platform_stats[pname] = {
            "jobs": len(pj),
            "avgBudgetFixed": round(statistics.mean(fixed_vals), 2) if fixed_vals else None,
            "avgRateHourly": round(statistics.mean(hourly_vals), 2) if hourly_vals else None,
            "medianProposals": int(statistics.median(props)) if props else None,
            "opportunityScore": opportunity_score(
                [{**j, "_fixed": parse_budget(j.get("budget"), j.get("type") or "")[0], "_hourly": parse_budget(j.get("budget"), j.get("type") or "")[1]} for j in pj]
            ),
            "sampleConfidence": confidence(len(pj)),
        }
    (BASE / "platform-stats.json").write_text(json.dumps(platform_stats, indent=2))

    top3 = sorted(kw_stats.items(), key=lambda x: x[1]["jobsLast24h"], reverse=True)[:3]
    top3_kw = [t[0] for t in top3]

    log = {
        "timestamp": RUN_AT.isoformat(),
        "runNumber": run_number,
        "keywordsAttempted": attempted,
        "keywordsCompleted": completed,
        "newJobs": len(new_jobs),
        "totalJobs": total_jobs,
        "top3Keywords": top3_kw,
        "errors": errors,
    }
    with open(BASE / "run-log.jsonl", "a") as f:
        f.write(json.dumps(log) + "\n")

    state_out = {
        "lastRunAt": RUN_AT.isoformat(),
        "runNumber": run_number,
        "totalJobs": total_jobs,
        "knownJobUrls": sorted(all_urls),
        "lastInsightRefresh": RUN_AT.isoformat(),
    }
    (BASE / "state.json").write_text(json.dumps(state_out, indent=2))

    # summary md
    top10 = sorted(kw_stats.items(), key=lambda x: x[1]["opportunityScore"], reverse=True)[:10]
    groups_ranked = sorted(group_stats.items(), key=lambda x: x[1]["avgOpportunityScore"], reverse=True)

    primary = top10[0][0] if top10 else "wordpress developer"
    secondary = top10[1][0] if len(top10) > 1 else "next.js developer"

    summary = f"""# Upwork Market Intelligence

Last updated: {RUN_AT.isoformat()}
Run: {run_number}
Total jobs tracked: {total_jobs}
Keywords attempted: {attempted}
Keywords completed: {completed}

## Top Opportunities

"""
    for kw, st in top10:
        summary += f"- **{kw}** — score {st['opportunityScore']}, jobs24h {st['jobsLast24h']}, total {st['totalJobs']}, avg fixed ${st['avgBudgetFixed'] or 'n/a'}, avg hourly ${st['avgRateHourly'] or 'n/a'}, median proposals {st['medianProposals']}, confidence {st['sampleConfidence']}\n"

    summary += "\n## Strongest Groups\n\n"
    for g, st in groups_ranked[:5]:
        summary += f"- {g}: score {st['avgOpportunityScore']}, jobs24h {st['jobsLast24h']}\n"

    summary += "\n## Platform Ranking\n\n"
    pl_rank = sorted(platform_stats.items(), key=lambda x: x[1]["opportunityScore"], reverse=True)
    for p, st in pl_rank:
        summary += f"- {p}: {st['jobs']} jobs, score {st['opportunityScore']}\n"

    summary += f"""
## Positioning Recommendation

Primary keyword: {primary}
Secondary keyword: {secondary}
Best platform/service: WordPress + Next.js hybrid positioning
Overview keywords: {primary}, {secondary}, full stack developer, AI web development
Skill tags: WordPress, Next.js, React, Supabase, Webflow, Shopify

## Current Verdicts

WordPress: Steady volume; mix of Elementor fixes and redesigns.
Webflow: Lower immediate volume in this window.
Framer: Niche; fewer fresh posts.
GoHighLevel: HubSpot migration posts show strong hourly budgets.
AI/Vibe Coding: SaaS takeover and Next.js rebuild posts appearing.
Ecommerce: Shopify Figma builds and cleanup jobs active.
Maintenance: WordPress security/malware and ongoing dev mentions.

## Important Changes

First run baseline established.
"""
    (BASE / "current-summary.md").write_text(summary)

    if run_number == 1:
        insights = """# Upwork Intelligence Insights

- Initial baseline run on 2026-09-13. WordPress and core web keywords dominate fresh postings.
- GoHighLevel migration work (HubSpot to GHL) shows verified clients with meaningful spend.
- Shopify Figma-to-code jobs posting with low proposal counts early.
"""
        (BASE / "insights.md").write_text(insights)

    print(json.dumps({"runNumber": run_number, "newJobs": len(new_jobs), "totalJobs": total_jobs, "completed": completed, "errors": errors, "new_jobs": [{k: v for k, v in j.items() if not k.startswith("_")} for j in new_jobs]}))


if __name__ == "__main__":
    main()
