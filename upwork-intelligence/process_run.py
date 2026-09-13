#!/usr/bin/env python3
"""Process raw search batches into intelligence files. Run after MCP searches."""
import json, statistics, re, urllib.parse
from datetime import datetime, timezone, timedelta
from pathlib import Path

BASE = Path(__file__).parent
RAW = BASE / "_search_batches.json"
STATE_FILE = BASE / "state.json"
JOBS_FILE = BASE / "jobs.jsonl"
RUN_LOG = BASE / "run-log.jsonl"

SKIP_RE = re.compile(
    r"\b(alcohol|gambling|casino|betting|porn|adult content|escort|crypto trading|bitcoin trading|forex trading|dating app|dating site)\b",
    re.I,
)

PLATFORM_KEYWORDS = {
    "WordPress": ["wordpress", "elementor", "woocommerce", "bricks"],
    "Webflow": ["webflow"],
    "Framer": ["framer"],
    "GoHighLevel": ["gohighlevel", "go high level", "ghl"],
    "Shopify": ["shopify", "shopify developer", "shopify website"],
    "WooCommerce": ["woocommerce"],
    "Shopware": ["shopware"],
    "Lovable": ["lovable", "lovable developer", "lovable app"],
    "Bolt": ["bolt.new", "bolt developer"],
    "v0": ["v0 developer", "v0 vercel"],
    "Next.js": ["nextjs", "next.js"],
}


def norm_url(url):
    if not url:
        return None
    u = url.split("?")[0]
    return u


def parse_money(s):
    if not s:
        return None
    s = str(s).replace(",", "").replace("$", "")
    if "–" in s or "-" in s:
        parts = re.split(r"[–-]", s)
        nums = []
        for p in parts:
            p = p.strip().replace("/hr", "").strip()
            try:
                nums.append(float(p))
            except ValueError:
                pass
        return sum(nums) / len(nums) if nums else None
    s = s.replace("/hr", "").strip()
    try:
        return float(s)
    except ValueError:
        return None


def job_record(raw, keyword, group):
    client = raw.get("client") or {}
    url = norm_url(raw.get("url"))
    budget = raw.get("budget")
    jt = raw.get("job_type")
    fixed = parse_money(budget) if jt == "fixed" and budget else None
    hourly = parse_money(budget) if jt == "hourly" and budget else None
    spend = client.get("total_spent")
    if spend and isinstance(spend, str):
        spend = spend.replace("$", "").replace(",", "")
        try:
            spend = float(spend)
        except ValueError:
            spend = None
    verified = client.get("verification_status") == "VERIFIED"
    posted = raw.get("published_date") or raw.get("created_date")
    return {
        "url": url,
        "title": raw.get("title"),
        "matchedKeyword": [keyword],
        "keywordGroup": group,
        "postedAt": posted,
        "type": jt,
        "budget": budget if jt == "fixed" else None,
        "hourlyRate": budget if jt == "hourly" else None,
        "budgetFixedNum": fixed,
        "hourlyRateNum": hourly,
        "duration": raw.get("duration"),
        "proposals": raw.get("proposal_count"),
        "clientCountry": client.get("country"),
        "paymentVerified": verified if client else None,
        "clientSpend": spend,
        "clientHireRate": None,
        "clientRating": client.get("rating"),
        "experienceLevel": raw.get("experience_level"),
        "skills": raw.get("skills") or [],
        "_highBudget": (fixed is not None and fixed >= 1000)
        or (hourly is not None and hourly >= 40),
    }


def should_skip(job):
    if not job.get("url"):
        return True
    text = (job.get("title") or "") + " " + " ".join(job.get("skills") or [])
    if SKIP_RE.search(text):
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
    now = datetime.now(timezone.utc)
    scores = []
    for j in jobs:
        rec = 50
        if j.get("budgetFixedNum"):
            rec += min(25, j["budgetFixedNum"] / 80)
        if j.get("hourlyRateNum"):
            rec += min(25, j["hourlyRateNum"])
        p = j.get("proposals")
        if p is not None:
            rec += max(0, 20 - p)
        if j.get("_highBudget"):
            rec += 10
        if j.get("paymentVerified"):
            rec += 5
        posted = j.get("postedAt")
        if posted:
            try:
                dt = datetime.fromisoformat(posted.replace("Z", "+00:00"))
                hours = (now - dt).total_seconds() / 3600
                if hours < 2:
                    rec += 15
                elif hours < 24:
                    rec += 8
            except ValueError:
                pass
        scores.append(min(100, max(1, rec)))
    return round(sum(scores) / len(scores))


def main():
    if not RAW.exists():
        print("No raw batches file")
        return
    data = json.loads(RAW.read_text())
    run_meta = data["meta"]
    window_hours = run_meta.get("windowHours", 2)
    cutoff = datetime.now(timezone.utc) - timedelta(hours=window_hours)
    run_number = run_meta.get("runNumber", 1)

    known = set()
    if STATE_FILE.exists():
        st = json.loads(STATE_FILE.read_text())
        known = set(st.get("knownJobUrls") or [])

    by_url = {}
    if not data.get("batches") and JOBS_FILE.exists():
        for line in JOBS_FILE.read_text().splitlines():
            if not line.strip():
                continue
            j = json.loads(line)
            u = j.get("url")
            if u:
                by_url[u] = {**j, "_highBudget": False}
    for batch in data.get("batches", []):
        kw = batch["keyword"]
        grp = batch["group"]
        err = batch.get("error")
        if err:
            continue
        for raw in batch.get("jobs", []):
            posted = raw.get("published_date") or raw.get("created_date")
            if posted:
                try:
                    dt = datetime.fromisoformat(posted.replace("Z", "+00:00"))
                    if dt < cutoff:
                        continue
                except ValueError:
                    pass
            rec = job_record(raw, kw, grp)
            if should_skip(rec):
                continue
            u = rec["url"]
            if not u:
                continue
            if u in by_url:
                if kw not in by_url[u]["matchedKeyword"]:
                    by_url[u]["matchedKeyword"].append(kw)
            else:
                by_url[u] = rec

    new_jobs = [j for u, j in by_url.items() if u not in known]

    with JOBS_FILE.open("a") as f:
        for j in new_jobs:
            out = {k: v for k, v in j.items() if not k.startswith("_")}
            f.write(json.dumps(out, ensure_ascii=False) + "\n")

    all_jobs = list(by_url.values())
    for j in all_jobs:
        j.pop("_highBudget", None)

    # Load historical jobs for stats (this run only if first)
    hist = []
    if JOBS_FILE.exists():
        for line in JOBS_FILE.read_text().splitlines():
            if line.strip():
                hist.append(json.loads(line))
    # dedupe hist by url for stats
    stats_jobs = {}
    for j in hist:
        u = j.get("url")
        if u:
            if u in stats_jobs:
                for mk in j.get("matchedKeyword") or []:
                    if mk not in stats_jobs[u]["matchedKeyword"]:
                        stats_jobs[u]["matchedKeyword"].append(mk)
            else:
                stats_jobs[u] = j
    all_for_stats = list(stats_jobs.values())

    now = datetime.now(timezone.utc)
    cut24 = now - timedelta(hours=24)

    kw_stats = {}
    for j in all_for_stats:
        for kw in j.get("matchedKeyword") or []:
            kw_stats.setdefault(kw, []).append(j)

    keyword_stats = {}
    for kw, jobs in kw_stats.items():
        fixed = [parse_money(j.get("budget")) or j.get("budgetFixedNum") for j in jobs if j.get("type") == "fixed"]
        fixed = [x for x in fixed if x]
        hourly = []
        for j in jobs:
            if j.get("type") == "hourly":
                h = j.get("hourlyRateNum") or parse_money(j.get("hourlyRate"))
                if h:
                    hourly.append(h)
        props = [j["proposals"] for j in jobs if j.get("proposals") is not None]
        verified = sum(1 for j in jobs if j.get("paymentVerified"))
        spends = [j["clientSpend"] for j in jobs if j.get("clientSpend")]
        high = sum(
            1
            for j in jobs
            if (j.get("type") == "fixed" and (parse_money(j.get("budget")) or 0) >= 1000)
            or (j.get("type") == "hourly" and (parse_money(j.get("hourlyRate")) or 0) >= 40)
        )
        j24 = 0
        for j in jobs:
            pa = j.get("postedAt")
            if pa:
                try:
                    if datetime.fromisoformat(pa.replace("Z", "+00:00")) >= cut24:
                        j24 += 1
                except ValueError:
                    pass
        n = len(jobs)
        keyword_stats[kw] = {
            "totalJobs": n,
            "jobsLast24h": j24,
            "avgBudgetFixed": round(statistics.mean(fixed), 2) if fixed else None,
            "avgRateHourly": round(statistics.mean(hourly), 2) if hourly else None,
            "medianProposals": int(statistics.median(props)) if props else None,
            "pctVerified": round(100 * verified / n, 1) if n else 0,
            "avgClientSpend": round(statistics.mean(spends), 2) if spends else None,
            "pctHighBudget": round(100 * high / n, 1) if n else 0,
            "opportunityScore": opportunity_score(jobs),
            "sampleConfidence": confidence(n),
        }

    # group stats
    grp_map = {}
    for batch in data.get("keyword_manifest", []):
        grp_map[batch[0]] = batch[1]
    group_stats = {}
    for kw, st in keyword_stats.items():
        g = grp_map.get(kw, "OTHER")
        group_stats.setdefault(g, []).append(st)
    group_out = {}
    for g, sts in group_stats.items():
        group_out[g] = {
            "totalJobs": sum(s["totalJobs"] for s in sts),
            "jobsLast24h": sum(s["jobsLast24h"] for s in sts),
            "avgOpportunityScore": round(
                sum(s["opportunityScore"] for s in sts) / len(sts), 1
            )
            if sts
            else 0,
            "keywordCount": len(sts),
        }

    platform_stats = {}
    for plat, kws in PLATFORM_KEYWORDS.items():
        jobs_p = []
        for kw in kws:
            jobs_p.extend(kw_stats.get(kw, []))
        # dedupe
        seen = set()
        ujobs = []
        for j in jobs_p:
            if j["url"] not in seen:
                seen.add(j["url"])
                ujobs.append(j)
        if not ujobs:
            platform_stats[plat] = {
                "jobs": 0,
                "avgBudgetOrRate": None,
                "medianProposals": None,
                "score": 0,
                "confidence": confidence(0),
            }
            continue
        vals = []
        for j in ujobs:
            if j.get("type") == "fixed":
                v = parse_money(j.get("budget"))
                if v:
                    vals.append(v)
            else:
                v = parse_money(j.get("hourlyRate"))
                if v:
                    vals.append(v)
        props = [j["proposals"] for j in ujobs if j.get("proposals") is not None]
        platform_stats[plat] = {
            "jobs": len(ujobs),
            "avgBudgetOrRate": round(statistics.mean(vals), 2) if vals else None,
            "medianProposals": int(statistics.median(props)) if props else None,
            "score": opportunity_score(ujobs),
            "confidence": confidence(len(ujobs)),
        }

    total = len(known) + len(new_jobs)
    known.update(by_url.keys())

    STATE_FILE.write_text(
        json.dumps(
            {
                "lastRunAt": run_meta.get("timestamp"),
                "runNumber": run_number,
                "totalJobs": len(known),
                "knownJobUrls": sorted(known),
                "lastInsightRefresh": run_meta.get("timestamp"),
            },
            indent=2,
        )
    )

    top3 = sorted(keyword_stats.items(), key=lambda x: -x[1]["jobsLast24h"])[:3]
    log = {
        "timestamp": run_meta.get("timestamp"),
        "runNumber": run_number,
        "keywordsAttempted": run_meta.get("keywordsAttempted"),
        "keywordsCompleted": run_meta.get("keywordsCompleted"),
        "newJobs": len(new_jobs),
        "totalJobs": len(known),
        "top3Keywords": [t[0] for t in top3],
        "errors": run_meta.get("errors", []),
    }
    with RUN_LOG.open("a") as f:
        f.write(json.dumps(log) + "\n")

    (BASE / "keyword-stats.json").write_text(json.dumps(keyword_stats, indent=2))
    (BASE / "group-stats.json").write_text(json.dumps(group_out, indent=2))
    (BASE / "platform-stats.json").write_text(json.dumps(platform_stats, indent=2))

    # summary md
    top10 = sorted(keyword_stats.items(), key=lambda x: (-x[1]["opportunityScore"], -x[1]["jobsLast24h"]))[:10]
    groups_rank = sorted(group_out.items(), key=lambda x: -x[1]["avgOpportunityScore"])

    md = f"""# Upwork Market Intelligence

Last updated: {run_meta.get('timestamp')}
Run: {run_number}
Total jobs tracked: {len(known)}
Keywords attempted: {run_meta.get('keywordsAttempted')}
Keywords completed: {run_meta.get('keywordsCompleted')}

## Top Opportunities

"""
    for kw, st in top10:
        md += f"- **{kw}** — score {st['opportunityScore']}, jobs24h {st['jobsLast24h']}, total {st['totalJobs']}, conf {st['sampleConfidence']}\n"

    md += "\n## Strongest Groups\n\n"
    for g, st in groups_rank[:8]:
        md += f"- {g}: score {st['avgOpportunityScore']}, jobs24h {st['jobsLast24h']}\n"

    md += "\n## Platform Ranking\n\n"
    plats = sorted(platform_stats.items(), key=lambda x: -x[1]["score"])
    for p, st in plats:
        md += f"- {p}: jobs {st['jobs']}, score {st['score']}\n"

    (BASE / "current-summary.md").write_text(md)

    out = {
        "new_jobs": [{k: v for k, v in j.items() if not k.startswith("_")} for j in new_jobs],
        "keyword_stats": keyword_stats,
        "group_stats": group_out,
        "platform_stats": platform_stats,
        "run_log": log,
        "top10": top10,
    }
    (BASE / "_processed.json").write_text(json.dumps(out, indent=2, default=str))
    print(f"new={len(new_jobs)} total={len(known)}")


if __name__ == "__main__":
    main()
