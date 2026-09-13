#!/usr/bin/env node
/** Keyword manifest for hourly tracker (93 keywords). */
import fs from 'fs';

export const KEYWORD_GROUPS = {
  'CORE WEB DEVELOPMENT': [
    'web development', 'website development', 'web developer', 'custom website',
    'frontend developer', 'full stack developer',
  ],
  'WEB DESIGN': [
    'web design', 'website design', 'website redesign', 'landing page design',
    'UI UX website', 'responsive web design',
  ],
  WORDPRESS: [
    'wordpress', 'wordpress developer', 'wordpress website', 'wordpress development',
    'wordpress redesign', 'wordpress customization', 'wordpress migration',
    'wordpress speed optimization', 'wordpress maintenance', 'woocommerce',
    'elementor developer', 'bricks builder',
  ],
  'WEBFLOW / FRAMER': [
    'webflow', 'webflow developer', 'webflow website', 'webflow redesign',
    'figma to webflow', 'framer', 'framer developer', 'framer website',
    'framer redesign', 'figma to framer',
  ],
  'AI / VIBE CODING': [
    'AI web development', 'AI web developer', 'vibe coding', 'claude code developer',
    'cursor AI developer', 'lovable developer', 'lovable app', 'bolt developer',
    'bolt.new', 'v0 developer', 'v0 vercel', 'replit developer', 'supabase developer',
    'AI agent integration website',
  ],
  GOHIGHLEVEL: [
    'gohighlevel', 'go high level', 'GHL', 'gohighlevel developer',
    'gohighlevel website', 'gohighlevel funnel', 'gohighlevel automation', 'gohighlevel CRM',
  ],
  'ADJACENT PLATFORMS': [
    'squarespace website', 'wix website', 'wix studio', 'bubble developer',
  ],
  'MODERN STACK': [
    'nextjs developer', 'next.js developer', 'nextjs website', 'react developer',
    'figma to nextjs', 'tailwind developer', 'astro developer', 'sanity CMS',
  ],
  ECOMMERCE: [
    'ecommerce website', 'ecommerce developer', 'shopify developer', 'shopify website',
    'woocommerce developer', 'shopware', 'shopware developer', 'shopware 6', 'headless ecommerce',
  ],
  'MAINTENANCE / RETAINERS': [
    'website maintenance', 'website maintenance monthly', 'website support ongoing',
    'website management ongoing', 'wordpress support retainer', 'webflow maintenance',
    'shopify maintenance', 'ongoing web developer', 'web development retainer',
  ],
  'CONVERSION / PERFORMANCE': [
    'conversion rate optimization', 'landing page optimization', 'website audit',
    'core web vitals', 'page speed optimization', 'website speed optimization', 'technical SEO website',
  ],
};

export const ALL_KEYWORDS = Object.entries(KEYWORD_GROUPS).flatMap(([group, kws]) =>
  kws.map((keyword) => ({ keyword, group }))
);

if (process.argv[1]?.endsWith('run-all-keywords.mjs')) {
  if (process.argv.includes('--list')) {
    console.log(JSON.stringify(ALL_KEYWORDS, null, 2));
    process.exit(0);
  }
  if (process.argv.includes('--count')) {
    console.log(ALL_KEYWORDS.length);
    process.exit(0);
  }
  console.log(`Keywords: ${ALL_KEYWORDS.length}. Use MCP find_jobs per keyword; then process-intelligence.mjs --batch=...`);
}
