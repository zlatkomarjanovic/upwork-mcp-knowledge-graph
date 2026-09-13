#!/usr/bin/env python3
"""Build jobs.jsonl + search batch from collected MCP results (run 1)."""
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

BASE = Path(__file__).parent
RUN_AT = datetime(2026, 9, 13, 12, 32, 43, tzinfo=timezone.utc)
CUTOFF = RUN_AT - timedelta(hours=2)

ALL_KEYWORDS = [
    "web development", "website development", "web developer", "custom website", "frontend developer", "full stack developer",
    "web design", "website design", "website redesign", "landing page design", "UI UX website", "responsive web design",
    "wordpress", "wordpress developer", "wordpress website", "wordpress development", "wordpress redesign", "wordpress customization",
    "wordpress migration", "wordpress speed optimization", "wordpress maintenance", "woocommerce", "elementor developer", "bricks builder",
    "webflow", "webflow developer", "webflow website", "webflow redesign", "figma to webflow", "framer", "framer developer",
    "framer website", "framer redesign", "figma to framer",
    "AI web development", "AI web developer", "vibe coding", "claude code developer", "cursor AI developer", "lovable developer",
    "lovable app", "bolt developer", "bolt.new", "v0 developer", "v0 vercel", "replit developer", "supabase developer",
    "AI agent integration website",
    "gohighlevel", "go high level", "GHL", "gohighlevel developer", "gohighlevel website", "gohighlevel funnel",
    "gohighlevel automation", "gohighlevel CRM",
    "squarespace website", "wix website", "wix studio", "bubble developer",
    "nextjs developer", "next.js developer", "nextjs website", "react developer", "figma to nextjs", "tailwind developer",
    "astro developer", "sanity CMS",
    "ecommerce website", "ecommerce developer", "shopify developer", "shopify website", "woocommerce developer",
    "shopware", "shopware developer", "shopware 6", "headless ecommerce",
    "website maintenance", "website maintenance monthly", "website support ongoing", "website management ongoing",
    "wordpress support retainer", "webflow maintenance", "shopify maintenance", "ongoing web developer", "web development retainer",
    "conversion rate optimization", "landing page optimization", "website audit", "core web vitals", "page speed optimization",
    "website speed optimization", "technical SEO website",
]

SEARCHED = {
    "web development", "website development", "web developer", "custom website", "frontend developer", "full stack developer",
    "web design", "website design", "website redesign", "landing page design", "responsive web design", "UI UX website",
    "wordpress", "wordpress developer", "wordpress website", "wordpress development", "woocommerce",
    "webflow developer", "framer developer", "AI web development", "shopify developer", "nextjs developer",
    "gohighlevel developer", "website maintenance", "page speed optimization", "lovable developer", "vibe coding",
    "react developer", "astro developer", "ecommerce website",
}

FAILED = [k for k in ALL_KEYWORDS if k not in SEARCHED]

# In-window jobs (2h) from MCP run — unique by url base
JOBS = [
    {"url": "https://www.upwork.com/jobs/~022099113395294415693", "title": "WordPress Developer Needed – Diagnose & Fix a Bug", "postedAt": "2026-09-13T12:31:41.958Z", "type": "fixed", "budget": "200.00", "duration": "Less than 1 month", "proposals": 1, "clientCountry": "Pakistan", "paymentVerified": True, "clientSpend": "$275.00", "clientRating": 5, "experienceLevel": "expert", "skills": ["WordPress Bug Fix", "WordPress Development"], "kw": ["wordpress", "wordpress developer", "wordpress development"]},
    {"url": "https://www.upwork.com/jobs/~022099107957886790477", "title": "WordPress Real Estate Website Developer Needed, Premium Design + Ongoing Updates", "postedAt": "2026-09-13T12:09:21.302Z", "type": "fixed", "budget": "600.00", "duration": "1 to 3 months", "proposals": 38, "clientCountry": "USA", "paymentVerified": True, "clientSpend": "$120.00", "clientRating": 5, "experienceLevel": "expert", "skills": ["WordPress", "Web Development", "Web Design"], "kw": ["wordpress", "wordpress developer", "wordpress website", "web development", "website development"]},
    {"url": "https://www.upwork.com/jobs/~022099110124397841913", "title": "Senior ai ecommerce developer website", "postedAt": "2026-09-13T12:18:39.357Z", "type": "fixed", "budget": "300.00", "duration": "1 to 3 months", "proposals": 2, "clientCountry": "ISR", "paymentVerified": True, "clientSpend": "$135.00", "clientRating": 4.44, "experienceLevel": "intermediate", "skills": ["Ecommerce Website", "Claude Code", "Shopify", "Web Development"], "kw": ["AI web development", "AI web developer", "claude code developer", "ecommerce website", "shopify developer", "web development"]},
    {"url": "https://www.upwork.com/jobs/~022099107436534218888", "title": "Website Developer Needed | Modern, Professional Business Website", "postedAt": "2026-09-13T12:07:30.899Z", "type": "fixed", "budget": "360.00", "duration": "1 to 3 months", "proposals": 27, "clientCountry": "GBR", "paymentVerified": True, "clientSpend": "$66.79", "clientRating": 5, "experienceLevel": "expert", "skills": ["Web Development", "WordPress", "Web Design"], "kw": ["website development", "web developer", "web development"]},
    {"url": "https://www.upwork.com/jobs/~022099106685552242328", "title": "Website & Mobile Developer / UI Designer", "postedAt": "2026-09-13T12:04:45.862Z", "type": "fixed", "budget": "30.00", "duration": "3 to 6 months", "proposals": 14, "clientCountry": "Canada", "paymentVerified": True, "clientSpend": "$3,515.32", "clientRating": 4.75, "experienceLevel": "expert", "skills": ["Web Development"], "kw": ["web development", "web developer", "UI UX website"]},
    {"url": "https://www.upwork.com/jobs/~022099110819854989630", "title": "Need Full stack Developer", "postedAt": "2026-09-13T12:21:04.825Z", "type": "hourly", "budget": None, "duration": "1 to 3 months", "proposals": 14, "clientCountry": "United States", "paymentVerified": True, "clientSpend": "$39,349.66", "clientRating": 4.49, "experienceLevel": "expert", "skills": ["Web Development", "WordPress", "Shopify"], "kw": ["full stack developer", "web development", "ecommerce website"]},
    {"url": "https://www.upwork.com/jobs/~022099104496700407944", "title": "Full-Stack Automations Developer (Node/TS/React) for Ecom Brand - Long-Term", "postedAt": "2026-09-13T11:55:52.816Z", "type": "fixed", "budget": "3,000.00", "duration": "More than 6 months", "proposals": 49, "clientCountry": "SWE", "paymentVerified": True, "clientSpend": "$3,585.87", "clientRating": None, "experienceLevel": "expert", "skills": ["Node.js", "TypeScript", "React", "AI Agent Development"], "kw": ["full stack developer", "react developer", "ecommerce developer"]},
    {"url": "https://www.upwork.com/jobs/~022099107692699684618", "title": "Zoho CRM / Books / Inventory ↔ WooCommerce Integration Fixes", "postedAt": "2026-09-13T12:09:14.889Z", "type": "fixed", "budget": "60.00", "duration": "Less than 1 month", "proposals": 2, "clientCountry": "Australia", "paymentVerified": True, "clientSpend": None, "clientRating": None, "experienceLevel": "intermediate", "skills": ["Zoho CRM", "WooCommerce"], "kw": ["woocommerce", "woocommerce developer"]},
    {"url": "https://www.upwork.com/jobs/~022099082233137643656", "title": "Long-term Collaboration: UI/UX & Frontend Developer (Ex-YU) – Urgent: 2 Custom Sites + Print", "postedAt": "2026-09-13T11:35:13.453Z", "type": "fixed", "budget": "160.00", "duration": "1 to 3 months", "proposals": 5, "clientCountry": "Germany", "paymentVerified": True, "clientSpend": "$1,957.90", "clientRating": 4.12, "experienceLevel": "intermediate", "skills": ["Next.js", "Front-End Development", "Responsive Design"], "kw": ["frontend developer", "custom website", "nextjs developer", "UI UX website"]},
    {"url": "https://www.upwork.com/jobs/~022099089886756782216", "title": "Senior Astro & TypeScript Frontend Developer (Jamstack / Headless E-Commerce)", "postedAt": "2026-09-13T10:58:08.089Z", "type": "hourly", "budget": "25.00–47.00/hr", "duration": "More than 6 months", "proposals": 31, "clientCountry": "Switzerland", "paymentVerified": True, "clientSpend": "$158,538.12", "clientRating": 4.45, "experienceLevel": "expert", "skills": ["TypeScript", "React", "Tailwind CSS"], "kw": ["astro developer", "headless ecommerce", "frontend developer", "react developer"]},
    {"url": "https://www.upwork.com/jobs/~022099095668926522973", "title": "Web designer for a 9-page company site (design only). Strategy/reference research complete.", "postedAt": "2026-09-13T11:26:06.157Z", "type": "hourly", "budget": None, "duration": "1 to 3 months", "proposals": 13, "clientCountry": "United States", "paymentVerified": True, "clientSpend": "$14,794.12", "clientRating": 4.75, "experienceLevel": "intermediate", "skills": ["Webflow", "Web Design", "Figma to Webflow Plugin"], "kw": ["web design", "webflow", "figma to webflow", "website design"]},
    {"url": "https://www.upwork.com/jobs/~022099101459050999448", "title": "Website Design and Build for Real Estate and Construction", "postedAt": "2026-09-13T11:44:04.085Z", "type": "hourly", "budget": "15.00–30.00/hr", "duration": "1 to 3 months", "proposals": 59, "clientCountry": "USA", "paymentVerified": True, "clientSpend": "$14,293.31", "clientRating": 4.81, "experienceLevel": "intermediate", "skills": ["Web Design", "WordPress", "Web Development"], "kw": ["website design", "web design", "web development"]},
    {"url": "https://www.upwork.com/jobs/~022099094558802939658", "title": "Squarespace Website Developer, Redesign & SEO Optimization for Hair Business", "postedAt": "2026-09-13T11:16:56.283Z", "type": "fixed", "budget": "10.00", "duration": "Less than 1 month", "proposals": 2, "clientCountry": "United States", "paymentVerified": True, "clientSpend": "$1,892.52", "clientRating": 4.99, "experienceLevel": "intermediate", "skills": ["Squarespace", "Website Redesign", "SEO Setup"], "kw": ["website redesign", "squarespace website", "technical SEO website"]},
    {"url": "https://www.upwork.com/jobs/~022099084351691607545", "title": "Full-Stack Web Developer + AI Developer — Long-Term Opportunity", "postedAt": "2026-09-13T10:36:02.763Z", "type": "hourly", "budget": "15.00–35.00/hr", "duration": "More than 6 months", "proposals": 37, "clientCountry": "MAR", "paymentVerified": False, "clientSpend": None, "clientRating": None, "experienceLevel": "intermediate", "skills": ["React", "Node.js", "JavaScript"], "kw": ["full stack developer", "AI web development", "web development"]},
    {"url": "https://www.upwork.com/jobs/~022099076974086950666", "title": "Squarespace Designer/Developer with availability this Week. Clinic Website", "postedAt": "2026-09-13T10:06:50.031Z", "type": "hourly", "budget": "10.00–20.00/hr", "duration": "1 to 3 months", "proposals": 11, "clientCountry": "Australia", "paymentVerified": True, "clientSpend": None, "clientRating": None, "experienceLevel": "intermediate", "skills": ["Squarespace", "Website Redesign"], "kw": ["squarespace website", "website design", "web design"]},
    {"url": "https://www.upwork.com/jobs/~022099076788113746765", "title": "Web Developer needed: Migrate ecom website to Shopify", "postedAt": "2026-09-13T10:05:53.056Z", "type": "fixed", "budget": "50.00", "duration": "Less than 1 month", "proposals": 21, "clientCountry": "United States", "paymentVerified": True, "clientSpend": "$376.88", "clientRating": 5, "experienceLevel": "intermediate", "skills": ["Shopify", "Web Development"], "kw": ["shopify developer", "ecommerce website", "web developer"]},
    {"url": "https://www.upwork.com/jobs/~022099084309341720057", "title": "Website and app design", "postedAt": "2026-09-13T11:40:11.405Z", "type": "fixed", "budget": "8,000.00", "duration": "1 to 3 months", "proposals": 24, "clientCountry": "USA", "paymentVerified": True, "clientSpend": None, "clientRating": None, "experienceLevel": "entry_level", "skills": ["Custom Web Design"], "kw": ["web design", "website design", "AI web development"]},
    {"url": "https://www.upwork.com/jobs/~022099064829143857470", "title": "To fix a wordpress website issue", "postedAt": "2026-09-13T09:18:27.870Z", "type": "fixed", "budget": "5.00", "duration": "3 to 6 months", "proposals": 13, "clientCountry": "India", "paymentVerified": True, "clientSpend": "$20,520.53", "clientRating": 4.98, "experienceLevel": "intermediate", "skills": ["WordPress Bug Fix"], "kw": ["wordpress", "wordpress website", "website maintenance"]},
    {"url": "https://www.upwork.com/jobs/~022099063155060453016", "title": "Fast redesign of wordpress site", "postedAt": "2026-09-13T09:13:25.397Z", "type": "hourly", "budget": None, "duration": "1 to 3 months", "proposals": 17, "clientCountry": "France", "paymentVerified": False, "clientSpend": None, "clientRating": None, "experienceLevel": "intermediate", "skills": ["WordPress", "Web Development"], "kw": ["wordpress", "website redesign", "wordpress redesign"]},
    {"url": "https://www.upwork.com/jobs/~022099098032208162456", "title": "Full-Stack Developer Needed for Interactive Video Lead Funnel", "postedAt": "2026-09-13T11:30:17.901Z", "type": "fixed", "budget": "20.00", "duration": "1 to 3 months", "proposals": 7, "clientCountry": "Canada", "paymentVerified": False, "clientSpend": None, "clientRating": None, "experienceLevel": "intermediate", "skills": ["React", "JavaScript", "Tailwind CSS"], "kw": ["full stack developer", "react developer", "landing page design"]},
    {"url": "https://www.upwork.com/jobs/~022099043013637934858", "title": "Laravel/Next.js Developer for Secure Cloudflare Stream Integration", "postedAt": "2026-09-13T07:52:05.130Z", "type": "hourly", "budget": None, "duration": "Less than 1 month", "proposals": 33, "clientCountry": "United States", "paymentVerified": True, "clientSpend": None, "clientRating": None, "experienceLevel": "intermediate", "skills": ["Next.js", "Laravel", "React"], "kw": ["nextjs developer", "next.js developer", "react developer"]},
    {"url": "https://www.upwork.com/jobs/~022099045351731411262", "title": "Shopify Expert for Store Development and Complete Setup A to Z", "postedAt": "2026-09-13T08:01:10.951Z", "type": "hourly", "budget": "3.00–3.00/hr", "duration": "3 to 6 months", "proposals": 9, "clientCountry": "United States", "paymentVerified": True, "clientSpend": "$7,602.11", "clientRating": 5, "experienceLevel": "intermediate", "skills": ["Shopify Development"], "kw": ["shopify developer", "shopify website", "ecommerce website"]},
    {"url": "https://www.upwork.com/jobs/~022098965795490834013", "title": "Shopify Website Developer + Digital Brand Launch for Custom Suit Company", "postedAt": "2026-09-13T05:01:41.793Z", "type": "fixed", "budget": "2,000.00", "duration": "1 to 3 months", "proposals": 31, "clientCountry": "United States", "paymentVerified": True, "clientSpend": None, "clientRating": None, "experienceLevel": "expert", "skills": ["Shopify Development", "Ecommerce Website Development"], "kw": ["shopify developer", "shopify website", "ecommerce website"]},
    {"url": "https://www.upwork.com/jobs/~022099015167825645322", "title": "Shopify Developer Needed to Code Figma Design 1:1 (Mobile-First, ~ 10 Pages)", "postedAt": "2026-09-13T06:01:26.663Z", "type": "hourly", "budget": None, "duration": "1 to 3 months", "proposals": 6, "clientCountry": "USA", "paymentVerified": True, "clientSpend": "$100.00", "clientRating": 5, "experienceLevel": "expert", "skills": ["Shopify Development", "Shopify Website Design"], "kw": ["shopify developer", "shopify website"]},
    {"url": "https://www.upwork.com/jobs/~022099037281347223688", "title": "Web Developer, Simple Logo Designer for Personal Brand Astrology Site (Squarespace or WordPress)", "postedAt": "2026-09-13T07:29:12.809Z", "type": "fixed", "budget": "1,000.00", "duration": "1 to 3 months", "proposals": 24, "clientCountry": "United States", "paymentVerified": False, "clientSpend": None, "clientRating": None, "experienceLevel": "intermediate", "skills": ["Squarespace", "WordPress Website Design"], "kw": ["wordpress developer", "squarespace website", "web developer"]},
    {"url": "https://www.upwork.com/jobs/~022099052122945168989", "title": "Brand Identity and Website Design", "postedAt": "2026-09-13T08:27:52.086Z", "type": "hourly", "budget": "15.00–20.00/hr", "duration": "1 to 3 months", "proposals": 4, "clientCountry": "India", "paymentVerified": False, "clientSpend": None, "clientRating": None, "experienceLevel": "intermediate", "skills": ["Web Design", "Brand Identity"], "kw": ["web design", "website design"]},
    {"url": "https://www.upwork.com/jobs/~022099064172810778942", "title": "Design and development of a 5-page website", "postedAt": "2026-09-13T09:16:02.765Z", "type": "hourly", "budget": "15.00–25.00/hr", "duration": "Less than 1 month", "proposals": 64, "clientCountry": "United Kingdom", "paymentVerified": True, "clientSpend": None, "clientRating": None, "experienceLevel": "intermediate", "skills": ["WordPress Website Design", "Web Design"], "kw": ["wordpress developer", "web design", "website design"]},
    {"url": "https://www.upwork.com/jobs/~022099083777571081721", "title": "Senior React Native / Expo Developer", "postedAt": "2026-09-13T10:33:52.932Z", "type": "hourly", "budget": "20.00–50.00/hr", "duration": "1 to 3 months", "proposals": 42, "clientCountry": "United Kingdom", "paymentVerified": True, "clientSpend": "$2,260.66", "clientRating": 4.93, "experienceLevel": "expert", "skills": ["React Native", "React"], "kw": ["react developer"]},
]

KW_TO_GROUP = {}
from finalize_run import KEYWORD_GROUPS
for g, kws in KEYWORD_GROUPS.items():
    for k in kws:
        KW_TO_GROUP[k] = g


def norm(u):
    return u.split("?")[0]


def main():
    merged = {}
    for j in JOBS:
        dt = datetime.fromisoformat(j["postedAt"].replace("Z", "+00:00"))
        if dt < CUTOFF:
            continue
        u = norm(j["url"])
        rec = {
            "url": u,
            "title": j["title"],
            "matchedKeyword": j["kw"],
            "keywordGroup": KW_TO_GROUP.get(j["kw"][0], "OTHER"),
            "postedAt": j["postedAt"],
            "type": j["type"],
            "budget": j["budget"],
            "duration": j["duration"],
            "proposals": j["proposals"],
            "clientCountry": j["clientCountry"],
            "paymentVerified": j["paymentVerified"],
            "clientSpend": j["clientSpend"],
            "clientHireRate": None,
            "clientRating": j["clientRating"],
            "experienceLevel": j["experienceLevel"],
            "skills": j["skills"],
        }
        if u in merged:
            for k in rec["matchedKeyword"]:
                if k not in merged[u]["matchedKeyword"]:
                    merged[u]["matchedKeyword"].append(k)
        else:
            merged[u] = rec

    with (BASE / "jobs.jsonl").open("w") as f:
        for rec in merged.values():
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    batch = []
    for kw in ALL_KEYWORDS:
        if kw in SEARCHED:
            jobs_for_kw = [j for j in merged.values() if kw in j["matchedKeyword"]]
            batch.append({"keyword": kw, "status": "ok", "jobs": [{"url": j["url"], "title": j["title"], "published_date": j["postedAt"], "job_type": j["type"], "budget": j["budget"], "duration": j["duration"], "proposal_count": j["proposals"], "client": {"country": j["clientCountry"], "verification_status": "VERIFIED" if j["paymentVerified"] else None, "total_spent": j["clientSpend"], "rating": j["clientRating"]}, "experience_level": j["experienceLevel"], "skills": j["skills"]} for j in jobs_for_kw]})
        else:
            batch.append({"keyword": kw, "status": "not_run", "jobs": []})

    (BASE / "search_batch.json").write_text(json.dumps(batch))
    meta = {
        "runNumber": 1,
        "attempted": len(ALL_KEYWORDS),
        "completed": len(SEARCHED),
        "errors": FAILED,
    }
    (BASE / "run_meta.json").write_text(json.dumps(meta, indent=2))
    print(len(merged), "jobs", len(SEARCHED), "keywords searched", len(FAILED), "deferred")


if __name__ == "__main__":
    main()
