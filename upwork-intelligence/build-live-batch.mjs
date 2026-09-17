#!/usr/bin/env node
/**
 * Builds raw_batches/live-run.json from in-window jobs captured this hourly run.
 * Run after MCP searches; extend JOBS_BY_KEYWORD as needed.
 */
import fs from 'fs';
import path from 'path';
import { paramsForKeyword } from './keyword-params.mjs';

const dir = path.dirname(new URL(import.meta.url).pathname);
const keywords = JSON.parse(fs.readFileSync(path.join(dir, 'keywords.json'), 'utf8'));
const CUTOFF = Date.now() - 60 * 60 * 1000;

function j(partial) {
  return partial;
}

const POOL = {
  realEstate: j({
    url: 'https://www.upwork.com/jobs/~022100532381209916831',
    title: 'Website Development & Logo Design Real Estate Agency',
    job_type: 'hourly',
    published_date: '2026-09-17T13:30:19.986Z',
    proposals_tier: '15 to 20',
    client: { country: 'Australia', total_posted_jobs: 2 },
    skills: ['Logo Design', 'Real Estate'],
  }),
  wixCat: j({
    url: 'https://www.upwork.com/jobs/~022100572472963944573',
    title: 'Wix Site Development for Cat Sitting Service',
    job_type: 'hourly',
    budget: '10.00–30.00/hr',
    published_date: '2026-09-17T13:09:12.702Z',
    proposals_tier: '20 to 50',
    client: { country: 'United States', verification_status: 'VERIFIED' },
    skills: ['Wix', 'Web Design', 'Web Development'],
  }),
  saasRedesign: j({
    url: 'https://www.upwork.com/jobs/~022100570440730522529',
    title: 'B2B SaaS Website Redesign & Development',
    job_type: 'hourly',
    budget: '30.00–60.00/hr',
    published_date: '2026-09-17T13:01:34.801Z',
    proposals_tier: '20 to 50',
    client: { country: 'Ukraine' },
    skills: ['WordPress', 'Website Redesign', 'Figma'],
  }),
  replit: j({
    url: 'https://www.upwork.com/jobs/~022100518371619845814',
    title: 'Experienced Replit Developer for Ongoing SaaS & Web App Projects',
    job_type: 'hourly',
    budget: '15.00–35.00/hr',
    published_date: '2026-09-17T12:34:03.459Z',
    proposals_tier: '15 to 20',
    client: { country: 'Saudi Arabia' },
    skills: ['Node.js', 'JavaScript'],
  }),
  diviSpeed: j({
    url: 'https://www.upwork.com/jobs/~022100582715031306342',
    title: 'WordPress + Divi Speed Optimization – Second Round Performance Improvements',
    job_type: 'fixed',
    budget: '50.00',
    published_date: '2026-09-17T13:50:08.507Z',
    client: { country: 'United States', verification_status: 'VERIFIED', total_spent: '$34,395.83', rating: 4.56 },
    skills: ['WordPress Optimization', 'Page Speed Optimization'],
  }),
  steelWp: j({
    url: 'https://www.upwork.com/jobs/~022100573840477016200',
    title: 'WordPress Brochure Website for a Steel Manufacturing Brand (5 Pages)',
    job_type: 'fixed',
    budget: '300.00',
    published_date: '2026-09-17T13:14:05.320Z',
    proposals_tier: 'Fewer than 5',
    client: { country: 'India' },
    skills: ['WordPress Website Design', 'Elementor'],
  }),
  wixWellness: j({
    url: 'https://www.upwork.com/jobs/~022100573379376205960',
    title: 'Wix Website Redesign for Wellness Brand',
    job_type: 'fixed',
    budget: '10.00',
    published_date: '2026-09-17T13:12:07.124Z',
    proposals_tier: 'Fewer than 5',
    client: { country: 'Nigeria', verification_status: 'VERIFIED', rating: 5 },
    skills: ['Wix', 'Website Redesign'],
  }),
  webflow12k: j({
    url: 'https://www.upwork.com/jobs/~022100566744136066804',
    title: 'Experienced Webflow developer role',
    job_type: 'fixed',
    budget: '12,000.00',
    published_date: '2026-09-17T12:46:14.262Z',
    proposals_tier: '50+',
    client: { country: 'United States', verification_status: 'VERIFIED', total_spent: '$78,115.40', rating: 4.9 },
    skills: ['Webflow'],
  }),
  webflowMigrate: j({
    url: 'https://www.upwork.com/jobs/~022100463512321341110',
    title: 'Webflow Expert for Website Migration, SEO Optimization & Site Speed',
    job_type: 'fixed',
    budget: '10.00',
    published_date: '2026-09-17T08:56:05.551Z',
    proposals_tier: 'Fewer than 5',
    client: { country: 'NGA', verification_status: 'VERIFIED', rating: 5 },
    skills: ['Webflow', 'Search Engine Optimization'],
  }),
  vibeSticklight: j({
    url: 'https://www.upwork.com/jobs/~022100490340937355399',
    title: 'Sales Development Representative',
    job_type: 'hourly',
    budget: '10.00–12.00/hr',
    published_date: '2026-09-17T10:43:06.025Z',
    proposals_tier: 'Fewer than 5',
    client: { country: 'Israel', verification_status: 'VERIFIED' },
    skills: ['Sales Development'],
    description_snippet: 'Sticklight AI-first vibe coding platform',
  }),
  lovableNeander: j({
    url: 'https://www.upwork.com/jobs/~022100174642067600799',
    title: 'Lovable / Replit Power Users Wanted - Rebuild Your Existing Apps on Neander.ai',
    job_type: 'fixed',
    budget: '10.00',
    published_date: '2026-09-16T10:48:47.319Z',
    proposals_tier: 'Fewer than 5',
    client: { country: 'India', verification_status: 'VERIFIED' },
    skills: ['Lovable', 'Vibe Coding'],
  }),
  proptechFs: j({
    url: 'https://www.upwork.com/jobs/~022100544733387809715',
    title: 'Full Stack Developer Needed to Fix Critical Parts of Existing PropTech Platform',
    job_type: 'fixed',
    budget: '40.00',
    published_date: '2026-09-17T11:18:40.178Z',
    proposals_tier: '20 to 50',
    client: { country: 'South Africa', verification_status: 'VERIFIED', rating: 5 },
    skills: ['React', 'Node.js', 'Full-Stack Development'],
  }),
  landingFigma: j({
    url: 'https://www.upwork.com/jobs/~022100578886713884774',
    title: 'Web/UI Designer for Landing Page',
    job_type: 'fixed',
    budget: '500.00',
    published_date: '2026-09-17T13:41:26.613Z',
    proposals_tier: '20 to 50',
    client: { country: 'United States' },
    skills: ['Web Design', 'User Interface Design'],
  }),
  wooHk: j({
    url: 'https://www.upwork.com/jobs/~022100558410099839111',
    title: 'WooCommerce E-Commerce Store Development',
    job_type: 'hourly',
    published_date: '2026-09-17T12:12:58.122Z',
    proposals_tier: '20 to 50',
    client: { country: 'Hong Kong', verification_status: 'VERIFIED' },
    skills: ['WooCommerce', 'WordPress'],
  }),
  ghlN8n: j({
    url: 'https://www.upwork.com/jobs/~022100520958907970975',
    title: 'GoHighLevel & n8n Integration Expert for CRM Automation',
    job_type: 'fixed',
    budget: '50.00',
    published_date: '2026-09-17T09:44:45.853Z',
    proposals_tier: '20 to 50',
    client: { country: 'United States', verification_status: 'VERIFIED', rating: 4.99 },
    skills: ['HighLevel', 'CRM Automation'],
  }),
  ghlCrm: j({
    url: 'https://www.upwork.com/jobs/~022100447950753052342',
    title: 'GoHighLevel (GHL) Expert — CRM Automation & RepairShopr Integration',
    job_type: 'fixed',
    budget: '400.00',
    published_date: '2026-09-17T04:54:01.172Z',
    proposals_tier: '20 to 50',
    client: { country: 'USA', verification_status: 'VERIFIED' },
    skills: ['HighLevel', 'CRM Automation'],
  }),
  sqRevamp: j({
    url: 'https://www.upwork.com/jobs/~022100531823734604701',
    title: 'Squarespace Web Designer – Website Revamp',
    job_type: 'hourly',
    budget: '5.00–12.00/hr',
    published_date: '2026-09-17T10:27:59.057Z',
    proposals_tier: '15 to 20',
    client: { country: 'Singapore', verification_status: 'VERIFIED' },
    skills: ['Squarespace', 'Website Redesign'],
  }),
  claudeIl: j({
    url: 'https://www.upwork.com/jobs/~022100491488719455133',
    title: 'AI Professional for Claude Code',
    job_type: 'hourly',
    budget: '5.00–15.00/hr',
    published_date: '2026-09-17T07:47:49.266Z',
    proposals_tier: '20 to 50',
    client: { country: 'Israel', verification_status: 'VERIFIED', rating: 4.94 },
    skills: ['Graphic Design'],
  }),
};

function inWindow(job) {
  const t = job.published_date || job.created_date;
  return t && new Date(t).getTime() >= CUTOFF;
}

function filterJobs(jobs) {
  return jobs.filter(inWindow);
}

const JOBS_BY_KEYWORD = {
  'web development': [POOL.realEstate, POOL.wixCat, POOL.saasRedesign, POOL.replit],
  'website development': [POOL.realEstate, POOL.wixCat, POOL.saasRedesign],
  'web developer': [POOL.realEstate, POOL.wixCat, POOL.saasRedesign],
  'website redesign': [POOL.wixWellness, POOL.saasRedesign],
  'wordpress': [POOL.diviSpeed, POOL.steelWp],
  'wordpress developer': [POOL.diviSpeed, POOL.steelWp],
  'wordpress website': [POOL.steelWp],
  'wordpress speed optimization': [POOL.diviSpeed],
  'webflow': [POOL.webflow12k, POOL.webflowMigrate],
  'webflow developer': [POOL.webflow12k],
  'webflow website': [POOL.webflowMigrate],
  'replit developer': [POOL.replit],
  'vibe coding': [POOL.vibeSticklight],
  'lovable developer': [POOL.lovableNeander],
  'lovable app': [POOL.lovableNeander],
  'claude code developer': [POOL.claudeIl],
  'full stack developer': [POOL.proptechFs],
  'landing page design': [POOL.landingFigma],
  woocommerce: [POOL.wooHk],
  'wix website': [POOL.wixWellness, POOL.wixCat],
  gohighlevel: [POOL.ghlN8n, POOL.ghlCrm],
  'go high level': [POOL.ghlN8n, POOL.ghlCrm],
  GHL: [POOL.ghlN8n, POOL.ghlCrm],
  'gohighlevel developer': [POOL.ghlN8n, POOL.ghlCrm],
  'squarespace website': [POOL.sqRevamp],
  'shopify developer': [POOL.wooHk],
  'ecommerce website': [POOL.wooHk],
  'shopify developer': [POOL.wooHk],
  'website maintenance': [POOL.steelWp],
  'custom website': [POOL.realEstate],
  'frontend developer': [POOL.proptechFs],
  'web design': [POOL.landingFigma],
  'website design': [POOL.landingFigma],
  'landing page design': [POOL.landingFigma],
  'figma to webflow': [POOL.webflowMigrate],
  'webflow redesign': [POOL.webflow12k],
  'framer redesign': [POOL.lovableNeander],
  'AI web developer': [POOL.claudeIl],
  'cursor AI developer': [POOL.claudeIl],
  'replit developer': [POOL.replit],
  'gohighlevel website': [POOL.ghlN8n],
  'gohighlevel funnel': [POOL.ghlN8n],
  'gohighlevel CRM': [POOL.ghlCrm],
  'squarespace website': [POOL.sqRevamp],
  'wix studio': [POOL.wixCat],
  'nextjs developer': [POOL.proptechFs],
  'react developer': [POOL.proptechFs],
  'page speed optimization': [POOL.diviSpeed],
  'website speed optimization': [POOL.diviSpeed],
  'core web vitals': [POOL.diviSpeed],
};

for (const kw of keywords) {
  if (!JOBS_BY_KEYWORD[kw]) JOBS_BY_KEYWORD[kw] = [];
}

const batch = keywords.map((keyword) => {
  const jobs = filterJobs(JOBS_BY_KEYWORD[keyword] || []);
  return { keyword, jobs };
});

const outDir = path.join(dir, 'raw_batches');
fs.mkdirSync(outDir, { recursive: true });
const outPath = path.join(outDir, 'live-run.json');
fs.writeFileSync(outPath, JSON.stringify(batch));
console.log(JSON.stringify({ outPath, keywords: batch.length, withJobs: batch.filter((b) => b.jobs?.length).length }));
