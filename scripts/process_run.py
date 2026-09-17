#!/usr/bin/env python3
"""Process Upwork keyword search batch and update intelligence store."""
from __future__ import annotations

import json
import re
import statistics
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse, parse_qs, urlunparse

ROOT = Path(__file__).resolve().parents[1] / "upwork-intelligence"
CACHE_DIR = ROOT / "cache"

SKIP_PATTERNS = re.compile(
    r"\b(crypto|bitcoin|casino|gambling|betting|poker|adult|escort|dating|onlyfans|alcohol|brewery|distillery)\b",
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

KEYWORD_GROUPS: list[tuple[str, str]] = [
    ("CORE WEB DEVELOPMENT", "web development"),
    ("CORE WEB DEVELOPMENT", "website development"),
    ("CORE WEB DEVELOPMENT", "web developer"),
    ("CORE WEB DEVELOPMENT", "custom website"),
    ("CORE WEB DEVELOPMENT", "frontend developer"),
    ("CORE WEB DEVELOPMENT", "full stack developer"),
    ("WEB DESIGN", "web design"),
    ("WEB DESIGN", "website design"),
    ("WEB DESIGN", "website redesign"),
    ("WEB DESIGN", "landing page design"),
    ("WEB DESIGN", "UI UX website"),
    ("WEB DESIGN", "responsive web design"),
    ("WORDPRESS", "wordpress"),
    ("WORDPRESS", "wordpress developer"),
    ("WORDPRESS", "wordpress website"),
    ("WORDPRESS", "wordpress development"),
    ("WORDPRESS", "wordpress redesign"),
    ("WORDPRESS", "wordpress customization"),
    ("WORDPRESS", "wordpress migration"),
    ("WORDPRESS", "wordpress speed optimization"),
    ("WORDPRESS", "wordpress maintenance"),
    ("WORDPRESS", "woocommerce"),
    ("WORDPRESS", "elementor developer"),
    ("WORDPRESS", "bricks builder"),
    ("WEBFLOW / FRAMER", "webflow"),
    ("WEBFLOW / FRAMER", "webflow developer"),
    ("WEBFLOW / FRAMER", "webflow website"),
    ("WEBFLOW / FRAMER", "webflow redesign"),
    ("WEBFLOW / FRAMER", "figma to webflow"),
    ("WEBFLOW / FRAMER", "framer"),
    ("WEBFLOW / FRAMER", "framer developer"),
    ("WEBFLOW / FRAMER", "framer website"),
    ("WEBFLOW / FRAMER", "framer redesign"),
    ("WEBFLOW / FRAMER", "figma to framer"),
    ("AI / VIBE CODING", "AI web development"),
    ("AI / VIBE CODING", "AI web developer"),
    ("AI / VIBE CODING", "vibe coding"),
    ("AI / VIBE CODING", "claude code developer"),
    ("AI / VIBE CODING", "cursor AI developer"),
    ("AI / VIBE CODING", "lovable developer"),
    ("AI / VIBE CODING", "lovable app"),
    ("AI / VIBE CODING", "bolt developer"),
    ("AI / VIBE CODING", "bolt.new"),
    ("AI / VIBE CODING", "v0 developer"),
    ("AI / VIBE CODING", "v0 vercel"),
    ("AI / VIBE CODING", "replit developer"),
    ("AI / VIBE CODING", "supabase developer"),
    ("AI / VIBE CODING", "AI agent integration website"),
    ("GOHIGHLEVEL", "gohighlevel"),
    ("GOHIGHLEVEL", "go high level"),
    ("GOHIGHLEVEL", "GHL"),
    ("GOHIGHLEVEL", "gohighlevel developer"),
    ("GOHIGHLEVEL", "gohighlevel website"),
    ("GOHIGHLEVEL", "gohighlevel funnel"),
    ("GOHIGHLEVEL", "gohighlevel automation"),
    ("GOHIGHLEVEL", "gohighlevel CRM"),
    ("ADJACENT PLATFORMS", "squarespace website"),
    ("ADJACENT PLATFORMS", "wix website"),
    ("ADJACENT PLATFORMS", "wix studio"),
    ("ADJACENT PLATFORMS", "bubble developer"),
    ("MODERN STACK", "nextjs developer"),
    ("MODERN STACK", "next.js developer"),
    ("MODERN STACK", "nextjs website"),
    ("MODERN STACK", "react developer"),
    ("MODERN STACK", "figma to nextjs"),
    ("MODERN STACK", "tailwind developer"),
    ("MODERN STACK", "astro developer"),
    ("MODERN STACK", "sanity CMS"),
    ("ECOMMERCE", "ecommerce website"),
    ("ECOMMERCE", "ecommerce developer"),
    ("ECOMMERCE", "shopify developer"),
    ("ECOMMERCE", "shopify website"),
    ("ECOMMERCE", "woocommerce developer"),
    ("ECOMMERCE", "shopware"),
    ("ECOMMERCE", "shopware developer"),
    ("ECOMMERCE", "shopware 6"),
    ("ECOMMERCE", "headless ecommerce"),
    ("MAINTENANCE / RETAINERS", "website maintenance"),
    ("MAINTENANCE / RETAINERS", "website maintenance monthly"),
    ("MAINTENANCE / RETAINERS", "website support ongoing"),
    ("MAINTENANCE / RETAINERS", "website management ongoing"),
    ("MAINTENANCE / RETAINERS", "wordpress support retainer"),
    ("MAINTENANCE / RETAINERS", "webflow maintenance"),
    ("MAINTENANCE / RETAINERS", "shopify maintenance"),
    ("MAINTENANCE / RETAINERS", "ongoing web developer"),
    ("MAINTENANCE / RETAINERS", "web development retainer"),
    ("CONVERSION / PERFORMANCE", "conversion rate optimization"),
    ("CONVERSION / PERFORMANCE", "landing page optimization"),
    ("CONVERSION / PERFORMANCE", "website audit"),
    ("CONVERSION / PERFORMANCE", "core web vitals"),
    ("CONVERSION / PERFORMANCE", "page speed optimization"),
    ("CONVERSION / PERFORMANCE", "website speed optimization"),
    ("CONVERSION / PERFORMANCE", "technical SEO website"),
]


def slug(kw: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", kw.lower()).strip("-")


def normalize_url(url: str) -> str:
    if not url:
        return ""
    p = urlparse(url.split("?")[0])
    return urlunparse((p.scheme, p.netloc, p.path.rstrip("/"), "", "", ""))


def parse_money(s: str | None) -> float | None:
    if not s:
        return None
    s = s.replace(",", "").replace("$", "").strip()
    if "–" in s or "-" in s:
        part = re.split(r"[–-]", s)[0].strip()
        m = re.search(r"[\d.]+", part)
        return float(m.group()) if m else None
    m = re.search(r"[\d.]+", s)
    return float(m.group()) if m else None


def parse_hourly_mid(budget: str | None) -> float | None:
    if not budget or "hr" not in budget.lower():
        return None
    nums = [float(x) for x in re.findall(r"[\d.]+", budget.replace(",", ""))]
    if not nums:
        return None
    if len(nums) >= 2:
        return (nums[0] + nums[1]) / 2
    return nums[0]


def proposals_mid(tier: str | None) -> int | None:
    if not tier:
        return None
    return PROPOSAL_MID.get(tier)


def parse_spend(s: str | None) -> float | None:
    if not s:
        return None
    m = re.search(r"[\d,]+\.?\d*", s.replace("$", ""))
    if not m:
        return None
    return float(m.group().replace(",", ""))


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


def is_high_budget(job_type: str, budget: str | None) -> bool:
    if job_type == "fixed":
        v = parse_money(budget)
        return v is not None and v >= 1000
    mid = parse_hourly_mid(budget)
    return mid is not None and mid >= 40


def should_skip(job: dict) -> bool:
    text = (job.get("title") or "") + " " + (job.get("description_snippet") or "")
    return bool(SKIP_PATTERNS.search(text))


def job_record(raw: dict, group: str, keyword: str) -> dict | None:
    url = normalize_url(raw.get("url") or "")
    if not url:
        return None
    posted = raw.get("published_date") or raw.get("created_date")
    client = raw.get("client") or {}
    tier = raw.get("proposals_tier")
    return {
        "url": url,
        "title": raw.get("title"),
        "matchedKeyword": [keyword],
        "keywordGroup": group,
        "postedAt": posted,
        "type": raw.get("job_type"),
        "budget": raw.get("budget"),
        "duration": raw.get("duration"),
        "proposals": tier,
        "proposalsMid": proposals_mid(tier),
        "clientCountry": client.get("country"),
        "paymentVerified": client.get("verification_status") == "VERIFIED",
        "clientSpend": client.get("total_spent"),
        "clientHireRate": None,
        "clientRating": client.get("rating"),
        "experienceLevel": raw.get("experience_level"),
        "skills": raw.get("skills") or [],
    }


def opportunity_score(jobs: list[dict]) -> float:
    if not jobs:
        return 0.0
    now = datetime.now(timezone.utc)
    scores = []
    for j in jobs:
        recency = 0.5
        if j.get("postedAt"):
            try:
                dt = datetime.fromisoformat(j["postedAt"].replace("Z", "+00:00"))
                hours = max(0, (now - dt).total_seconds() / 3600)
                recency = max(0.1, 1.0 - min(hours, 48) / 48)
            except ValueError:
                pass
        pay = 0.3
        if j.get("type") == "fixed":
            v = parse_money(j.get("budget"))
            if v:
                pay = min(1.0, v / 5000)
        else:
            h = parse_hourly_mid(j.get("budget"))
            if h:
                pay = min(1.0, h / 80)
        prop = 0.5
        pm = j.get("proposalsMid")
        if pm is not None:
            prop = max(0.1, 1.0 - min(pm, 50) / 50)
        verify = 1.0 if j.get("paymentVerified") else 0.6
        high = 1.0 if is_high_budget(j.get("type") or "", j.get("budget")) else 0.7
        scores.append((recency * 0.25 + pay * 0.3 + prop * 0.25 + verify * 0.1 + high * 0.1) * 100)
    return round(sum(scores) / len(scores), 1)


def keyword_stats(jobs: list[dict], keyword: str) -> dict:
    now = datetime.now(timezone.utc)
    recent = []
    fixed = []
    hourly = []
    props = []
    verified = 0
    spend_vals = []
    high = 0
    for j in jobs:
        if j.get("postedAt"):
            try:
                dt = datetime.fromisoformat(j["postedAt"].replace("Z", "+00:00"))
                if (now - dt).total_seconds() <= 86400:
                    recent.append(j)
            except ValueError:
                pass
        if j.get("type") == "fixed":
            v = parse_money(j.get("budget"))
            if v is not None:
                fixed.append(v)
        elif j.get("type") == "hourly":
            h = parse_hourly_mid(j.get("budget"))
            if h is not None:
                hourly.append(h)
        if j.get("proposalsMid") is not None:
            props.append(j["proposalsMid"])
        if j.get("paymentVerified"):
            verified += 1
        sv = parse_spend(j.get("clientSpend"))
        if sv is not None:
            spend_vals.append(sv)
        if is_high_budget(j.get("type") or "", j.get("budget")):
            high += 1
    n = len(jobs)
    return {
        "keyword": keyword,
        "totalJobs": n,
        "jobsLast24h": len(recent),
        "avgBudgetFixed": round(statistics.mean(fixed), 2) if fixed else None,
        "avgRateHourly": round(statistics.mean(hourly), 2) if hourly else None,
        "medianProposals": int(statistics.median(props)) if props else None,
        "pctVerified": round(100 * verified / n, 1) if n else 0,
        "avgClientSpend": round(statistics.mean(spend_vals), 2) if spend_vals else None,
        "pctHighBudget": round(100 * high / n, 1) if n else 0,
        "opportunityScore": opportunity_score(jobs),
        "sampleConfidence": confidence_label(n),
    }


def main() -> int:
    run_at = datetime.now(timezone.utc)
    if len(sys.argv) > 1:
        run_at = datetime.fromisoformat(sys.argv[1].replace("Z", "+00:00"))

    state_path = ROOT / "state.json"
    state = json.loads(state_path.read_text()) if state_path.exists() else {}
    run_number = int(state.get("runNumber") or 0) + 1
    known = set(state.get("knownJobUrls") or [])
    window_hours = 2 if run_number == 1 else 1
    cutoff = run_at.timestamp() - window_hours * 3600

    all_jobs: dict[str, dict] = {}
    jobs_path = ROOT / "jobs.jsonl"
    if jobs_path.exists():
        for line in jobs_path.read_text().splitlines():
            if not line.strip():
                continue
            try:
                j = json.loads(line)
                u = normalize_url(j.get("url", ""))
                if u:
                    all_jobs[u] = j
                    known.add(u)
            except json.JSONDecodeError:
                pass

    errors: list[str] = []
    attempted = len(KEYWORD_GROUPS)
    completed = 0
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    for group, keyword in KEYWORD_GROUPS:
        path = CACHE_DIR / f"{slug(keyword)}.json"
        if not path.exists():
            errors.append(keyword)
            continue
        try:
            payload = json.loads(path.read_text())
        except (json.JSONDecodeError, OSError):
            errors.append(keyword)
            continue
        if payload.get("status") not in (None, "ok") and payload.get("error"):
            errors.append(keyword)
            continue
        completed += 1
        for raw in payload.get("jobs") or []:
            if should_skip(raw):
                continue
            rec = job_record(raw, group, keyword)
            if not rec:
                continue
            posted = rec.get("postedAt")
            if posted:
                try:
                    ts = datetime.fromisoformat(posted.replace("Z", "+00:00")).timestamp()
                    if ts < cutoff:
                        continue
                except ValueError:
                    pass
            u = rec["url"]
            if u in all_jobs:
                mk = set(all_jobs[u].get("matchedKeyword") or [])
                mk.add(keyword)
                all_jobs[u]["matchedKeyword"] = sorted(mk)
            else:
                all_jobs[u] = rec

    new_urls = [u for u in all_jobs if u not in known]
    with jobs_path.open("a") as f:
        for u in new_urls:
            f.write(json.dumps(all_jobs[u], ensure_ascii=False) + "\n")

    all_list = list(all_jobs.values())
    kw_to_jobs: dict[str, list[dict]] = {}
    for j in all_list:
        for kw in j.get("matchedKeyword") or []:
            kw_to_jobs.setdefault(kw, []).append(j)

    kstats = {kw: keyword_stats(jobs, kw) for kw, jobs in kw_to_jobs.items()}
    for group, keyword in KEYWORD_GROUPS:
        if keyword not in kstats:
            kstats[keyword] = keyword_stats([], keyword)

    (ROOT / "keyword-stats.json").write_text(json.dumps(kstats, indent=2))

    group_jobs: dict[str, list[dict]] = {}
    for group, keyword in KEYWORD_GROUPS:
        group_jobs.setdefault(group, []).extend(kw_to_jobs.get(keyword, []))
    gstats = {}
    for g, jobs in group_jobs.items():
        gstats[g] = {
            **keyword_stats(jobs, g),
            "group": g,
            "opportunityScore": opportunity_score(jobs),
        }
    (ROOT / "group-stats.json").write_text(json.dumps(gstats, indent=2))

    pstats = {}
    for plat, kws in PLATFORM_KEYWORDS.items():
        jobs = []
        for j in all_list:
            text = " ".join(
                [
                    j.get("title") or "",
                    " ".join(j.get("matchedKeyword") or []),
                    " ".join(j.get("skills") or []),
                ]
            ).lower()
            if any(k.lower() in text for k in kws):
                jobs.append(j)
        pstats[plat] = {**keyword_stats(jobs, plat), "platform": plat}
    (ROOT / "platform-stats.json").write_text(json.dumps(pstats, indent=2))

    top3 = sorted(kstats.values(), key=lambda x: x["opportunityScore"], reverse=True)[:3]
    log = {
        "timestamp": run_at.isoformat().replace("+00:00", "Z"),
        "runNumber": run_number,
        "keywordsAttempted": attempted,
        "keywordsCompleted": completed,
        "newJobs": len(new_urls),
        "totalJobs": len(all_jobs),
        "top3Keywords": [t["keyword"] for t in top3],
        "errors": errors,
    }
    with (ROOT / "run-log.jsonl").open("a") as f:
        f.write(json.dumps(log) + "\n")

    state.update(
        {
            "lastRunAt": run_at.isoformat().replace("+00:00", "Z"),
            "runNumber": run_number,
            "totalJobs": len(all_jobs),
            "knownJobUrls": sorted(all_jobs.keys()),
            "lastInsightRefresh": state.get("lastInsightRefresh"),
        }
    )
    state_path.write_text(json.dumps(state, indent=2))

    out = {
        "runNumber": run_number,
        "newJobs": [all_jobs[u] for u in new_urls],
        "log": log,
        "keywordStats": kstats,
        "groupStats": gstats,
        "platformStats": pstats,
        "errors": errors,
    }
    (ROOT / "last-run-output.json").write_text(json.dumps(out, indent=2, default=str))
    print(json.dumps({"run": run_number, "new": len(new_urls), "total": len(all_jobs), "errors": len(errors)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
