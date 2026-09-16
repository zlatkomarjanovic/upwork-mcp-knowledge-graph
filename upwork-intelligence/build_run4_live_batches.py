#!/usr/bin/env python3
"""Build _search_batches.jsonl from live MCP results (run 4, ~1h window)."""
import json
from pathlib import Path

from process_run import ALL_KEYWORDS, KEYWORD_GROUPS

BASE = Path(__file__).parent
OUT = BASE / "_search_batches.jsonl"

# Slim in-window jobs captured via live Upwork MCP this run (published >= 2026-09-16T04:33Z)
LIVE_BY_KEYWORD: dict[str, list] = {
    "web development": [
        {
            "url": "https://www.upwork.com/jobs/~022100095325372733505",
            "title": "WordPress + OwnerRez Developer Needed — Take Over & Launch Vacation Rental Platform",
            "published_date": "2026-09-16T05:33:17.422Z",
            "job_type": "hourly",
            "budget": "25.00–60.00/hr",
            "duration": "1 to 3 months",
            "experience_level": "expert",
            "skills": ["PHP", "WordPress Development", "WordPress Customization", "API Integration", "Stripe API", "REST API"],
            "client": {"country": "United States", "verification_status": "VERIFIED", "total_spent": "$7,542.12", "rating": 5, "total_posted_jobs": 18, "total_reviews": 7},
        },
        {
            "url": "https://www.upwork.com/jobs/~022100094116144992391",
            "title": "Full-Stack developer needed",
            "published_date": "2026-09-16T05:28:30.237Z",
            "job_type": "fixed",
            "budget": "500.00",
            "duration": "1 to 3 months",
            "proposals_tier": "Fewer than 5",
            "experience_level": "expert",
            "skills": ["Java", "Full-Stack Development", "AI Development", "Next.js", "Spring Boot", "Nuxt.js", "PostgreSQL"],
            "client": {"country": "China", "verification_status": "VERIFIED", "total_spent": "$1,845.00", "rating": 5, "total_reviews": 4},
        },
    ],
    "full stack developer": [
        {
            "url": "https://www.upwork.com/jobs/~022100094116144992391",
            "title": "Full-Stack developer needed",
            "published_date": "2026-09-16T05:28:30.237Z",
            "job_type": "fixed",
            "budget": "500.00",
            "duration": "1 to 3 months",
            "proposals_tier": "Fewer than 5",
            "experience_level": "expert",
            "skills": ["Java", "Full-Stack Development", "AI Development", "Next.js", "Spring Boot", "Nuxt.js", "PostgreSQL"],
            "client": {"country": "China", "verification_status": "VERIFIED", "total_spent": "$1,845.00", "rating": 5, "total_reviews": 4},
        },
        {
            "url": "https://www.upwork.com/jobs/~022100091492561909151",
            "title": "Vibe Coded Project Review",
            "published_date": "2026-09-16T05:18:09.195Z",
            "job_type": "hourly",
            "budget": "15.00–35.00/hr",
            "duration": "Less than 1 month",
            "proposals_tier": "5 to 10",
            "experience_level": "intermediate",
            "skills": ["Project Management", "Python", "API", "SQL"],
            "client": {"country": "United States"},
        },
    ],
    "wordpress": [
        {
            "url": "https://www.upwork.com/jobs/~022100095325372733505",
            "title": "WordPress + OwnerRez Developer Needed — Take Over & Launch Vacation Rental Platform",
            "published_date": "2026-09-16T05:33:17.422Z",
            "job_type": "hourly",
            "budget": "25.00–60.00/hr",
            "duration": "1 to 3 months",
            "experience_level": "expert",
            "skills": ["PHP", "WordPress Development", "WordPress Customization", "API Integration", "Stripe API", "REST API"],
            "client": {"country": "United States", "verification_status": "VERIFIED", "total_spent": "$7,542.12", "rating": 5},
        }
    ],
    "wordpress developer": [
        {
            "url": "https://www.upwork.com/jobs/~022100095325372733505",
            "title": "WordPress + OwnerRez Developer Needed — Take Over & Launch Vacation Rental Platform",
            "published_date": "2026-09-16T05:33:17.422Z",
            "job_type": "hourly",
            "budget": "25.00–60.00/hr",
            "duration": "1 to 3 months",
            "experience_level": "expert",
            "skills": ["PHP", "WordPress Development", "WordPress Customization", "API Integration", "Stripe API", "REST API"],
            "client": {"country": "United States", "verification_status": "VERIFIED", "total_spent": "$7,542.12", "rating": 5},
        }
    ],
    "shopify developer": [
        {
            "url": "https://www.upwork.com/jobs/~022100091907728917405",
            "title": "URGENT: Senior Shopify Developer (Custom Liquid / CRO) – High-Speed Beauty Landing Page",
            "published_date": "2026-09-16T05:19:44.374Z",
            "job_type": "fixed",
            "budget": "1,000.00",
            "duration": "1 to 3 months",
            "proposals_tier": "10 to 15",
            "experience_level": "expert",
            "skills": ["Liquid", "HTML", "Shopify Development", "Shopify Theme", "Ecommerce Website Development"],
            "client": {"country": "Germany", "verification_status": "VERIFIED", "total_posted_jobs": 4},
        }
    ],
    "ecommerce website": [
        {
            "url": "https://www.upwork.com/jobs/~022100091907728917405",
            "title": "URGENT: Senior Shopify Developer (Custom Liquid / CRO) – High-Speed Beauty Landing Page",
            "published_date": "2026-09-16T05:19:44.374Z",
            "job_type": "fixed",
            "budget": "1,000.00",
            "duration": "1 to 3 months",
            "proposals_tier": "10 to 15",
            "experience_level": "expert",
            "skills": ["Liquid", "HTML", "Shopify Development", "Shopify Theme", "Ecommerce Website Development"],
            "client": {"country": "Germany", "verification_status": "VERIFIED", "total_posted_jobs": 4},
        }
    ],
    "vibe coding": [
        {
            "url": "https://www.upwork.com/jobs/~022100091492561909151",
            "title": "Vibe Coded Project Review",
            "published_date": "2026-09-16T05:18:09.195Z",
            "job_type": "hourly",
            "budget": "15.00–35.00/hr",
            "duration": "Less than 1 month",
            "proposals_tier": "5 to 10",
            "experience_level": "intermediate",
            "skills": ["Project Management", "Python", "API", "SQL"],
            "client": {"country": "United States"},
        }
    ],
    "AI web development": [
        {
            "url": "https://www.upwork.com/jobs/~022100042536961497153",
            "title": "Build AI-Powered CRM for Existing SaaS Platform – Next.js, Twilio, AI Agents",
            "published_date": "2026-09-16T05:03:16.956Z",
            "job_type": "hourly",
            "proposals_tier": "20 to 50",
            "duration": "Less than 1 month",
            "experience_level": "intermediate",
            "skills": ["Next.js", "CRM Software", "Salesforce"],
            "client": {"country": "United States", "verification_status": "VERIFIED", "total_posted_jobs": 1},
        },
        {
            "url": "https://www.upwork.com/jobs/~022100081275490326593",
            "title": "Full-Stack Developer for Scientific Imaging Startup — Website, Backend, ML & Deployment",
            "published_date": "2026-09-16T04:37:22.816Z",
            "job_type": "fixed",
            "budget": "5,000.00",
            "duration": "1 to 3 months",
            "proposals_tier": "20 to 50",
            "experience_level": "expert",
            "skills": ["Full-Stack Development", "AI Development", "Web Services Development"],
            "client": {"country": "South Korea", "verification_status": "VERIFIED", "total_posted_jobs": 2},
        },
    ],
    "nextjs developer": [
        {
            "url": "https://www.upwork.com/jobs/~022100042536961497153",
            "title": "Build AI-Powered CRM for Existing SaaS Platform – Next.js, Twilio, AI Agents",
            "published_date": "2026-09-16T05:03:16.956Z",
            "job_type": "hourly",
            "proposals_tier": "20 to 50",
            "duration": "Less than 1 month",
            "experience_level": "intermediate",
            "skills": ["Next.js", "CRM Software"],
            "client": {"country": "United States", "verification_status": "VERIFIED"},
        }
    ],
    "webflow developer": [
        {
            "url": "https://www.upwork.com/jobs/~022100010206128305567",
            "title": "Senior Webflow + Stripe + Zapier Integration Developer for Automated Digital Product Platform",
            "published_date": "2026-09-15T23:55:25.086Z",
            "job_type": "hourly",
            "budget": "25.00–90.00/hr",
            "duration": "1 to 3 months",
            "proposals_tier": "50+",
            "experience_level": "expert",
            "skills": ["API Integration", "JavaScript", "Webflow", "Stripe", "Zapier"],
            "client": {"country": "USA", "verification_status": "VERIFIED", "total_spent": "$820.92", "rating": 5},
        }
    ],
    "landing page design": [
        {
            "url": "https://www.upwork.com/jobs/~022100077770563044253",
            "title": "Squarespace & Social Landing Page Specialist for Tech App Startup.",
            "published_date": "2026-09-16T04:23:34.915Z",
            "job_type": "fixed",
            "budget": "500.00",
            "duration": "Less than 1 month",
            "proposals_tier": "10 to 15",
            "experience_level": "expert",
            "skills": ["Webflow", "Landing Page", "Squarespace", "Conversion Rate Optimization"],
            "client": {"country": "USA", "verification_status": "VERIFIED", "total_spent": "$602.50", "rating": 1},
        }
    ],
    "conversion rate optimization": [
        {
            "url": "https://www.upwork.com/jobs/~022100077770563044253",
            "title": "Squarespace & Social Landing Page Specialist for Tech App Startup.",
            "published_date": "2026-09-16T04:23:34.915Z",
            "job_type": "fixed",
            "budget": "500.00",
            "duration": "Less than 1 month",
            "proposals_tier": "10 to 15",
            "experience_level": "expert",
            "skills": ["Webflow", "Landing Page", "Conversion Rate Optimization"],
            "client": {"country": "USA", "verification_status": "VERIFIED"},
        }
    ],
}

FAILED: list[str] = []


def main():
    lines = []
    for kw in ALL_KEYWORDS:
        if kw in FAILED:
            lines.append(json.dumps({"keyword": kw, "error": True}))
            continue
        jobs = LIVE_BY_KEYWORD.get(kw, [])
        lines.append(json.dumps({"keyword": kw, "jobs": jobs}, ensure_ascii=False))
    OUT.write_text("\n".join(lines) + "\n")
    print(json.dumps({"keywords": len(lines), "with_jobs": sum(1 for k in ALL_KEYWORDS if LIVE_BY_KEYWORD.get(k))}))


if __name__ == "__main__":
    main()
