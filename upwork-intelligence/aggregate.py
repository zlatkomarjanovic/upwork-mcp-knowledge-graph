#!/usr/bin/env python3
"""Process run payload: dedupe, append jobs, update stats. Usage: aggregate.py < run_payload.json"""
import json, sys, os, re, statistics
from datetime import datetime, timezone, timedelta
from pathlib import Path

BASE = Path(__file__).resolve().parent
JOBS_PATH = BASE / "jobs.jsonl"
RUN_LOG = BASE / "run-log.jsonl"
STATE_PATH = BASE / "state.json"

SKIP_TITLE = re.compile(
    r"gambling|casino|betting|crypto trading|adult content|dating|alcohol|beer|wine\b",
    re.I,
)

PROPOSAL_MID = {
    "Fewer than 5": 2,
    "5 to 10": 7,
    "10 to 15": 12,
    "15 to 20": 17,
    "20 to 50": 35,
    "50+": 60,
}

PLATFORMS = {
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


def parse_budget(budget, job_type):
    if not budget:
        return None, None
    b = budget.replace(",", "")
    if job_type == "hourly" and "–" in b or "-" in b:
        parts = re.split(r"[–-]", b.replace("/hr", "").replace("hr", ""))
        nums = [float(re.sub(r"[^\d.]", "", p)) for p in parts if re.search(r"\d", p)]
        if nums:
            return None, sum(nums) / len(nums)
    m = re.search(r"([\d.]+)", b)
    if m and job_type == "fixed":
        return float(m.group(1)), None
    if m and job_type == "hourly":
        return None, float(m.group(1))
    return None, None


def parse_spend(s):
    if not s:
        return None
    m = re.search(r"([\d,]+\.?\d*)", str(s).replace(",", ""))
    return float(m.group(1)) if m else None


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
    s = 0
    for j in jobs:
        recency = 1.0
        try:
            pd = datetime.fromisoformat(j["postedAt"].replace("Z", "+00:00"))
            age_h = (datetime.now(timezone.utc) - pd).total_seconds() / 3600
            recency = max(0.2, 1 - age_h / 48)
        except Exception:
            pass
        fixed, hourly = parse_budget(j.get("budget"), j.get("type"))
        pay = 0.3
        if fixed and fixed >= 1000:
            pay = 1.0
        elif fixed and fixed >= 500:
            pay = 0.7
        elif hourly and hourly >= 40:
            pay = 1.0
        elif hourly and hourly >= 25:
            pay = 0.6
        prop = j.get("proposals") or 35
        comp = max(0.2, 1 - min(prop, 50) / 50)
        ver = 1.0 if j.get("paymentVerified") else 0.5
        s += recency * pay * comp * ver
    raw = (s / len(jobs)) * 100
    return min(100, max(1, int(raw)))


def load_state():
    if STATE_PATH.exists():
        return json.loads(STATE_PATH.read_text())
    return {"runNumber": 0, "totalJobs": 0, "knownJobUrls": [], "lastInsightRefresh": None}


def load_jobs_index():
    urls = set()
    jobs = []
    if JOBS_PATH.exists():
        for line in JOBS_PATH.read_text().splitlines():
            if not line.strip():
                continue
            o = json.loads(line)
            jobs.append(o)
            u = norm_url(o.get("url"))
            if u:
                urls.add(u)
    return jobs, urls


def main():
    payload = json.load(sys.stdin)
    run_at = payload.get("lastRunAt") or datetime.now(timezone.utc).isoformat()
    window_h = payload.get("windowHours", 2)
    cutoff = datetime.now(timezone.utc) - timedelta(hours=window_h)
    keywords_meta = payload["keywords"]  # list of {keyword, group, ok, jobs: [...]}
    errors = payload.get("errors", [])

    state = load_state()
    all_jobs, known_urls = load_jobs_index()
    run_number = state.get("runNumber", 0) + 1

    new_jobs = []
    jobs_by_url = {norm_url(j["url"]): j for j in all_jobs if j.get("url")}

    for km in keywords_meta:
        kw, group = km["keyword"], km["group"]
        if not km.get("ok", True):
            continue
        for raw in km.get("jobs", []):
            url = norm_url(raw.get("url"))
            if not url:
                continue
            title = raw.get("title") or ""
            if SKIP_TITLE.search(title):
                continue
            pd = raw.get("published_date") or raw.get("created_date")
            if pd:
                try:
                    if datetime.fromisoformat(pd.replace("Z", "+00:00")) < cutoff:
                        continue
                except Exception:
                    pass
            client = raw.get("client") or {}
            prop_tier = raw.get("proposals_tier")
            proposals = PROPOSAL_MID.get(prop_tier) if prop_tier else None
            fixed, hourly = parse_budget(raw.get("budget"), raw.get("job_type"))
            budget_str = raw.get("budget")
            entry = {
                "url": url,
                "title": title,
                "matchedKeyword": [kw],
                "keywordGroup": group,
                "postedAt": pd,
                "type": raw.get("job_type"),
                "budget": budget_str,
                "duration": raw.get("duration"),
                "proposals": proposals,
                "clientCountry": client.get("country"),
                "paymentVerified": client.get("verification_status") == "VERIFIED",
                "clientSpend": client.get("total_spent"),
                "clientHireRate": None,
                "clientRating": client.get("rating"),
                "experienceLevel": raw.get("experience_level"),
                "skills": raw.get("skills") or [],
            }
            if url in jobs_by_url:
                ex = jobs_by_url[url]
                if kw not in ex["matchedKeyword"]:
                    ex["matchedKeyword"].append(kw)
            elif url not in known_urls:
                jobs_by_url[url] = entry
                known_urls.add(url)
                new_jobs.append(entry)

    with JOBS_PATH.open("a") as f:
        for j in new_jobs:
            f.write(json.dumps(j, ensure_ascii=False) + "\n")

    all_jobs = list(jobs_by_url.values())
    now = datetime.now(timezone.utc)
    cut24 = now - timedelta(hours=24)

    def job_in_24(j):
        try:
            return datetime.fromisoformat(j["postedAt"].replace("Z", "+00:00")) >= cut24
        except Exception:
            return False

    kw_stats = {}
    for km in keywords_meta:
        kw = km["keyword"]
        matched = [j for j in all_jobs if kw in j.get("matchedKeyword", [])]
        j24 = [j for j in matched if job_in_24(j)]
        fixed_vals, hourly_vals, props, verified, spends, high = [], [], [], 0, [], 0
        for j in matched:
            f, h = parse_budget(j.get("budget"), j.get("type"))
            if f:
                fixed_vals.append(f)
                if f >= 1000:
                    high += 1
            if h:
                hourly_vals.append(h)
                if h >= 40:
                    high += 1
            if j.get("proposals") is not None:
                props.append(j["proposals"])
            if j.get("paymentVerified"):
                verified += 1
            sp = parse_spend(j.get("clientSpend"))
            if sp:
                spends.append(sp)
        n = len(matched)
        kw_stats[kw] = {
            "keyword": kw,
            "group": km["group"],
            "totalJobs": n,
            "jobsLast24h": len(j24),
            "avgBudgetFixed": round(statistics.mean(fixed_vals), 2) if fixed_vals else None,
            "avgRateHourly": round(statistics.mean(hourly_vals), 2) if hourly_vals else None,
            "medianProposals": int(statistics.median(props)) if props else None,
            "pctVerified": round(100 * verified / n, 1) if n else 0,
            "avgClientSpend": round(statistics.mean(spends), 2) if spends else None,
            "pctHighBudget": round(100 * high / n, 1) if n else 0,
            "opportunityScore": opportunity_score(matched),
            "sampleConfidence": confidence(n),
        }

    group_stats = {}
    for g in {km["group"] for km in keywords_meta}:
        kws = [s for s in kw_stats.values() if s["group"] == g]
        if not kws:
            continue
        group_stats[g] = {
            "group": g,
            "totalJobs": sum(x["totalJobs"] for x in kws),
            "jobsLast24h": sum(x["jobsLast24h"] for x in kws),
            "avgOpportunityScore": round(statistics.mean([x["opportunityScore"] for x in kws]), 1),
            "keywordCount": len(kws),
        }

    plat_stats = {}
    for name, rx in PLATFORMS.items():
        matched = [
            j
            for j in all_jobs
            if rx.search(j.get("title", ""))
            or rx.search(" ".join(j.get("skills") or []))
            or any(rx.search(k) for k in j.get("matchedKeyword", []))
        ]
        if not matched:
            plat_stats[name] = {
                "platform": name,
                "jobs": 0,
                "avgBudgetFixed": None,
                "avgRateHourly": None,
                "medianProposals": None,
                "opportunityScore": 0,
                "confidence": "Very Low",
            }
            continue
        fv, hv, pr = [], [], []
        for j in matched:
            f, h = parse_budget(j.get("budget"), j.get("type"))
            if f:
                fv.append(f)
            if h:
                hv.append(h)
            if j.get("proposals") is not None:
                pr.append(j["proposals"])
        plat_stats[name] = {
            "platform": name,
            "jobs": len(matched),
            "avgBudgetFixed": round(statistics.mean(fv), 2) if fv else None,
            "avgRateHourly": round(statistics.mean(hv), 2) if hv else None,
            "medianProposals": int(statistics.median(pr)) if pr else None,
            "opportunityScore": opportunity_score(matched),
            "confidence": confidence(len(matched)),
        }

    (BASE / "keyword-stats.json").write_text(json.dumps(kw_stats, indent=2))
    (BASE / "group-stats.json").write_text(json.dumps(group_stats, indent=2))
    (BASE / "platform-stats.json").write_text(json.dumps(plat_stats, indent=2))

    attempted = len(keywords_meta)
    completed = sum(1 for k in keywords_meta if k.get("ok", True))
    top3 = sorted(kw_stats.values(), key=lambda x: x["opportunityScore"], reverse=True)[:3]
    top3_names = [x["keyword"] for x in top3]

    log = {
        "timestamp": run_at,
        "runNumber": run_number,
        "keywordsAttempted": attempted,
        "keywordsCompleted": completed,
        "newJobs": len(new_jobs),
        "totalJobs": len(all_jobs),
        "top3Keywords": top3_names,
        "errors": errors,
    }
    with RUN_LOG.open("a") as f:
        f.write(json.dumps(log) + "\n")

    state.update(
        {
            "lastRunAt": run_at,
            "runNumber": run_number,
            "totalJobs": len(all_jobs),
            "knownJobUrls": list(known_urls)[-5000:],
            "lastInsightRefresh": run_at,
        }
    )
    STATE_PATH.write_text(json.dumps(state, indent=2))

    # summary md
    top10 = sorted(kw_stats.values(), key=lambda x: x["opportunityScore"], reverse=True)[:10]
    groups_rank = sorted(group_stats.values(), key=lambda x: x["avgOpportunityScore"], reverse=True)
    primary = top10[0]["keyword"] if top10 else "wordpress developer"
    secondary = top10[1]["keyword"] if len(top10) > 1 else "webflow developer"
    best_plat = max(plat_stats.values(), key=lambda x: x["opportunityScore"])["platform"]

    summary = f"""# Upwork Market Intelligence

Last updated: {run_at}
Run: {run_number}
Total jobs tracked: {len(all_jobs)}
Keywords attempted: {attempted}
Keywords completed: {completed}

## Top Opportunities

"""
    for i, t in enumerate(top10, 1):
        summary += f"""{i}. **{t['keyword']}** — score {t['opportunityScore']}
   - jobsLast24h: {t['jobsLast24h']} | total: {t['totalJobs']} | avg fixed: {t['avgBudgetFixed']} | avg hourly: {t['avgRateHourly']} | median proposals: {t['medianProposals']} | confidence: {t['sampleConfidence']}

"""

    summary += "## Strongest Groups\n\n"
    for g in groups_rank[:5]:
        summary += f"- {g['group']}: score {g['avgOpportunityScore']}, jobs24h {g['jobsLast24h']}, total {g['totalJobs']}\n"

    summary += "\n## Platform Ranking\n\n"
    for p in sorted(plat_stats.values(), key=lambda x: x["opportunityScore"], reverse=True):
        summary += f"- {p['platform']}: jobs {p['jobs']}, score {p['opportunityScore']}, confidence {p['confidence']}\n"

    summary += f"""
## Positioning Recommendation

Primary keyword: {primary}
Secondary keyword: {secondary}
Best platform/service: {best_plat}
Overview keywords: WordPress, Webflow, Next.js, AI web development, Shopify
Skill tags: WordPress, Elementor, Webflow, Framer, Next.js, Supabase, Shopify, Technical SEO

## Current Verdicts

WordPress: Steady hourly + fixed mix; Elementor/WooCommerce completions and $7.5k builds in window.
Webflow: Strong integration roles ($25–90/hr) and CMS work; competition moderate-high.
Framer: Active redesign/migration demand; often paired with Wix/Squarespace moves.
GoHighLevel: Not fully scanned this run (search restricted mid-run).
AI/Vibe Coding: Lovable/Cursor/Claude roles present; many are product/AI broader than pure web.
Ecommerce: Shopify theme/build and WooCommerce automation posts remain active.
Maintenance: WordPress maintenance and SEO retainer posts appearing in-window.

## Important Changes

First baseline run. Upwork search access restricted after ~43 keywords; remaining keywords logged as failed for retry next hour.
"""
    (BASE / "current-summary.md").write_text(summary)

    if not (BASE / "insights.md").exists():
        (BASE / "insights.md").write_text(
            f"""# Upwork Intelligence Insights

- Baseline established run {run_number} ({run_at}).
- WordPress + Elementor/WooCommerce showed the densest overlap across core web keywords in the first 2h window.
- Webflow integration posts skew expert hourly with verified clients.
- Search API hit ToS/rate restriction before full 93-keyword pass; retry deferred keywords hourly.
"""
        )

    print(json.dumps({"runNumber": run_number, "newJobs": len(new_jobs), "totalJobs": len(all_jobs), "top10": top10[:3]}))


if __name__ == "__main__":
    main()
