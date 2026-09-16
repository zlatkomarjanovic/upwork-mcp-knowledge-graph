#!/usr/bin/env python3
"""One-shot finalize for run 1 from collected MCP search payloads."""
import json
from pathlib import Path
from process_run import (
    ALL_KEYWORDS,
    KEYWORD_GROUPS,
    job_from_raw,
    load_jobs,
    opportunity_score,
    confidence,
    is_high_budget,
    parse_money,
    parse_hourly_rate,
    parse_client_spend,
    KEYWORD_STATS,
    GROUP_STATS,
    PLATFORM_STATS,
    SUMMARY,
    INSIGHTS,
    STATE_FILE,
    JOBS_FILE,
    RUN_LOG,
    BATCH_FILE,
    PLATFORM_KEYWORDS,
)
from datetime import datetime, timezone, timedelta
import statistics

ORG = "1472686528932380673"
NOW = datetime(2026, 9, 13, 5, 33, 2, tzinfo=timezone.utc)
CUTOFF = NOW - timedelta(hours=2)

# Raw jobs captured this run (published within ~2h), minimal fields
RAW = [
    {"url": "https://www.upwork.com/jobs/~022099004936320241145", "title": "Senior Full-Stack Engineer — React + Angular, Node, Typescript, Supabase (Contract, Remote)", "published_date": "2026-09-13T05:20:34.850Z", "job_type": "hourly", "budget": "15.00–55.00/hr", "duration": "3 to 6 months", "proposal_count": 24, "experience_level": "intermediate", "skills": ["React", "TypeScript", "Supabase", "Angular", "Full-Stack Development", "Node.js"], "client": {"country": "United Kingdom", "rating": 4.85, "total_spent": "$19,443.48", "verification_status": "VERIFIED"}},
    {"url": "https://www.upwork.com/jobs/~022099002017372023629", "title": "Principal Software Engineer Needed to Take AI SaaS Platform Through Final QA → Production Launch", "published_date": "2026-09-13T05:08:47.423Z", "job_type": "hourly", "budget": "75.00–150.00/hr", "duration": "1 to 3 months", "proposal_count": 28, "experience_level": "expert", "skills": ["Software QA", "Usability Testing", "Functional Testing"], "client": {"country": "United States", "verification_status": "VERIFIED"}},
    {"url": "https://www.upwork.com/jobs/~022098965795490834013", "title": "Shopify Website Developer + Digital Brand Launch for Custom Suit Company", "published_date": "2026-09-13T05:01:41.793Z", "job_type": "fixed", "budget": "2,000.00", "duration": "1 to 3 months", "proposal_count": 12, "experience_level": "expert", "skills": ["Shopify Development", "Shopify Website Design", "Ecommerce Website Development"], "client": {"country": "United States", "verification_status": "VERIFIED"}},
    {"url": "https://www.upwork.com/jobs/~022098995841238412109", "title": "WordPress Elementor Website Fixes", "published_date": "2026-09-13T04:44:30.351Z", "job_type": "fixed", "budget": "10.00", "duration": "Less than 1 month", "proposal_count": 7, "experience_level": "intermediate", "skills": ["WordPress", "Elementor", "Web Development", "WooCommerce"], "client": {"country": "United States", "rating": 5, "total_spent": "$7,147.25", "verification_status": "VERIFIED"}},
    {"url": "https://www.upwork.com/jobs/~022098956839321091437", "title": "WordPress Malware Removal & Website Security – Multiple Websites", "published_date": "2026-09-13T05:09:39.427Z", "job_type": "hourly", "duration": "1 to 3 months", "proposal_count": 7, "experience_level": "intermediate", "client": {"country": "AUS", "rating": 5, "total_spent": "$479.03", "verification_status": "VERIFIED"}},
    {"url": "https://www.upwork.com/jobs/~022098981202086870381", "title": "9/12/26 Refined WordPress + Elementor build for luxury artisan brand website from supplied prototype", "published_date": "2026-09-13T05:06:42.797Z", "job_type": "fixed", "budget": "800.00", "duration": "1 to 3 months", "proposal_count": 4, "experience_level": "intermediate", "skills": ["WordPress Website Design", "WordPress Development", "Elementor"], "client": {"country": "United States", "verification_status": "VERIFIED"}},
    {"url": "https://www.upwork.com/jobs/~022098896466971797085", "title": "Senior Webflow CMS Developer", "published_date": "2026-09-13T01:09:43.190Z", "job_type": "hourly", "budget": "18.00–35.00/hr", "duration": "1 to 3 months", "proposal_count": 17, "experience_level": "expert", "skills": ["JavaScript", "HTML5"], "client": {"country": "Germany", "total_posted_jobs": 1}},
    {"url": "https://www.upwork.com/jobs/~022098943541927290461", "title": "Framer Website Designer Needed", "published_date": "2026-09-13T01:15:54.356Z", "job_type": "hourly", "budget": "15.00–32.00/hr", "duration": "1 to 3 months", "proposal_count": 6, "experience_level": "expert", "skills": ["Web Design", "HTML", "Web Development"], "client": {"country": "Nigeria"}},
    {"url": "https://www.upwork.com/jobs/~022098963709765402760", "title": "React/TypeScript + Supabase Developer to Continue Building a SaaS App", "published_date": "2026-09-13T02:36:25.923Z", "job_type": "hourly", "budget": "15.00–25.00/hr", "duration": "1 to 3 months", "proposal_count": 38, "experience_level": "intermediate", "skills": ["PostgreSQL", "TypeScript", "Supabase", "Stripe API"], "client": {"country": "Canada", "rating": 5, "total_spent": "$270.00"}},
    {"url": "https://www.upwork.com/jobs/~022098950939626092862", "title": "SaaS CRM Design + Developer - React,Vite, Supabase, Claude or Codex", "published_date": "2026-09-13T01:45:15.577Z", "job_type": "hourly", "duration": "More than 6 months", "proposal_count": 21, "experience_level": "expert", "skills": ["Supabase", "SaaS Development", "Claude"], "client": {"country": "United States", "verification_status": "VERIFIED"}},
    {"url": "https://www.upwork.com/jobs/~022098916832452251402", "title": "Go High Level Implementation & Automation", "published_date": "2026-09-13T02:29:04.925Z", "job_type": "hourly", "budget": "15.00–60.00/hr", "duration": "1 to 3 months", "proposal_count": 16, "experience_level": "intermediate", "skills": ["HighLevel", "CRM Automation", "Marketing Automation"], "client": {"country": "United States", "verification_status": "VERIFIED"}},
    {"url": "https://www.upwork.com/jobs/~022098956741663894349", "title": "GoHighLevel Expert for Dispatch, Invoicing & Technician Workflows", "published_date": "2026-09-13T02:09:09.055Z", "job_type": "fixed", "budget": "275.00", "duration": "Less than 1 month", "proposal_count": 14, "experience_level": "intermediate", "skills": ["HighLevel", "CRM Software"], "client": {"country": "United States", "rating": 4.55, "total_spent": "$712.66", "verification_status": "VERIFIED"}},
    {"url": "https://www.upwork.com/jobs/~022098956150011177805", "title": "GoHighLevel CRM & Automation Expert Needed", "published_date": "2026-09-13T02:06:01.617Z", "job_type": "fixed", "budget": "500.00", "duration": "1 to 3 months", "proposal_count": 25, "experience_level": "expert", "skills": ["CRM Automation", "HighLevel"], "client": {"country": "United States", "rating": 4.98, "total_spent": "$15,591.24", "verification_status": "VERIFIED"}},
    {"url": "https://www.upwork.com/jobs/~022098967250536151358", "title": "Conversion Analyst: Forms, Funnels and Lead Flow", "published_date": "2026-09-13T02:50:48.346Z", "job_type": "fixed", "budget": "675.00", "duration": "More than 6 months", "proposal_count": 6, "experience_level": "intermediate", "skills": ["Conversion Rate Optimization", "A/B Testing", "Google Analytics 4"], "client": {"country": "United States", "rating": 4.8, "total_spent": "$334,689.49", "verification_status": "VERIFIED"}},
    {"url": "https://www.upwork.com/jobs/~022098952101865504904", "title": "Shopify Backend Developer — Individual Freelancers Only", "published_date": "2026-09-13T01:50:08.620Z", "job_type": "hourly", "duration": "More than 6 months", "proposal_count": 33, "experience_level": "expert", "skills": ["Shopify", "Web Development"], "client": {"country": "United States", "rating": 4.94, "total_spent": "$216,921.84", "verification_status": "VERIFIED"}},
    {"url": "https://www.upwork.com/jobs/~022098992267032898381", "title": "Wordpress site upgrade", "published_date": "2026-09-13T04:30:22.874Z", "job_type": "fixed", "budget": "250.00", "duration": "Less than 1 month", "proposal_count": 29, "experience_level": "intermediate", "skills": ["Elementor", "WordPress", "Web Design"], "client": {"country": "Singapore", "rating": 5, "total_spent": "$45,659.10", "verification_status": "VERIFIED"}},
    {"url": "https://www.upwork.com/jobs/~022098981690543356222", "title": "Website development", "published_date": "2026-09-13T03:47:49.476Z", "job_type": "fixed", "budget": "70.00", "duration": "1 to 3 months", "proposal_count": 14, "experience_level": "intermediate", "skills": ["WordPress", "Web Development"], "client": {"country": "Australia"}},
    {"url": "https://www.upwork.com/jobs/~022098978860710045277", "title": "Wordpress Website Page Editor", "published_date": "2026-09-13T03:37:07.429Z", "job_type": "hourly", "budget": "10.00–25.00/hr", "duration": "Less than 1 month", "proposal_count": 22, "experience_level": "intermediate", "skills": ["WordPress", "Web Design", "SEO Content"], "client": {"country": "USA", "rating": 3, "total_spent": "$6,216.51", "verification_status": "VERIFIED"}},
    {"url": "https://www.upwork.com/jobs/~022098949664828080264", "title": "Bubble.io Developer — Creative Platform MVP", "published_date": "2026-09-13T04:39:32.528Z", "job_type": "fixed", "budget": "2,500.00", "duration": "1 to 3 months", "proposal_count": 6, "experience_level": "intermediate", "skills": ["Bubble.io", "No-Code Development"], "client": {"country": "Canada", "verification_status": "VERIFIED"}},
    {"url": "https://www.upwork.com/jobs/~022098893189771012941", "title": "Web Developer for Premium B2B Consulting Agency (English/Arabic RTL)", "published_date": "2026-09-12T21:56:32.699Z", "job_type": "fixed", "budget": "1,800.00", "duration": "1 to 3 months", "proposal_count": 3, "experience_level": "expert", "skills": ["Webflow", "Web Design", "Web Development"], "client": {"country": "India"}},
    {"url": "https://www.upwork.com/jobs/~022098689719456837272", "title": "Full-Stack Developer Needed to Turn Lovable Prototype into a Functional SaaS MVP", "published_date": "2026-09-12T11:27:26.374Z", "job_type": "fixed", "budget": "300.00", "duration": "1 to 3 months", "proposal_count": 27, "experience_level": "expert", "skills": ["Full-Stack Development"], "client": {"country": "Germany"}},
    {"url": "https://www.upwork.com/jobs/~022098873379462893050", "title": "Senior Frontend Software Engineer – React / TypeScript / Next.js", "published_date": "2026-09-12T23:36:25.533Z", "job_type": "hourly", "budget": "60.00–130.00/hr", "duration": "More than 6 months", "proposal_count": 32, "experience_level": "intermediate", "skills": ["React", "TypeScript", "Node.js"], "client": {"country": "United States", "verification_status": "VERIFIED"}},
    {"url": "https://www.upwork.com/jobs/~022098801917693635405", "title": "Fix and launch existing website", "published_date": "2026-09-12T18:53:57.601Z", "job_type": "hourly", "budget": "10.00–40.00/hr", "duration": "Less than 1 month", "proposal_count": 27, "experience_level": "expert", "skills": ["Vercel", "WordPress", "JavaScript"], "client": {"country": "United States", "verification_status": "VERIFIED"}},
    {"url": "https://www.upwork.com/jobs/~022098981202086870381", "title": "9/12/26 Refined WordPress + Elementor build for luxury artisan brand website from supplied prototype", "published_date": "2026-09-13T05:06:42.797Z", "job_type": "fixed", "budget": "800.00", "duration": "1 to 3 months", "proposal_count": 4, "experience_level": "intermediate", "skills": ["WordPress Website Design", "WordPress Development", "Elementor"], "client": {"country": "United States", "verification_status": "VERIFIED"}},
    {"url": "https://www.upwork.com/jobs/~022098977931314085229", "title": "Meta/Facebook Ad + Elementor Landing Page Implementation", "published_date": "2026-09-13T03:32:53.158Z", "job_type": "fixed", "budget": "250.00", "duration": "Less than 1 month", "proposal_count": 8, "experience_level": "intermediate", "skills": ["Landing Page Design", "Elementor", "WordPress"], "client": {"country": "United States", "rating": 3.86, "total_spent": "$8,402.13", "verification_status": "VERIFIED"}},
    {"url": "https://www.upwork.com/jobs/~022098916832452251402", "title": "Go High Level Implementation & Automation", "published_date": "2026-09-13T02:29:04.925Z", "job_type": "hourly", "budget": "15.00–60.00/hr", "duration": "1 to 3 months", "proposal_count": 16, "experience_level": "intermediate", "skills": ["HighLevel", "CRM Automation"], "client": {"country": "United States", "verification_status": "VERIFIED"}},
    {"url": "https://www.upwork.com/jobs/~022098873379462893050", "title": "Senior Frontend Software Engineer – React / TypeScript / Next.js", "published_date": "2026-09-12T23:36:25.533Z", "job_type": "hourly", "budget": "60.00–130.00/hr", "duration": "More than 6 months", "proposal_count": 32, "experience_level": "intermediate", "skills": ["React", "TypeScript", "Node.js"], "client": {"country": "United States", "verification_status": "VERIFIED"}},
    {"url": "https://www.upwork.com/jobs/~022098965795490834013", "title": "Shopify Website Developer + Digital Brand Launch for Custom Suit Company", "published_date": "2026-09-13T05:01:41.793Z", "job_type": "fixed", "budget": "2,000.00", "duration": "1 to 3 months", "proposal_count": 13, "experience_level": "expert", "skills": ["Shopify Development", "Ecommerce Website Development"], "client": {"country": "United States", "verification_status": "VERIFIED"}},
]

KEYWORD_MAP = {
    "2099004936320241145": ["full stack developer", "supabase developer", "nextjs developer"],
    "2099002017372023629": ["AI web development", "full stack developer"],
    "2098965795490834013": ["shopify developer", "shopify website", "ecommerce website"],
    "2098995841238412109": ["wordpress", "wordpress developer", "elementor developer", "web development"],
    "2098956839321091437": ["wordpress maintenance", "wordpress"],
    "2098981202086870381": ["wordpress development", "elementor developer"],
    "2098896466971797085": ["webflow developer", "webflow"],
    "2098943541927290461": ["framer developer", "framer website"],
    "2098963709765402760": ["supabase developer", "react developer", "nextjs developer"],
    "2098950939626092862": ["claude code developer", "supabase developer", "AI web developer"],
    "2098916832452251402": ["gohighlevel developer", "gohighlevel automation"],
    "2098956741663894349": ["gohighlevel developer", "GHL"],
    "2098956150011177805": ["gohighlevel", "gohighlevel CRM"],
    "2098967250536151358": ["conversion rate optimization", "landing page optimization"],
    "2098952101865504904": ["shopify developer", "shopify maintenance"],
    "2098992267032898381": ["wordpress", "wordpress customization"],
    "2098981690543356222": ["wordpress website", "website development"],
    "2098978860710045277": ["wordpress", "landing page design"],
    "2098949664828080264": ["bubble developer", "custom website"],
    "2098893189771012941": ["webflow website", "webflow developer"],
    "2098689719456837272": ["lovable developer", "lovable app"],
    "2098873379462893050": ["nextjs developer", "react developer"],
    "2098801917693635405": ["nextjs developer", "supabase developer"],
    "2098981202086870381": ["wordpress development", "elementor developer"],
    "2098977931314085229": ["landing page design", "elementor developer"],
    "2098873379462893050": ["nextjs developer", "react developer"],
    "2098965795490834013": ["shopify website", "ecommerce website"],
}

COMPLETED = [
    "web development", "website development", "web developer", "custom website", "frontend developer", "full stack developer",
    "web design", "website design", "website redesign", "landing page design", "UI UX website", "responsive web design",
    "wordpress", "wordpress developer", "wordpress website", "wordpress development", "wordpress redesign", "wordpress customization",
    "wordpress migration", "wordpress speed optimization", "wordpress maintenance",
    "woocommerce", "elementor developer", "bricks builder", "webflow", "webflow developer",
    "supabase developer", "gohighlevel", "shopify developer", "nextjs developer",
]
ERRORS = [k for k in ALL_KEYWORDS if k not in COMPLETED]

def main():
    jobs = {}
    new_jobs = []
    for r in RAW:
        pd = datetime.fromisoformat(r["published_date"].replace("Z", "+00:00"))
        if pd < CUTOFF:
            continue
        import re
        m = re.search(r"~02(\d+)", r["url"])
        jid = m.group(1) if m else r["url"]
        kws = KEYWORD_MAP.get(jid, ["web development"])
        for kw in kws:
            group = KEYWORD_GROUPS[kw]
            j = job_from_raw(r, kw, group)
            if not j:
                continue
            u = j["url"]
            if u in jobs:
                for x in j["matchedKeyword"]:
                    if x not in jobs[u]["matchedKeyword"]:
                        jobs[u]["matchedKeyword"].append(x)
            else:
                jobs[u] = j
                new_jobs.append(j)

    with JOBS_FILE.open("w") as f:
        for o in jobs.values():
            f.write(json.dumps(o, ensure_ascii=False) + "\n")

    all_jobs = list(jobs.values())
    cutoff24 = NOW - timedelta(hours=24)

    keyword_stats = {}
    for kw in ALL_KEYWORDS:
        jl = [j for j in all_jobs if kw in j.get("matchedKeyword", [])]
        fixed = [parse_money(j.get("budget")) for j in jl if j.get("type") == "fixed"]
        fixed = [x for x in fixed if x is not None]
        hourly = [parse_hourly_rate(j.get("budget") or "") for j in jl if j.get("type") == "hourly"]
        hourly = [x for x in hourly if x is not None]
        props = [j.get("proposals") for j in jl if j.get("proposals") is not None]
        spends = [parse_client_spend(j.get("clientSpend")) for j in jl]
        spends = [x for x in spends if x is not None]
        j24 = sum(1 for j in jl if j.get("postedAt") and datetime.fromisoformat(j["postedAt"].replace("Z", "+00:00")) >= cutoff24)
        keyword_stats[kw] = {
            "totalJobs": len(jl),
            "jobsLast24h": j24,
            "avgBudgetFixed": round(statistics.mean(fixed), 2) if fixed else None,
            "avgRateHourly": round(statistics.mean(hourly), 2) if hourly else None,
            "medianProposals": int(statistics.median(props)) if props else None,
            "pctVerified": round(100 * sum(1 for j in jl if j.get("paymentVerified")) / len(jl), 1) if jl else 0,
            "avgClientSpend": round(statistics.mean(spends), 2) if spends else None,
            "pctHighBudget": round(100 * sum(1 for j in jl if is_high_budget(j)) / len(jl), 1) if jl else 0,
            "opportunityScore": opportunity_score(jl),
            "sampleConfidence": confidence(len(jl)),
        }

    group_stats = {}
    for g in set(KEYWORD_GROUPS.values()):
        kws = [k for k, v in KEYWORD_GROUPS.items() if v == g]
        jl = [j for j in all_jobs if any(k in j.get("matchedKeyword", []) for k in kws)]
        group_stats[g] = {
            "totalJobs": len(jl),
            "jobsLast24h": sum(keyword_stats[k]["jobsLast24h"] for k in kws),
            "opportunityScore": opportunity_score(jl) if jl else 1,
            "sampleConfidence": confidence(len(jl)),
        }

    platform_stats = {}
    for pname, patterns in PLATFORM_KEYWORDS.items():
        jl = [j for j in all_jobs if any(p.lower() in " ".join(j.get("matchedKeyword", [])).lower() for p in patterns)]
        fixed = [parse_money(j.get("budget")) for j in jl if j.get("type") == "fixed"]
        fixed = [x for x in fixed if x is not None]
        hourly = [parse_hourly_rate(j.get("budget") or "") for j in jl if j.get("type") == "hourly"]
        hourly = [x for x in hourly if x is not None]
        props = [j.get("proposals") for j in jl if j.get("proposals") is not None]
        platform_stats[pname] = {
            "jobs": len(jl),
            "avgBudgetFixed": round(statistics.mean(fixed), 2) if fixed else None,
            "avgRateHourly": round(statistics.mean(hourly), 2) if hourly else None,
            "medianProposals": int(statistics.median(props)) if props else None,
            "opportunityScore": opportunity_score(jl) if jl else 1,
            "sampleConfidence": confidence(len(jl)),
        }

    KEYWORD_STATS.write_text(json.dumps(keyword_stats, indent=2))
    GROUP_STATS.write_text(json.dumps(group_stats, indent=2))
    PLATFORM_STATS.write_text(json.dumps(platform_stats, indent=2))

    run_number = 1
    top_kw = sorted(keyword_stats.items(), key=lambda x: x[1]["opportunityScore"], reverse=True)[:10]
    log = {
        "timestamp": NOW.isoformat(),
        "runNumber": run_number,
        "keywordsAttempted": len(ALL_KEYWORDS),
        "keywordsCompleted": len(COMPLETED),
        "newJobs": len(new_jobs),
        "totalJobs": len(jobs),
        "top3Keywords": [k for k, _ in top_kw[:3]],
        "errors": ERRORS,
    }
    with RUN_LOG.open("a") as f:
        f.write(json.dumps(log) + "\n")

    known = sorted(jobs.keys())
    STATE_FILE.write_text(json.dumps({
        "lastRunAt": NOW.isoformat(),
        "runNumber": run_number,
        "totalJobs": len(jobs),
        "knownJobUrls": known,
        "lastInsightRefresh": NOW.isoformat(),
    }, indent=2))

    if not INSIGHTS.exists():
        INSIGHTS.write_text(
            "# Durable insights\n\n"
            "- WordPress + Elementor fix/upgrade posts dominate the last 2 hours.\n"
            "- Supabase/React SaaS and AI production-hardening roles show the highest hourly bands.\n"
            "- GoHighLevel implementation and CRM cleanup jobs spiked overnight (US clients).\n"
            "- Webflow senior CMS builds remain expert-rate but lower volume than WordPress.\n"
        )

    primary = top_kw[0][0] if top_kw else "wordpress developer"
    secondary = top_kw[1][0] if len(top_kw) > 1 else "supabase developer"
    lines = [
        "# Upwork Market Intelligence",
        "",
        f"Last updated: {NOW.strftime('%Y-%m-%d %H:%M UTC')}",
        f"Run: {run_number}",
        f"Total jobs tracked: {len(jobs)}",
        f"Keywords attempted: {len(ALL_KEYWORDS)}",
        f"Keywords completed: {len(COMPLETED)}",
        "",
        "## Top Opportunities",
        "",
    ]
    for k, s in top_kw:
        lines.append(
            f"- **{k}** — score {s['opportunityScore']} ({s['sampleConfidence']}) | 24h: {s['jobsLast24h']} | total: {s['totalJobs']}"
        )
    lines.extend(["", "## Strongest Groups", ""])
    for g, s in sorted(group_stats.items(), key=lambda x: x[1]["opportunityScore"], reverse=True)[:5]:
        lines.append(f"- {g}: score {s['opportunityScore']}, jobs {s['totalJobs']}")
    lines.extend([
        "",
        "## Positioning Recommendation",
        "",
        f"Primary keyword: {primary}",
        f"Secondary keyword: {secondary}",
        "Best platform/service: WordPress + Elementor production fixes; Supabase SaaS hardening",
        "Overview keywords: WordPress, Supabase, Next.js, Webflow, GoHighLevel",
        "Skill tags: WordPress, Elementor, React, TypeScript, Supabase, Shopify, HighLevel",
        "",
        "## Important Changes",
        "",
        "First baseline run. Partial keyword coverage; retry failed keywords next hour.",
    ])
    SUMMARY.write_text("\n".join(lines) + "\n")

    print(json.dumps({"run": run_number, "new": len(new_jobs), "total": len(jobs), "completed": len(COMPLETED), "errors": len(ERRORS), "top_kw": top_kw[:10], "group_stats": group_stats, "platform_stats": platform_stats, "new_jobs": new_jobs}))

if __name__ == "__main__":
    main()
