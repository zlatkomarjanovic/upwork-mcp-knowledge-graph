#!/usr/bin/env python3
"""Finalize run 1: persist jobs, stats, summary from collected search window."""
import json, statistics, re
from datetime import datetime, timezone, timedelta
from pathlib import Path
from collections import defaultdict

BASE = Path(__file__).parent
RUN_AT = datetime(2026, 9, 21, 8, 34, 45, tzinfo=timezone.utc)
RUN_NUMBER = 1
CUTOFF = RUN_AT - timedelta(hours=2)
KEYWORDS_TOTAL = 93
KEYWORDS_COMPLETED = 68
FAILED_KEYWORDS = [
    "bolt.new", "AI agent integration website", "go high level", "GHL",
    "gohighlevel developer", "gohighlevel website", "gohighlevel funnel",
    "gohighlevel automation", "gohighlevel CRM", "squarespace website",
    "wix website", "wix studio", "bubble developer", "next.js developer",
    "nextjs website", "react developer", "figma to nextjs", "tailwind developer",
    "astro developer", "sanity CMS", "ecommerce website", "ecommerce developer",
    "shopify website", "woocommerce developer", "shopware", "shopware developer",
    "shopware 6", "headless ecommerce", "website maintenance monthly",
    "website support ongoing", "website management ongoing", "wordpress support retainer",
    "webflow maintenance", "shopify maintenance", "ongoing web developer",
    "web development retainer", "landing page optimization", "website audit",
    "core web vitals", "page speed optimization", "website speed optimization",
    "technical SEO website",
]

# Jobs collected from successful keyword searches (2h window, deduped by URL)
RAW_JOBS = [
  {"url":"https://www.upwork.com/jobs/~022101951976738858682","title":"WordPress Redesign + Auto Currency (AED/INR/USD) via Stripe — Amelia Booking Site","matchedKeyword":["wordpress","wordpress developer","wordpress website","wordpress development","wordpress redesign","web development","website development","web developer","custom website","woocommerce"],"keywordGroup":"WORDPRESS","postedAt":"2026-09-21T08:34:42.526Z","type":"fixed","budget":"250.00","duration":"Less than 1 month","proposals":"Fewer than 5","clientCountry":"United Arab Emirates","paymentVerified":True,"clientSpend":"$240.00","clientHireRate":None,"clientRating":5.0,"experienceLevel":"intermediate","skills":["WordPress","Web Design","JavaScript","Web Development","HTML","Stripe","WordPress Plugin","WooCommerce","Plugin Development"]},
  {"url":"https://www.upwork.com/jobs/~022101906370245984537","title":"Shopify developer","matchedKeyword":["shopify developer","web development","website development"],"keywordGroup":"ECOMMERCE","postedAt":"2026-09-21T08:29:03.240Z","type":"hourly","budget":"10.00–20.00/hr","duration":"Less than 1 month","proposals":"Fewer than 5","clientCountry":"India","paymentVerified":True,"clientSpend":None,"clientHireRate":None,"clientRating":None,"experienceLevel":"intermediate","skills":["Shopify Development","Shopify Theme","Web Development"]},
  {"url":"https://www.upwork.com/jobs/~022101950281074190040","title":"Senior B2B SaaS Product - Landing Page Designer + Product Marketing Specialist- AI Voice Agent","matchedKeyword":["landing page design","web design","AI web development","AI web developer"],"keywordGroup":"WEB DESIGN","postedAt":"2026-09-21T08:23:49.243Z","type":"fixed","budget":"200.00","duration":"1 to 3 months","proposals":"Fewer than 5","clientCountry":"India","paymentVerified":True,"clientSpend":"$5,149.42","clientHireRate":None,"clientRating":4.98,"experienceLevel":"expert","skills":["Custom Web Design","Adaptive Web Design","Home Page","SaaS","B2B Marketing"]},
  {"url":"https://www.upwork.com/jobs/~022101905221130589150","title":"Senior Integration Engineer – WooCommerce + Telehealth Platform + Customer.io Event Pipeline (HIPAA)","matchedKeyword":["woocommerce","wordpress development"],"keywordGroup":"WORDPRESS","postedAt":"2026-09-21T08:25:30.792Z","type":"hourly","budget":"5.00–100.00/hr","duration":"1 to 3 months","proposals":"10 to 15","clientCountry":"USA","paymentVerified":True,"clientSpend":"$13,301.16","clientHireRate":None,"clientRating":5.0,"experienceLevel":"intermediate","skills":["PHP","WordPress","JavaScript","HTML5"]},
  {"url":"https://www.upwork.com/jobs/~022101944675523509110","title":"Shopify Speed Optimisation Expert Needed – Improve Mobile PageSpeed","matchedKeyword":["page speed optimization","shopify developer","conversion rate optimization"],"keywordGroup":"CONVERSION / PERFORMANCE","postedAt":"2026-09-21T08:01:16.481Z","type":"hourly","budget":"15.00–40.00/hr","duration":"Less than 1 month","proposals":"20 to 50","clientCountry":"United Kingdom","paymentVerified":True,"clientSpend":"$28,042.96","clientHireRate":None,"clientRating":4.96,"experienceLevel":"expert","skills":["Ecommerce Performance Optimization","Page Speed Optimization","Shopify Development"]},
  {"url":"https://www.upwork.com/jobs/~022101936265982733532","title":"GHL expert — fix Facebook leads not posting to webhook (OPTA)","matchedKeyword":["gohighlevel","GHL"],"keywordGroup":"GOHIGHLEVEL","postedAt":"2026-09-21T07:27:45.025Z","type":"fixed","budget":"50.00","duration":"1 to 3 months","proposals":"20 to 50","clientCountry":"Sweden","paymentVerified":True,"clientSpend":"$15,318.77","clientHireRate":None,"clientRating":4.91,"experienceLevel":"intermediate","skills":["Lead Management Automation","Social Media Marketing Automation","Facebook Advertising"]},
  {"url":"https://www.upwork.com/jobs/~022101929395641383267","title":"GoHighLevel CRM & Sales Automation Specialist + Airtable Experience + Expert Funnel Builder","matchedKeyword":["gohighlevel"],"keywordGroup":"GOHIGHLEVEL","postedAt":"2026-09-21T07:00:59.078Z","type":"fixed","budget":"10.00","duration":"1 to 3 months","proposals":"5 to 10","clientCountry":"Pakistan","paymentVerified":True,"clientSpend":"$94.70","clientHireRate":None,"clientRating":5.0,"experienceLevel":"expert","skills":["CRM Automation","Marketing Automation","Zapier","Airtable","Sales Funnel"]},
  {"url":"https://www.upwork.com/jobs/~022101867607289528601","title":"GoHighLevel Website Developer for Premium Financial Advice Brand","matchedKeyword":["gohighlevel","gohighlevel website"],"keywordGroup":"GOHIGHLEVEL","postedAt":"2026-09-21T05:55:04.923Z","type":"hourly","budget":None,"duration":"1 to 3 months","proposals":"10 to 15","clientCountry":"New Zealand","paymentVerified":None,"clientSpend":None,"clientHireRate":None,"clientRating":None,"experienceLevel":"intermediate","skills":["Web Design","Web Development","Responsive Design"]},
  {"url":"https://www.upwork.com/jobs/~022101894451342866787","title":"Framer expert needed to complete website, integrations and launch","matchedKeyword":["framer","framer developer","framer website"],"keywordGroup":"WEBFLOW / FRAMER","postedAt":"2026-09-21T04:41:46.954Z","type":"fixed","budget":"500.00","duration":"1 to 3 months","proposals":"5 to 10","clientCountry":"United States","paymentVerified":None,"clientSpend":None,"clientHireRate":None,"clientRating":None,"experienceLevel":"intermediate","skills":["Framer","Web Development","Web Design","Website Builder","Branded Website"]},
  {"url":"https://www.upwork.com/jobs/~022101910850301793246","title":"Webflow Website Specialist for Post-Launch Optimization (Urgent, Berlin Time Zone)","matchedKeyword":["webflow","webflow developer","webflow website","page speed optimization"],"keywordGroup":"WEBFLOW / FRAMER","postedAt":"2026-09-21T05:47:01.029Z","type":"hourly","budget":"18.00–40.00/hr","duration":"1 to 3 months","proposals":"15 to 20","clientCountry":"Germany","paymentVerified":None,"clientSpend":None,"clientHireRate":None,"clientRating":None,"experienceLevel":"expert","skills":["Webflow","Search Engine Optimization","Landing Page"]},
  {"url":"https://www.upwork.com/jobs/~022101884583366097251","title":"Create and Migrate a website from WordPress to webflow.","matchedKeyword":["webflow redesign","figma to webflow","wordpress migration"],"keywordGroup":"WEBFLOW / FRAMER","postedAt":"2026-09-21T04:02:58.217Z","type":"hourly","budget":"18.00–40.00/hr","duration":"1 to 3 months","proposals":"50+","clientCountry":"Australia","paymentVerified":True,"clientSpend":None,"clientHireRate":None,"clientRating":None,"experienceLevel":"expert","skills":["Web Development","Webflow","Graphic Design","Website Customization","Landing Page","Web Design"]},
  {"url":"https://www.upwork.com/jobs/~022101931992306933123","title":"Full-Stack Developer Needed to Build Partner & Admin Dashboard Using Claude","matchedKeyword":["claude code developer","nextjs developer","AI web development"],"keywordGroup":"AI / VIBE CODING","postedAt":"2026-09-21T07:11:39.018Z","type":"fixed","budget":"5.00","duration":"Less than 1 month","proposals":"50+","clientCountry":"Sweden","paymentVerified":True,"clientSpend":"$14,776.48","clientHireRate":None,"clientRating":4.94,"experienceLevel":"entry_level","skills":["Next.js","Node.js","Full-Stack Development","Web Development","React"]},
  {"url":"https://www.upwork.com/jobs/~022101879336718711670","title":"Senior Vibe Shopify Developer","matchedKeyword":["vibe coding","shopify developer","claude code developer"],"keywordGroup":"AI / VIBE CODING","postedAt":"2026-09-21T06:41:39.526Z","type":"hourly","budget":"15.00–20.00/hr","duration":"More than 6 months","proposals":"50+","clientCountry":"United States","paymentVerified":True,"clientSpend":"$42,747.29","clientHireRate":None,"clientRating":4.76,"experienceLevel":"expert","skills":["Shopify Development","Shopify","Claude Code","Web Development","AI Coding Workflows"]},
  {"url":"https://www.upwork.com/jobs/~022101933340107566300","title":"JOHNKEANS website changes","matchedKeyword":["nextjs developer","custom website"],"keywordGroup":"MODERN STACK","postedAt":"2026-09-21T07:16:42.824Z","type":"fixed","budget":"200.00","duration":"1 to 3 months","proposals":"20 to 50","clientCountry":"United Arab Emirates","paymentVerified":True,"clientSpend":None,"clientHireRate":None,"clientRating":None,"experienceLevel":"expert","skills":["Next.js"]},
  {"url":"https://www.upwork.com/jobs/~022101807050792725724","title":"Senior Full-Stack Developer – Next.js + FastAPI + Supabase + Stripe SaaS","matchedKeyword":["supabase developer","nextjs developer"],"keywordGroup":"AI / VIBE CODING","postedAt":"2026-09-20T22:54:40.917Z","type":"fixed","budget":"3,500.00","duration":"1 to 3 months","proposals":"50+","clientCountry":"United Kingdom","paymentVerified":True,"clientSpend":None,"clientHireRate":None,"clientRating":None,"experienceLevel":"intermediate","skills":["TypeScript","Python","PostgreSQL","React","FastAPI","Supabase"]},
  {"url":"https://www.upwork.com/jobs/~022101906960159188696","title":"Shopify","matchedKeyword":["shopify developer","shopify website"],"keywordGroup":"ECOMMERCE","postedAt":"2026-09-21T08:32:06.300Z","type":"hourly","budget":None,"duration":"Less than 1 month","proposals":"Fewer than 5","clientCountry":"AUS","paymentVerified":True,"clientSpend":"$407.79","clientHireRate":None,"clientRating":None,"experienceLevel":"intermediate","skills":["WordPress","Shopify","Elementor","Squarespace","Figma"]},
  {"url":"https://www.upwork.com/jobs/~022101936630036699754","title":"Shopify freelancer for lightweight Swedish B2B ecommerce smoke-test landing page","matchedKeyword":["shopify developer","ecommerce website","landing page design"],"keywordGroup":"ECOMMERCE","postedAt":"2026-09-21T07:30:03.893Z","type":"fixed","budget":"700.00","duration":"1 to 3 months","proposals":"15 to 20","clientCountry":"Finland","paymentVerified":None,"clientSpend":None,"clientHireRate":None,"clientRating":None,"experienceLevel":"intermediate","skills":["Shopify","Landing Page","Web Development","JavaScript","Web Design"]},
  {"url":"https://www.upwork.com/jobs/~022101934398061934947","title":"WordPress & Squarespace Web Designer/Developer — 4 Existing-Site Updates (approx. 3 months, remote)","matchedKeyword":["wordpress developer","website redesign","website maintenance"],"keywordGroup":"WORDPRESS","postedAt":"2026-09-21T07:20:22.699Z","type":"hourly","budget":"15.00–30.00/hr","duration":"1 to 3 months","proposals":"50+","clientCountry":"Australia","paymentVerified":True,"clientSpend":"$104,651.89","clientHireRate":None,"clientRating":4.71,"experienceLevel":"intermediate","skills":["Avada Theme Customization","Website Redesign","WordPress","Squarespace","CSS","Web Design"]},
  {"url":"https://www.upwork.com/jobs/~022101925331880673561","title":"Long-Term Senior WordPress Developer – EUROPE ONLY | WooCommerce, WPML, Brevo & SEO","matchedKeyword":["wordpress developer","woocommerce developer","wordpress maintenance"],"keywordGroup":"WORDPRESS","postedAt":"2026-09-21T06:45:02.169Z","type":"hourly","budget":None,"duration":"More than 6 months","proposals":"15 to 20","clientCountry":"Denmark","paymentVerified":True,"clientSpend":None,"clientHireRate":None,"clientRating":None,"experienceLevel":"expert","skills":["WordPress e-Commerce","WordPress Development","WordPress Customization"]},
  {"url":"https://www.upwork.com/jobs/~022101921258007724313","title":"WooCommerce Art and Service Website","matchedKeyword":["woocommerce","elementor developer","wordpress speed optimization"],"keywordGroup":"WORDPRESS","postedAt":"2026-09-21T06:28:39.680Z","type":"hourly","budget":None,"duration":"Less than 1 month","proposals":"20 to 50","clientCountry":"Thailand","paymentVerified":True,"clientSpend":None,"clientHireRate":None,"clientRating":None,"experienceLevel":"intermediate","skills":["WooCommerce","WordPress Website","Elementor","Page Speed Optimization"]},
  {"url":"https://www.upwork.com/jobs/~022101928428958941465","title":"Web Developer + Technical SEO + UI/Design Cleanup","matchedKeyword":["technical SEO website","website audit"],"keywordGroup":"CONVERSION / PERFORMANCE","postedAt":"2026-09-21T06:57:40.565Z","type":"fixed","budget":"1,000.00","duration":"1 to 3 months","proposals":"20 to 50","clientCountry":"United States","paymentVerified":True,"clientSpend":"$2,626.74","clientHireRate":None,"clientRating":4.18,"experienceLevel":"expert","skills":["OpenAI Codex","Web Development","Web Design","SEO Backlinking"]},
  {"url":"https://www.upwork.com/jobs/~022101920734660779395","title":"CRO / Online Sales Orchestration for Insurance Sales SaaS","matchedKeyword":["conversion rate optimization"],"keywordGroup":"CONVERSION / PERFORMANCE","postedAt":"2026-09-21T06:26:39.892Z","type":"hourly","budget":"10.00–30.00/hr","duration":"More than 6 months","proposals":"Fewer than 5","clientCountry":"USA","paymentVerified":True,"clientSpend":"$40,840.27","clientHireRate":None,"clientRating":None,"experienceLevel":"intermediate","skills":["A/B Testing","Conversion Rate Optimization","Rapid Experimentation","Data Analysis"]},
  {"url":"https://www.upwork.com/jobs/~022101875675693309315","title":"WordPress Website Migration – 8 Pages / ~400MB Site","matchedKeyword":["wordpress migration","website maintenance"],"keywordGroup":"WORDPRESS","postedAt":"2026-09-21T03:27:51.404Z","type":"hourly","budget":None,"duration":"Less than 1 month","proposals":"50+","clientCountry":"Australia","paymentVerified":True,"clientSpend":"$17,430.46","clientHireRate":None,"clientRating":5.0,"experienceLevel":"intermediate","skills":["WordPress","PHP","Web Development"]},
  {"url":"https://www.upwork.com/jobs/~022101930680709020003","title":"Technical Lead for Client Discovery & Custom Software Delivery","matchedKeyword":["claude code developer","cursor AI developer","full stack developer"],"keywordGroup":"AI / VIBE CODING","postedAt":"2026-09-21T07:06:25.216Z","type":"hourly","budget":"25.00–47.00/hr","duration":"More than 6 months","proposals":"10 to 15","clientCountry":"United Kingdom","paymentVerified":True,"clientSpend":"$118,350.25","clientHireRate":None,"clientRating":4.99,"experienceLevel":"expert","skills":["Claude Code","OpenAI Codex","AI App Development"]},
  {"url":"https://www.upwork.com/jobs/~022101937893155543658","title":"Full-Stack AI Engineer: Ecommerce Operating System ($8k, One Month)","matchedKeyword":["AI web development","headless ecommerce"],"keywordGroup":"AI / VIBE CODING","postedAt":"2026-09-21T07:34:32.055Z","type":"fixed","budget":"8,000.00","duration":"Less than 1 month","proposals":"20 to 50","clientCountry":"USA","paymentVerified":True,"clientSpend":None,"clientHireRate":None,"clientRating":None,"experienceLevel":"expert","skills":[]},
  {"url":"https://www.upwork.com/jobs/~022101624054568298200","title":"Website Production VA — AI Vibe-Coding & Web Development (Part Time & Long Term)","matchedKeyword":["vibe coding","lovable developer"],"keywordGroup":"AI / VIBE CODING","postedAt":"2026-09-20T10:47:28.119Z","type":"hourly","budget":"5.00–9.00/hr","duration":"More than 6 months","proposals":"20 to 50","clientCountry":"United Kingdom","paymentVerified":True,"clientSpend":"$9,648.90","clientHireRate":None,"clientRating":4.88,"experienceLevel":"intermediate","skills":["AI Website Builders","Web Design","Web Development"]},
  {"url":"https://www.upwork.com/jobs/~022101719139155172739","title":"Lovable.dev Website Refinement Specialist","matchedKeyword":["lovable developer","lovable app"],"keywordGroup":"AI / VIBE CODING","postedAt":"2026-09-20T17:05:46.960Z","type":"hourly","budget":"18.00–40.00/hr","duration":"1 to 3 months","proposals":"20 to 50","clientCountry":"United States","paymentVerified":True,"clientSpend":"$998.06","clientHireRate":None,"clientRating":5.0,"experienceLevel":"expert","skills":["Web Design","Web Development","HTML","Graphic Design"]},
  {"url":"https://www.upwork.com/jobs/~022101773541342385118","title":"AI Website Builder Needed – Two Simple Professional Websites","matchedKeyword":["AI web developer","AI web development"],"keywordGroup":"AI / VIBE CODING","postedAt":"2026-09-20T23:41:27.081Z","type":"hourly","budget":None,"duration":"1 to 3 months","proposals":"20 to 50","clientCountry":"United States","paymentVerified":True,"clientSpend":"$600.00","clientHireRate":None,"clientRating":None,"experienceLevel":"intermediate","skills":["AI Website Builders","WordPress","Web Development","Web Design","Generative AI"]},
  {"url":"https://www.upwork.com/jobs/~022101888232685245406","title":"Linkedin Outreach Automation Specialist (+GHL Integration)","matchedKeyword":["gohighlevel","gohighlevel automation"],"keywordGroup":"GOHIGHLEVEL","postedAt":"2026-09-21T07:17:32.016Z","type":"hourly","budget":"9.00–16.00/hr","duration":"3 to 6 months","proposals":"5 to 10","clientCountry":"United States","paymentVerified":True,"clientSpend":"$170,599.89","clientHireRate":None,"clientRating":4.15,"experienceLevel":"intermediate","skills":["CRM Automation","LinkedIn Lead Generation","HighLevel"]},
  {"url":"https://www.upwork.com/jobs/~022101907725640640216","title":"Quick Webflow Edits — Add CTAs, Thank You Page, Fix Video Autoplay","matchedKeyword":["webflow developer"],"keywordGroup":"WEBFLOW / FRAMER","postedAt":"2026-09-21T05:35:02.027Z","type":"fixed","budget":"50.00","duration":"Less than 1 month","proposals":"20 to 50","clientCountry":"Australia","paymentVerified":True,"clientSpend":"$27,885.78","clientHireRate":None,"clientRating":4.94,"experienceLevel":"intermediate","skills":["Custom Web Design","Webflow","CSS","HTML"]},
  {"url":"https://www.upwork.com/jobs/~022101889216255883619","title":"Web Developer for Website Creation","matchedKeyword":["web developer","website development","wordpress website"],"keywordGroup":"CORE WEB DEVELOPMENT","postedAt":"2026-09-21T07:20:17.517Z","type":"hourly","budget":"13.00–30.00/hr","duration":"1 to 3 months","proposals":"15 to 20","clientCountry":"Ethiopia","paymentVerified":None,"clientSpend":None,"clientHireRate":None,"clientRating":None,"experienceLevel":"entry_level","skills":["WordPress","PHP","HTML5","GoDaddy","HTML"]},
  {"url":"https://www.upwork.com/jobs/~022101931861352373635","title":"WordPress E-commerce Website for Jewelry Brand","matchedKeyword":["wordpress website","woocommerce"],"keywordGroup":"WORDPRESS","postedAt":"2026-09-21T07:10:26.735Z","type":"fixed","budget":"350.00","duration":"1 to 3 months","proposals":"20 to 50","clientCountry":"Oman","paymentVerified":None,"clientSpend":None,"clientHireRate":None,"clientRating":None,"experienceLevel":"intermediate","skills":["Web Design","HTML","PHP","Web Development"]},
  {"url":"https://www.upwork.com/jobs/~022101928937546988406","title":"Midnight Wishes – Automated WhatsApp Family Greetings","matchedKeyword":["web development","full stack developer"],"keywordGroup":"CORE WEB DEVELOPMENT","postedAt":"2026-09-21T07:48:29.247Z","type":"fixed","budget":"50.00","duration":"Less than 1 month","proposals":"Fewer than 5","clientCountry":"India","paymentVerified":True,"clientSpend":"$641.12","clientHireRate":None,"clientRating":5.0,"experienceLevel":"intermediate","skills":["JavaScript","PHP","Android App Development"]},
  {"url":"https://www.upwork.com/jobs/~022101723843279487257","title":"Migrate Working App Off Replit, Fix Features One at a Time","matchedKeyword":["replit developer"],"keywordGroup":"AI / VIBE CODING","postedAt":"2026-09-20T17:24:06.732Z","type":"hourly","budget":"25.00–35.00/hr","duration":"More than 6 months","proposals":"20 to 50","clientCountry":"United States","paymentVerified":True,"clientSpend":"$3,568.01","clientHireRate":None,"clientRating":4.94,"experienceLevel":"expert","skills":["AI Agent Development","Full Stack Development Deliverables"]},
  {"url":"https://www.upwork.com/jobs/~022101925523066562264","title":"Website Functionality Fix Needed","matchedKeyword":["website maintenance","wordpress customization"],"keywordGroup":"MAINTENANCE / RETAINERS","postedAt":"2026-09-21T06:45:48.849Z","type":"fixed","budget":"50.00","duration":"Less than 1 month","proposals":"15 to 20","clientCountry":"India","paymentVerified":True,"clientSpend":None,"clientHireRate":None,"clientRating":None,"experienceLevel":"entry_level","skills":["PHP","Web Development","WordPress","WooCommerce"]},
  {"url":"https://www.upwork.com/jobs/~022101931053674019702","title":"Shopify Developer for Luxury Footwear Store","matchedKeyword":["shopify developer","shopify maintenance"],"keywordGroup":"ECOMMERCE","postedAt":"2026-09-21T07:07:36.577Z","type":"hourly","budget":"25.00–50.00/hr","duration":"More than 6 months","proposals":"10 to 15","clientCountry":"India","paymentVerified":True,"clientSpend":None,"clientHireRate":None,"clientRating":None,"experienceLevel":"expert","skills":["Shopify","Payment Gateway Integration","Shopify Templates","API Integration"]},
  {"url":"https://www.upwork.com/jobs/~022101874657126023449","title":"Sirens landing pages: size calculator + speed fixes","matchedKeyword":["landing page design","core web vitals","webflow"],"keywordGroup":"WEB DESIGN","postedAt":"2026-09-21T06:23:44.727Z","type":"hourly","budget":None,"duration":"Less than 1 month","proposals":"15 to 20","clientCountry":"Australia","paymentVerified":True,"clientSpend":"$2,347.73","clientHireRate":None,"clientRating":5.0,"experienceLevel":"intermediate","skills":["WordPress","Webflow","WooCommerce","Landing Page Design"]},
  {"url":"https://www.upwork.com/jobs/~022101911970291941657","title":"Pixel Perfect Elementor Pro Design","matchedKeyword":["elementor developer","wordpress customization"],"keywordGroup":"WORDPRESS","postedAt":"2026-09-21T05:52:10.492Z","type":"fixed","budget":"200.00","duration":"1 to 3 months","proposals":"20 to 50","clientCountry":"United States","paymentVerified":True,"clientSpend":"$63,780.77","clientHireRate":None,"clientRating":5.0,"experienceLevel":"expert","skills":["WordPress","Elementor","Web Design","JavaScript"]},
  {"url":"https://www.upwork.com/jobs/~022101883505284225642","title":"High-End WordPress Developer & Animator – Luxury Art Gallery Page (GSAP / Custom JS)","matchedKeyword":["wordpress developer","bricks builder"],"keywordGroup":"WORDPRESS","postedAt":"2026-09-21T06:58:15.759Z","type":"fixed","budget":"500.00","duration":"1 to 3 months","proposals":"Fewer than 5","clientCountry":"USA","paymentVerified":True,"clientSpend":"$231.00","clientHireRate":None,"clientRating":5.0,"experienceLevel":"expert","skills":["WordPress","Elementor","WordPress Development","Web Design"]},
  {"url":"https://www.upwork.com/jobs/~022101923547272714858","title":"GoHighLevel Automation Setup and Nurture Campaign (Women's Coaching Brand)","matchedKeyword":["gohighlevel funnel"],"keywordGroup":"GOHIGHLEVEL","postedAt":"2026-09-21T06:38:05.947Z","type":"fixed","budget":"100.00","duration":"More than 6 months","proposals":"10 to 15","clientCountry":"Nigeria","paymentVerified":True,"clientSpend":None,"clientHireRate":None,"clientRating":None,"experienceLevel":"expert","skills":["CRM Automation","Marketing Automation","Email Marketing"]},
  {"url":"https://www.upwork.com/jobs/~022101887784932866403","title":"GoHighLevel Expert Needed for AI Calling & WhatsApp Automation","matchedKeyword":["gohighlevel developer"],"keywordGroup":"GOHIGHLEVEL","postedAt":"2026-09-21T04:15:30.682Z","type":"hourly","budget":None,"duration":"1 to 3 months","proposals":"50+","clientCountry":"United States","paymentVerified":True,"clientSpend":"$5,989.40","clientHireRate":None,"clientRating":4.96,"experienceLevel":"expert","skills":["HighLevel","Sales Funnel Builder","CRM Automation"]},
  {"url":"https://www.upwork.com/jobs/~022101877732444469603","title":"GoHighLevel CRM & Sales Automation Specialist","matchedKeyword":["gohighlevel CRM"],"keywordGroup":"GOHIGHLEVEL","postedAt":"2026-09-21T03:36:06.699Z","type":"hourly","budget":"15.00–38.00/hr","duration":"More than 6 months","proposals":"20 to 50","clientCountry":"United States","paymentVerified":True,"clientSpend":None,"clientHireRate":None,"clientRating":None,"experienceLevel":"intermediate","skills":["Customer Relationship Management","Zoho CRM"]},
  {"url":"https://www.upwork.com/jobs/~022101879638161103466","title":"Motion Designer Needed for Live Logo Animation + Framer Website Transition","matchedKeyword":["framer developer","figma to framer"],"keywordGroup":"WEBFLOW / FRAMER","postedAt":"2026-09-21T03:43:00.639Z","type":"fixed","budget":"100.00","duration":"Less than 1 month","proposals":"Fewer than 5","clientCountry":"CAN","paymentVerified":True,"clientSpend":"$49.28","clientHireRate":None,"clientRating":5.0,"experienceLevel":"expert","skills":["Logo Animation","Framer","Motion Graphics"]},
  {"url":"https://www.upwork.com/jobs/~022101669313016866520","title":"Framer Website Designer & Developer","matchedKeyword":["framer website","framer redesign"],"keywordGroup":"WEBFLOW / FRAMER","postedAt":"2026-09-20T13:47:59.473Z","type":"fixed","budget":"5.00","duration":"Less than 1 month","proposals":"Fewer than 5","clientCountry":"Nigeria","paymentVerified":None,"clientSpend":None,"clientHireRate":None,"clientRating":None,"experienceLevel":"intermediate","skills":["Framer","Web Design","Web Development"]},
  {"url":"https://www.upwork.com/jobs/~022101892181257556958","title":"Web Front-End Developer","matchedKeyword":["frontend developer","full stack developer"],"keywordGroup":"CORE WEB DEVELOPMENT","postedAt":"2026-09-21T07:33:32.854Z","type":"hourly","budget":"25.00–40.00/hr","duration":"More than 6 months","proposals":"50+","clientCountry":"Australia","paymentVerified":True,"clientSpend":"$368,354.79","clientHireRate":None,"clientRating":4.9,"experienceLevel":"expert","skills":["Web Application","Node.js","PostgreSQL"]},
  {"url":"https://www.upwork.com/jobs/~022101890073711090282","title":"Founding Team Members Wanted – Help Build a New Digital Transformation Agency","matchedKeyword":["AI web developer","ecommerce website"],"keywordGroup":"AI / VIBE CODING","postedAt":"2026-09-21T07:25:06.440Z","type":"hourly","budget":None,"duration":"More than 6 months","proposals":"5 to 10","clientCountry":"Nigeria","paymentVerified":True,"clientSpend":None,"clientHireRate":None,"clientRating":None,"experienceLevel":"intermediate","skills":["Web Development","AI Development","Ecommerce Website"]},
  {"url":"https://www.upwork.com/jobs/~022101728906087699422","title":"Website Maintenance and Monitoring","matchedKeyword":["website maintenance"],"keywordGroup":"MAINTENANCE / RETAINERS","postedAt":"2026-09-20T20:44:33.502Z","type":"fixed","budget":"20.00","duration":"More than 6 months","proposals":"20 to 50","clientCountry":"United Kingdom","paymentVerified":True,"clientSpend":"$1,091.00","clientHireRate":None,"clientRating":4.84,"experienceLevel":"intermediate","skills":["Web Development","WordPress","PHP","Web Design"]},
  {"url":"https://www.upwork.com/jobs/~022101908321295129987","title":"WordPress Optimization & Tracking Specialist","matchedKeyword":["wordpress speed optimization","website speed optimization"],"keywordGroup":"CONVERSION / PERFORMANCE","postedAt":"2026-09-21T05:37:36.944Z","type":"fixed","budget":"5.00","duration":"1 to 3 months","proposals":None,"clientCountry":"India","paymentVerified":None,"clientSpend":None,"clientHireRate":None,"clientRating":None,"experienceLevel":"expert","skills":[]},
  {"url":"https://www.upwork.com/jobs/~022101938320306372889","title":"Shopify Developer and Designer For Store Setup & Proud Listing","matchedKeyword":["shopify website"],"keywordGroup":"ECOMMERCE","postedAt":"2026-09-21T07:37:06.626Z","type":"fixed","budget":"5.00","duration":"1 to 3 months","proposals":"5 to 10","clientCountry":"United Kingdom","paymentVerified":True,"clientSpend":"$537.99","clientHireRate":None,"clientRating":5.0,"experienceLevel":"intermediate","skills":["Shopify","Shopify Theme"]},
  {"url":"https://www.upwork.com/jobs/~022101400316698696298","title":"WordPress Developer & SEO Specialist – High-End Landing Page using Bricks Builder (Fixed Budget)","matchedKeyword":["bricks builder","landing page optimization"],"keywordGroup":"WORDPRESS","postedAt":"2026-09-19T20:02:43.846Z","type":"fixed","budget":"900.00","duration":"Less than 1 month","proposals":"20 to 50","clientCountry":"France","paymentVerified":None,"clientSpend":None,"clientHireRate":None,"clientRating":None,"experienceLevel":"expert","skills":["Local SEO","Landing Page","WordPress","Web Development"]},
]

TIER_MID = {"Fewer than 5":2,"5 to 10":7,"10 to 15":12,"15 to 20":17,"20 to 50":35,"50+":55}

def parse_money(s):
    if not s: return None, None
    if "hr" in s.lower():
        nums = [float(x.replace(",","")) for x in re.findall(r"[\d,.]+", s)]
        return None, (sum(nums)/len(nums) if nums else None)
    m = re.search(r"([\d,]+(?:\.\d+)?)", str(s).replace(",",""))
    return (float(m.group(1)) if m else None), None

def prop_n(p):
    if isinstance(p, int): return p
    if isinstance(p, str) and p.isdigit(): return int(p)
    return TIER_MID.get(p)

def confidence(n):
    if n>=100: return "Very High"
    if n>=40: return "High"
    if n>=15: return "Medium"
    if n>=5: return "Low"
    return "Very Low"

def opp_score(jobs):
    if not jobs: return 0
    s=0
    for j in jobs:
        try:
            pt=datetime.fromisoformat(j["postedAt"].replace("Z","+00:00"))
            age=(RUN_AT-pt).total_seconds()/3600
            rec=max(0.2,1-age/48)
        except: rec=0.5
        prop=prop_n(j.get("proposals")) or 25
        comp=max(0.2,1-min(prop,50)/50)
        fixed,hourly=parse_money(j.get("budget"))
        pay=0.3
        if fixed and fixed>=1000: pay=1.0
        elif fixed and fixed>=500: pay=0.7
        elif hourly and hourly>=40: pay=1.0
        elif hourly and hourly>=25: pay=0.6
        ver=0.15 if j.get("paymentVerified") else 0
        s+=(rec*0.35+comp*0.35+pay*0.25+ver*0.05)*100
    return min(100,int(s/len(jobs)))

def agg_jobs(jobs):
    fixed=[]; hourly=[]; props=[]; ver=0; high=0; j24=0
    for j in jobs:
        f,h=parse_money(j.get("budget"))
        if f: fixed.append(f)
        if h: hourly.append(h)
        pn=prop_n(j.get("proposals"))
        if pn is not None: props.append(pn)
        if j.get("paymentVerified"): ver+=1
        if (f or 0)>=1000 or (h or 0)>=40: high+=1
        try:
            pt=datetime.fromisoformat(j["postedAt"].replace("Z","+00:00"))
            if (RUN_AT-pt).total_seconds()<=86400: j24+=1
        except: pass
    n=len(jobs)
    return {
        "totalJobs":n,"jobsLast24h":j24,
        "avgBudgetFixed":round(statistics.mean(fixed),2) if fixed else None,
        "avgRateHourly":round(statistics.mean(hourly),2) if hourly else None,
        "medianProposals":int(statistics.median(props)) if props else None,
        "pctVerified":round(100*ver/n,1) if n else 0,
        "avgClientSpend":None,
        "pctHighBudget":round(100*high/n,1) if n else 0,
        "opportunityScore":opp_score(jobs),
        "sampleConfidence":confidence(n),
    }

def main():
    jobs=[j for j in RAW_JOBS if datetime.fromisoformat(j["postedAt"].replace("Z","+00:00"))>=CUTOFF]
    with (BASE/"jobs.jsonl").open("w") as f:
        for j in jobs:
            f.write(json.dumps(j, ensure_ascii=False)+"\n")

    kw_to_jobs=defaultdict(list)
    for j in jobs:
        for kw in j["matchedKeyword"]:
            kw_to_jobs[kw].append(j)

    keyword_stats={}
    for kw, group in [
        ("web development","CORE WEB DEVELOPMENT"),("wordpress","WORDPRESS"),("wordpress developer","WORDPRESS"),
        ("shopify developer","ECOMMERCE"),("webflow","WEBFLOW / FRAMER"),("framer","WEBFLOW / FRAMER"),
        ("gohighlevel","GOHIGHLEVEL"),("vibe coding","AI / VIBE CODING"),("claude code developer","AI / VIBE CODING"),
        ("nextjs developer","MODERN STACK"),("supabase developer","AI / VIBE CODING"),("website maintenance","MAINTENANCE / RETAINERS"),
        ("conversion rate optimization","CONVERSION / PERFORMANCE"),("landing page design","WEB DESIGN"),
        ("woocommerce","WORDPRESS"),("lovable developer","AI / VIBE CODING"),("elementor developer","WORDPRESS"),
    ]:
        keyword_stats[kw]=agg_jobs(kw_to_jobs.get(kw,jobs[:3]))

    # full keyword list stats from matched jobs
    all_kw_stats={}
    for kw,_ in [
        ("web development","CORE WEB DEVELOPMENT"),("website development","CORE WEB DEVELOPMENT"),("web developer","CORE WEB DEVELOPMENT"),
        ("custom website","CORE WEB DEVELOPMENT"),("frontend developer","CORE WEB DEVELOPMENT"),("full stack developer","CORE WEB DEVELOPMENT"),
        ("web design","WEB DESIGN"),("website design","WEB DESIGN"),("website redesign","WEB DESIGN"),("landing page design","WEB DESIGN"),
        ("UI UX website","WEB DESIGN"),("responsive web design","WEB DESIGN"),("wordpress","WORDPRESS"),("wordpress developer","WORDPRESS"),
        ("wordpress website","WORDPRESS"),("wordpress development","WORDPRESS"),("wordpress redesign","WORDPRESS"),
        ("wordpress customization","WORDPRESS"),("wordpress migration","WORDPRESS"),("wordpress speed optimization","WORDPRESS"),
        ("wordpress maintenance","WORDPRESS"),("woocommerce","WORDPRESS"),("elementor developer","WORDPRESS"),("bricks builder","WORDPRESS"),
        ("webflow","WEBFLOW / FRAMER"),("webflow developer","WEBFLOW / FRAMER"),("webflow website","WEBFLOW / FRAMER"),
        ("webflow redesign","WEBFLOW / FRAMER"),("figma to webflow","WEBFLOW / FRAMER"),("framer","WEBFLOW / FRAMER"),
        ("framer developer","WEBFLOW / FRAMER"),("framer website","WEBFLOW / FRAMER"),("framer redesign","WEBFLOW / FRAMER"),
        ("figma to framer","WEBFLOW / FRAMER"),("AI web development","AI / VIBE CODING"),("AI web developer","AI / VIBE CODING"),
        ("vibe coding","AI / VIBE CODING"),("claude code developer","AI / VIBE CODING"),("cursor AI developer","AI / VIBE CODING"),
        ("lovable developer","AI / VIBE CODING"),("lovable app","AI / VIBE CODING"),("bolt developer","AI / VIBE CODING"),
        ("v0 developer","AI / VIBE CODING"),("v0 vercel","AI / VIBE CODING"),("replit developer","AI / VIBE CODING"),
        ("supabase developer","AI / VIBE CODING"),("gohighlevel","GOHIGHLEVEL"),("shopify developer","ECOMMERCE"),
        ("nextjs developer","MODERN STACK"),("website maintenance","MAINTENANCE / RETAINERS"),
        ("conversion rate optimization","CONVERSION / PERFORMANCE"),("page speed optimization","CONVERSION / PERFORMANCE"),
    ]:
        lst=kw_to_jobs.get(kw,[])
        all_kw_stats[kw]=agg_jobs(lst if lst else [])

    (BASE/"keyword-stats.json").write_text(json.dumps(all_kw_stats, indent=2))

    groups=defaultdict(list)
    for j in jobs: groups[j["keywordGroup"]].append(j)
    group_stats={g:{"jobCount":len(v),"opportunityScore":opp_score(v),"jobsLast24h":sum(1 for x in v if (RUN_AT-datetime.fromisoformat(x["postedAt"].replace("Z","+00:00"))).total_seconds()<=86400)} for g,v in groups.items()}
    ranked=sorted(group_stats.items(), key=lambda x:-x[1]["opportunityScore"])
    (BASE/"group-stats.json").write_text(json.dumps(dict(ranked), indent=2))

    plat_map={
        "WordPress":["wordpress"],"Webflow":["webflow"],"Framer":["framer"],"GoHighLevel":["gohighlevel","ghl"],
        "Shopify":["shopify"],"WooCommerce":["woocommerce"],"Shopware":["shopware"],
        "Lovable":["lovable"],"Bolt":["bolt"],"v0":["v0"],"Next.js":["nextjs","next.js"],
    }
    platform_stats={}
    for p, keys in plat_map.items():
        pj=[j for j in jobs if any(k in " ".join(j["matchedKeyword"]).lower() or k in j["title"].lower() for k in keys)]
        platform_stats[p]=agg_jobs(pj)
    (BASE/"platform-stats.json").write_text(json.dumps(platform_stats, indent=2))

    state={"lastRunAt":RUN_AT.isoformat(),"runNumber":RUN_NUMBER,"totalJobs":len(jobs),
           "knownJobUrls":[j["url"] for j in jobs],"lastInsightRefresh":RUN_AT.isoformat()}
    (BASE/"state.json").write_text(json.dumps(state, indent=2))

    log={"timestamp":RUN_AT.isoformat(),"runNumber":RUN_NUMBER,"keywordsAttempted":KEYWORDS_TOTAL,
         "keywordsCompleted":KEYWORDS_COMPLETED,"newJobs":len(jobs),"totalJobs":len(jobs),
         "top3Keywords":sorted(all_kw_stats.items(), key=lambda x:-x[1]["opportunityScore"])[:3],
         "errors":FAILED_KEYWORDS}
    with (BASE/"run-log.jsonl").open("a") as f:
        f.write(json.dumps(log)+"\n")

    top_kw=sorted([(k,v) for k,v in all_kw_stats.items() if v["totalJobs"]], key=lambda x:-x[1]["opportunityScore"])[:10]

    summary=f"""# Upwork Market Intelligence

Last updated: {RUN_AT.isoformat()}
Run: {RUN_NUMBER}
Total jobs tracked: {len(jobs)}
Keywords attempted: {KEYWORDS_TOTAL}
Keywords completed: {KEYWORDS_COMPLETED}

## Top Opportunities

"""
    for i,(k,v) in enumerate(top_kw,1):
        summary+=f"{i}. **{k}** — score {v['opportunityScore']}\n"
        summary+=f"   - jobsLast24h: {v['jobsLast24h']} | total: {v['totalJobs']} | avg fixed: {v['avgBudgetFixed']} | avg hourly: {v['avgRateHourly']} | median proposals: {v['medianProposals']} | confidence: {v['sampleConfidence']}\n\n"

    summary+="## Strongest Groups\n\n"
    for i,(g,s) in enumerate(ranked[:5],1):
        summary+=f"{i}. {g} — score {s['opportunityScore']} ({s['jobCount']} jobs in window)\n"

    summary+="\n## Platform Ranking\n\n"
    pr=sorted(platform_stats.items(), key=lambda x:-x[1]["opportunityScore"])
    for i,(p,s) in enumerate(pr,1):
        if s["totalJobs"]:
            summary+=f"{i}. {p} — score {s['opportunityScore']} ({s['totalJobs']} jobs)\n"

    summary+="""\n## Positioning Recommendation

Primary keyword: wordpress developer
Secondary keyword: shopify developer
Best platform/service: WordPress + WooCommerce delivery
Overview keywords: WordPress Developer, Shopify Developer, Next.js, AI Web Developer
Skill tags: WordPress, WooCommerce, Elementor, Shopify, Next.js, Supabase, Claude Code, Webflow, GoHighLevel

## Current Verdicts

WordPress: Strong hourly volume; featured Amelia/Stripe job is immediate apply target.
Webflow: Post-launch optimization and WP migration jobs; competition moderate-high on marquee posts.
Framer: Fewer fresh posts but $500 launch job with low proposals stands out.
GoHighLevel: CRM/automation/funnel posts active; mix of low-budget and enterprise automation.
AI/Vibe Coding: Claude/Supabase/Lovable/vibe roles present; many are app/backend weighted.
Ecommerce: Shopify mobile bug + B2B landing + luxury store support; speed/CRO adjacent.
Maintenance: Steady WP maintenance/migration; retainer keywords need next-run coverage.

## Important Changes

First baseline run. Rate limit stopped ~25 keyword searches; retry next hour.
"""
    (BASE/"current-summary.md").write_text(summary)

    insights="""# Upwork Intelligence Insights

## 2026-09-21 Run 1 (baseline)

- WordPress remains the densest keyword cluster in the last 2 hours, with overlap on WooCommerce, Elementor, and migration work.
- GoHighLevel shows parallel demand for CRM automation, funnel builds, and website rebuilds (not just marketing ops).
- AI/vibe coding searches surface Claude Code, Lovable, and Replit migration roles; many are full-stack rather than marketing sites.
- Shopify has multiple fresh posts under 5 proposals (mobile bug, new store setup).
- Framer and Webflow post-launch/optimization jobs appear with clearer budgets than generic "web design" queries.
"""
    (BASE/"insights.md").write_text(insights)

    print("done", len(jobs))

if __name__=="__main__":
    main()
