#!/usr/bin/env python3
"""Process raw Upwork search batches into jobs.jsonl and stats files."""
import json
import re
import statistics
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parent
RAW = BASE / "raw-search-batch.jsonl"
SKIP_PATTERNS = re.compile(
    r"\b(alcohol|gambling|casino|adult content|porn|crypto trading|dating app)\b", re.I
)

PLATFORMS = {
    "WordPress": re.compile(r"wordpress|elementor|woocommerce|oxygen|bricks", re.I),
    "Webflow": re.compile(r"webflow", re.I),
    "Framer": re.compile(r"framer", re.I),
    "GoHighLevel": re.compile(r"gohighlevel|go high level|\bghl\b|highlevel", re.I),
    "Shopify": re.compile(r"shopify", re.I),
    "WooCommerce": re.compile(r"woocommerce", re.I),
    "Shopware": re.compile(r"shopware", re.I),
    "Lovable": re.compile(r"lovable", re.I),
    "Bolt": re.compile(r"\bbolt\.new\b|\bbolt developer\b", re.I),
    "v0": re.compile(r"\bv0\b|v0 vercel", re.I),
    "Next.js": re.compile(r"next\.?js", re.I),
}


def norm_url(url: str) -> str:
    return url.split("?")[0] if url else ""


def parse_budget(budget_str):
    if not budget_str:
        return None, None
    s = budget_str.replace(",", "")
    if "–" in s or "-" in s:
        parts = re.split(r"[–-]", s)
        nums = []
        for p in parts:
            p = p.strip().replace("/hr", "").replace("$", "").strip()
            try:
                nums.append(float(p))
            except ValueError:
                pass
        if nums:
            return sum(nums) / len(nums), "hourly" if "/hr" in budget_str or "hr" in budget_str.lower() else None
    m = re.search(r"[\d.]+", s.replace("$", ""))
    if m:
        return float(m.group()), "fixed"
    return None, None


def parse_job(raw, keyword, group, window_hours):
    url = raw.get("url")
    if not url:
        return None
    posted = raw.get("published_date") or raw.get("created_date")
    if not posted:
        return None
    try:
        dt = datetime.fromisoformat(posted.replace("Z", "+00:00"))
    except ValueError:
        return None
    now = datetime.now(timezone.utc)
    age_h = (now - dt).total_seconds() / 3600
    if age_h > window_hours:
        return None
    title = raw.get("title") or ""
    snippet = raw.get("description_snippet") or ""
    if SKIP_PATTERNS.search(title + " " + snippet):
        return None
    client = raw.get("client") or {}
    budget_raw = raw.get("budget")
    avg_b, _ = parse_budget(budget_raw) if budget_raw else (None, None)
    jtype = raw.get("job_type")
    spend = client.get("total_spent")
    if spend and isinstance(spend, str):
        spend = spend.replace(",", "").replace("$", "").strip() or None
    return {
        "url": norm_url(url),
        "title": title,
        "matchedKeyword": [keyword],
        "keywordGroup": group,
        "postedAt": posted,
        "type": jtype,
        "budget": budget_raw,
        "budgetNumeric": avg_b,
        "duration": raw.get("duration"),
        "proposals": raw.get("proposal_count"),
        "clientCountry": client.get("country"),
        "paymentVerified": (client.get("verification_status") == "VERIFIED"),
        "clientSpend": spend,
        "clientHireRate": None,
        "clientRating": client.get("rating"),
        "experienceLevel": raw.get("experience_level"),
        "skills": raw.get("skills") or [],
    }


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


def is_high_budget(job):
    if job.get("type") == "fixed" and job.get("budgetNumeric") and job["budgetNumeric"] >= 1000:
        return True
    if job.get("type") == "hourly" and job.get("budgetNumeric") and job["budgetNumeric"] >= 40:
        return True
    b = job.get("budget") or ""
    if job.get("type") == "hourly":
        m = re.findall(r"([\d.]+)", b.replace(",", ""))
        if m:
            vals = [float(x) for x in m]
            if max(vals) >= 40:
                return True
    if job.get("type") == "fixed":
        m = re.search(r"([\d,]+)", b)
        if m and float(m.group(1).replace(",", "")) >= 1000:
            return True
    return False


def opportunity_score(jobs):
    if not jobs:
        return 1
    recency = min(1.0, sum(1 for j in jobs if j.get("_age_h", 24) <= 2) / max(len(jobs), 1))
    verified = sum(1 for j in jobs if j.get("paymentVerified")) / len(jobs)
    high_b = sum(1 for j in jobs if is_high_budget(j)) / len(jobs)
    props = [j["proposals"] for j in jobs if j.get("proposals") is not None]
    low_comp = 1.0 - min(1.0, (statistics.median(props) if props else 50) / 100)
    budgets = [j["budgetNumeric"] for j in jobs if j.get("budgetNumeric")]
    pay = min(1.0, (statistics.mean(budgets) if budgets else 0) / 2000)
    raw = 0.25 * recency + 0.2 * pay + 0.2 * low_comp + 0.2 * high_b + 0.15 * verified
    return max(1, min(100, int(raw * 100)))


def main():
    keywords = json.loads((BASE / "keywords.json").read_text())
    kw_map = {k["keyword"]: k["group"] for k in keywords}
    state_path = BASE / "state.json"
    if state_path.exists():
        state = json.loads(state_path.read_text())
        run_number = state.get("runNumber", 0) + 1
        known = set(state.get("knownJobUrls", []))
    else:
        run_number = 1
        known = set()
    window_hours = 2 if run_number == 1 else 1
    now_iso = datetime.now(timezone.utc).isoformat()

    jobs_by_url = {}
    if (BASE / "jobs.jsonl").exists():
        for line in (BASE / "jobs.jsonl").read_text().splitlines():
            if line.strip():
                j = json.loads(line)
                jobs_by_url[j["url"]] = j

    keywords_attempted = len(keywords)
    keywords_completed = 0
    errors = []
    kw_hits = {k["keyword"]: 0 for k in keywords}

    if RAW.exists():
        for line in RAW.read_text().splitlines():
            if not line.strip():
                continue
            batch = json.loads(line)
            kw = batch.get("keyword")
            if kw not in kw_map:
                continue
            if batch.get("error"):
                errors.append(kw)
                continue
            keywords_completed += 1
            group = kw_map[kw]
            for raw in batch.get("jobs", []):
                job = parse_job(raw, kw, group, window_hours)
                if not job:
                    continue
                kw_hits[kw] += 1
                u = job["url"]
                if u in jobs_by_url:
                    mk = jobs_by_url[u].setdefault("matchedKeyword", [])
                    if kw not in mk:
                        mk.append(kw)
                else:
                    jobs_by_url[u] = job

    new_jobs = [j for u, j in jobs_by_url.items() if u not in known]
    with (BASE / "jobs.jsonl").open("w") as f:
        for j in jobs_by_url.values():
            f.write(json.dumps(j, ensure_ascii=False) + "\n")

    all_jobs = list(jobs_by_url.values())
    now = datetime.now(timezone.utc)

    def age_h(j):
        try:
            dt = datetime.fromisoformat(j["postedAt"].replace("Z", "+00:00"))
            return (now - dt).total_seconds() / 3600
        except Exception:
            return 999

    for j in all_jobs:
        j["_age_h"] = age_h(j)

    keyword_stats = {}
    for k in keywords:
        kw = k["keyword"]
        kj = [j for j in all_jobs if kw in j.get("matchedKeyword", [])]
        fixed = [j["budgetNumeric"] for j in kj if j.get("type") == "fixed" and j.get("budgetNumeric")]
        hourly = [j["budgetNumeric"] for j in kj if j.get("type") == "hourly" and j.get("budgetNumeric")]
        props = [j["proposals"] for j in kj if j.get("proposals") is not None]
        spends = []
        for j in kj:
            s = j.get("clientSpend")
            if s:
                try:
                    spends.append(float(str(s).replace(",", "").replace("$", "")))
                except ValueError:
                    pass
        j24 = sum(1 for j in kj if j["_age_h"] <= 24)
        keyword_stats[kw] = {
            "totalJobs": len(kj),
            "jobsLast24h": j24,
            "avgBudgetFixed": round(statistics.mean(fixed), 2) if fixed else None,
            "avgRateHourly": round(statistics.mean(hourly), 2) if hourly else None,
            "medianProposals": int(statistics.median(props)) if props else None,
            "pctVerified": round(100 * sum(1 for j in kj if j.get("paymentVerified")) / len(kj), 1) if kj else 0,
            "avgClientSpend": round(statistics.mean(spends), 2) if spends else None,
            "pctHighBudget": round(100 * sum(1 for j in kj if is_high_budget(j)) / len(kj), 1) if kj else 0,
            "opportunityScore": opportunity_score(kj),
            "sampleConfidence": confidence(len(kj)),
        }

    group_stats = {}
    groups = sorted(set(k["group"] for k in keywords))
    for g in groups:
        gj = [j for j in all_jobs if j.get("keywordGroup") == g or any(
            kw_map.get(mk) == g for mk in j.get("matchedKeyword", [])
        )]
        group_stats[g] = {
            "totalJobs": len(gj),
            "jobsLast24h": sum(1 for j in gj if j["_age_h"] <= 24),
            "opportunityScore": opportunity_score(gj),
            "sampleConfidence": confidence(len(gj)),
        }

    platform_stats = {}
    for pname, pat in PLATFORMS.items():
        pj = [j for j in all_jobs if pat.search(j.get("title", "") + " " + " ".join(j.get("skills") or []))]
        platform_stats[pname] = {
            "jobs": len(pj),
            "jobsLast24h": sum(1 for j in pj if j["_age_h"] <= 24),
            "avgBudgetOrRate": None,
            "medianProposals": int(statistics.median([x for x in [j.get("proposals") for j in pj] if x is not None])) if pj else None,
            "opportunityScore": opportunity_score(pj),
            "sampleConfidence": confidence(len(pj)),
        }
        nums = [j["budgetNumeric"] for j in pj if j.get("budgetNumeric")]
        if nums:
            platform_stats[pname]["avgBudgetOrRate"] = round(statistics.mean(nums), 2)

    (BASE / "keyword-stats.json").write_text(json.dumps(keyword_stats, indent=2))
    (BASE / "group-stats.json").write_text(json.dumps(group_stats, indent=2))
    (BASE / "platform-stats.json").write_text(json.dumps(platform_stats, indent=2))

    top3 = sorted(keyword_stats.items(), key=lambda x: x[1]["jobsLast24h"], reverse=True)[:3]
    log = {
        "timestamp": now_iso,
        "runNumber": run_number,
        "keywordsAttempted": keywords_attempted,
        "keywordsCompleted": keywords_completed,
        "newJobs": len(new_jobs),
        "totalJobs": len(all_jobs),
        "top3Keywords": [t[0] for t in top3],
        "errors": errors,
    }
    with (BASE / "run-log.jsonl").open("a") as f:
        f.write(json.dumps(log) + "\n")

    state_out = {
        "lastRunAt": now_iso,
        "runNumber": run_number,
        "totalJobs": len(all_jobs),
        "knownJobUrls": list(jobs_by_url.keys()),
        "lastInsightRefresh": now_iso if run_number == 1 else state.get("lastInsightRefresh") if state_path.exists() else now_iso,
    }
    state_path.write_text(json.dumps(state_out, indent=2))

    write_summary(
        run_number,
        keywords_attempted,
        keywords_completed,
        len(all_jobs),
        keyword_stats,
        group_stats,
        platform_stats,
        errors,
    )

    out = {
        "run": run_number,
        "new": len(new_jobs),
        "new_jobs": new_jobs,
        "total": len(all_jobs),
        "completed": keywords_completed,
        "errors": errors,
        "keyword_stats": keyword_stats,
        "group_stats": group_stats,
        "platform_stats": platform_stats,
        "log": log,
    }
    (BASE / "last-run-output.json").write_text(json.dumps(out, default=str))
    print(json.dumps({"run": run_number, "new": len(new_jobs), "total": len(all_jobs), "completed": keywords_completed, "errors": len(errors)}))


def write_summary(run_number, attempted, completed, total_jobs, keyword_stats, group_stats, platform_stats, errors):
    top_kw = sorted(keyword_stats.items(), key=lambda x: (-x[1]["opportunityScore"], -x[1]["jobsLast24h"]))[:10]
    top_groups = sorted(group_stats.items(), key=lambda x: -x[1]["opportunityScore"])
    lines = [
        "# Upwork Market Intelligence",
        "",
        f"Last updated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        f"Run: {run_number}",
        f"Total jobs tracked: {total_jobs}",
        f"Keywords attempted: {attempted}",
        f"Keywords completed: {completed}",
        "",
        "## Top Opportunities",
        "",
    ]
    for kw, st in top_kw:
        lines.append(
            f"- **{kw}** — score {st['opportunityScore']}, confidence {st['sampleConfidence']}, "
            f"24h {st['jobsLast24h']}, total {st['totalJobs']}, "
            f"avg fixed {st['avgBudgetFixed']}, avg hourly {st['avgRateHourly']}, "
            f"median proposals {st['medianProposals']}"
        )
    lines.extend(["", "## Strongest Groups", ""])
    for i, (g, st) in enumerate(top_groups, 1):
        lines.append(f"{i}. {g} — score {st['opportunityScore']}, 24h {st['jobsLast24h']}, total {st['totalJobs']}")
    lines.extend(["", "## Platform Ranking", ""])
    for pname, st in sorted(platform_stats.items(), key=lambda x: -x[1]["opportunityScore"]):
        lines.append(
            f"- {pname}: jobs {st['jobs']}, 24h {st['jobsLast24h']}, "
            f"avg {st.get('avgBudgetOrRate')}, median proposals {st['medianProposals']}, "
            f"score {st['opportunityScore']}, {st['sampleConfidence']}"
        )
    best_kw = top_kw[0][0] if top_kw else "full stack developer"
    sec_kw = top_kw[1][0] if len(top_kw) > 1 else "wordpress developer"
    lines.extend(
        [
            "",
            "## Positioning Recommendation",
            "",
            f"Primary keyword: {best_kw}",
            f"Secondary keyword: {sec_kw}",
            "Best platform/service: WordPress / Next.js (volume) with AI-assisted delivery",
            "Overview keywords: Next.js, WordPress, Webflow, Supabase, AI web development",
            "Skill tags: Next.js, React, TypeScript, WordPress, Elementor, Webflow, Supabase, Stripe",
            "",
            "## Current Verdicts",
            "",
            "WordPress: Steady hourly and fixed volume; Elementor and maintenance retainers show up often.",
            "Webflow: Lower volume than WordPress; good for design-led agency work.",
            "Framer: Niche but less competition on specialized Framer posts.",
            "GoHighLevel: Funnel and CRM integration demand; often lower rates unless US clients.",
            "AI/Vibe Coding: Growing mentions (Cursor, Claude, Lovable); quality clients filter AI spam.",
            "Ecommerce: Shopify and WooCommerce both active; fixed budgets vary widely.",
            "Maintenance: Retainer keywords slower but higher fit for long-term positioning.",
            "",
            "## Important Changes",
            "",
            "Baseline run established." if run_number == 1 else "See hourly chat update for deltas.",
        ]
    )
    if errors:
        lines.append(f"Failed keyword searches: {', '.join(errors)}")
    (BASE / "current-summary.md").write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
