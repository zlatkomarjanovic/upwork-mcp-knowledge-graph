#!/usr/bin/env python3
"""Process raw search payloads into jobs.jsonl and stats files."""
import json
import re
import statistics
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parent
WINDOW_HOURS_FIRST = 2
WINDOW_HOURS = 1

SKIP_PATTERNS = re.compile(
    r"\b(crypto|bitcoin|gambling|casino|adult|dating|escort|porn|alcohol|brewery|wine\b.*\bjob)\b",
    re.I,
)

PLATFORM_MAP = {
    "wordpress": "WordPress",
    "webflow": "Webflow",
    "framer": "Framer",
    "gohighlevel": "GoHighLevel",
    "go high level": "GoHighLevel",
    "ghl": "GoHighLevel",
    "shopify": "Shopify",
    "woocommerce": "WooCommerce",
    "shopware": "Shopware",
    "lovable": "Lovable",
    "bolt": "Bolt",
    "v0": "v0",
    "nextjs": "Next.js",
    "next.js": "Next.js",
}


def norm_url(url: str) -> str:
    if not url:
        return ""
    return url.split("?")[0]


def parse_money(s):
    if not s:
        return None
    s = str(s).replace(",", "").replace("$", "")
    if "–" in s or "-" in s:
        parts = re.split(r"[–-]", s)
        nums = []
        for p in parts:
            p = p.strip().replace("/hr", "").replace("hr", "").strip()
            m = re.search(r"([\d.]+)", p)
            if m:
                nums.append(float(m.group(1)))
        if nums:
            return sum(nums) / len(nums)
    m = re.search(r"([\d.]+)", s)
    return float(m.group(1)) if m else None


def parse_client_spend(s):
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
    for j in jobs:
        recency = 1.0
        posted = j.get("postedAt")
        if posted:
            try:
                dt = datetime.fromisoformat(posted.replace("Z", "+00:00"))
                age_h = (datetime.now(timezone.utc) - dt).total_seconds() / 3600
                recency = max(0.2, 1 - age_h / 24)
            except Exception:
                pass
        budget = j.get("_fixed") or 0
        rate = j.get("_hourly") or 0
        pay = max(budget, rate * 10 if rate else 0)
        pay_factor = min(1.0, pay / 2000) if pay else 0.3
        props = j.get("proposals") or 50
        comp = max(0.2, 1 - min(props, 100) / 100)
        verified = 1.1 if j.get("paymentVerified") else 1.0
        high = 1.15 if (j.get("_fixed") or 0) >= 1000 or (j.get("_hourly") or 0) >= 40 else 1.0
        score += recency * pay_factor * comp * verified * high
    return min(100, max(1, int(score / len(jobs) * 35)))


def job_record(raw, keyword, group):
    url = raw.get("url") or ""
    if not url:
        return None
    title = raw.get("title") or ""
    if SKIP_PATTERNS.search(title + " " + (raw.get("description_snippet") or "")):
        return None
    client = raw.get("client") or {}
    budget_raw = raw.get("budget")
    jt = raw.get("job_type")
    fixed = parse_money(budget_raw) if jt == "fixed" else None
    hourly = parse_money(budget_raw) if jt == "hourly" else None
    spend = parse_client_spend(client.get("total_spent"))
    return {
        "url": norm_url(url),
        "title": title,
        "matchedKeyword": [keyword],
        "keywordGroup": group,
        "postedAt": raw.get("published_date") or raw.get("created_date"),
        "type": jt,
        "budget": budget_raw if jt == "fixed" else None,
        "hourlyRate": budget_raw if jt == "hourly" else None,
        "duration": raw.get("duration"),
        "proposals": raw.get("proposal_count"),
        "clientCountry": client.get("country"),
        "paymentVerified": client.get("verification_status") == "VERIFIED",
        "clientSpend": spend,
        "clientHireRate": None,
        "clientRating": client.get("rating"),
        "experienceLevel": raw.get("experience_level"),
        "skills": raw.get("skills") or [],
        "_fixed": fixed,
        "_hourly": hourly,
    }


def in_window(posted_at, hours):
    if not posted_at:
        return False
    try:
        dt = datetime.fromisoformat(posted_at.replace("Z", "+00:00"))
        age = (datetime.now(timezone.utc) - dt).total_seconds() / 3600
        return age <= hours
    except Exception:
        return False


def main():
    import sys

    payload_path = Path(sys.argv[1]) if len(sys.argv) > 1 else BASE / "raw_run.json"
    data = json.loads(payload_path.read_text())
    run_number = data["runNumber"]
    first_run = data.get("firstRun", True)
    window = WINDOW_HOURS_FIRST if first_run else WINDOW_HOURS
    errors = data.get("errors", [])
    searches = data["searches"]

    state_path = BASE / "state.json"
    known = set()
    if state_path.exists():
        st = json.loads(state_path.read_text())
        known = set(st.get("knownJobUrls", []))

    all_jobs = {}
    keyword_hits = {}

    for item in searches:
        kw = item["keyword"]
        group = item["group"]
        resp = item.get("response") or {}
        if resp.get("status") == "error":
            continue
        keyword_hits.setdefault(kw, [])
        for raw in resp.get("jobs") or []:
            rec = job_record(raw, kw, group)
            if not rec:
                continue
            if not in_window(rec["postedAt"], window):
                continue
            u = rec["url"]
            if u in all_jobs:
                if kw not in all_jobs[u]["matchedKeyword"]:
                    all_jobs[u]["matchedKeyword"].append(kw)
            else:
                all_jobs[u] = rec
            keyword_hits[kw].append(all_jobs[u])

    new_jobs = [j for u, j in all_jobs.items() if u not in known]
    for j in new_jobs:
        known.add(j["url"])

    jobs_path = BASE / "jobs.jsonl"
    with jobs_path.open("a") as f:
        for j in new_jobs:
            out = {k: v for k, v in j.items() if not k.startswith("_")}
            f.write(json.dumps(out, ensure_ascii=False) + "\n")

    # reload all jobs for stats (first run small)
    all_stored = []
    if jobs_path.exists():
        for line in jobs_path.read_text().splitlines():
            if line.strip():
                all_stored.append(json.loads(line))

    now = datetime.now(timezone.utc)
    kw_stats = {}
    for item in searches:
        kw = item["keyword"]
        group = item["group"]
        jobs_kw = [j for j in all_stored if kw in j.get("matchedKeyword", [])]
        jobs_24 = []
        for j in jobs_kw:
            pa = j.get("postedAt")
            if pa:
                try:
                    dt = datetime.fromisoformat(pa.replace("Z", "+00:00"))
                    if (now - dt).total_seconds() <= 86400:
                        jobs_24.append(j)
                except Exception:
                    pass
        fixed_vals = []
        hourly_vals = []
        props = []
        verified = 0
        spend_vals = []
        high_budget = 0
        for j in jobs_kw:
            b = j.get("budget")
            h = j.get("hourlyRate")
            fv = parse_money(b) if b else None
            hv = parse_money(h) if h else None
            if fv is not None:
                fixed_vals.append(fv)
            if hv is not None:
                hourly_vals.append(hv)
            if j.get("proposals") is not None:
                props.append(j["proposals"])
            if j.get("paymentVerified"):
                verified += 1
            cs = j.get("clientSpend")
            if cs is not None:
                spend_vals.append(cs)
            if (fv or 0) >= 1000 or (hv or 0) >= 40:
                high_budget += 1
        n = len(jobs_kw)
        kw_stats[kw] = {
            "keyword": kw,
            "group": group,
            "totalJobs": n,
            "jobsLast24h": len(jobs_24),
            "avgBudgetFixed": round(statistics.mean(fixed_vals), 2) if fixed_vals else None,
            "avgRateHourly": round(statistics.mean(hourly_vals), 2) if hourly_vals else None,
            "medianProposals": int(statistics.median(props)) if props else None,
            "pctVerified": round(100 * verified / n, 1) if n else 0,
            "avgClientSpend": round(statistics.mean(spend_vals), 2) if spend_vals else None,
            "pctHighBudget": round(100 * high_budget / n, 1) if n else 0,
            "opportunityScore": opportunity_score(jobs_kw),
            "sampleConfidence": confidence(n),
        }

    (BASE / "keyword-stats.json").write_text(json.dumps(kw_stats, indent=2))

    group_stats = {}
    for kw, st in kw_stats.items():
        g = st["group"]
        group_stats.setdefault(g, []).append(st)
    group_out = {}
    for g, items in group_stats.items():
        n = sum(x["totalJobs"] for x in items)
        group_out[g] = {
            "group": g,
            "keywords": len(items),
            "totalJobs": n,
            "jobsLast24h": sum(x["jobsLast24h"] for x in items),
            "avgOpportunityScore": round(statistics.mean([x["opportunityScore"] for x in items]), 1)
            if items
            else 0,
            "sampleConfidence": confidence(n),
        }
    ranked_groups = sorted(group_out.values(), key=lambda x: x["avgOpportunityScore"], reverse=True)
    (BASE / "group-stats.json").write_text(json.dumps({"groups": group_out, "ranked": ranked_groups}, indent=2))

    plat_stats = {}
    for j in all_stored:
        text = " ".join(
            [
                j.get("title") or "",
                " ".join(j.get("skills") or []),
                " ".join(j.get("matchedKeyword") or []),
            ]
        ).lower()
        for key, name in PLATFORM_MAP.items():
            if key in text or any(key in (m or "").lower() for m in j.get("matchedKeyword", [])):
                plat_stats.setdefault(name, []).append(j)
    plat_out = {}
    for name, jobs in plat_stats.items():
        fixed_vals = [parse_money(x.get("budget")) for x in jobs if x.get("budget")]
        fixed_vals = [x for x in fixed_vals if x is not None]
        hourly_vals = [parse_money(x.get("hourlyRate")) for x in jobs if x.get("hourlyRate")]
        hourly_vals = [x for x in hourly_vals if x is not None]
        props = [x["proposals"] for x in jobs if x.get("proposals") is not None]
        plat_out[name] = {
            "platform": name,
            "jobs": len(jobs),
            "avgBudgetFixed": round(statistics.mean(fixed_vals), 2) if fixed_vals else None,
            "avgRateHourly": round(statistics.mean(hourly_vals), 2) if hourly_vals else None,
            "medianProposals": int(statistics.median(props)) if props else None,
            "opportunityScore": opportunity_score(jobs),
            "sampleConfidence": confidence(len(jobs)),
        }
    (BASE / "platform-stats.json").write_text(json.dumps(plat_out, indent=2))

    log = {
        "timestamp": now.isoformat(),
        "runNumber": run_number,
        "keywordsAttempted": data.get("keywordsAttempted"),
        "keywordsCompleted": data.get("keywordsCompleted"),
        "newJobs": len(new_jobs),
        "totalJobs": len(all_stored),
        "top3Keywords": sorted(kw_stats.values(), key=lambda x: x["opportunityScore"], reverse=True)[:3],
        "errors": errors,
    }
    with (BASE / "run-log.jsonl").open("a") as f:
        f.write(json.dumps(log) + "\n")

    state = {
        "lastRunAt": now.isoformat(),
        "runNumber": run_number,
        "totalJobs": len(all_stored),
        "knownJobUrls": sorted(known),
        "lastInsightRefresh": now.isoformat(),
    }
    state_path.write_text(json.dumps(state, indent=2))

    top10 = sorted(kw_stats.values(), key=lambda x: x["opportunityScore"], reverse=True)[:10]
    summary = data.get("summary_template", {})
    (BASE / "current-summary.md").write_text(summary.get("md", ""))

    print(json.dumps({"newJobs": len(new_jobs), "totalJobs": len(all_stored), "top10": top10}))


if __name__ == "__main__":
    main()
