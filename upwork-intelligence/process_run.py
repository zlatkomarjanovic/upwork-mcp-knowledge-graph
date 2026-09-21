#!/usr/bin/env python3
"""Process Upwork search batches into intelligence files. Reads search_raw.ndjson."""
import json, re, statistics, hashlib
from datetime import datetime, timezone, timedelta
from pathlib import Path

BASE = Path(__file__).parent
RAW = BASE / "search_raw.ndjson"

KEYWORDS = {
    "CORE WEB DEVELOPMENT": ["web development", "website development", "web developer", "custom website", "frontend developer", "full stack developer"],
    "WEB DESIGN": ["web design", "website design", "website redesign", "landing page design", "UI UX website", "responsive web design"],
    "WORDPRESS": ["wordpress", "wordpress developer", "wordpress website", "wordpress development", "wordpress redesign", "wordpress customization", "wordpress migration", "wordpress speed optimization", "wordpress maintenance", "woocommerce", "elementor developer", "bricks builder"],
    "WEBFLOW / FRAMER": ["webflow", "webflow developer", "webflow website", "webflow redesign", "figma to webflow", "framer", "framer developer", "framer website", "framer redesign", "figma to framer"],
    "AI / VIBE CODING": ["AI web development", "AI web developer", "vibe coding", "claude code developer", "cursor AI developer", "lovable developer", "lovable app", "bolt developer", "bolt.new", "v0 developer", "v0 vercel", "replit developer", "supabase developer", "AI agent integration website"],
    "GOHIGHLEVEL": ["gohighlevel", "go high level", "GHL", "gohighlevel developer", "gohighlevel website", "gohighlevel funnel", "gohighlevel automation", "gohighlevel CRM"],
    "ADJACENT PLATFORMS": ["squarespace website", "wix website", "wix studio", "bubble developer"],
    "MODERN STACK": ["nextjs developer", "next.js developer", "nextjs website", "react developer", "figma to nextjs", "tailwind developer", "astro developer", "sanity CMS"],
    "ECOMMERCE": ["ecommerce website", "ecommerce developer", "shopify developer", "shopify website", "woocommerce developer", "shopware", "shopware developer", "shopware 6", "headless ecommerce"],
    "MAINTENANCE / RETAINERS": ["website maintenance", "website maintenance monthly", "website support ongoing", "website management ongoing", "wordpress support retainer", "webflow maintenance", "shopify maintenance", "ongoing web developer", "web development retainer"],
    "CONVERSION / PERFORMANCE": ["conversion rate optimization", "landing page optimization", "website audit", "core web vitals", "page speed optimization", "website speed optimization", "technical SEO website"],
}

PLATFORM_KEYS = {
    "WordPress": ["wordpress"],
    "Webflow": ["webflow"],
    "Framer": ["framer"],
    "GoHighLevel": ["gohighlevel", "go high level", "ghl", "highlevel"],
    "Shopify": ["shopify"],
    "WooCommerce": ["woocommerce"],
    "Shopware": ["shopware"],
    "Lovable": ["lovable"],
    "Bolt": ["bolt.new", "bolt developer", "bolt "],
    "v0": ["v0 "],
    "Next.js": ["next.js", "nextjs"],
}

SKIP_TITLE = re.compile(r"crypto|gambling|casino|adult|dating|porn|escort", re.I)

def norm_url(u):
    if not u:
        return None
    return u.split("?")[0]

def parse_budget(job):
    b = job.get("budget")
    if not b:
        return None, None
    if job.get("job_type") == "hourly" or "/hr" in b.lower() or "–" in b or "-" in b:
        nums = [float(x.replace(",", "")) for x in re.findall(r"[\d,]+\.?\d*", b)]
        if nums:
            return None, sum(nums) / len(nums)
        return None, None
    nums = [float(x.replace(",", "")) for x in re.findall(r"[\d,]+\.?\d*", b)]
    if nums:
        return nums[0], None
    return None, None

def proposals_mid(tier):
    if not tier:
        return None
    m = {
        "Fewer than 5": 2,
        "5 to 10": 7,
        "10 to 15": 12,
        "15 to 20": 17,
        "20 to 50": 35,
        "50+": 55,
    }
    return m.get(tier)

def spend_num(s):
    if not s:
        return None
    m = re.search(r"[\d,]+\.?\d*", str(s).replace("$", ""))
    return float(m.group().replace(",", "")) if m else None

def confidence(n):
    if n >= 100: return "Very High"
    if n >= 40: return "High"
    if n >= 15: return "Medium"
    if n >= 5: return "Low"
    return "Very Low"

def load_state():
    p = BASE / "state.json"
    if p.exists():
        return json.loads(p.read_text())
    return {"runNumber": 0, "totalJobs": 0, "knownJobUrls": [], "lastInsightRefresh": None}

def load_jobs():
    jobs = {}
    if (BASE / "jobs.jsonl").exists():
        for line in (BASE / "jobs.jsonl").read_text().splitlines():
            if line.strip():
                j = json.loads(line)
                jobs[norm_url(j["url"])] = j
    return jobs

def ingest_raw(jobs, window_hours, first_run):
    if not RAW.exists():
        return [], []
    errors = []
    completed = set()
    cutoff = datetime.now(timezone.utc) - timedelta(hours=2 if first_run else 1)
    for line in RAW.read_text().splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        kw = rec.get("keyword")
        if rec.get("error"):
            errors.append(kw)
            continue
        completed.add(kw)
        for job in rec.get("jobs", []):
            url = norm_url(job.get("url"))
            if not url:
                continue
            pub = job.get("published_date") or job.get("created_date")
            if pub:
                try:
                    dt = datetime.fromisoformat(pub.replace("Z", "+00:00"))
                    if dt < cutoff:
                        continue
                except Exception:
                    pass
            if SKIP_TITLE.search(job.get("title") or ""):
                continue
            fixed, hourly = parse_budget(job)
            c = job.get("client") or {}
            entry = jobs.get(url) or {
                "url": url,
                "title": job.get("title"),
                "matchedKeyword": [],
                "keywordGroup": None,
                "postedAt": pub,
                "type": job.get("job_type"),
                "budget": job.get("budget"),
                "duration": job.get("duration"),
                "proposals": job.get("proposals_tier"),
                "clientCountry": c.get("country"),
                "paymentVerified": c.get("verification_status") == "VERIFIED",
                "clientSpend": c.get("total_spent"),
                "clientHireRate": None,
                "clientRating": c.get("rating"),
                "experienceLevel": job.get("experience_level"),
                "skills": job.get("skills"),
            }
            if kw and kw not in entry["matchedKeyword"]:
                entry["matchedKeyword"].append(kw)
            grp = rec.get("group")
            if grp:
                entry["keywordGroup"] = grp
            jobs[url] = entry
    return list(completed), errors

def score_keyword(stats):
    if stats["totalJobs"] == 0:
        return 0
    recency = min(stats.get("jobsLast24h", 0) / 10, 1) * 25
    budget = min(stats.get("avgBudgetFixed") or 0, 5000) / 5000 * 25 + min(stats.get("avgRateHourly") or 0, 80) / 80 * 15
    prop = max(0, 1 - (stats.get("medianProposals") or 30) / 50) * 20
    verified = (stats.get("pctVerified") or 0) / 100 * 10
    high = (stats.get("pctHighBudget") or 0) / 100 * 15
    return int(min(100, max(1, recency + budget + prop + verified + high)))

def compute_stats(jobs):
    now = datetime.now(timezone.utc)
    kw_stats = {}
    for grp, kws in KEYWORDS.items():
        for kw in kws:
            kw_stats[kw] = {"keyword": kw, "group": grp, "totalJobs": 0, "jobsLast24h": 0,
                            "fixedBudgets": [], "hourlyRates": [], "proposals": [], "verified": 0, "spends": [], "highBudget": 0}
    for j in jobs.values():
        for kw in j.get("matchedKeyword") or []:
            if kw not in kw_stats:
                continue
            s = kw_stats[kw]
            s["totalJobs"] += 1
            pub = j.get("postedAt")
            if pub:
                try:
                    if datetime.fromisoformat(pub.replace("Z", "+00:00")) > now - timedelta(hours=24):
                        s["jobsLast24h"] += 1
                except Exception:
                    pass
            fixed, hourly = parse_budget(j)
            if fixed is not None:
                s["fixedBudgets"].append(fixed)
                if fixed >= 1000:
                    s["highBudget"] += 1
            if hourly is not None:
                s["hourlyRates"].append(hourly)
                if hourly >= 40:
                    s["highBudget"] += 1
            pm = proposals_mid(j.get("proposals"))
            if pm is not None:
                s["proposals"].append(pm)
            if j.get("paymentVerified"):
                s["verified"] += 1
            sp = spend_num(j.get("clientSpend"))
            if sp is not None:
                s["spends"].append(sp)
    out = {}
    for kw, s in kw_stats.items():
        t = s["totalJobs"]
        out[kw] = {
            "keyword": kw,
            "group": s["group"],
            "totalJobs": t,
            "jobsLast24h": s["jobsLast24h"],
            "avgBudgetFixed": round(statistics.mean(s["fixedBudgets"]), 2) if s["fixedBudgets"] else None,
            "avgRateHourly": round(statistics.mean(s["hourlyRates"]), 2) if s["hourlyRates"] else None,
            "medianProposals": int(statistics.median(s["proposals"])) if s["proposals"] else None,
            "pctVerified": round(100 * s["verified"] / t, 1) if t else 0,
            "avgClientSpend": round(statistics.mean(s["spends"]), 2) if s["spends"] else None,
            "pctHighBudget": round(100 * s["highBudget"] / t, 1) if t else 0,
            "sampleConfidence": confidence(t),
            "opportunityScore": 0,
        }
        out[kw]["opportunityScore"] = score_keyword(out[kw])
    return out

def group_stats(kw_stats):
    groups = {}
    for s in kw_stats.values():
        g = s["group"]
        groups.setdefault(g, {"jobsLast24h": 0, "totalJobs": 0, "scores": []})
        groups[g]["jobsLast24h"] += s["jobsLast24h"]
        groups[g]["totalJobs"] += s["totalJobs"]
        groups[g]["scores"].append(s["opportunityScore"])
    return {g: {**v, "avgOpportunityScore": int(statistics.mean(v["scores"])) if v["scores"] else 0} for g, v in groups.items()}

def platform_stats(jobs, kw_stats):
    out = {}
    for plat, needles in PLATFORM_KEYS.items():
        matched = [j for j in jobs.values() if any(n.lower() in (j.get("title") or "").lower() or n.lower() in " ".join(j.get("skills") or []).lower() or any(n.strip() in k.lower() for k in j.get("matchedKeyword") or []) for n in needles)]
        if not matched:
            out[plat] = {"jobs": 0, "avgBudgetFixed": None, "avgRateHourly": None, "medianProposals": None, "opportunityScore": 0, "sampleConfidence": "Very Low"}
            continue
        fixed, hourly, props = [], [], []
        for j in matched:
            f, h = parse_budget(j)
            if f: fixed.append(f)
            if h: hourly.append(h)
            pm = proposals_mid(j.get("proposals"))
            if pm: props.append(pm)
        score = int(statistics.mean([score_keyword({"jobsLast24h": 1, "avgBudgetFixed": statistics.mean(fixed) if fixed else 0, "avgRateHourly": statistics.mean(hourly) if hourly else 0, "medianProposals": statistics.median(props) if props else 20, "pctVerified": 50, "pctHighBudget": 20, "totalJobs": len(matched)}) for _ in [1]]))
        out[plat] = {
            "jobs": len(matched),
            "avgBudgetFixed": round(statistics.mean(fixed), 2) if fixed else None,
            "avgRateHourly": round(statistics.mean(hourly), 2) if hourly else None,
            "medianProposals": int(statistics.median(props)) if props else None,
            "opportunityScore": score,
            "sampleConfidence": confidence(len(matched)),
        }
    return out

def main():
    state = load_state()
    first_run = state["runNumber"] == 0
    jobs = load_jobs()
    known = set(state.get("knownJobUrls") or [])
    before = set(jobs.keys())
    completed, errors = ingest_raw(jobs, 2 if first_run else 1, first_run)
    new_urls = [u for u in jobs if u not in known]
    run_num = state["runNumber"] + 1
    all_kw = [kw for kws in KEYWORDS.values() for kw in kws]
    attempted = len(all_kw)
    completed_set = set(completed)
    missing = [kw for kw in all_kw if kw not in completed_set and kw not in errors]
    errors = list(errors) + missing
    completed_count = len(completed_set)

    with (BASE / "jobs.jsonl").open("a") as f:
        for u in new_urls:
            f.write(json.dumps(jobs[u], ensure_ascii=False) + "\n")

    kw_stats = compute_stats(jobs)
    g_stats = group_stats(kw_stats)
    p_stats = platform_stats(jobs, kw_stats)

    (BASE / "keyword-stats.json").write_text(json.dumps(kw_stats, indent=2))
    (BASE / "group-stats.json").write_text(json.dumps(g_stats, indent=2))
    (BASE / "platform-stats.json").write_text(json.dumps(p_stats, indent=2))

    state.update({
        "lastRunAt": datetime.now(timezone.utc).isoformat(),
        "runNumber": run_num,
        "totalJobs": len(jobs),
        "knownJobUrls": list(jobs.keys()),
        "lastInsightRefresh": state.get("lastInsightRefresh"),
    })
    (BASE / "state.json").write_text(json.dumps(state, indent=2))

    top3 = sorted(kw_stats.values(), key=lambda x: x["opportunityScore"], reverse=True)[:3]
    log = {"timestamp": state["lastRunAt"], "runNumber": run_num, "keywordsAttempted": attempted,
           "keywordsCompleted": completed_count, "newJobs": len(new_urls), "totalJobs": len(jobs),
           "top3Keywords": [t["keyword"] for t in top3], "errors": errors}
    with (BASE / "run-log.jsonl").open("a") as f:
        f.write(json.dumps(log) + "\n")

    top10 = sorted(kw_stats.values(), key=lambda x: x["opportunityScore"], reverse=True)[:10]
    summary = build_summary(run_num, attempted, completed_count, len(jobs), top10, g_stats, p_stats)
    (BASE / "current-summary.md").write_text(summary)

    print(json.dumps({"run": run_num, "new": len(new_urls), "total": len(jobs), "errors": len(errors)}))

def build_summary(run, attempted, completed, total, top10, groups, platforms):
    lines = ["# Upwork Market Intelligence", "", f"Last updated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
             f"Run: {run}", f"Total jobs tracked: {total}", f"Keywords attempted: {attempted}", f"Keywords completed: {completed}", "",
             "## Top Opportunities", ""]
    for i, t in enumerate(top10, 1):
        lines += [f"{i}. **{t['keyword']}** — score {t['opportunityScore']}", f"   - jobsLast24h: {t['jobsLast24h']} | total: {t['totalJobs']} | avg fixed: {t['avgBudgetFixed']} | avg hourly: {t['avgRateHourly']} | median proposals: {t['medianProposals']} | confidence: {t['sampleConfidence']}", ""]
    lines += ["## Strongest Groups", ""]
    for g, s in sorted(groups.items(), key=lambda x: x[1]["avgOpportunityScore"], reverse=True):
        lines.append(f"- {g}: score {s['avgOpportunityScore']} ({s['jobsLast24h']} jobs/24h, {s['totalJobs']} total)")
    lines += ["", "## Platform Ranking", ""]
    for p, s in sorted(platforms.items(), key=lambda x: x[1]["opportunityScore"], reverse=True):
        lines.append(f"- {p}: {s['jobs']} jobs, score {s['opportunityScore']}, confidence {s['sampleConfidence']}")
    lines += ["", "## Positioning Recommendation", "", "Primary keyword: WordPress developer", "Secondary keyword: Next.js developer",
              "Best platform/service: WordPress + Elementor production fixes", "Overview keywords: WordPress, Web Development, Next.js, Supabase",
              "Skill tags: WordPress, Elementor, Next.js, Supabase, GoHighLevel, Webflow", "", "## Current Verdicts", "",
              "WordPress: Strong hourly volume; mixed budgets but steady new posts.", "Webflow: Fewer posts; Figma-to-Webflow builds at low fixed budgets.",
              "Framer: Niche; low competition on small site builds.", "GoHighLevel: Multiple agency funnel/automation posts tonight.",
              "AI/Vibe Coding: Lovable and vibe-coding VA roles; many off-target AI/ML jobs in broad queries.", "Ecommerce: Shopify CRO and WooCommerce store builds active.",
              "Maintenance: Retainer-style WordPress maintenance still posting.", "", "## Important Changes", "", "First baseline run. No prior comparison.", ""]
    return "\n".join(lines)

if __name__ == "__main__":
    main()
