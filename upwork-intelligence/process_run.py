#!/usr/bin/env python3
"""Process raw search results JSON into jobs.jsonl and stats. Input: _run_raw.json"""
import json, re, statistics
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).parent
WINDOW_HOURS_FIRST = 2
WINDOW_HOURS = 1

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
        "core web vitals", "page speed optimization", "website speed optimization",
        "technical SEO website",
    ],
}

SKIP_PATTERNS = re.compile(
    r"casino|gambling|betting|poker|alcohol|brewery|distillery|"
    r"adult content|escort|onlyfans|crypto trading|forex trading|dating app",
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
    "Bolt": ["bolt.new", "bolt developer", "bolt"],
    "v0": ["v0 developer", "v0 vercel", "v0"],
    "Next.js": ["nextjs", "next.js"],
}


def norm_url(url):
    if not url:
        return None
    return url.split("?")[0]


def parse_budget(budget_str, job_type):
    if not budget_str:
        return None, None
    s = budget_str.replace(",", "")
    if job_type == "hourly" or "/hr" in s.lower():
        nums = [float(x) for x in re.findall(r"[\d.]+", s)]
        if len(nums) >= 2:
            return None, (nums[0] + nums[1]) / 2
        if len(nums) == 1:
            return None, nums[0]
        return None, None
    nums = [float(x) for x in re.findall(r"[\d.]+", s)]
    if len(nums) >= 2:
        return (nums[0] + nums[1]) / 2, None
    if len(nums) == 1:
        return nums[0], None
    return None, None


def parse_spend(s):
    if not s:
        return None
    m = re.search(r"[\d,]+\.?\d*", str(s).replace(",", ""))
    return float(m.group()) if m else None


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
        recency = 1 if j.get("_recent") else 0.3
        fixed, hourly = j.get("_fixed"), j.get("_hourly")
        pay = 0
        if fixed and fixed >= 1000:
            pay += 1.5
        elif fixed and fixed >= 500:
            pay += 1
        elif hourly and hourly >= 40:
            pay += 1.5
        elif hourly and hourly >= 25:
            pay += 0.8
        props = j.get("proposals") or 10
        comp = max(0, 1 - min(props, 50) / 50)
        ver = 0.3 if j.get("paymentVerified") else 0
        score += recency * (pay + comp + ver) * 10
    return min(100, int(score / max(len(jobs), 1) * 3))


def job_record(raw, keyword, group, now, cutoff):
    pub = raw.get("published_date") or raw.get("created_date")
    if not pub:
        return None
    try:
        dt = datetime.fromisoformat(pub.replace("Z", "+00:00"))
    except ValueError:
        return None
    if dt < cutoff:
        return None
    url = norm_url(raw.get("url"))
    if not url:
        return None
    title = raw.get("title") or ""
    desc = raw.get("description_snippet") or ""
    if SKIP_PATTERNS.search(title + " " + desc):
        return None
    client = raw.get("client") or {}
    fixed, hourly = parse_budget(raw.get("budget"), raw.get("job_type"))
    spend = parse_spend(client.get("total_spent"))
    return {
        "url": url,
        "title": title,
        "matchedKeyword": [keyword],
        "keywordGroup": group,
        "postedAt": pub,
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
        "skills": raw.get("skills"),
        "_recent": (now - dt).total_seconds() <= 3600 * WINDOW_HOURS,
        "_fixed": fixed,
        "_hourly": hourly,
        "_spend_num": spend,
    }


def main():
    log_path = BASE / "search_log.jsonl"
    ingest = BASE / "ingest_jsonl.py"
    if log_path.exists() and ingest.exists():
        import subprocess
        subprocess.run(["python3", str(ingest)], check=False)
    sr_path = BASE / "search_responses.json"
    rr_path = BASE / "run-results.jsonl"
    if sr_path.exists() and (not rr_path.exists() or sr_path.stat().st_mtime >= rr_path.stat().st_mtime):
        with rr_path.open("w") as out:
            for entry in json.loads(sr_path.read_text()):
                kw = entry.get("keyword")
                if not kw:
                    continue
                jobs = (entry.get("response") or {}).get("jobs") or []
                out.write(
                    json.dumps(
                        {"keyword": kw, "group": entry.get("group", ""), "jobs": jobs},
                        separators=(",", ":"),
                    )
                    + "\n"
                )
    raw_path = BASE / "_run_raw.json"
    if rr_path.exists():
        data_rr = {"searches": {}, "errors": []}
        if raw_path.exists():
            data_rr = json.loads(raw_path.read_text())
        for line in rr_path.read_text().splitlines():
            if not line.strip():
                continue
            o = json.loads(line)
            kw = o.get("keyword")
            if not kw:
                continue
            data_rr["searches"][kw] = {"status": "ok", "jobs": o.get("jobs") or []}
        raw_path.write_text(json.dumps(data_rr))
    raw_path = BASE / "_run_raw.json"
    if not raw_path.exists():
        print("No _run_raw.json")
        return
    data = json.loads(raw_path.read_text())
    state_path = BASE / "state.json"
    state = json.loads(state_path.read_text()) if state_path.exists() else {}
    run_number = (state.get("runNumber") or 0) + 1
    first_run = state.get("runNumber", 0) == 0
    window = WINDOW_HOURS_FIRST if first_run else WINDOW_HOURS
    now = datetime.now(timezone.utc)
    cutoff = now.timestamp() - window * 3600
    cutoff_dt = datetime.fromtimestamp(cutoff, tz=timezone.utc)

    known = set(state.get("knownJobUrls") or [])
    all_jobs = {}
    kw_hits = {}
    errors = data.get("errors") or []
    searches = data.get("searches") or {}

    for group, keywords in KEYWORD_GROUPS.items():
        for kw in keywords:
            resp = searches.get(kw)
            if resp is None:
                if kw not in errors:
                    errors.append(kw)
                continue
            if resp.get("status") != "ok":
                errors.append(kw)
                continue
            for raw in resp.get("jobs") or []:
                rec = job_record(raw, kw, group, now, cutoff_dt)
                if not rec:
                    continue
                u = rec["url"]
                kw_hits.setdefault(kw, 0)
                kw_hits[kw] += 1
                if u in all_jobs:
                    if kw not in all_jobs[u]["matchedKeyword"]:
                        all_jobs[u]["matchedKeyword"].append(kw)
                else:
                    all_jobs[u] = rec

    new_jobs = [j for u, j in all_jobs.items() if u not in known]
    jobs_path = BASE / "jobs.jsonl"
    with jobs_path.open("a") as f:
        for j in new_jobs:
            out = {k: v for k, v in j.items() if not k.startswith("_")}
            f.write(json.dumps(out) + "\n")

    all_tracked = []
    if jobs_path.exists():
        for line in jobs_path.read_text().splitlines():
            if line.strip():
                all_tracked.append(json.loads(line))
    for j in new_jobs:
        all_tracked.append({k: v for k, v in j.items() if not k.startswith("_")})

    known.update(j["url"] for j in new_jobs)

    def enrich(j):
        fixed, hourly = parse_budget(j.get("budget"), j.get("type"))
        j["_fixed"], j["_hourly"] = fixed, hourly
        try:
            dt = datetime.fromisoformat(j["postedAt"].replace("Z", "+00:00"))
            j["_recent24"] = (now - dt).total_seconds() <= 86400
        except Exception:
            j["_recent24"] = False
        j["paymentVerified"] = j.get("paymentVerified") or False
        return j

    enriched = [enrich(dict(j)) for j in all_tracked]

    keyword_stats = {}
    for group, keywords in KEYWORD_GROUPS.items():
        for kw in keywords:
            matched = [j for j in enriched if kw in j.get("matchedKeyword", [])]
            fixed_vals = [j["_fixed"] for j in matched if j.get("_fixed")]
            hourly_vals = [j["_hourly"] for j in matched if j.get("_hourly")]
            props = [j["proposals"] for j in matched if j.get("proposals") is not None]
            verified = sum(1 for j in matched if j.get("paymentVerified"))
            spends = [parse_spend(j.get("clientSpend")) for j in matched]
            spends = [s for s in spends if s is not None]
            high = sum(
                1
                for j in matched
                if (j.get("_fixed") or 0) >= 1000 or (j.get("_hourly") or 0) >= 40
            )
            n = len(matched)
            keyword_stats[kw] = {
                "group": group,
                "totalJobs": n,
                "jobsLast24h": sum(1 for j in matched if j.get("_recent24")),
                "avgBudgetFixed": round(statistics.mean(fixed_vals), 2) if fixed_vals else None,
                "avgRateHourly": round(statistics.mean(hourly_vals), 2) if hourly_vals else None,
                "medianProposals": int(statistics.median(props)) if props else None,
                "pctVerified": round(100 * verified / n, 1) if n else 0,
                "avgClientSpend": round(statistics.mean(spends), 2) if spends else None,
                "pctHighBudget": round(100 * high / n, 1) if n else 0,
                "opportunityScore": opportunity_score(matched),
                "sampleConfidence": confidence_label(n),
            }

    (BASE / "keyword-stats.json").write_text(json.dumps(keyword_stats, indent=2))

    group_stats = {}
    for group in KEYWORD_GROUPS:
        kws = KEYWORD_GROUPS[group]
        jobs_g = [j for j in enriched if j.get("keywordGroup") == group or any(k in j.get("matchedKeyword", []) for k in kws)]
        group_stats[group] = {
            "totalJobs": len(jobs_g),
            "jobsLast24h": sum(1 for j in jobs_g if j.get("_recent24")),
            "opportunityScore": opportunity_score(jobs_g),
            "sampleConfidence": confidence_label(len(jobs_g)),
        }
    (BASE / "group-stats.json").write_text(json.dumps(group_stats, indent=2))

    platform_stats = {}
    for pname, patterns in PLATFORM_MAP.items():
        jobs_p = [
            j
            for j in enriched
            if any(p.lower() in " ".join(j.get("matchedKeyword", [])).lower() for p in patterns)
            or any(
                p.lower() in (j.get("title") or "").lower()
                or any(p.lower() in (s or "").lower() for s in (j.get("skills") or []))
                for p in patterns
            )
        ]
        fixed_vals = [j["_fixed"] for j in jobs_p if j.get("_fixed")]
        hourly_vals = [j["_hourly"] for j in jobs_p if j.get("_hourly")]
        props = [j["proposals"] for j in jobs_p if j.get("proposals") is not None]
        platform_stats[pname] = {
            "jobs": len(jobs_p),
            "avgBudgetFixed": round(statistics.mean(fixed_vals), 2) if fixed_vals else None,
            "avgRateHourly": round(statistics.mean(hourly_vals), 2) if hourly_vals else None,
            "medianProposals": int(statistics.median(props)) if props else None,
            "opportunityScore": opportunity_score(jobs_p),
            "sampleConfidence": confidence_label(len(jobs_p)),
        }
    (BASE / "platform-stats.json").write_text(json.dumps(platform_stats, indent=2))

    top3 = sorted(keyword_stats.items(), key=lambda x: x[1]["jobsLast24h"], reverse=True)[:3]
    log = {
        "timestamp": now.isoformat(),
        "runNumber": run_number,
        "keywordsAttempted": sum(len(v) for v in KEYWORD_GROUPS.values()),
        "keywordsCompleted": sum(len(v) for v in KEYWORD_GROUPS.values()) - len(errors),
        "newJobs": len(new_jobs),
        "totalJobs": len(enriched),
        "top3Keywords": [t[0] for t in top3],
        "errors": errors,
    }
    with (BASE / "run-log.jsonl").open("a") as f:
        f.write(json.dumps(log) + "\n")

    state.update(
        {
            "lastRunAt": now.isoformat(),
            "runNumber": run_number,
            "totalJobs": len(enriched),
            "knownJobUrls": sorted(known),
            "lastInsightRefresh": state.get("lastInsightRefresh"),
        }
    )
    (BASE / "state.json").write_text(json.dumps(state, indent=2))

    sorted_kw = sorted(keyword_stats.items(), key=lambda x: x[1]["opportunityScore"], reverse=True)
    summary_lines = [
        "# Upwork Market Intelligence",
        "",
        f"Last updated: {now.strftime('%Y-%m-%d %H:%M UTC')}",
        f"Run: {run_number}",
        f"Total jobs tracked: {len(enriched)}",
        f"Keywords attempted: {log['keywordsAttempted']}",
        f"Keywords completed: {log['keywordsCompleted']}",
        "",
        "## Top Opportunities",
        "",
    ]
    for i, (kw, st) in enumerate(sorted_kw[:10], 1):
        summary_lines.append(
            f"{i}. **{kw}** — score {st['opportunityScore']}, confidence {st['sampleConfidence']}, "
            f"24h {st['jobsLast24h']}, total {st['totalJobs']}, fixed avg {st['avgBudgetFixed']}, "
            f"hourly avg {st['avgRateHourly']}, median proposals {st['medianProposals']}"
        )
    summary_lines.extend(["", "## Strongest Groups", ""])
    for g, st in sorted(group_stats.items(), key=lambda x: x[1]["opportunityScore"], reverse=True):
        summary_lines.append(f"- {g}: score {st['opportunityScore']}, 24h {st['jobsLast24h']}, total {st['totalJobs']}")
    (BASE / "current-summary.md").write_text("\n".join(summary_lines) + "\n")

    print(json.dumps({"run": run_number, "new": len(new_jobs), "total": len(enriched), "errors": len(errors)}))


if __name__ == "__main__":
    main()
