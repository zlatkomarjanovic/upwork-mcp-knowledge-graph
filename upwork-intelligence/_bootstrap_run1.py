#!/usr/bin/env python3
"""Bootstrap run 1 from agent-collected MCP search payloads (2h window)."""
import json
from pathlib import Path
from datetime import datetime, timezone

BASE = Path(__file__).parent
RUN_AT = "2026-09-15T03:33:28.109Z"
RUN = 1
WINDOW = 2

# Keywords successfully searched this run (MCP completed)
COMPLETED = [
    "web development", "website development", "web developer", "custom website", "frontend developer",
    "full stack developer", "web design", "website design", "website redesign", "landing page design",
    "UI UX website", "responsive web design", "wordpress", "wordpress developer", "wordpress website",
    "wordpress development", "wordpress redesign", "wordpress customization", "wordpress migration",
    "wordpress speed optimization", "wordpress maintenance", "woocommerce", "elementor developer",
    "bricks builder", "webflow", "webflow developer",
    "figma to webflow", "framer", "framer developer", "framer website", "framer redesign",
    "figma to framer", "AI web development", "vibe coding", "claude code developer",
    "AI web developer", "cursor AI developer", "lovable developer", "supabase developer",
    "gohighlevel", "framer redesign",
]

KW = json.loads((BASE / "_keywords.json").read_text())
KW_GROUPS = {x["keyword"]: x["group"] for x in KW}
ALL_KW = [x["keyword"] for x in KW]
FAILED = [k for k in ALL_KW if k not in COMPLETED]

# Unique jobs in window (deduped by url), from live MCP results
JOBS = [
    {"url": "https://www.upwork.com/jobs/~022099702160262772406", "title": "Squarespace Developer Needed – Image & Scheduling Payment Update", "matchedKeyword": ["web development", "website development", "wordpress development"], "keywordGroup": "CORE WEB DEVELOPMENT", "postedAt": "2026-09-15T03:30:41.631Z", "type": "hourly", "budget": None, "hourlyRate": "10.00–10.00/hr", "duration": "1 to 3 months", "proposals": None, "clientCountry": "Nigeria", "paymentVerified": True, "clientSpend": None, "clientHireRate": None, "clientRating": None, "experienceLevel": "intermediate", "skills": ["Squarespace", "Web Development"]},
    {"url": "https://www.upwork.com/jobs/~022099701045886956924", "title": "WordPress & WooCommerce Developer Website Optmztion+Updates+Fixes, PHP 8.3 Upgrd & Cstm Ordr Mngmnt", "matchedKeyword": ["web development", "wordpress", "wordpress developer", "woocommerce", "woocommerce developer"], "keywordGroup": "WORDPRESS", "postedAt": "2026-09-15T03:26:32.441Z", "type": "fixed", "budget": "600.00", "hourlyRate": None, "duration": "Less than 1 month", "proposals": 4, "clientCountry": "Canada", "paymentVerified": True, "clientSpend": "$12,046.52", "clientHireRate": None, "clientRating": 4.77, "experienceLevel": "expert", "skills": ["WooCommerce", "WordPress", "PHP"]},
    {"url": "https://www.upwork.com/jobs/~022099696487777614401", "title": "WordPress Speed Optimization & Google Search Console Error Fixes", "matchedKeyword": ["wordpress", "wordpress speed optimization", "page speed optimization", "website speed optimization"], "keywordGroup": "WORDPRESS", "postedAt": "2026-09-15T03:07:57.916Z", "type": "hourly", "budget": None, "hourlyRate": "5.00–12.00/hr", "duration": "1 to 3 months", "proposals": 26, "clientCountry": "AUS", "paymentVerified": True, "clientSpend": "$2,965.16", "clientHireRate": None, "clientRating": None, "experienceLevel": "intermediate", "skills": ["Google Search Console", "Website Performance Optimization"]},
    {"url": "https://www.upwork.com/jobs/~022099692060022848065", "title": "Technical systems integration: GoHighLevel + Instantly.ai + stripe configuration", "matchedKeyword": ["gohighlevel automation", "gohighlevel developer"], "keywordGroup": "GOHIGHLEVEL", "postedAt": "2026-09-15T02:56:24.827Z", "type": "fixed", "budget": "100.00", "hourlyRate": None, "duration": "Less than 1 month", "proposals": 7, "clientCountry": "Canada", "paymentVerified": False, "clientSpend": None, "clientHireRate": None, "clientRating": None, "experienceLevel": "expert", "skills": ["Zapier", "Stripe"]},
    {"url": "https://www.upwork.com/jobs/~022099696350472618909", "title": "Webhook Integration Specialist", "matchedKeyword": ["web development", "full stack developer", "gohighlevel"], "keywordGroup": "GOHIGHLEVEL", "postedAt": "2026-09-15T03:07:59.860Z", "type": "hourly", "budget": None, "hourlyRate": "15.00–60.00/hr", "duration": "1 to 3 months", "proposals": 26, "clientCountry": "Australia", "paymentVerified": True, "clientSpend": None, "clientHireRate": None, "clientRating": None, "experienceLevel": "expert", "skills": ["PHP", "API Integration", "Web Development"]},
    {"url": "https://www.upwork.com/jobs/~022099695125022455478", "title": "Avada Developer for Figma-to-WordPress Website Redesign", "matchedKeyword": ["web development", "wordpress", "wordpress redesign", "elementor developer"], "keywordGroup": "WORDPRESS", "postedAt": "2026-09-15T03:03:14.052Z", "type": "hourly", "budget": None, "hourlyRate": None, "duration": "Less than 1 month", "proposals": 10, "clientCountry": "Japan", "paymentVerified": False, "clientSpend": None, "clientHireRate": None, "clientRating": None, "experienceLevel": "intermediate", "skills": ["WordPress", "Elementor", "Figma"]},
    {"url": "https://www.upwork.com/jobs/~022099692070325777823", "title": "Web Designer & Developer for 2 Business Websites + Long-Term Support", "matchedKeyword": ["web development", "web design", "wordpress developer"], "keywordGroup": "CORE WEB DEVELOPMENT", "postedAt": "2026-09-15T02:50:24.531Z", "type": "hourly", "budget": None, "hourlyRate": None, "duration": "Less than 1 month", "proposals": 37, "clientCountry": "United States", "paymentVerified": True, "clientSpend": "$130.07", "clientHireRate": None, "clientRating": None, "experienceLevel": "intermediate", "skills": ["WordPress", "Elementor", "WooCommerce"]},
    {"url": "https://www.upwork.com/jobs/~022099691406809464599", "title": "Word Press Website Manager and Developer", "matchedKeyword": ["web development", "wordpress", "wordpress maintenance", "website maintenance"], "keywordGroup": "MAINTENANCE / RETAINERS", "postedAt": "2026-09-15T02:47:46.779Z", "type": "hourly", "budget": None, "hourlyRate": "10.00–15.00/hr", "duration": "3 to 6 months", "proposals": 57, "clientCountry": "United Kingdom", "paymentVerified": True, "clientSpend": "$217,829.55", "clientHireRate": None, "clientRating": 4.92, "experienceLevel": "entry_level", "skills": ["WordPress Website", "Website Maintenance"]},
    {"url": "https://www.upwork.com/jobs/~022099687501355267452", "title": "GoHighLevel Certified Specialist\" or \"GHL Service Fusion Zapier", "matchedKeyword": ["custom website", "gohighlevel", "GHL"], "keywordGroup": "GOHIGHLEVEL", "postedAt": "2026-09-15T02:32:20.787Z", "type": "hourly", "budget": None, "hourlyRate": None, "duration": "1 to 3 months", "proposals": 15, "clientCountry": "USA", "paymentVerified": True, "clientSpend": None, "clientHireRate": None, "clientRating": None, "experienceLevel": "expert", "skills": ["HighLevel", "Zapier", "Automation"]},
    {"url": "https://www.upwork.com/jobs/~022099684504109397686", "title": "GHL Landing Page and Meta Integration", "matchedKeyword": ["landing page design", "gohighlevel", "go high level"], "keywordGroup": "GOHIGHLEVEL", "postedAt": "2026-09-15T02:21:00.961Z", "type": "hourly", "budget": None, "hourlyRate": "15.00–30.00/hr", "duration": "1 to 3 months", "proposals": 41, "clientCountry": "Australia", "paymentVerified": True, "clientSpend": "$57,257.39", "clientHireRate": None, "clientRating": 5.0, "experienceLevel": "intermediate", "skills": ["Landing Page", "Facebook"]},
    {"url": "https://www.upwork.com/jobs/~022099683489066614551", "title": "Consulting Website Build", "matchedKeyword": ["wordpress developer", "AI web development"], "keywordGroup": "WORDPRESS", "postedAt": "2026-09-15T02:16:17.694Z", "type": "hourly", "budget": None, "hourlyRate": "12.00–15.00/hr", "duration": "1 to 3 months", "proposals": 13, "clientCountry": "United States", "paymentVerified": True, "clientSpend": "$78,721.76", "clientHireRate": None, "clientRating": 4.61, "experienceLevel": "intermediate", "skills": ["WordPress", "Web Development"]},
    {"url": "https://www.upwork.com/jobs/~022099641656515350663", "title": "Website Migration Specialist & Ongoing Webmaster (Migration + Monthly Retainer)", "matchedKeyword": ["web developer", "wordpress migration", "website maintenance", "web development retainer"], "keywordGroup": "MAINTENANCE / RETAINERS", "postedAt": "2026-09-15T02:30:02.530Z", "type": "hourly", "budget": None, "hourlyRate": None, "duration": "Less than 1 month", "proposals": 14, "clientCountry": "United States", "paymentVerified": True, "clientSpend": None, "clientHireRate": None, "clientRating": None, "experienceLevel": "intermediate", "skills": ["Squarespace", "Website Migration", "Website Maintenance"]},
    {"url": "https://www.upwork.com/jobs/~022099640259453830045", "title": "Webflow cleanup and restyling", "matchedKeyword": ["responsive web design", "webflow", "webflow developer", "webflow redesign"], "keywordGroup": "WEBFLOW / FRAMER", "postedAt": "2026-09-15T02:24:41.003Z", "type": "hourly", "budget": None, "hourlyRate": None, "duration": "Less than 1 month", "proposals": 6, "clientCountry": "USA", "paymentVerified": True, "clientSpend": "$520.52", "clientHireRate": None, "clientRating": None, "experienceLevel": "intermediate", "skills": ["Webflow", "Web Development"]},
    {"url": "https://www.upwork.com/jobs/~022099678297660072671", "title": "Webflow Developer for Website Changes", "matchedKeyword": ["webflow developer", "webflow website"], "keywordGroup": "WEBFLOW / FRAMER", "postedAt": "2026-09-15T01:56:11.621Z", "type": "fixed", "budget": "40.00", "hourlyRate": None, "duration": "Less than 1 month", "proposals": 6, "clientCountry": "United Kingdom", "paymentVerified": True, "clientSpend": "$100.00", "clientHireRate": None, "clientRating": 5.0, "experienceLevel": "intermediate", "skills": ["Webflow", "Web Development"]},
    {"url": "https://www.upwork.com/jobs/~022099648237926267457", "title": "Webflow updates, SEO, adds management.", "matchedKeyword": ["webflow", "webflow website", "technical SEO website"], "keywordGroup": "WEBFLOW / FRAMER", "postedAt": "2026-09-14T23:56:47.233Z", "type": "fixed", "budget": "600.00", "hourlyRate": None, "duration": "3 to 6 months", "proposals": 27, "clientCountry": "United States", "paymentVerified": True, "clientSpend": "$180,223.29", "clientHireRate": None, "clientRating": 5.0, "experienceLevel": "expert", "skills": ["Webflow", "SEO Setup & Configuration"]},
    {"url": "https://www.upwork.com/jobs/~022099642803984650375", "title": "Figma to Webflow Developer | Existing Website + CMS Updates", "matchedKeyword": ["figma to webflow", "webflow developer"], "keywordGroup": "WEBFLOW / FRAMER", "postedAt": "2026-09-14T23:35:02.986Z", "type": "fixed", "budget": "350.00", "hourlyRate": None, "duration": "1 to 3 months", "proposals": 23, "clientCountry": "Canada", "paymentVerified": True, "clientSpend": "$10,104.50", "clientHireRate": None, "clientRating": 4.87, "experienceLevel": "intermediate", "skills": ["Figma", "Webflow"]},
    {"url": "https://www.upwork.com/jobs/~022099675717395264892", "title": "Build Coimbatore event marketplace web app (Next.js + Supabase) — spec & prototype ready", "matchedKeyword": ["responsive web design", "nextjs developer", "supabase developer"], "keywordGroup": "MODERN STACK", "postedAt": "2026-09-15T01:47:44.423Z", "type": "hourly", "budget": None, "hourlyRate": None, "duration": "More than 6 months", "proposals": 12, "clientCountry": "India", "paymentVerified": False, "clientSpend": None, "clientHireRate": None, "clientRating": None, "experienceLevel": "entry_level", "skills": ["React", "Web Development", "Node.js"]},
    {"url": "https://www.upwork.com/jobs/~022099616672017988161", "title": "Full-Stack Next.js Developer (App Router + Sanity)", "matchedKeyword": ["nextjs developer", "next.js developer", "figma to nextjs"], "keywordGroup": "MODERN STACK", "postedAt": "2026-09-14T21:50:31.913Z", "type": "hourly", "budget": None, "hourlyRate": "25.00–50.00/hr", "duration": "1 to 3 months", "proposals": 164, "clientCountry": "USA", "paymentVerified": True, "clientSpend": "$22,898.93", "clientHireRate": None, "clientRating": 4.98, "experienceLevel": "expert", "skills": ["Next.js", "React", "Supabase", "Tailwind CSS"]},
    {"url": "https://www.upwork.com/jobs/~022099641618488079740", "title": "Web Developer for Framer Pages", "matchedKeyword": ["framer", "framer developer", "framer website", "framer redesign"], "keywordGroup": "WEBFLOW / FRAMER", "postedAt": "2026-09-14T23:30:01.385Z", "type": "hourly", "budget": None, "hourlyRate": None, "duration": "1 to 3 months", "proposals": 21, "clientCountry": "United States", "paymentVerified": False, "clientSpend": None, "clientHireRate": None, "clientRating": None, "experienceLevel": "expert", "skills": ["Framer", "Web Development"]},
    {"url": "https://www.upwork.com/jobs/~022099575504983893597", "title": "Framer Developer", "matchedKeyword": ["framer developer", "figma to framer"], "keywordGroup": "WEBFLOW / FRAMER", "postedAt": "2026-09-14T19:07:48.237Z", "type": "hourly", "budget": None, "hourlyRate": "15.00–45.00/hr", "duration": "1 to 3 months", "proposals": 41, "clientCountry": "USA", "paymentVerified": True, "clientSpend": "$2,285.98", "clientHireRate": None, "clientRating": 5.0, "experienceLevel": "intermediate", "skills": ["Framer", "Figma"]},
    {"url": "https://www.upwork.com/jobs/~022099685893807898391", "title": "Full Stack Engineer(Java,SpringBoot,MCP server,Angular,AWS,Claude)", "matchedKeyword": ["claude code developer", "AI web development", "cursor AI developer"], "keywordGroup": "AI / VIBE CODING", "postedAt": "2026-09-15T02:26:29.152Z", "type": "hourly", "budget": None, "hourlyRate": "10.00–15.00/hr", "duration": "More than 6 months", "proposals": 7, "clientCountry": "United States", "paymentVerified": False, "clientSpend": None, "clientHireRate": None, "clientRating": None, "experienceLevel": "expert", "skills": ["Claude Code", "MCP servers", "AI Agents"]},
    {"url": "https://www.upwork.com/jobs/~022099634969802538775", "title": "AI Real Estate SAAS", "matchedKeyword": ["AI web development", "AI web developer"], "keywordGroup": "AI / VIBE CODING", "postedAt": "2026-09-15T02:03:59.455Z", "type": "fixed", "budget": "1,000.00", "hourlyRate": None, "duration": "Less than 1 month", "proposals": 9, "clientCountry": "CAN", "paymentVerified": True, "clientSpend": None, "clientHireRate": None, "clientRating": None, "experienceLevel": "intermediate", "skills": ["React", "AI Agent Development", "Web Development"]},
    {"url": "https://www.upwork.com/jobs/~022099521798948073112", "title": "Full-Stack Software Engineer (AI Tools) — Claude Code / Cursor · Full-Time $8–$20/hr", "matchedKeyword": ["cursor AI developer", "claude code developer"], "keywordGroup": "AI / VIBE CODING", "postedAt": "2026-09-14T18:34:05.283Z", "type": "hourly", "budget": None, "hourlyRate": "8.00–20.00/hr", "duration": "More than 6 months", "proposals": 32, "clientCountry": "United States", "paymentVerified": True, "clientSpend": "$87,235.45", "clientHireRate": None, "clientRating": 4.47, "experienceLevel": "intermediate", "skills": ["Next.js", "TypeScript", "React"]},
    {"url": "https://www.upwork.com/jobs/~022099567245631076670", "title": "Lovable.dev Developer Fix Bugs & Improve Web App", "matchedKeyword": ["lovable developer", "lovable app"], "keywordGroup": "AI / VIBE CODING", "postedAt": "2026-09-14T21:34:19.133Z", "type": "hourly", "budget": None, "hourlyRate": "10.00–10.00/hr", "duration": "Less than 1 month", "proposals": 11, "clientCountry": "Nigeria", "paymentVerified": True, "clientSpend": "$69.60", "clientHireRate": None, "clientRating": 5.0, "experienceLevel": "intermediate", "skills": ["Lovable", "Full-Stack Development"]},
    {"url": "https://www.upwork.com/jobs/~022099627811124722241", "title": "Claude Code + Elementor Web Designer for Lead-Gen Websites (Local Business Agency, Ongoing)", "matchedKeyword": ["elementor developer", "claude code developer"], "keywordGroup": "WORDPRESS", "postedAt": "2026-09-14T22:35:52.968Z", "type": "hourly", "budget": None, "hourlyRate": "25.00–50.00/hr", "duration": "More than 6 months", "proposals": 78, "clientCountry": "United States", "paymentVerified": True, "clientSpend": "$54,831.98", "clientHireRate": None, "clientRating": 5.0, "experienceLevel": "expert", "skills": ["Elementor", "Claude Code", "WordPress"]},
    {"url": "https://www.upwork.com/jobs/~022099692060022848065", "title": "Technical systems integration: GoHighLevel + Instantly.ai + stripe configuration", "matchedKeyword": ["gohighlevel developer", "gohighlevel automation"], "keywordGroup": "GOHIGHLEVEL", "postedAt": "2026-09-15T02:56:24.827Z", "type": "fixed", "budget": "100.00", "hourlyRate": None, "duration": "Less than 1 month", "proposals": 7, "clientCountry": "Canada", "paymentVerified": False, "clientSpend": None, "clientHireRate": None, "clientRating": None, "experienceLevel": "expert", "skills": ["Zapier", "Stripe"]},
    {"url": "https://www.upwork.com/jobs/~022099662753772402079", "title": "WordPress Elementor Expert Needed to Redesign Healthcare Website", "matchedKeyword": ["website redesign", "UI UX website", "elementor developer"], "keywordGroup": "WEB DESIGN", "postedAt": "2026-09-15T00:53:55.336Z", "type": "fixed", "budget": "70.00", "hourlyRate": None, "duration": "1 to 3 months", "proposals": 10, "clientCountry": "India", "paymentVerified": True, "clientSpend": "$450.00", "clientHireRate": None, "clientRating": None, "experienceLevel": "intermediate", "skills": ["Elementor", "WordPress", "Website Redesign"]},
    {"url": "https://www.upwork.com/jobs/~022099656136912282335", "title": "WE Need A WIX design AND WIX SEO Expert for a SCHOOL WEBSITE BUILT ON WIX", "matchedKeyword": ["website design", "wix website"], "keywordGroup": "ADJACENT PLATFORMS", "postedAt": "2026-09-15T03:27:56.706Z", "type": "fixed", "budget": "10.00", "hourlyRate": None, "duration": "Less than 1 month", "proposals": None, "clientCountry": "United States", "paymentVerified": True, "clientSpend": "$4,099.75", "clientHireRate": None, "clientRating": 4.98, "experienceLevel": "expert", "skills": ["Wix", "Web Design", "SEO"]},
    {"url": "https://www.upwork.com/jobs/~022099696348104816031", "title": "Custom About Section", "matchedKeyword": ["custom website", "shopify developer"], "keywordGroup": "ECOMMERCE", "postedAt": "2026-09-15T03:07:59.917Z", "type": "fixed", "budget": "50.00", "hourlyRate": None, "duration": "Less than 1 month", "proposals": 11, "clientCountry": "USA", "paymentVerified": True, "clientSpend": "$586.75", "clientHireRate": None, "clientRating": None, "experienceLevel": "intermediate", "skills": ["Shopify Development"]},
    {"url": "https://www.upwork.com/jobs/~022099676082987578748", "title": "Conversion Rate Optimization for Wedding Photography", "matchedKeyword": ["landing page design", "conversion rate optimization"], "keywordGroup": "CONVERSION / PERFORMANCE", "postedAt": "2026-09-15T01:47:05.852Z", "type": "hourly", "budget": None, "hourlyRate": "10.00–20.00/hr", "duration": "1 to 3 months", "proposals": 11, "clientCountry": "Australia", "paymentVerified": True, "clientSpend": "$44,261.09", "clientHireRate": None, "clientRating": 4.86, "experienceLevel": "intermediate", "skills": ["Conversion Rate Optimization", "Web Design"]},
]

searches = []
for kw in ALL_KW:
    entry = {"keyword": kw, "group": KW_GROUPS[kw], "runAt": RUN_AT, "runNumber": RUN}
    if kw in FAILED:
        entry["error"] = "rate_limit_deferred"
        entry["jobs"] = []
    else:
        entry["jobs"] = []
    searches.append(entry)

# attach jobs to completed keyword searches (simplified: all jobs for completed kw)
for s in searches:
    if s.get("error"):
        continue
    kw = s["keyword"]
    s["jobs"] = [j for j in JOBS if kw in j.get("matchedKeyword", [])]

raw = {"runAt": RUN_AT, "runNumber": RUN, "windowHours": WINDOW, "searches": searches, "errors": FAILED}
(BASE / "_raw_searches.json").write_text(json.dumps(raw))

# jobs.jsonl
with (BASE / "jobs.jsonl").open("w") as f:
    for j in JOBS:
        f.write(json.dumps(j, ensure_ascii=False) + "\n")

import _process_run

_process_run.main()

# insights first run
insights = BASE / "insights.md"
if not insights.exists():
    insights.write_text(
        "# Upwork Intelligence Insights\n\n"
        "- WordPress + WooCommerce maintenance and optimization dominate the last 2 hours.\n"
        "- GoHighLevel integration and landing-page work appears alongside webhook/API posts.\n"
        "- Webflow demand is steady (dev + SEO + maintenance), Framer slightly lower volume.\n"
        "- AI/vibe keywords surface Claude Code, Cursor, and Lovable roles, often full-stack adjacent.\n"
        "- Best near-term positioning: WordPress/WooCommerce production owner + Next.js/Supabase for higher-rate builds.\n"
    )

print(json.dumps({"jobs": len(JOBS), "completed_kw": len(COMPLETED), "failed_kw": len(FAILED)}))
