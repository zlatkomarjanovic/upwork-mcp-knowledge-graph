/** Title (1–3 words) or query for Upwork find_jobs search */
export function paramsForKeyword(kw) {
  const queryOnly = new Set([
    'vibe coding',
    'bolt.new',
    'go high level',
    'GHL',
    'gohighlevel funnel',
    'gohighlevel automation',
    'gohighlevel CRM',
    'AI agent integration website',
    'core web vitals',
    'headless ecommerce',
    'sanity CMS',
    'UI UX website',
  ]);
  if (queryOnly.has(kw)) return { query: kw, sort: 'recency', limit: 10 };
  const special = {
    'figma to webflow': { title: 'figma webflow', sort: 'recency', limit: 10 },
    'figma to framer': { title: 'figma framer', sort: 'recency', limit: 10 },
    'figma to nextjs': { title: 'figma nextjs', sort: 'recency', limit: 10 },
    'next.js developer': { title: 'next.js developer', sort: 'recency', limit: 10 },
    'v0 vercel': { title: 'v0 vercel', sort: 'recency', limit: 10 },
    'cursor AI developer': { title: 'cursor developer', sort: 'recency', limit: 10 },
    'claude code developer': { title: 'claude code', sort: 'recency', limit: 10 },
    'AI web development': { title: 'AI web', sort: 'recency', limit: 10 },
    'AI web developer': { title: 'AI web', sort: 'recency', limit: 10 },
    'website maintenance monthly': { title: 'website maintenance', sort: 'recency', limit: 10 },
    'website support ongoing': { title: 'website support', sort: 'recency', limit: 10 },
    'website management ongoing': { title: 'website management', sort: 'recency', limit: 10 },
    'wordpress support retainer': { title: 'wordpress support', sort: 'recency', limit: 10 },
    'web development retainer': { title: 'web development', sort: 'recency', limit: 10 },
    'landing page optimization': { title: 'landing page', sort: 'recency', limit: 10 },
    'technical SEO website': { title: 'technical SEO', sort: 'recency', limit: 10 },
    'conversion rate optimization': { title: 'conversion rate', sort: 'recency', limit: 10 },
  };
  if (special[kw]) return special[kw];
  let title = kw.replace(/\./g, ' ').replace(/\s+to\s+/gi, ' ').trim();
  const words = title.split(/\s+/);
  if (words.length > 3) title = words.slice(0, 3).join(' ');
  return { title, sort: 'recency', limit: 10 };
}
