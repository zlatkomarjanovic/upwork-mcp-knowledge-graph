#!/usr/bin/env python3
"""Process Upwork search batch results into intelligence files."""
import json
import re
import statistics
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parent
WINDOW_HOURS = 2  # first run

SKIP_PATTERNS = re.compile(
    r"\b(alcohol|gambling|casino|betting|porn|adult content|crypto trading|dating)\b",
    re.I,
)

PROPOSAL_MID = {
    "Fewer than 5": 2,
    "5 to 10": 7,
    "10 to 15": 12,
    "15 to 20": 17,
    "20 to 50": 35,
    "50+": 55,
}

PLATFORM_KEYWORDS = {
    "WordPress": ["wordpress"],
    "Webflow": ["webflow"],
    "Framer": ["framer"],
    "GoHighLevel": ["gohighlevel", "go high level", "ghl"],
    "Shopify": ["shopify"],
    "WooCommerce": ["woocommerce"],
    "Shopware": ["shopware"],
    "Lovable": ["lovable"],
    "Bolt": ["bolt.new", "bolt developer"],
    "v0": ["v0 developer", "v0 vercel"],
    "Next.js": ["nextjs", "next.js"],
}


def norm_url(url: str) -> str:
    return url.split("?")[0] if url else ""


def parse_money(s):
    if not s:
        return None
    s = str(s).replace(",", "")
    m = re.search(r"([\d.]+)", s)
    return float(m.group(1)) if m else None


def parse_hourly_mid(budget: str):
    if not budget or "hr" not in budget.lower():
        return None
    parts = re.findall(r"([\d.]+)", budget.replace(",", ""))
    if len(parts) >= 2:
        return (float(parts[0]) + float(parts[1])) / 2
    if len(parts) == 1:
        return float(parts[0])
    return None


def parse_fixed(budget: str):
    if not budget or "hr" in budget.lower():
        return None
    return parse_money(budget)


def proposals_mid(tier):
    if not tier:
        return None
    return PROPOSAL_MID.get(tier)


def client_spend_num(spent):
    if not spent:
        return None
    return parse_money(str(spent).replace("$", ""))


def in_window(iso: str, now: datetime, hours: float) -> bool:
    if not iso:
        return False
    try:
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        return (now - dt).total_seconds() <= hours * 3600
    except ValueError:
        return False


def should_skip(job: dict) -> bool:
    text = (job.get("title") or "") + " " + (job.get("description_snippet") or "")
    return bool(SKIP_PATTERNS.search(text))


def job_record(job: dict, keyword: str, group: str) -> dict:
    client = job.get("client") or {}
    ver = client.get("verification_status") == "VERIFIED"
    return {
        "url": norm_url(job.get("url") or ""),
        "title": job.get("title"),
        "matchedKeyword": [keyword],
        "keywordGroup": group,
        "postedAt": job.get("published_date") or job.get("created_date"),
        "type": job.get("job_type"),
        "budget": job.get("budget"),
        "duration": job.get("duration"),
        "proposals": job.get("proposals_tier"),
        "clientCountry": client.get("country"),
        "paymentVerified": ver,
        "clientSpend": client.get("total_spent"),
        "clientHireRate": None,
        "clientRating": client.get("rating"),
        "experienceLevel": job.get("experience_level"),
        "skills": job.get("skills") or [],
    }


def confidence_label(n: int) -> str:
    if n <= 4:
        return "Very Low"
    if n <= 14:
        return "Low"
    if n <= 39:
        return "Medium"
    if n <= 99:
        return "High"
    return "Very High"


def is_high_budget(rec: dict) -> bool:
    b = rec.get("budget") or ""
    if rec.get("type") == "fixed":
        v = parse_fixed(b)
        return v is not None and v >= 1000
    if rec.get("type") == "hourly":
        v = parse_hourly_mid(b)
        return v is not None and v >= 40
    return False


def opportunity_score(jobs: list, now: datetime) -> float:
    if not jobs:
        return 0.0
    score = 0.0
    for j in jobs:
        recency = 1.0
        pa = j.get("postedAt")
        if pa:
            try:
                dt = datetime.fromisoformat(pa.replace("Z", "+00:00"))
                age_h = (now - dt).total_seconds() / 3600
                recency = max(0.2, 1.0 - age_h / 48)
            except ValueError:
                pass
        prop = proposals_mid(j.get("proposals")) or 20
        comp = max(0.3, 1.0 - prop / 60)
        pay = 0.5
        if j.get("type") == "fixed":
            v = parse_fixed(j.get("budget") or "")
            if v:
                pay = min(1.5, v / 1000)
        else:
            v = parse_hourly_mid(j.get("budget") or "")
            if v:
                pay = min(1.5, v / 40)
        hb = 1.2 if is_high_budget(j) else 1.0
        ver = 1.1 if j.get("paymentVerified") else 1.0
        score += recency * comp * pay * hb * ver
    raw = score / len(jobs) * 25
    return max(1, min(100, round(raw)))


def keyword_stats(keyword: str, jobs: list, now: datetime) -> dict:
    last24 = [
        j
        for j in jobs
        if in_window(j.get("postedAt") or "", now, 24)
    ]
    fixed = [parse_fixed(j["budget"]) for j in jobs if j.get("type") == "fixed"]
    fixed = [x for x in fixed if x is not None]
    hourly = [parse_hourly_mid(j["budget"]) for j in jobs if j.get("type") == "hourly"]
    hourly = [x for x in hourly if x is not None]
    props = [proposals_mid(j.get("proposals")) for j in jobs]
    props = [x for x in props if x is not None]
    verified = sum(1 for j in jobs if j.get("paymentVerified"))
    spends = [client_spend_num(j.get("clientSpend")) for j in jobs]
    spends = [x for x in spends if x is not None]
    high = sum(1 for j in jobs if is_high_budget(j))
    n = len(jobs)
    return {
        "keyword": keyword,
        "totalJobs": n,
        "jobsLast24h": len(last24),
        "avgBudgetFixed": round(statistics.mean(fixed), 2) if fixed else None,
        "avgRateHourly": round(statistics.mean(hourly), 2) if hourly else None,
        "medianProposals": int(statistics.median(props)) if props else None,
        "pctVerified": round(100 * verified / n, 1) if n else 0,
        "avgClientSpend": round(statistics.mean(spends), 2) if spends else None,
        "pctHighBudget": round(100 * high / n, 1) if n else 0,
        "opportunityScore": opportunity_score(jobs, now),
        "sampleConfidence": confidence_label(n),
    }


def platform_jobs(all_jobs: list, needles: list) -> list:
    out = []
    for j in all_jobs:
        blob = " ".join(
            [
                j.get("title") or "",
                " ".join(j.get("skills") or []),
                " ".join(j.get("matchedKeyword") or []),
            ]
        ).lower()
        if any(n.lower() in blob for n in needles):
            out.append(j)
    return out


def main():
    batch_path = BASE / "batch_results.json"
    data = json.loads(batch_path.read_text())
    now = datetime.now(timezone.utc)
    run_number = data.get("runNumber", 1)
    window = data.get("windowHours", WINDOW_HOURS)
    searches = data["searches"]

    jobs_by_url: dict[str, dict] = {}
    errors = []

    for entry in searches:
        kw = entry["keyword"]
        group = entry["group"]
        if entry.get("error"):
            errors.append(kw)
            continue
        for job in entry.get("jobs") or []:
            if not job.get("url"):
                continue
            if not in_window(
                job.get("published_date") or job.get("created_date") or "",
                now,
                window,
            ):
                continue
            if should_skip(job):
                continue
            url = norm_url(job["url"])
            rec = job_record(job, kw, group)
            if url in jobs_by_url:
                existing = jobs_by_url[url]
                for mk in rec["matchedKeyword"]:
                    if mk not in existing["matchedKeyword"]:
                        existing["matchedKeyword"].append(mk)
            else:
                jobs_by_url[url] = rec

    all_jobs = list(jobs_by_url.values())

    # append jobs.jsonl
    jobs_path = BASE / "jobs.jsonl"
    known = set()
    if (BASE / "state.json").exists():
        st = json.loads((BASE / "state.json").read_text())
        known = set(st.get("knownJobUrls") or [])
    new_jobs = [j for j in all_jobs if j["url"] not in known]
    with jobs_path.open("a") as f:
        for j in new_jobs:
            f.write(json.dumps(j, ensure_ascii=False) + "\n")

    # load historical jobs for stats (compact: only this run if first)
    hist = []
    if jobs_path.exists():
        for line in jobs_path.read_text().splitlines():
            if line.strip():
                hist.append(json.loads(line))
    # dedupe hist by url keeping latest merge
    hist_map = {}
    for j in hist:
        u = j["url"]
        if u in hist_map:
            for mk in j.get("matchedKeyword") or []:
                if mk not in hist_map[u]["matchedKeyword"]:
                    hist_map[u]["matchedKeyword"].append(mk)
        else:
            hist_map[u] = j
    hist = list(hist_map.values())

    kw_stats = {}
    for entry in searches:
        kw = entry["keyword"]
        kw_jobs = [j for j in hist if kw in (j.get("matchedKeyword") or [])]
        kw_stats[kw] = keyword_stats(kw, kw_jobs, now)

    groups = {}
    for j in hist:
        g = j.get("keywordGroup") or "Other"
        groups.setdefault(g, []).append(j)
    group_stats = {
        g: {
            "group": g,
            "totalJobs": len(js),
            "jobsLast24h": len(
                [x for x in js if in_window(x.get("postedAt") or "", now, 24)]
            ),
            "opportunityScore": opportunity_score(js, now),
            "sampleConfidence": confidence_label(len(js)),
        }
        for g, js in groups.items()
    }

    plat_stats = {}
    for name, needles in PLATFORM_KEYWORDS.items():
        js = platform_jobs(hist, needles)
        fixed = [parse_fixed(j["budget"]) for j in js if j.get("type") == "fixed"]
        fixed = [x for x in fixed if x is not None]
        hourly = [parse_hourly_mid(j["budget"]) for j in js if j.get("type") == "hourly"]
        hourly = [x for x in hourly if x is not None]
        props = [proposals_mid(j.get("proposals")) for j in js]
        props = [x for x in props if x is not None]
        plat_stats[name] = {
            "platform": name,
            "jobs": len(js),
            "avgBudgetFixed": round(statistics.mean(fixed), 2) if fixed else None,
            "avgRateHourly": round(statistics.mean(hourly), 2) if hourly else None,
            "medianProposals": int(statistics.median(props)) if props else None,
            "opportunityScore": opportunity_score(js, now),
            "sampleConfidence": confidence_label(len(js)),
        }

    (BASE / "keyword-stats.json").write_text(json.dumps(kw_stats, indent=2))
    (BASE / "group-stats.json").write_text(json.dumps(group_stats, indent=2))
    (BASE / "platform-stats.json").write_text(json.dumps(plat_stats, indent=2))

    attempted = len(searches)
    completed = attempted - len(errors)
    total_jobs = len(hist)
    known_urls = list(hist_map.keys())

    top3 = sorted(kw_stats.values(), key=lambda x: x["opportunityScore"], reverse=True)[
        :3
    ]
    top3_kw = [t["keyword"] for t in top3]

    log = {
        "timestamp": now.isoformat(),
        "runNumber": run_number,
        "keywordsAttempted": attempted,
        "keywordsCompleted": completed,
        "newJobs": len(new_jobs),
        "totalJobs": total_jobs,
        "top3Keywords": top3_kw,
        "errors": errors,
    }
    with (BASE / "run-log.jsonl").open("a") as f:
        f.write(json.dumps(log) + "\n")

    state = {
        "lastRunAt": now.isoformat(),
        "runNumber": run_number,
        "totalJobs": total_jobs,
        "knownJobUrls": known_urls,
        "lastInsightRefresh": now.isoformat(),
    }
    (BASE / "state.json").write_text(json.dumps(state, indent=2))

    # summary md
    top10 = sorted(kw_stats.values(), key=lambda x: x["opportunityScore"], reverse=True)[
        :10
    ]
    top_groups = sorted(
        group_stats.values(), key=lambda x: x["opportunityScore"], reverse=True
    )[:5]
    primary = top10[0]["keyword"] if top10 else "web development"
    secondary = top10[1]["keyword"] if len(top10) > 1 else "wordpress"
    best_plat = max(plat_stats.values(), key=lambda x: x["opportunityScore"])[
        "platform"
    ]

    lines = [
        "# Upwork Market Intelligence",
        "",
        f"Last updated: {now.strftime('%Y-%m-%d %H:%M UTC')}",
        f"Run: {run_number}",
        f"Total jobs tracked: {total_jobs}",
        f"Keywords attempted: {attempted}",
        f"Keywords completed: {completed}",
        "",
        "## Top Opportunities",
        "",
    ]
    for t in top10:
        lines.append(
            f"- **{t['keyword']}** — score {t['opportunityScore']} ({t['sampleConfidence']}); "
            f"24h: {t['jobsLast24h']}; total: {t['totalJobs']}; "
            f"avg fixed: {t['avgBudgetFixed']}; avg hourly: {t['avgRateHourly']}; "
            f"median proposals: {t['medianProposals']}"
        )
    lines += ["", "## Strongest Groups", ""]
    for g in top_groups:
        lines.append(
            f"- **{g['group']}** — score {g['opportunityScore']}; jobs: {g['totalJobs']}; 24h: {g['jobsLast24h']}"
        )
    lines += ["", "## Platform Ranking", ""]
    for p in sorted(plat_stats.values(), key=lambda x: x["opportunityScore"], reverse=True):
        lines.append(
            f"- **{p['platform']}** — score {p['opportunityScore']}; jobs: {p['jobs']}"
        )
    lines += [
        "",
        "## Positioning Recommendation",
        "",
        f"Primary keyword: {primary}",
        f"Secondary keyword: {secondary}",
        f"Best platform/service: {best_plat}",
        "Overview keywords: WordPress, Shopify, Webflow, Next.js, website redesign",
        "Skill tags: WordPress, Shopify, Webflow, React, SEO, performance",
        "",
        "## Current Verdicts",
        "",
        "WordPress: Steady volume; mix of small fixes and migrations.",
        "Webflow: Niche but higher-rate one-page builds appearing.",
        "Framer: Low sample; monitor.",
        "GoHighLevel: Often bundled with ads/CRM, not pure web dev.",
        "AI/Vibe Coding: Claude Code and AI SaaS takeover posts show up in full-stack searches.",
        "Ecommerce: Shopify migrations and checkout customization lead.",
        "Maintenance: Retainer keywords sparse in short window; INP/speed posts fill gap.",
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
        "totalJobs": total_jobs,
        "top10": top10,
        "topGroups": top_groups,
        "platStats": plat_stats,
        "newJobsList": new_jobs,
        "errors": errors,
        "primary": primary,
        "secondary": secondary,
        "best_plat": best_plat,
    }
    (BASE / "run_output.json").write_text(json.dumps(out, indent=2, default=str))
    print(json.dumps({"ok": True, "newJobs": len(new_jobs), "total": total_jobs}))


if __name__ == "__main__":
    main()
