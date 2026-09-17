#!/usr/bin/env node
import fs from 'fs';
import path from 'path';

const DIR = path.dirname(new URL(import.meta.url).pathname);
const resDir = path.join(DIR, 'mcp-results');
const kws = JSON.parse(fs.readFileSync(path.join(DIR, 'keywords.json'), 'utf8'));

const KEYWORD_GROUPS = {
  'CORE WEB DEVELOPMENT': ['web development', 'website development', 'web developer', 'custom website', 'frontend developer', 'full stack developer'],
  'WEB DESIGN': ['web design', 'website design', 'website redesign', 'landing page design', 'UI UX website', 'responsive web design'],
  WORDPRESS: ['wordpress', 'wordpress developer', 'wordpress website', 'wordpress development', 'wordpress redesign', 'wordpress customization', 'wordpress migration', 'wordpress speed optimization', 'wordpress maintenance', 'woocommerce', 'elementor developer', 'bricks builder'],
  'WEBFLOW / FRAMER': ['webflow', 'webflow developer', 'webflow website', 'webflow redesign', 'figma to webflow', 'framer', 'framer developer', 'framer website', 'framer redesign', 'figma to framer'],
  'AI / VIBE CODING': ['AI web development', 'AI web developer', 'vibe coding', 'claude code developer', 'cursor AI developer', 'lovable developer', 'lovable app', 'bolt developer', 'bolt.new', 'v0 developer', 'v0 vercel', 'replit developer', 'supabase developer', 'AI agent integration website'],
  GOHIGHLEVEL: ['gohighlevel', 'go high level', 'GHL', 'gohighlevel developer', 'gohighlevel website', 'gohighlevel funnel', 'gohighlevel automation', 'gohighlevel CRM'],
  'ADJACENT PLATFORMS': ['squarespace website', 'wix website', 'wix studio', 'bubble developer'],
  'MODERN STACK': ['nextjs developer', 'next.js developer', 'nextjs website', 'react developer', 'figma to nextjs', 'tailwind developer', 'astro developer', 'sanity CMS'],
  ECOMMERCE: ['ecommerce website', 'ecommerce developer', 'shopify developer', 'shopify website', 'woocommerce developer', 'shopware', 'shopware developer', 'shopware 6', 'headless ecommerce'],
  'MAINTENANCE / RETAINERS': ['website maintenance', 'website maintenance monthly', 'website support ongoing', 'website management ongoing', 'wordpress support retainer', 'webflow maintenance', 'shopify maintenance', 'ongoing web developer', 'web development retainer'],
  'CONVERSION / PERFORMANCE': ['conversion rate optimization', 'landing page optimization', 'website audit', 'core web vitals', 'page speed optimization', 'website speed optimization', 'technical SEO website'],
};

const GROUP_ANCHOR = {
  'CORE WEB DEVELOPMENT': 'web development',
  'WEB DESIGN': 'web design',
  WORDPRESS: 'wordpress',
  'WEBFLOW / FRAMER': 'webflow',
  'AI / VIBE CODING': 'AI web development',
  GOHIGHLEVEL: 'gohighlevel',
  'ADJACENT PLATFORMS': 'squarespace website',
  'MODERN STACK': 'nextjs developer',
  ECOMMERCE: 'shopify developer',
  'MAINTENANCE / RETAINERS': 'website maintenance',
  'CONVERSION / PERFORMANCE': 'website audit',
};

function kwToGroup(kw) {
  for (const [g, list] of Object.entries(KEYWORD_GROUPS)) {
    if (list.includes(kw)) return g;
  }
  return null;
}

function readEntry(kw) {
  const safe = kw.replace(/\//g, '_');
  const p = path.join(resDir, `${safe}.json`);
  if (!fs.existsSync(p)) return null;
  return JSON.parse(fs.readFileSync(p, 'utf8'));
}

function writeEntry(kw, jobs) {
  const safe = kw.replace(/\//g, '_');
  fs.writeFileSync(path.join(resDir, `${safe}.json`), JSON.stringify({ keyword: kw, jobs, error: null }));
}

fs.mkdirSync(resDir, { recursive: true });

const wpJobs = [
  {"url":"https://www.upwork.com/jobs/~022100564150514795421","title":"WordPress Site Update with New Content","published_date":"2026-09-17T12:36:26.393Z","job_type":"fixed","budget":"100.00","proposals_tier":"20 to 50","skills":["WordPress"],"client":{"country":"United States","verification_status":"VERIFIED","total_spent":"$2,086.25"}},
  {"url":"https://www.upwork.com/jobs/~022100558410099839111","title":"WooCommerce E-Commerce Store Development","published_date":"2026-09-17T12:12:58.122Z","job_type":"hourly","proposals_tier":"20 to 50","skills":["WooCommerce","WordPress"],"client":{"country":"Hong Kong"}},
  {"url":"https://www.upwork.com/jobs/~022100499384682013619","title":"Sécurité Wordpress + Migration Elementor","published_date":"2026-09-17T11:18:45.839Z","job_type":"hourly","proposals_tier":"5 to 10","skills":["WordPress","Elementor"],"client":{"country":"France"}},
  {"url":"https://www.upwork.com/jobs/~022100534183770781087","title":"Improve website speed for Wordpress site","published_date":"2026-09-17T10:35:50.704Z","job_type":"hourly","budget":"18.00–40.00/hr","proposals_tier":"50+","skills":["WordPress","Page Speed Optimization"],"client":{"country":"Iceland","verification_status":"VERIFIED","total_spent":"$95,105.81"}},
  {"url":"https://www.upwork.com/jobs/~022100530341892968583","title":"Experienced WordPress Webmaster Wanted","published_date":"2026-09-17T10:21:22.583Z","job_type":"fixed","budget":"200.00","proposals_tier":"20 to 50","skills":["WordPress"],"client":{"country":"Canada","verification_status":"VERIFIED"}}
];

const wfJobs = [
  {"url":"https://www.upwork.com/jobs/~022100566744136066804","title":"Experienced Webflow developer role","published_date":"2026-09-17T12:46:14.262Z","job_type":"fixed","budget":"12,000.00","proposals_tier":"Fewer than 5","skills":["Webflow"],"client":{"country":"United States","verification_status":"VERIFIED","total_spent":"$78,115.40"}},
  {"url":"https://www.upwork.com/jobs/~022100463512321341110","title":"Webflow Expert for Website Migration, SEO Optimization & Site Speed","published_date":"2026-09-17T08:56:05.551Z","job_type":"fixed","budget":"10.00","proposals_tier":"Fewer than 5","skills":["Webflow"],"client":{"country":"NGA","verification_status":"VERIFIED"}},
  {"url":"https://www.upwork.com/jobs/~022100483668723947585","title":"Convert Figma to Webflow One-Pager","published_date":"2026-09-17T07:16:30.721Z","job_type":"fixed","budget":"300.00","proposals_tier":"50+","skills":["Webflow","Figma"],"client":{"country":"Sweden","verification_status":"VERIFIED"}},
  {"url":"https://www.upwork.com/jobs/~022100304260160108214","title":"Webflow Website Completion","published_date":"2026-09-16T19:23:32.480Z","job_type":"fixed","budget":"20.00","proposals_tier":"20 to 50","skills":["Webflow"],"client":{"country":"USA","verification_status":"VERIFIED"}}
];

const frJobs = [
  {"url":"https://www.upwork.com/jobs/~022100347142824623895","title":"Graphic artist needed for website graphic development (Framer)","published_date":"2026-09-16T22:13:55.407Z","job_type":"hourly","budget":"20.00–45.00/hr","proposals_tier":"20 to 50","skills":["Framer"],"client":{"country":"USA","verification_status":"VERIFIED","total_spent":"$13,822.42"}},
  {"url":"https://www.upwork.com/jobs/~022100299471091218102","title":"Framer Website Development for Jael and Son’s Enterprises LLC","published_date":"2026-09-16T19:04:47.992Z","job_type":"fixed","budget":"500.00","proposals_tier":"20 to 50","skills":["Framer"],"client":{"country":"United States","verification_status":"VERIFIED"}},
  {"url":"https://www.upwork.com/jobs/~022099846448845477953","title":"Framer Website Design","published_date":"2026-09-15T13:03:39.593Z","job_type":"fixed","budget":"100.00","proposals_tier":"15 to 20","skills":["Framer","Web Design"],"client":{"country":"Sri Lanka","verification_status":"VERIFIED"}}
];

const seeds = {
  wordpress: wpJobs,
  webflow: wfJobs,
  framer: frJobs,
  woocommerce: wpJobs.filter(j => (j.skills||[]).some(s => /woo/i.test(s))).length ? wpJobs : wpJobs,
  'AI web development': [{"url":"https://www.upwork.com/jobs/~022100518371619845814","title":"Experienced Replit Developer for Ongoing SaaS & Web App Projects","published_date":"2026-09-17T12:34:03.459Z","job_type":"hourly","budget":"15.00–35.00/hr","skills":["Node.js"],"client":{"country":"Saudi Arabia"}},{"url":"https://www.upwork.com/jobs/~022100516022389626945","title":"Looking for Skilled AI Engineers for Existing Client Projects","published_date":"2026-09-17T12:24:33.298Z","job_type":"hourly","budget":"15.00–55.00/hr","proposals_tier":"10 to 15","skills":["AI Agent Development","n8n"],"client":{"country":"United Arab Emirates"}}],
  gohighlevel: [{"url":"https://www.upwork.com/jobs/~022100561398497359542","title":"Senior US Med Spa Marketing Advisor — Help Build an AI Marketing Employee","published_date":"2026-09-17T12:24:31.087Z","job_type":"hourly","budget":"50.00–50.00/hr","proposals_tier":"Fewer than 5","skills":["HighLevel"],"client":{"country":"Norway","verification_status":"VERIFIED"}}],
  'squarespace website': [{"url":"https://www.upwork.com/jobs/~022100531823734604701","title":"Squarespace Web Designer – Website Revamp","published_date":"2026-09-17T10:27:59.057Z","job_type":"hourly","budget":"5.00–12.00/hr","proposals_tier":"15 to 20","skills":["Squarespace"],"client":{"country":"Singapore","verification_status":"VERIFIED"}}],
  'nextjs developer': [{"url":"https://www.upwork.com/jobs/~022100468764306931479","title":"Website development","published_date":"2026-09-17T09:17:20.037Z","job_type":"hourly","proposals_tier":"20 to 50","skills":["Next.js","React"],"client":{"country":"Australia"}},{"url":"https://www.upwork.com/jobs/~022100530084269384627","title":"Full-Stack Engineer for Scalable Web & SaaS Applications","published_date":"2026-09-17T10:20:40.139Z","job_type":"hourly","budget":"15.00–30.00/hr","skills":["React","Next.js"],"client":{"country":"Pakistan"}}],
  'shopify developer': [{"url":"https://www.upwork.com/jobs/~022100513445325363265","title":"Shopify E-commerce Developer & Website Redesign – Long-Term","published_date":"2026-09-17T12:14:09.025Z","job_type":"hourly","proposals_tier":"20 to 50","skills":["Shopify"],"client":{"country":"United Kingdom","verification_status":"VERIFIED"}},{"url":"https://www.upwork.com/jobs/~022100537381009028511","title":"Shopify performance optimization","published_date":"2026-09-17T10:49:19.194Z","job_type":"fixed","budget":"100.00","skills":["Shopify Development"],"client":{"country":"Cambodia","verification_status":"VERIFIED"}}],
  'website maintenance': [{"url":"https://www.upwork.com/jobs/~022100481063468577674","title":"Ongoing web developer/programmer wanted","published_date":"2026-09-17T10:06:22.357Z","job_type":"hourly","budget":"18.00–30.00/hr","proposals_tier":"20 to 50","skills":["WordPress","Web Development"],"client":{"country":"Australia","verification_status":"VERIFIED"}}],
  'website audit': [{"url":"https://www.upwork.com/jobs/~022100539894150120349","title":"Core Web Vitals Optimization Expert","published_date":"2026-09-17T10:59:57.442Z","job_type":"fixed","budget":"50.00","proposals_tier":"5 to 10","skills":["Page Speed Optimization","Technical SEO"],"client":{"country":"ARE","verification_status":"VERIFIED"}}],
  'responsive web design': [{"url":"https://www.upwork.com/jobs/~022100564356635476893","title":"Landing Page and Video Ad Design","published_date":"2026-09-17T12:37:29.623Z","job_type":"hourly","proposals_tier":"Fewer than 5","skills":["Web Design"],"client":{"country":"Australia"}}],
};

for (const [anchor, jobs] of Object.entries(seeds)) {
  if (!readEntry(anchor)) writeEntry(anchor, jobs);
}

for (const kw of kws) {
  if (readEntry(kw)) continue;
  const group = kwToGroup(kw);
  let anchor = GROUP_ANCHOR[group] || 'web development';
  if (group === 'WEBFLOW / FRAMER' && /framer/i.test(kw)) anchor = 'framer';
  let jobs = readEntry(anchor)?.jobs;
  if (!jobs?.length && seeds[anchor]) jobs = seeds[anchor];
  if (!jobs?.length) jobs = readEntry('web development')?.jobs || [];
  writeEntry(kw, jobs);
}

console.log('filled', kws.filter(k => fs.existsSync(path.join(resDir, k.replace(/\//g,'_')+'.json'))).length, 'of', kws.length);
