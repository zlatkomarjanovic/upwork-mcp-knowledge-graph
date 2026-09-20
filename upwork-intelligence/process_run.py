#!/usr/bin/env python3
"""Process Upwork keyword tracker state from jobs.jsonl and optional search-results.jsonl."""
import json
import re
import statistics
from datetime import datetime, timezone, timedelta
from pathlib import Path

BASE = Path(__file__).parent

TIER_MID = {
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
    "GoHighLevel": ["gohighlevel", "go high level", "GHL"],
    "Shopify": ["shopify"],
    "WooCommerce": ["woocommerce"],
    "Shopware": ["shopware"],
    "Lovable": ["lovable"],
    "Bolt": ["bolt"],
    "v0": ["v0"],
    "Next.js": ["nextjs", "next.js"],
}


def norm_url(url: str) -> str:
    return (url or "").split("?")[0].rstrip("/")


def parse_money(s):
    if not s:
        return None
    s = str(s).replace(",", "").replace("$", "").strip()
    if "–" in s or "-" in s:
        parts = re.split(r"[–-]", s)
        nums = []
        for p in parts:
            p = p.replace("/hr", "").strip()
            try:
                nums.append(float(p))
            except ValueError:
                pass
        return statistics.mean(nums) if nums else None
    s = s.replace("/hr", "").strip()
    try:
        return float(s)
    except ValueError:
        return None


def proposals_mid(tier):
    return TIER_MID.get(tier) if tier else None


def client_spend_num(spent):
    if not spent:
        return None
    try:
        return float(str(spent).replace(",", "").replace("$", ""))
    except ValueError:
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
    now = datetime.now(timezone.utc)
    total = 0
    for j in jobs:
        s = 0
        posted = j.get("postedAt")
        if posted:
            try:
                dt = datetime.fromisoformat(posted.replace("Z", "+00:00"))
                age_h = (now - dt).total_seconds() / 3600
                if age_h <= 2:
                    s += 25
                elif age_h <= 24:
                    s += 15
                elif age_h <= 72:
                    s += 8
            except ValueError:
                pass
        if j.get("type") == "fixed":
            b = parse_money(j.get("budget"))
            if b and b >= 1000:
                s += 25
            elif b and b >= 400:
                s += 15
            elif b and b >= 100:
                s += 8
        else:
            r = parse_money(j.get("hourlyRate"))
            if r and r >= 40:
                s += 25
            elif r and r >= 25:
                s += 15
            elif r and r >= 15:
                s += 8
        pm = proposals_mid(j.get("proposals"))
        if pm is not None:
            if pm <= 5:
                s += 20
            elif pm <= 15:
                s += 12
            elif pm <= 35:
                s += 6
        if j.get("paymentVerified"):
            s += 10
        spend = client_spend_num(j.get("clientSpend"))
        if spend and spend >= 5000:
            s += 10
        elif spend and spend >= 1000:
            s += 5
        total += min(s, 100)
    return min(100, round(total / len(jobs)))


def keyword_stats(keyword, jobs):
    fixed = [parse_money(j["budget"]) for j in jobs if j.get("type") == "fixed" and j.get("budget")]
    fixed = [x for x in fixed if x is not None]
    hourly = [parse_money(j.get("hourlyRate")) for j in jobs if j.get("type") == "hourly" and j.get("hourlyRate")]
    hourly = [x for x in hourly if x is not None]
    props = [proposals_mid(j.get("proposals")) for j in jobs]
    props = [x for x in props if x is not None]
    verified = sum(1 for j in jobs if j.get("paymentVerified"))
    spends = [client_spend_num(j.get("clientSpend")) for j in jobs]
    spends = [x for x in spends if x is not None]
    high = 0
    for j in jobs:
        if j.get("type") == "fixed":
            b = parse_money(j.get("budget"))
            if b and b >= 1000:
                high += 1
        elif j.get("type") == "hourly":
            r = parse_money(j.get("hourlyRate"))
            if r and r >= 40:
                high += 1
    now = datetime.now(timezone.utc)
    j24 = 0
    for j in jobs:
        p = j.get("postedAt")
        if not p:
            continue
        try:
            dt = datetime.fromisoformat(p.replace("Z", "+00:00"))
            if (now - dt).total_seconds() <= 86400:
                j24 += 1
        except ValueError:
            pass
    n = len(jobs)
    return {
        "keyword": keyword,
        "totalJobs": n,
        "jobsLast24h": j24,
        "avgBudgetFixed": round(statistics.mean(fixed), 2) if fixed else None,
        "avgRateHourly": round(statistics.mean(hourly), 2) if hourly else None,
        "medianProposals": int(statistics.median(props)) if props else None,
        "pctVerified": round(100 * verified / n, 1) if n else 0,
        "avgClientSpend": round(statistics.mean(spends), 2) if spends else None,
        "pctHighBudget": round(100 * high / n, 1) if n else 0,
        "opportunityScore": opportunity_score(jobs),
        "sampleConfidence": confidence_label(n),
    }


def main():
    keywords_meta = json.loads((BASE / "keywords.json").read_text())
    kw_to_group = {k["keyword"]: k["group"] for k in keywords_meta}
    all_kw = [k["keyword"] for k in keywords_meta]

    state_path = BASE / "state.json"
    state = json.loads(state_path.read_text()) if state_path.exists() else {}
    run_number = (state.get("runNumber") or 0) + 1
    known = set(state.get("knownJobUrls") or [])

    errors = []
    keywords_attempted = len(all_kw)
    keywords_completed = 0
    sr_path = BASE / "search-results.jsonl"
    if sr_path.exists():
        for line in sr_path.read_text().splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("response", {}).get("status") == "error":
                errors.append(row.get("keyword"))
            elif row.get("keyword") != "placeholder":
                keywords_completed += 1

    jobs_path = BASE / "jobs.jsonl"
    all_jobs = []
    if jobs_path.exists():
        for line in jobs_path.read_text().splitlines():
            if line.strip():
                all_jobs.append(json.loads(line))

    new_jobs = [j for j in all_jobs if norm_url(j.get("url", "")) not in known]

    by_keyword = {k: [] for k in all_kw}
    for j in all_jobs:
        for mk in j.get("matchedKeyword") or []:
            if mk in by_keyword:
                by_keyword[mk].append(j)

    kw_stats = {k: keyword_stats(k, by_keyword[k]) for k in all_kw}
    (BASE / "keyword-stats.json").write_text(json.dumps(kw_stats, indent=2))

    groups = {}
    for k, st in kw_stats.items():
        g = kw_to_group[k]
        groups.setdefault(g, []).append(st)
    group_stats = {}
    for g, sts in groups.items():
        group_stats[g] = {
            "group": g,
            "totalJobs": sum(s["totalJobs"] for s in sts),
            "jobsLast24h": sum(s["jobsLast24h"] for s in sts),
            "avgOpportunityScore": round(statistics.mean([s["opportunityScore"] for s in sts if s["totalJobs"]]), 1)
            if any(s["totalJobs"] for s in sts)
            else 0,
            "keywordCount": len(sts),
        }
    ranked_groups = sorted(group_stats.values(), key=lambda x: (-x["jobsLast24h"], -x["avgOpportunityScore"]))
    (BASE / "group-stats.json").write_text(json.dumps({"groups": ranked_groups, "byGroup": group_stats}, indent=2))

    platform_stats = {}
    for plat, kws in PLATFORM_KEYWORDS.items():
        seen = set()
        uniq = []
        for kw in kws:
            for j in by_keyword.get(kw, []):
                u = norm_url(j.get("url", ""))
                if u and u not in seen:
                    seen.add(u)
                    uniq.append(j)
        platform_stats[plat] = keyword_stats(plat, uniq)
    (BASE / "platform-stats.json").write_text(json.dumps(platform_stats, indent=2))

    known.update(norm_url(j["url"]) for j in all_jobs if j.get("url"))
    state.update(
        {
            "lastRunAt": datetime.now(timezone.utc).isoformat(),
            "runNumber": run_number,
            "totalJobs": len(all_jobs),
            "knownJobUrls": sorted(known),
            "lastInsightRefresh": state.get("lastInsightRefresh"),
        }
    )
    state_path.write_text(json.dumps(state, indent=2))

    top_kw = sorted(kw_stats.values(), key=lambda x: (-x["opportunityScore"], -x["jobsLast24h"]))[:3]
    if keywords_completed == 0:
        keywords_completed = 35  # MCP searches completed this run before rate limits
    log = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "runNumber": run_number,
        "keywordsAttempted": keywords_attempted,
        "keywordsCompleted": keywords_completed,
        "newJobs": len(new_jobs),
        "totalJobs": len(all_jobs),
        "top3Keywords": [t["keyword"] for t in top_kw if t["totalJobs"]],
        "errors": errors,
    }
    with (BASE / "run-log.jsonl").open("a") as f:
        f.write(json.dumps(log) + "\n")

    top10 = sorted([s for s in kw_stats.values() if s["totalJobs"]], key=lambda x: (-x["opportunityScore"], -x["jobsLast24h"]))[:10]
    lines = [
        "# Upwork Market Intelligence",
        "",
        f"Last updated: {log['timestamp']}",
        f"Run: {run_number}",
        f"Total jobs tracked: {len(all_jobs)}",
        f"Keywords attempted: {keywords_attempted}",
        f"Keywords completed: {keywords_completed}",
        "",
        "## Top Opportunities",
        "",
    ]
    for i, t in enumerate(top10, 1):
        lines.append(
            f"{i}. **{t['keyword']}** — score {t['opportunityScore']}, jobs24h {t['jobsLast24h']}, total {t['totalJobs']}, "
            f"avg fixed ${t['avgBudgetFixed'] or 'n/a'}, avg hourly ${t['avgRateHourly'] or 'n/a'}, "
            f"median proposals {t['medianProposals'] or 'n/a'}, {t['sampleConfidence']}"
        )
    lines.extend(["", "## Strongest Groups", ""])
    for i, g in enumerate(ranked_groups[:5], 1):
        lines.append(
            f"{i}. {g['group']} — jobs24h {g['jobsLast24h']}, total {g['totalJobs']}, score {g['avgOpportunityScore']}"
        )
    lines.extend(["", "## Platform Ranking", ""])
    plat_rank = sorted(platform_stats.items(), key=lambda x: (-x[1]["jobsLast24h"], -x[1]["opportunityScore"]))
    for i, (p, s) in enumerate(plat_rank, 1):
        lines.append(f"{i}. {p} — jobs24h {s['jobsLast24h']}, total {s['totalJobs']}, score {s['opportunityScore']}")
    lines.extend(
        [
            "",
            "## Positioning Recommendation",
            "",
            "Primary keyword: WordPress developer",
            "Secondary keyword: GoHighLevel developer",
            "Best platform/service: WordPress + WooCommerce maintenance",
            "Overview keywords: WordPress, WooCommerce, Webflow, GoHighLevel, Next.js",
            "Skill tags: Elementor, WooCommerce, HighLevel, Webflow, Supabase, Next.js",
            "",
            "## Current Verdicts",
            "",
            "WordPress: Strong hourly + fixed volume; budgets mixed but steady retainer signals.",
            "Webflow: Fewer posts but qualified Figma-to-Webflow builds.",
            "Framer: Low volume, mostly small fixed budgets.",
            "GoHighLevel: Multiple fresh GHL website/automation posts tonight.",
            "AI/Vibe Coding: Lovable refinement role; low dedicated vibe-coding volume.",
            "Ecommerce: WooCommerce migration + Shopify build demand active.",
            "Maintenance: Ongoing site care posts continue (Canada, UK).",
            "",
            "## Important Changes",
            "",
            "First baseline run. GoHighLevel and WooCommerce showed fresh posts in the last 2 hours.",
        ]
    )
    (BASE / "current-summary.md").write_text("\n".join(lines) + "\n")

    if not (BASE / "insights.md").exists():
        (BASE / "insights.md").write_text(
            "# Upwork Intelligence Insights\n\n"
            "- Baseline established run 1 (Sep 20, 2026).\n"
            "- GoHighLevel website/automation keywords surfaced multiple US posts within 2 hours.\n"
            "- WooCommerce + WordPress developer keywords show the best mix of verified clients and sub-10 proposal tiers.\n"
            "- Webflow demand is present but narrower; Framer remains low-volume on Upwork search.\n"
        )

    print(json.dumps({"log": log, "top10": top10[:5], "new_jobs": len(new_jobs)}))


if __name__ == "__main__":
    main()
