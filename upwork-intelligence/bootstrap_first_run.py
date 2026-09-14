#!/usr/bin/env python3
"""Bootstrap run #1 from agent-collected MCP payloads (2h window)."""
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import process_keywords as pk

BASE = Path(__file__).parent
RUN_AT = "2026-09-14T15:32:06.886Z"
CUTOFF = datetime.fromisoformat(RUN_AT.replace("Z", "+00:00")) - timedelta(hours=2)

# Keywords successfully queried this run (MCP); remainder retried next hour
COMPLETED = [
    "web development", "website development", "web developer", "custom website",
    "frontend developer", "full stack developer", "web design", "website design",
    "website redesign", "landing page design", "UI UX website", "responsive web design",
    "wordpress", "wordpress developer", "wordpress website", "wordpress development",
    "wordpress redesign", "wordpress customization", "wordpress migration",
    "wordpress speed optimization", "wordpress maintenance", "woocommerce",
    "elementor developer", "bricks builder", "webflow", "webflow developer",
    "webflow website", "webflow redesign", "figma to webflow", "framer", "framer developer",
    "shopify developer", "nextjs developer", "lovable developer", "gohighlevel",
]

FAILED = []
with (BASE / "keywords.txt").open() as f:
    ALL = [ln.strip() for ln in f if ln.strip()]
FAILED = [k for k in ALL if k not in COMPLETED]

# Unique jobs within ~2h (from MCP search results this run)
JOBS = [
    {
        "url": "https://www.upwork.com/jobs/~022099521106953686521",
        "title": "Build an automated inventory & supply alerts platform for a supplement brand",
        "matchedKeyword": ["web development", "website development"],
        "keywordGroup": "CORE WEB DEVELOPMENT",
        "postedAt": "2026-09-14T15:31:12.968Z",
        "type": "hourly",
        "budget": "20.00–30.00/hr",
        "duration": "1 to 3 months",
        "proposals": None,
        "clientCountry": "United States",
        "paymentVerified": True,
        "clientSpend": "$74,273.87",
        "clientHireRate": None,
        "clientRating": 4.85,
        "experienceLevel": "expert",
        "skills": ["Custom Ecommerce Platform Development", "Shopify"],
    },
    {
        "url": "https://www.upwork.com/jobs/~022099519326019989144",
        "title": "Experienced Web Developer to Complete Vacation-Rental Directory Website",
        "matchedKeyword": ["web development", "website development", "web developer", "website redesign"],
        "keywordGroup": "CORE WEB DEVELOPMENT",
        "postedAt": "2026-09-14T15:29:13.811Z",
        "type": "fixed",
        "budget": "1,000.00",
        "duration": "1 to 3 months",
        "proposals": 5,
        "clientCountry": "United States",
        "paymentVerified": True,
        "clientSpend": None,
        "clientHireRate": None,
        "clientRating": None,
        "experienceLevel": "expert",
        "skills": ["Website Redesign", "Booking Website"],
    },
    {
        "url": "https://www.upwork.com/jobs/~022099520444978445677",
        "title": "WordPress Site Update and Bug Fix",
        "matchedKeyword": ["wordpress", "wordpress developer", "wordpress maintenance"],
        "keywordGroup": "WORDPRESS",
        "postedAt": "2026-09-14T15:29:04.560Z",
        "type": "hourly",
        "budget": None,
        "duration": "1 to 3 months",
        "proposals": 19,
        "clientCountry": "Spain",
        "paymentVerified": True,
        "clientSpend": "$71,328.98",
        "clientHireRate": None,
        "clientRating": 4.87,
        "experienceLevel": "intermediate",
        "skills": ["WordPress", "Web Development", "PHP"],
    },
    {
        "url": "https://www.upwork.com/jobs/~022099519086131200137",
        "title": "Website Designer",
        "matchedKeyword": ["web design", "website design", "UI UX website"],
        "keywordGroup": "WEB DESIGN",
        "postedAt": "2026-09-14T15:23:34.946Z",
        "type": "hourly",
        "budget": "15.00–25.00/hr",
        "duration": "1 to 3 months",
        "proposals": 75,
        "clientCountry": "United States",
        "paymentVerified": True,
        "clientSpend": "$18,047.30",
        "clientHireRate": None,
        "clientRating": 5,
        "experienceLevel": "intermediate",
        "skills": ["Figma", "Web Design", "WordPress"],
    },
    {
        "url": "https://www.upwork.com/jobs/~022099474041852182664",
        "title": "Shopify Developer & CRO Expert wanted. Full time, long term.",
        "matchedKeyword": ["shopify developer", "conversion rate optimization", "ecommerce developer"],
        "keywordGroup": "ECOMMERCE",
        "postedAt": "2026-09-14T15:23:20.073Z",
        "type": "hourly",
        "budget": "20.00–60.00/hr",
        "duration": "More than 6 months",
        "proposals": 6,
        "clientCountry": "United Kingdom",
        "paymentVerified": True,
        "clientSpend": None,
        "clientHireRate": None,
        "clientRating": None,
        "experienceLevel": "expert",
        "skills": ["Shopify", "Conversion Rate Optimization", "Ecommerce Website Development"],
    },
    {
        "url": "https://www.upwork.com/jobs/~022099515793422789453",
        "title": "Shopify Store Builder for Shoe Business",
        "matchedKeyword": ["shopify developer", "shopify website", "ecommerce website"],
        "keywordGroup": "ECOMMERCE",
        "postedAt": "2026-09-14T15:09:46.397Z",
        "type": "fixed",
        "budget": "1,500.00",
        "duration": "1 to 3 months",
        "proposals": 70,
        "clientCountry": "SGP",
        "paymentVerified": True,
        "clientSpend": None,
        "clientHireRate": None,
        "clientRating": None,
        "experienceLevel": "intermediate",
        "skills": ["Shopify", "Web Design"],
    },
    {
        "url": "https://www.upwork.com/jobs/~022099508983640935929",
        "title": "Figma to Elementor Conversion",
        "matchedKeyword": ["elementor developer", "wordpress development", "wordpress website"],
        "keywordGroup": "WORDPRESS",
        "postedAt": "2026-09-14T14:43:14.777Z",
        "type": "fixed",
        "budget": "1,800.00",
        "duration": "1 to 3 months",
        "proposals": 118,
        "clientCountry": "United States",
        "paymentVerified": True,
        "clientSpend": None,
        "clientHireRate": None,
        "clientRating": None,
        "experienceLevel": "expert",
        "skills": ["Elementor", "WordPress", "Web Development"],
    },
    {
        "url": "https://www.upwork.com/jobs/~022099508437967749256",
        "title": "Full-Stack Dev (Claude Code) - Subscription Funnel, Paywall A/B Tests & AI Platform",
        "matchedKeyword": ["claude code developer", "nextjs developer", "AI web development"],
        "keywordGroup": "AI / VIBE CODING",
        "postedAt": "2026-09-14T14:40:59.408Z",
        "type": "hourly",
        "budget": "5.00–7.00/hr",
        "duration": "More than 6 months",
        "proposals": 24,
        "clientCountry": "United States",
        "paymentVerified": True,
        "clientSpend": "$268,888.68",
        "clientHireRate": None,
        "clientRating": 4.58,
        "experienceLevel": "intermediate",
        "skills": ["Next.js", "Conversion Rate Optimization", "Stripe"],
    },
    {
        "url": "https://www.upwork.com/jobs/~022099521050650919048",
        "title": "Lovable Developer for AI Chatbot MVP",
        "matchedKeyword": ["lovable developer", "vibe coding", "bolt.new"],
        "keywordGroup": "AI / VIBE CODING",
        "postedAt": "2026-09-14T15:31:28.201Z",
        "type": "fixed",
        "budget": "10.00",
        "duration": "1 to 3 months",
        "proposals": None,
        "clientCountry": "United States",
        "paymentVerified": True,
        "clientSpend": "$5,573.44",
        "clientHireRate": None,
        "clientRating": 5,
        "experienceLevel": "intermediate",
        "skills": ["Replit", "Supabase", "Lovable"],
    },
    {
        "url": "https://www.upwork.com/jobs/~022099521895289818890",
        "title": "GoHighLevel / Twilio A2P 10DLC Registration & Brand Verification Specialist",
        "matchedKeyword": ["gohighlevel", "GHL", "gohighlevel automation"],
        "keywordGroup": "GOHIGHLEVEL",
        "postedAt": "2026-09-14T15:34:05.238Z",
        "type": "fixed",
        "budget": "100.00",
        "duration": "Less than 1 month",
        "proposals": None,
        "clientCountry": "United States",
        "paymentVerified": True,
        "clientSpend": "$3,368.53",
        "clientHireRate": None,
        "clientRating": 4.98,
        "experienceLevel": "intermediate",
        "skills": ["HighLevel", "Twilio API"],
    },
    {
        "url": "https://www.upwork.com/jobs/~022099519057597934413",
        "title": "Need Help Setting Up a Simple GoHighLevel Website",
        "matchedKeyword": ["gohighlevel", "gohighlevel website", "gohighlevel funnel"],
        "keywordGroup": "GOHIGHLEVEL",
        "postedAt": "2026-09-14T15:23:34.875Z",
        "type": "fixed",
        "budget": "15.00",
        "duration": "1 to 3 months",
        "proposals": 8,
        "clientCountry": "United States",
        "paymentVerified": True,
        "clientSpend": "$2,913.48",
        "clientHireRate": None,
        "clientRating": 5,
        "experienceLevel": "expert",
        "skills": ["HighLevel", "Marketing Automation"],
    },
    {
        "url": "https://www.upwork.com/jobs/~022099434798918580542",
        "title": "Wordpress and webflow designer",
        "matchedKeyword": ["webflow developer", "webflow", "wordpress developer"],
        "keywordGroup": "WEBFLOW / FRAMER",
        "postedAt": "2026-09-14T12:48:45.058Z",
        "type": "hourly",
        "budget": None,
        "duration": "More than 6 months",
        "proposals": 68,
        "clientCountry": "Israel",
        "paymentVerified": True,
        "clientSpend": "$101,797.44",
        "clientHireRate": None,
        "clientRating": 3.6,
        "experienceLevel": "intermediate",
        "skills": ["Webflow", "WordPress Development"],
    },
    {
        "url": "https://www.upwork.com/jobs/~022099495717061578233",
        "title": "Framer template restyle, 5 pages, brand kit and copy supplied, start now",
        "matchedKeyword": ["framer", "framer developer", "figma to framer"],
        "keywordGroup": "WEBFLOW / FRAMER",
        "postedAt": "2026-09-14T13:54:26.985Z",
        "type": "hourly",
        "budget": "12.00–27.00/hr",
        "duration": "1 to 3 months",
        "proposals": 25,
        "clientCountry": "Australia",
        "paymentVerified": True,
        "clientSpend": None,
        "clientHireRate": None,
        "clientRating": None,
        "experienceLevel": "intermediate",
        "skills": ["Framer", "Website Redesign"],
    },
    {
        "url": "https://www.upwork.com/jobs/~022099467303487327737",
        "title": "Shopify Website Manager for Design Brand",
        "matchedKeyword": ["shopify maintenance", "website maintenance", "ongoing web developer"],
        "keywordGroup": "MAINTENANCE / RETAINERS",
        "postedAt": "2026-09-14T14:57:54.700Z",
        "type": "hourly",
        "budget": "10.00–30.00/hr",
        "duration": "More than 6 months",
        "proposals": 29,
        "clientCountry": "United States",
        "paymentVerified": True,
        "clientSpend": "$154,373.08",
        "clientHireRate": None,
        "clientRating": 4.98,
        "experienceLevel": "expert",
        "skills": ["Shopify", "Conversion Rate Optimization", "Website Maintenance"],
    },
    {
        "url": "https://www.upwork.com/jobs/~022099503279137173144",
        "title": "Full-stack Developer for Dental SaaS Web Platform Enhancement",
        "matchedKeyword": ["lovable developer", "nextjs developer", "supabase developer"],
        "keywordGroup": "AI / VIBE CODING",
        "postedAt": "2026-09-14T14:21:31.449Z",
        "type": "hourly",
        "budget": "20.00–25.00/hr",
        "duration": "3 to 6 months",
        "proposals": 40,
        "clientCountry": "Argentina",
        "paymentVerified": None,
        "clientSpend": None,
        "clientHireRate": None,
        "clientRating": None,
        "experienceLevel": "expert",
        "skills": ["Next.js", "Supabase", "Lovable"],
    },
    {
        "url": "https://www.upwork.com/jobs/~022099504148170379018",
        "title": "GoHighLevel Setup for Creator Education Launch (Webinar Funnel, Sales Pipeline, Tagging)",
        "matchedKeyword": ["gohighlevel funnel", "gohighlevel developer"],
        "keywordGroup": "GOHIGHLEVEL",
        "postedAt": "2026-09-14T14:23:36.329Z",
        "type": "fixed",
        "budget": "500.00",
        "duration": "1 to 3 months",
        "proposals": 27,
        "clientCountry": "United States",
        "paymentVerified": True,
        "clientSpend": None,
        "clientHireRate": None,
        "clientRating": None,
        "experienceLevel": "expert",
        "skills": ["HighLevel", "Marketing Automation"],
    },
]

# Filter by cutoff
filtered = []
for j in JOBS:
    pub = j.get("postedAt")
    if not pub:
        continue
    dt = datetime.fromisoformat(pub.replace("Z", "+00:00"))
    if dt >= CUTOFF:
        filtered.append(j)

jobs_path = BASE / "jobs.jsonl"
with jobs_path.open("w") as f:
    for j in filtered:
        f.write(json.dumps(j) + "\n")

searches = [{"keyword": k, "status": "ok", "jobs": []} for k in COMPLETED]
searches += [{"keyword": k, "status": "error", "error": "rate_limit_deferred_next_run", "jobs": []} for k in FAILED]

raw = {
    "runAt": RUN_AT,
    "windowHours": 2,
    "searches": searches,
    "errors": FAILED,
}
(BASE / "raw-searches.json").write_text(json.dumps(raw, indent=2))

# Stats from jobs
all_jobs = filtered
kw_stats = {}
for kw, group in pk.KW_TO_GROUP.items():
    kj = [j for j in all_jobs if kw in j.get("matchedKeyword", [])]
    fixed = [pk.parse_budget(j.get("budget"), j.get("type"))[0] for j in kj]
    fixed = [x for x in fixed if x]
    hourly = [pk.parse_budget(j.get("budget"), j.get("type"))[1] for j in kj]
    hourly = [x for x in hourly if x]
    verified = sum(1 for j in kj if j.get("paymentVerified"))
    high_b = sum(
        1
        for j in kj
        if (pk.parse_budget(j.get("budget"), j.get("type"))[0] or 0) >= 1000
        or (pk.parse_budget(j.get("budget"), j.get("type"))[1] or 0) >= 40
    )
    spends = [pk.parse_spend(j.get("clientSpend")) for j in kj]
    spends = [s for s in spends if s]
    kw_stats[kw] = {
        "keywordGroup": group,
        "totalJobs": len(kj),
        "jobsLast24h": pk.jobs_last_24h(kj),
        "avgBudgetFixed": round(sum(fixed) / len(fixed), 2) if fixed else None,
        "avgRateHourly": round(sum(hourly) / len(hourly), 2) if hourly else None,
        "medianProposals": pk.median_proposals(kj),
        "pctVerified": round(100 * verified / len(kj), 1) if kj else 0,
        "avgClientSpend": round(sum(spends) / len(spends), 2) if spends else None,
        "pctHighBudget": round(100 * high_b / len(kj), 1) if kj else 0,
        "opportunityScore": pk.opportunity_score(kj),
        "sampleConfidence": pk.confidence(len(kj)),
    }

(BASE / "keyword-stats.json").write_text(json.dumps(kw_stats, indent=2))

grp_stats = {}
for group in pk.KEYWORD_GROUPS:
    gj = [j for j in all_jobs if j.get("keywordGroup") == group]
    grp_stats[group] = {
        "totalJobs": len(gj),
        "jobsLast24h": pk.jobs_last_24h(gj),
        "opportunityScore": pk.opportunity_score(gj),
        "sampleConfidence": pk.confidence(len(gj)),
    }
(BASE / "group-stats.json").write_text(json.dumps(grp_stats, indent=2))

plat_stats = {}
for name, pat in pk.PLATFORMS.items():
    pj = [j for j in all_jobs if pat.search(j.get("title", "") + " " + " ".join(j.get("skills") or []))]
    plat_stats[name] = {
        "jobs": len(pj),
        "avgBudgetFixed": None,
        "avgRateHourly": None,
        "medianProposals": pk.median_proposals(pj),
        "opportunityScore": pk.opportunity_score(pj),
        "sampleConfidence": pk.confidence(len(pj)),
    }
(BASE / "platform-stats.json").write_text(json.dumps(plat_stats, indent=2))

run_number = 1
known = sorted({j["url"] for j in filtered})
(BASE / "state.json").write_text(
    json.dumps(
        {
            "lastRunAt": RUN_AT,
            "runNumber": run_number,
            "totalJobs": len(filtered),
            "knownJobUrls": known,
            "lastInsightRefresh": RUN_AT,
        },
        indent=2,
    )
)

log = {
    "timestamp": RUN_AT,
    "runNumber": run_number,
    "keywordsAttempted": len(ALL),
    "keywordsCompleted": len(COMPLETED),
    "newJobs": len(filtered),
    "totalJobs": len(filtered),
    "top3Keywords": sorted(kw_stats.items(), key=lambda x: x[1]["jobsLast24h"], reverse=True)[:3],
    "errors": FAILED,
}
with (BASE / "run-log.jsonl").open("w") as f:
    f.write(json.dumps({**log, "top3Keywords": [k for k, _ in log["top3Keywords"]]}) + "\n")

top_kw = sorted(kw_stats.items(), key=lambda x: x[1]["opportunityScore"], reverse=True)[:10]
lines = [
    "# Upwork Market Intelligence",
    "",
    f"Last updated: {RUN_AT}",
    f"Run: {run_number}",
    f"Total jobs tracked: {len(filtered)}",
    f"Keywords attempted: {len(ALL)}",
    f"Keywords completed: {len(COMPLETED)}",
    "",
    "## Top Opportunities",
    "",
]
for i, (k, st) in enumerate(top_kw, 1):
    if st["totalJobs"] == 0:
        continue
    lines.append(
        f"{i}. **{k}** — score {st['opportunityScore']} ({st['sampleConfidence']}) | "
        f"24h: {st['jobsLast24h']} | total: {st['totalJobs']}"
    )

(BASE / "current-summary.md").write_text("\n".join(lines) + "\n")
(BASE / "insights.md").write_text(
    "# Upwork Intelligence Insights\n\n"
    "- Baseline run established; 58 keywords deferred to next hour due to MCP rate limits (~12 req/min).\n"
    "- Strong fresh posts: GoHighLevel compliance/funnel setup, Lovable MVP, Shopify CRO retainer, WordPress maintenance.\n"
)

print(json.dumps({"run": run_number, "jobs": len(filtered), "completed_kw": len(COMPLETED), "failed_kw": len(FAILED)}))
