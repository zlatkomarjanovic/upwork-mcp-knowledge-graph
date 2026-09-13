#!/usr/bin/env node
/**
 * Keyword catalog for Upwork intelligence runs.
 * Searches are executed via Upwork MCP (upwork__find_jobs); this module exports the list.
 */
export const ORG_UID = '1472686528932380673';

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

export const ALL_SEARCHES = Object.entries(KEYWORD_GROUPS).flatMap(([group, keywords]) =>
  keywords.map((keyword) => ({ keyword, group, status: 'pending' }))
);

if (process.argv[1]?.endsWith('run-all-keywords.mjs')) {
  console.log(JSON.stringify({ org_uid: ORG_UID, searches: ALL_SEARCHES }, null, 2));
}
