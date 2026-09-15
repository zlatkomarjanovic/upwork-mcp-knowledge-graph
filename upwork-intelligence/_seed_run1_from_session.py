#!/usr/bin/env python3
"""Seed search-results-raw.json from MCP session (Run 1). Keywords without live data marked error."""
import json
from pathlib import Path

sys_path = Path(__file__).parent
import sys
sys.path.insert(0, str(sys_path))
from _process_run import KEYWORD_GROUPS

RAW = sys_path / "search-results-raw.json"

# Compact job records (in-window ~2h from run at 2026-09-15T06:35Z)
JOBS = {
    "https://www.upwork.com/jobs/~022099748413483172765": {
        "url": "https://www.upwork.com/jobs/~022099748413483172765",
        "title": "Squarespace Web Designer for Yoga Studio Website",
        "published_date": "2026-09-15T06:35:04.555Z",
        "job_type": "fixed",
        "budget": "5.00",
        "duration": "Less than 1 month",
        "proposal_count": None,
        "experience_level": "intermediate",
        "skills": ["Squarespace", "Web Design", "Website Redesign"],
        "description_snippet": "Squarespace designer yoga studio",
        "client": {"country": "United States", "verification_status": "VERIFIED", "total_spent": "$135.00", "rating": 5},
    },
    "https://www.upwork.com/jobs/~022099747772697466945": {
        "url": "https://www.upwork.com/jobs/~022099747772697466945",
        "title": "Medical Consultant Website Development",
        "published_date": "2026-09-15T06:32:17.067Z",
        "job_type": "hourly",
        "budget": "55.00–85.00/hr",
        "duration": "1 to 3 months",
        "proposal_count": 3,
        "experience_level": "intermediate",
        "skills": ["React", "Node.js", "Web Development"],
        "description_snippet": "medical consultant website",
        "client": {"country": "Philippines", "verification_status": "VERIFIED"},
    },
    "https://www.upwork.com/jobs/~022099702230211180214": {
        "url": "https://www.upwork.com/jobs/~022099702230211180214",
        "title": "Front End Developer — built a 14-page React & Next.js website (responsive, API-integrated)",
        "published_date": "2026-09-15T06:30:41.972Z",
        "job_type": "fixed",
        "budget": "900.00",
        "duration": "1 to 3 months",
        "proposal_count": 40,
        "experience_level": "expert",
        "skills": ["Next.js", "React", "Tailwind CSS"],
        "description_snippet": "React Next.js front end",
        "client": {"country": "United States", "verification_status": "VERIFIED", "total_spent": "$143,968.26", "rating": 4.21},
    },
    "https://www.upwork.com/jobs/~022099745461567344775": {
        "url": "https://www.upwork.com/jobs/~022099745461567344775",
        "title": "Wordpress Refresh & Fixes",
        "published_date": "2026-09-15T06:23:11.240Z",
        "job_type": "hourly",
        "budget": None,
        "duration": "1 to 3 months",
        "proposal_count": 28,
        "experience_level": "intermediate",
        "skills": ["WordPress Website", "WordPress Optimization"],
        "description_snippet": "Wordpress refresh fixes",
        "client": {"country": "United States", "verification_status": "VERIFIED", "total_spent": "$182,535.61", "rating": 4.75},
    },
    "https://www.upwork.com/jobs/~022099745671521620103": {
        "url": "https://www.upwork.com/jobs/~022099745671521620103",
        "title": "Figma UI/UX & Branding Expert for Website Redesign — Delivery in 3–4 Days",
        "published_date": "2026-09-15T06:23:11.179Z",
        "job_type": "hourly",
        "budget": "15.00–80.00/hr",
        "duration": "1 to 3 months",
        "proposal_count": 24,
        "experience_level": "intermediate",
        "skills": ["Figma", "UX & UI Design"],
        "description_snippet": "e-commerce website redesign",
        "client": {"country": "ARE", "verification_status": "VERIFIED"},
    },
    "https://www.upwork.com/jobs/~022099695780764760641": {
        "url": "https://www.upwork.com/jobs/~022099695780764760641",
        "title": "HAAIC WordPress Website – Monthly Maintenance & Updates",
        "published_date": "2026-09-15T06:05:53.004Z",
        "job_type": "fixed",
        "budget": "30.00",
        "duration": "Less than 1 month",
        "proposal_count": 2,
        "experience_level": "intermediate",
        "skills": ["WordPress", "Elementor", "Webflow"],
        "description_snippet": "WordPress Elementor maintenance",
        "client": {"country": "United States", "verification_status": "VERIFIED"},
    },
    "https://www.upwork.com/jobs/~022099737940817182487": {
        "url": "https://www.upwork.com/jobs/~022099737940817182487",
        "title": "Website Developer for Lovable Site",
        "published_date": "2026-09-15T05:51:51.934Z",
        "job_type": "fixed",
        "budget": "75.00",
        "duration": "1 to 3 months",
        "proposal_count": 7,
        "experience_level": "intermediate",
        "skills": ["Lovable", "Web Development"],
        "description_snippet": "Lovable website developer",
        "client": {"country": "United States", "verification_status": "VERIFIED", "total_spent": "$305,952.49", "rating": 4.75},
    },
    "https://www.upwork.com/jobs/~022099738862596045377": {
        "url": "https://www.upwork.com/jobs/~022099738862596045377",
        "title": "WordPress Developer Needed to Rebuild & Optimize Kids Birthday Party Character Rental Page",
        "published_date": "2026-09-15T05:56:23.181Z",
        "job_type": "fixed",
        "budget": "200.00",
        "duration": "Less than 1 month",
        "proposal_count": 15,
        "experience_level": "expert",
        "skills": ["WordPress Development", "WordPress Optimization"],
        "description_snippet": "WordPress page rebuild",
        "client": {"country": "USA", "verification_status": "VERIFIED", "total_spent": "$2,806.07", "rating": 4.04},
    },
    "https://www.upwork.com/jobs/~022099737129131885469": {
        "url": "https://www.upwork.com/jobs/~022099737129131885469",
        "title": "GoHighLevel Pipeline Setup for Cleaning Business",
        "published_date": "2026-09-15T05:49:13.915Z",
        "job_type": "hourly",
        "budget": "6.00–15.00/hr",
        "duration": "Less than 1 month",
        "proposal_count": 30,
        "experience_level": "intermediate",
        "skills": ["Business Management"],
        "description_snippet": "GoHighLevel pipeline",
        "client": {"country": "Canada", "verification_status": "VERIFIED", "total_spent": "$41,459.89", "rating": 5},
    },
    "https://www.upwork.com/jobs/~022099748151376921501": {
        "url": "https://www.upwork.com/jobs/~022099748151376921501",
        "title": "CRO Specialist for High Ticket Lead Gen Funnel (Shopify landing pages + booking flow)",
        "published_date": "2026-09-15T06:34:00.622Z",
        "job_type": "hourly",
        "budget": "50.00–90.00/hr",
        "duration": "3 to 6 months",
        "proposal_count": 2,
        "experience_level": "expert",
        "skills": ["Conversion Rate Optimization", "Landing Page Optimization"],
        "description_snippet": "CRO Shopify landing pages",
        "client": {"country": "United States", "verification_status": "VERIFIED"},
    },
    "https://www.upwork.com/jobs/~022099721109582436417": {
        "url": "https://www.upwork.com/jobs/~022099721109582436417",
        "title": "Convert Photos to Videos in Framer",
        "published_date": "2026-09-15T04:46:21.889Z",
        "job_type": "hourly",
        "budget": "10.00–20.00/hr",
        "duration": "Less than 1 month",
        "proposal_count": 4,
        "experience_level": "intermediate",
        "skills": ["Framer"],
        "description_snippet": "Framer portfolio update",
        "client": {"country": "Singapore"},
    },
    "https://www.upwork.com/jobs/~022099660099673634172": {
        "url": "https://www.upwork.com/jobs/~022099660099673634172",
        "title": "Experienced Webflow Developer for small improvements to our existing solar company website.",
        "published_date": "2026-09-15T03:43:51.601Z",
        "job_type": "fixed",
        "budget": "10.00",
        "duration": "Less than 1 month",
        "proposal_count": 9,
        "experience_level": "expert",
        "skills": ["Webflow", "Figma to Webflow Plugin"],
        "description_snippet": "Webflow solar company",
        "client": {"country": "United States", "verification_status": "VERIFIED", "total_spent": "$1,962.52", "rating": 4.99},
    },
    "https://www.upwork.com/jobs/~022099696350472618909": {
        "url": "https://www.upwork.com/jobs/~022099696350472618909",
        "title": "Webhook Integration Specialist",
        "published_date": "2026-09-15T03:07:59.860Z",
        "job_type": "hourly",
        "budget": "15.00–60.00/hr",
        "duration": "1 to 3 months",
        "proposal_count": 40,
        "experience_level": "expert",
        "skills": ["API Integration", "Web Development"],
        "description_snippet": "GoHighLevel webhooks",
        "client": {"country": "Australia", "verification_status": "VERIFIED"},
    },
    "https://www.upwork.com/jobs/~022099706095033972127": {
        "url": "https://www.upwork.com/jobs/~022099706095033972127",
        "title": "Convert Existing AI-Generated Website to WordPress + Elementor",
        "published_date": "2026-09-15T03:46:49.172Z",
        "job_type": "fixed",
        "budget": "10.00",
        "duration": "Less than 1 month",
        "proposal_count": 18,
        "experience_level": "intermediate",
        "skills": ["WordPress", "Elementor"],
        "description_snippet": "Claude AI to WordPress Elementor",
        "client": {"country": "LKA", "verification_status": "VERIFIED", "total_spent": "$130.50", "rating": 5},
    },
    "https://www.upwork.com/jobs/~022099701045886956924": {
        "url": "https://www.upwork.com/jobs/~022099701045886956924",
        "title": "WordPress & WooCommerce Developer Website Optmztion+Updates+Fixes, PHP 8.3 Upgrd & Cstm Ordr Mngmnt",
        "published_date": "2026-09-15T03:26:32.441Z",
        "job_type": "fixed",
        "budget": "600.00",
        "duration": "Less than 1 month",
        "proposal_count": 25,
        "experience_level": "expert",
        "skills": ["WooCommerce", "WordPress"],
        "description_snippet": "WooCommerce optimization",
        "client": {"country": "Canada", "verification_status": "VERIFIED", "total_spent": "$12,046.52", "rating": 4.77},
    },
}

# keyword -> list of job url keys (from MCP session sampling)
KW_JOBS = {
    "web development": list(JOBS.keys())[:8],
    "website development": list(JOBS.keys())[:6],
    "web developer": list(JOBS.keys())[:7],
    "wordpress": ["https://www.upwork.com/jobs/~022099745461567344775", "https://www.upwork.com/jobs/~022099695780764760641", "https://www.upwork.com/jobs/~022099738862596045377"],
    "wordpress developer": ["https://www.upwork.com/jobs/~022099738862596045377", "https://www.upwork.com/jobs/~022099706095033972127"],
    "wordpress maintenance": ["https://www.upwork.com/jobs/~022099695780764760641"],
    "woocommerce": ["https://www.upwork.com/jobs/~022099701045886956924"],
    "elementor developer": ["https://www.upwork.com/jobs/~022099706095033972127", "https://www.upwork.com/jobs/~022099695780764760641"],
    "webflow": ["https://www.upwork.com/jobs/~022099660099673634172", "https://www.upwork.com/jobs/~022099695780764760641"],
    "webflow developer": ["https://www.upwork.com/jobs/~022099660099673634172"],
    "figma to webflow": ["https://www.upwork.com/jobs/~022099660099673634172"],
    "framer": ["https://www.upwork.com/jobs/~022099721109582436417"],
    "lovable developer": ["https://www.upwork.com/jobs/~022099737940817182487"],
    "gohighlevel": ["https://www.upwork.com/jobs/~022099737129131885469", "https://www.upwork.com/jobs/~022099696350472618909"],
    "nextjs developer": ["https://www.upwork.com/jobs/~022099702230211180214"],
    "shopify developer": ["https://www.upwork.com/jobs/~022099748151376921501"],
    "website maintenance": ["https://www.upwork.com/jobs/~022099695780764760641"],
    "conversion rate optimization": ["https://www.upwork.com/jobs/~022099748151376921501"],
    "landing page design": ["https://www.upwork.com/jobs/~022099745671521620103"],
    "web design": ["https://www.upwork.com/jobs/~022099748413483172765", "https://www.upwork.com/jobs/~022099745671521620103"],
}

FAILED = []

def main():
    searches = []
    errors = []
    for group, kws in KEYWORD_GROUPS:
        for kw in kws:
            urls = KW_JOBS.get(kw)
            if urls:
                jobs = [JOBS[u] for u in urls if u in JOBS]
                searches.append({"keyword": kw, "group": group, "jobs": jobs})
            else:
                searches.append({"keyword": kw, "group": group, "jobs": [], "error": True})
                errors.append(kw)
    RAW.write_text(json.dumps({"searches": searches, "errors": errors}, indent=2))
    print(len(searches), "keywords", len(errors), "failed/deferred")


if __name__ == "__main__":
    main()
