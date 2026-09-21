#!/usr/bin/env python3
"""Apply live MCP snapshots for keywords that were MISSING_SEARCH in transcript extract."""
import json
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).parent
SEARCH = ROOT / "search_responses.json"
CACHE = ROOT / "cache"
GROUPS = json.loads((ROOT / "keywords.json").read_text())["keywords"]

# Slim live search payloads (Sep 21 2026 hourly run)
LIVE: dict[str, dict] = {
    "shopware 6": {
        "status": "ok",
        "jobs": [
            {
                "budget": "20.00–50.00/hr",
                "client": {
                    "country": "Germany",
                    "rating": 4.99,
                    "total_posted_jobs": 65,
                    "total_reviews": 29,
                    "total_spent": "$77,096.69",
                    "verification_status": "VERIFIED",
                },
                "created_date": "2026-09-17T05:36:59.260Z",
                "duration": "3 to 6 months",
                "engagement": "PART_TIME",
                "experience_level": "expert",
                "freelancers_to_hire": 1,
                "id": "2100458974791512970",
                "job_type": "hourly",
                "proposals_tier": "50+",
                "published_date": "2026-09-17T05:38:09.805Z",
                "skills": ["Shopware"],
                "title": "Shopware Developer - Add text, images, change layout on Shopware shops",
                "url": "https://www.upwork.com/jobs/~022100458974791512970",
            }
        ],
    },
    "headless ecommerce": {
        "status": "ok",
        "jobs": [
            {
                "budget": "1,500.00",
                "client": {"country": "Bangladesh", "total_posted_jobs": 4, "verification_status": "VERIFIED"},
                "created_date": "2026-09-19T20:20:17.941Z",
                "duration": "1 to 3 months",
                "experience_level": "expert",
                "freelancers_to_hire": 1,
                "id": "2101406043348757724",
                "job_type": "fixed",
                "proposals_tier": "5 to 10",
                "published_date": "2026-09-19T23:20:24.358Z",
                "skills": ["Figma", "UI/UX Prototyping", "Custom Web Design"],
                "title": "Lead UI/UX Designer (Figma) for Premium House of Brands Multi-Vendor E-Commerce",
                "url": "https://www.upwork.com/jobs/~022101406043348757724",
            }
        ],
    },
    "website maintenance": {
        "status": "ok",
        "jobs": [
            {
                "budget": "20.00",
                "client": {
                    "country": "United Kingdom",
                    "rating": 4.84,
                    "total_posted_jobs": 25,
                    "total_reviews": 16,
                    "total_spent": "$1,091.00",
                    "verification_status": "VERIFIED",
                },
                "created_date": "2026-09-20T17:43:14.511Z",
                "duration": "More than 6 months",
                "experience_level": "intermediate",
                "freelancers_to_hire": 1,
                "id": "2101728906087699422",
                "job_type": "fixed",
                "proposals_tier": "15 to 20",
                "published_date": "2026-09-20T20:44:33.502Z",
                "skills": ["Web Development", "WordPress", "PHP", "Web Design"],
                "title": "Website Maintenance and Monitoring",
                "url": "https://www.upwork.com/jobs/~022101728906087699422",
            }
        ],
    },
    "website maintenance monthly": {
        "status": "ok",
        "jobs": [
            {
                "budget": "20.00",
                "client": {
                    "country": "United Kingdom",
                    "rating": 4.84,
                    "total_posted_jobs": 25,
                    "total_reviews": 16,
                    "total_spent": "$1,091.00",
                    "verification_status": "VERIFIED",
                },
                "created_date": "2026-09-20T17:43:14.511Z",
                "duration": "More than 6 months",
                "experience_level": "intermediate",
                "freelancers_to_hire": 1,
                "id": "2101728906087699422",
                "job_type": "fixed",
                "proposals_tier": "15 to 20",
                "published_date": "2026-09-20T20:44:33.502Z",
                "skills": ["Web Development", "WordPress", "PHP", "Web Design"],
                "title": "Website Maintenance and Monitoring",
                "url": "https://www.upwork.com/jobs/~022101728906087699422",
            }
        ],
    },
    "website support ongoing": {
        "status": "ok",
        "jobs": [
            {
                "budget": "3.00–4.00/hr",
                "client": {
                    "country": "United States",
                    "rating": 4.82,
                    "total_posted_jobs": 57,
                    "total_reviews": 20,
                    "total_spent": "$23,504.37",
                    "verification_status": "VERIFIED",
                },
                "created_date": "2026-09-21T01:48:27.056Z",
                "duration": "More than 6 months",
                "engagement": "PART_TIME",
                "experience_level": "intermediate",
                "freelancers_to_hire": 1,
                "id": "2101851013085126019",
                "job_type": "hourly",
                "proposals_tier": "10 to 15",
                "published_date": "2026-09-21T01:50:07.088Z",
                "skills": ["Shopify", "Graphic Design", "Shopify Templates", "HTML"],
                "title": "AI Dropshipping Shopify Store Creator",
                "url": "https://www.upwork.com/jobs/~022101851013085126019",
            }
        ],
    },
    "website management ongoing": {
        "status": "ok",
        "jobs": [
            {
                "client": {"country": "Luxembourg"},
                "created_date": "2026-09-21T00:06:22.849Z",
                "duration": "More than 6 months",
                "engagement": "AS_NEEDED",
                "experience_level": "expert",
                "freelancers_to_hire": 10,
                "id": "2101825326595473689",
                "job_type": "hourly",
                "proposals_tier": "15 to 20",
                "published_date": "2026-09-21T00:08:54.042Z",
                "skills": ["Web Design", "HTML5", "HTML", "Web Development"],
                "title": "Web Designer/Developer for Alix",
                "url": "https://www.upwork.com/jobs/~022101825326595473689",
            }
        ],
    },
    "wordpress support retainer": {
        "status": "ok",
        "jobs": [
            {
                "budget": "5.00–9.00/hr",
                "client": {
                    "country": "United Kingdom",
                    "rating": 4.88,
                    "total_posted_jobs": 167,
                    "total_reviews": 35,
                    "total_spent": "$9,648.90",
                    "verification_status": "VERIFIED",
                },
                "created_date": "2026-09-20T10:46:35.884Z",
                "duration": "More than 6 months",
                "engagement": "FULL_TIME",
                "experience_level": "intermediate",
                "freelancers_to_hire": 1,
                "id": "2101624054568298200",
                "job_type": "hourly",
                "proposals_tier": "20 to 50",
                "published_date": "2026-09-20T10:47:28.119Z",
                "skills": ["AI Website Builders", "Web Development", "Web Design"],
                "title": "Website Production VA — AI Vibe-Coding & Web Development (Part Time & Long Term)",
                "url": "https://www.upwork.com/jobs/~022101624054568298200",
            }
        ],
    },
    "webflow maintenance": {
        "status": "ok",
        "jobs": [
            {
                "client": {"country": "Singapore"},
                "created_date": "2026-09-21T01:47:38.847Z",
                "duration": "Less than 1 month",
                "engagement": "PART_TIME",
                "experience_level": "intermediate",
                "id": "2101850810709711466",
                "job_type": "hourly",
                "proposals_tier": "5 to 10",
                "published_date": "2026-09-21T01:48:32.851Z",
                "skills": ["Webflow", "Framer", "Web Design", "React"],
                "title": "Freelance UI/UX Developer",
                "url": "https://www.upwork.com/jobs/~022101850810709711466",
            }
        ],
    },
    "shopify maintenance": {
        "status": "ok",
        "jobs": [
            {
                "client": {"country": "United States", "verification_status": "VERIFIED"},
                "created_date": "2026-09-20T23:11:40.119Z",
                "duration": "Less than 1 month",
                "engagement": "PART_TIME",
                "experience_level": "intermediate",
                "freelancers_to_hire": 1,
                "id": "2101811557993012611",
                "job_type": "hourly",
                "proposals_tier": "10 to 15",
                "published_date": "2026-09-21T02:12:46.940Z",
                "skills": ["Shopify", "Shopify Templates", "Dropshipping"],
                "title": "Shopify Dropshipping Store Setup",
                "url": "https://www.upwork.com/jobs/~022101811557993012611",
            }
        ],
    },
    "ongoing web developer": {
        "status": "ok",
        "jobs": [
            {
                "client": {"country": "Luxembourg"},
                "created_date": "2026-09-21T00:06:22.849Z",
                "duration": "More than 6 months",
                "engagement": "AS_NEEDED",
                "experience_level": "expert",
                "freelancers_to_hire": 10,
                "id": "2101825326595473689",
                "job_type": "hourly",
                "proposals_tier": "15 to 20",
                "published_date": "2026-09-21T00:08:54.042Z",
                "skills": ["Web Design", "HTML", "Web Development"],
                "title": "Web Designer/Developer for Alix",
                "url": "https://www.upwork.com/jobs/~022101825326595473689",
            }
        ],
    },
    "web development retainer": {
        "status": "ok",
        "jobs": [
            {
                "budget": "10.00–25.00/hr",
                "client": {
                    "country": "USA",
                    "rating": 5,
                    "total_posted_jobs": 2,
                    "total_reviews": 2,
                    "total_spent": "$217.35",
                    "verification_status": "VERIFIED",
                },
                "created_date": "2026-09-20T17:50:28.370Z",
                "duration": "3 to 6 months",
                "engagement": "FULL_TIME",
                "experience_level": "expert",
                "freelancers_to_hire": 1,
                "id": "2101730725919565528",
                "job_type": "hourly",
                "proposals_tier": "50+",
                "published_date": "2026-09-20T17:51:19.953Z",
                "skills": ["Web Development"],
                "title": "Monthly Retainer Full-Stack Developer",
                "url": "https://www.upwork.com/jobs/~022101730725919565528",
            }
        ],
    },
    "conversion rate optimization": {
        "status": "ok",
        "jobs": [
            {
                "budget": "2,000.00",
                "client": {
                    "country": "AUS",
                    "rating": 5,
                    "total_posted_jobs": 3,
                    "total_reviews": 2,
                    "total_spent": "$2,700.00",
                    "verification_status": "VERIFIED",
                },
                "created_date": "2026-09-20T22:56:34.831Z",
                "duration": "1 to 3 months",
                "experience_level": "expert",
                "featured": True,
                "freelancers_to_hire": 1,
                "id": "2101807760482346712",
                "job_type": "fixed",
                "proposals_tier": "20 to 50",
                "published_date": "2026-09-20T22:57:15.718Z",
                "skills": ["Conversion Rate Optimization", "Shopify", "A/B Testing"],
                "title": "Shopify CRO Specialist to Lift Conversion (Australian Wine DTC)",
                "url": "https://www.upwork.com/jobs/~022101807760482346712",
            }
        ],
    },
    "landing page optimization": {
        "status": "ok",
        "jobs": [
            {
                "client": {"country": "Australia", "rating": 5, "total_posted_jobs": 11, "total_reviews": 12, "total_spent": "$6,904.41", "verification_status": "VERIFIED"},
                "created_date": "2026-09-21T01:23:50.276Z",
                "duration": "Less than 1 month",
                "engagement": "PART_TIME",
                "experience_level": "expert",
                "freelancers_to_hire": 1,
                "id": "2101844818898021596",
                "job_type": "hourly",
                "proposals_tier": "20 to 50",
                "published_date": "2026-09-21T01:24:54.100Z",
                "skills": ["Web Design", "Landing Page", "Web Development"],
                "title": "GoHighLevel Landing Page Designer – Improve Existing Page to Premium Design",
                "url": "https://www.upwork.com/jobs/~022101844818898021596",
            }
        ],
    },
    "website audit": {
        "status": "ok",
        "jobs": [
            {
                "budget": "100.00",
                "client": {
                    "country": "United Kingdom",
                    "rating": 4.95,
                    "total_posted_jobs": 153,
                    "total_reviews": 45,
                    "total_spent": "$11,954.50",
                    "verification_status": "VERIFIED",
                },
                "created_date": "2026-09-20T22:40:12.811Z",
                "duration": "Less than 1 month",
                "experience_level": "entry_level",
                "freelancers_to_hire": 1,
                "id": "2101803641603619171",
                "job_type": "fixed",
                "proposals_tier": "5 to 10",
                "published_date": "2026-09-20T22:41:15.581Z",
                "skills": ["Search Engine Optimization", "SEO Keyword Research", "On-Page SEO"],
                "title": "SEO Expert Needed for UGC Creator Portfolio Website",
                "url": "https://www.upwork.com/jobs/~022101803641603619171",
            }
        ],
    },
    "core web vitals": {
        "status": "ok",
        "jobs": [
            {
                "client": {
                    "country": "Australia",
                    "rating": 5,
                    "total_posted_jobs": 80,
                    "total_reviews": 46,
                    "total_spent": "$17,430.46",
                    "verification_status": "VERIFIED",
                },
                "created_date": "2026-09-21T01:30:02.838Z",
                "duration": "Less than 1 month",
                "engagement": "PART_TIME",
                "experience_level": "intermediate",
                "freelancers_to_hire": 1,
                "id": "2101846381750122851",
                "job_type": "hourly",
                "proposals_tier": "20 to 50",
                "published_date": "2026-09-21T01:31:36.039Z",
                "skills": ["WordPress", "PHP", "CSS", "Search Engine Optimization"],
                "title": "WordPress / Elementor Performance Expert Needed – Fix PageSpeed & Core Web Vitals",
                "url": "https://www.upwork.com/jobs/~022101846381750122851",
            }
        ],
    },
    "page speed optimization": {
        "status": "ok",
        "jobs": [
            {
                "budget": "3.00–40.00/hr",
                "client": {
                    "country": "Australia",
                    "rating": 4.64,
                    "total_posted_jobs": 1692,
                    "total_reviews": 651,
                    "total_spent": "$441,942.92",
                    "verification_status": "VERIFIED",
                },
                "created_date": "2026-09-21T02:02:48.003Z",
                "duration": "More than 6 months",
                "engagement": "FULL_TIME",
                "experience_level": "expert",
                "freelancers_to_hire": 1,
                "id": "2101854624720608643",
                "job_type": "hourly",
                "proposals_tier": "20 to 50",
                "published_date": "2026-09-21T02:03:30.101Z",
                "skills": ["Page Speed Optimization", "Website Performance Optimization", "SEO Performance"],
                "title": "Website Performance Optimisation",
                "url": "https://www.upwork.com/jobs/~022101854624720608643",
            }
        ],
    },
    "website speed optimization": {
        "status": "ok",
        "jobs": [
            {
                "budget": "3.00–40.00/hr",
                "client": {
                    "country": "Australia",
                    "rating": 4.64,
                    "total_posted_jobs": 1692,
                    "total_reviews": 651,
                    "total_spent": "$441,942.92",
                    "verification_status": "VERIFIED",
                },
                "created_date": "2026-09-21T02:02:48.003Z",
                "duration": "More than 6 months",
                "engagement": "FULL_TIME",
                "experience_level": "expert",
                "freelancers_to_hire": 1,
                "id": "2101854624720608643",
                "job_type": "hourly",
                "proposals_tier": "20 to 50",
                "published_date": "2026-09-21T02:03:30.101Z",
                "skills": ["Page Speed Optimization", "Website Performance Optimization"],
                "title": "Website Performance Optimisation",
                "url": "https://www.upwork.com/jobs/~022101854624720608643",
            }
        ],
    },
    "technical SEO website": {
        "status": "ok",
        "jobs": [
            {
                "client": {
                    "country": "United States",
                    "rating": 4.77,
                    "total_posted_jobs": 85,
                    "total_reviews": 49,
                    "total_spent": "$32,885.81",
                    "verification_status": "VERIFIED",
                },
                "created_date": "2026-09-21T01:05:24.745Z",
                "duration": "1 to 3 months",
                "engagement": "PART_TIME",
                "experience_level": "expert",
                "freelancers_to_hire": 1,
                "id": "2101840182296181091",
                "job_type": "hourly",
                "proposals_tier": "20 to 50",
                "published_date": "2026-09-21T01:06:30.407Z",
                "skills": ["Technical SEO", "SEO Strategy", "WordPress SEO Plugin"],
                "title": "Senior Technical SEO Specialist for Law Firm Website Expansion",
                "url": "https://www.upwork.com/jobs/~022101840182296181091",
            }
        ],
    },
}


def main() -> None:
    paired = json.loads(SEARCH.read_text())
    index = {e["keyword"]: i for i, e in enumerate(paired)}
    for kw, resp in LIVE.items():
        entry = {"keyword": kw, "group": GROUPS[kw], "response": resp}
        paired[index[kw]] = entry
        path = CACHE / (quote(kw, safe="") + ".json")
        path.write_text(json.dumps({"keyword": kw, "response": resp}, ensure_ascii=False))
    SEARCH.write_text(json.dumps(paired, indent=2))
    print("patched", len(LIVE))


if __name__ == "__main__":
    main()
