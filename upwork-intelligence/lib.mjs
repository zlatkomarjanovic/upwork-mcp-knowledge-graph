import fs from "fs";
import path from "path";

const ROOT = path.dirname(new URL(import.meta.url).pathname);
export const DIR = ROOT;

const HIGH_BUDGET_FIXED = 1000;
const HIGH_BUDGET_HOURLY = 40;

export const GROUPS = {
  "Core Web Development": [
    "web development",
    "website development",
    "web developer",
    "custom website",
    "frontend developer",
    "full stack developer",
  ],
  "Web Design": [
    "web design",
    "website design",
    "website redesign",
    "landing page design",
    "UI UX website",
    "responsive web design",
  ],
  WordPress: [
    "wordpress",
    "wordpress developer",
    "wordpress website",
    "wordpress development",
    "wordpress redesign",
    "wordpress customization",
    "wordpress migration",
    "wordpress speed optimization",
    "wordpress maintenance",
    "woocommerce",
    "elementor developer",
    "bricks builder",
  ],
  "Webflow / Framer": [
    "webflow",
    "webflow developer",
    "webflow website",
    "webflow redesign",
    "figma to webflow",
    "framer",
    "framer developer",
    "framer website",
    "framer redesign",
    "figma to framer",
  ],
  "AI / Vibe Coding": [
    "AI web development",
    "AI web developer",
    "vibe coding",
    "claude code developer",
    "cursor AI developer",
    "lovable developer",
    "lovable app",
    "bolt developer",
    "bolt.new",
    "v0 developer",
    "v0 vercel",
    "replit developer",
    "supabase developer",
    "AI agent integration website",
  ],
  GoHighLevel: [
    "gohighlevel",
    "go high level",
    "GHL",
    "gohighlevel developer",
    "gohighlevel website",
    "gohighlevel funnel",
    "gohighlevel automation",
    "gohighlevel CRM",
  ],
  "Adjacent Platforms": [
    "squarespace website",
    "wix website",
    "wix studio",
    "bubble developer",
  ],
  "Modern Stack": [
    "nextjs developer",
    "next.js developer",
    "nextjs website",
    "react developer",
    "figma to nextjs",
    "tailwind developer",
    "astro developer",
    "sanity CMS",
  ],
  Ecommerce: [
    "ecommerce website",
    "ecommerce developer",
    "shopify developer",
    "shopify website",
    "woocommerce developer",
    "shopware",
    "shopware developer",
    "shopware 6",
    "headless ecommerce",
  ],
  "Maintenance / Retainers": [
    "website maintenance",
    "website maintenance monthly",
    "website support ongoing",
    "website management ongoing",
    "wordpress support retainer",
    "webflow maintenance",
    "shopify maintenance",
    "ongoing web developer",
    "web development retainer",
  ],
  "Conversion / Performance": [
    "conversion rate optimization",
    "landing page optimization",
    "website audit",
    "core web vitals",
    "page speed optimization",
    "website speed optimization",
    "technical SEO website",
  ],
};

export const CYCLES = {
  A: ["Core Web Development", "Web Design", "Webflow / Framer", "GoHighLevel"],
  B: ["WordPress", "AI / Vibe Coding", "Modern Stack"],
  C: ["Ecommerce", "Maintenance / Retainers", "Conversion / Performance", "Adjacent Platforms"],
};

export const PRIORITY_KEYWORDS = [
  "web developer",
  "web design",
  "webflow developer",
  "framer developer",
  "wordpress developer",
  "gohighlevel",
  "shopify developer",
  "AI web developer",
];

export const PLATFORMS = [
  "WordPress",
  "Elementor",
  "Bricks",
  "Webflow",
  "Framer",
  "GoHighLevel",
  "Shopify",
  "WooCommerce",
  "Shopware",
  "Wix",
  "Squarespace",
  "Lovable",
  "Bolt",
  "v0",
  "Next.js",
];

const PLATFORM_PATTERNS = [
  ["WordPress", /\bwordpress\b/i],
  ["Elementor", /\belementor\b/i],
  ["Bricks", /\bbricks\b/i],
  ["Webflow", /\bwebflow\b/i],
  ["Framer", /\bframer\b/i],
  ["GoHighLevel", /\b(gohighlevel|go high level|\bghl\b)/i],
  ["Shopify", /\bshopify\b/i],
  ["WooCommerce", /\bwoocommerce\b/i],
  ["Shopware", /\bshopware\b/i],
  ["Wix", /\bwix\b/i],
  ["Squarespace", /\bsquarespace\b/i],
  ["Lovable", /\blovable\b/i],
  ["Bolt", /\bbolt(\.new)?\b/i],
  ["v0", /\bv0\b/i],
  ["Next.js", /\bnext\.?js\b/i],
];

const SKIP_TITLE = /\b(alcohol|gambling|casino|adult|crypto trading|dating)\b/i;

export function keywordToGroup(keyword) {
  for (const [group, kws] of Object.entries(GROUPS)) {
    if (kws.some((k) => k.toLowerCase() === keyword.toLowerCase())) return group;
  }
  return null;
}

export function cycleForHour(h) {
  const slot = h % 3;
  if (slot === 0) return "A";
  if (slot === 1) return "B";
  return "C";
}

export function nextCycle(c) {
  return { A: "B", B: "C", C: "A" }[c];
}

export function readJsonl(file) {
  if (!fs.existsSync(file)) return [];
  return fs
    .readFileSync(file, "utf8")
    .split("\n")
    .filter(Boolean)
    .map((l) => {
      try {
        return JSON.parse(l);
      } catch {
        return null;
      }
    })
    .filter(Boolean);
}

export function appendJsonl(file, obj) {
  fs.appendFileSync(file, JSON.stringify(obj) + "\n");
}

function proposalMid(v) {
  if (v == null) return null;
  if (typeof v === "number") return v;
  if (typeof v === "object" && v.min != null && v.max != null)
    return (Number(v.min) + Number(v.max)) / 2;
  if (typeof v === "object" && v.count != null) return Number(v.count);
  return null;
}

export function mapUpworkJob(raw, matchedKeyword, keywordGroup) {
  const title = raw.title || raw.job_title || "";
  if (SKIP_TITLE.test(title)) return null;
  const url = raw.url || raw.job_url;
  if (!url || !String(url).includes("upwork.com")) return null;

  const client = raw.client || raw.client_info || {};
  const budget = raw.budget || raw.amount || raw.fixed_price;
  let budgetFixed = null;
  let rateHourly = null;
  const jt = (raw.job_type || raw.type || "").toLowerCase();

  function parseMoney(v) {
    if (v == null) return null;
    if (typeof v === "number") return v;
    const s = String(v).replace(/,/g, "");
    const range = s.match(/([\d.]+)\s*[–-]\s*([\d.]+)/);
    if (range) return (parseFloat(range[1]) + parseFloat(range[2])) / 2;
    const n = parseFloat(s.replace(/[^\d.]/g, ""));
    return Number.isNaN(n) ? null : n;
  }

  if (jt.includes("fixed") || jt === "fixed-price") {
    budgetFixed =
      typeof budget === "object" ? parseMoney(budget.amount ?? budget.value) : parseMoney(budget);
  } else if (jt.includes("hourly")) {
    const hr = raw.hourly_budget || raw.rate || budget;
    if (typeof hr === "object") {
      rateHourly =
        hr.min != null && hr.max != null
          ? (Number(hr.min) + Number(hr.max)) / 2
          : parseMoney(hr.amount);
    } else rateHourly = parseMoney(hr);
  }

  const postedAt =
    raw.published_date || raw.created_date || raw.posted_on || raw.created_at || null;

  return {
    url: String(url).split("?")[0],
    title,
    matchedKeywords: [matchedKeyword],
    keywordGroup,
    postedAt,
    type: raw.job_type || raw.type || null,
    budgetFixed,
    rateHourly,
    duration: raw.duration || raw.project_length || null,
    proposals: proposalMid(raw.proposal_count ?? raw.proposals),
    clientCountry: client.country || raw.client_country || null,
    paymentVerified:
      client.verification_status === "verified" ||
      client.payment_verified === true ||
      raw.payment_verified === true ||
      null,
    clientSpend: client.total_spent ?? client.total_charge ?? null,
    clientHireRate: null,
    clientRating: client.rating ?? null,
    experienceLevel: raw.experience_level || null,
    skills: raw.skills || raw.skill_names || [],
  };
}

export function mergeJob(existing, incoming) {
  const kws = new Set([...(existing.matchedKeywords || []), ...(incoming.matchedKeywords || [])]);
  return { ...existing, matchedKeywords: [...kws] };
}

export function inTimeWindow(postedAt, hours) {
  if (!postedAt) return true;
  const t = new Date(postedAt).getTime();
  if (Number.isNaN(t)) return true;
  return Date.now() - t <= hours * 3600 * 1000;
}

function median(arr) {
  const a = arr.filter((x) => x != null && !Number.isNaN(x)).sort((x, y) => x - y);
  if (!a.length) return null;
  const m = Math.floor(a.length / 2);
  return a.length % 2 ? a[m] : (a[m - 1] + a[m]) / 2;
}

function avg(arr) {
  const a = arr.filter((x) => x != null && !Number.isNaN(x));
  if (!a.length) return null;
  return a.reduce((s, x) => s + x, 0) / a.length;
}

function confidence(n) {
  if (n <= 4) return "Very Low";
  if (n <= 14) return "Low";
  if (n <= 39) return "Medium";
  if (n <= 99) return "High";
  return "Very High";
}

function opportunityScore(jobs, now = Date.now()) {
  const last24 = jobs.filter((j) => {
    if (!j.postedAt) return false;
    const t = new Date(j.postedAt).getTime();
    return !Number.isNaN(t) && now - t <= 86400000;
  });
  const n24 = last24.length || 0;
  const props = jobs.map((j) => j.proposals).filter((x) => x != null);
  const medP = median(props) ?? 50;
  const fixed = jobs.map((j) => j.budgetFixed).filter((x) => x != null && x > 0);
  const hourly = jobs.map((j) => j.rateHourly).filter((x) => x != null && x > 0);
  const avgF = avg(fixed) ?? 0;
  const avgH = avg(hourly) ?? 0;
  let high = 0;
  let budgetN = 0;
  for (const j of jobs) {
    if (j.budgetFixed != null && j.budgetFixed > 0) {
      budgetN++;
      if (j.budgetFixed >= HIGH_BUDGET_FIXED) high++;
    } else if (j.rateHourly != null && j.rateHourly > 0) {
      budgetN++;
      if (j.rateHourly >= HIGH_BUDGET_HOURLY) high++;
    }
  }
  const pctHigh = budgetN ? (high / budgetN) * 100 : 0;
  const budgetNorm = Math.min(100, (avgF / 5000) * 50 + (avgH / 80) * 50);
  const propNorm = Math.max(0, 100 - medP * 2);
  const raw = n24 * 3 + budgetNorm * 0.35 + propNorm * 0.25 + pctHigh * 0.4;
  const score = Math.max(1, Math.min(100, Math.round(raw)));
  return { score, n24, pctHigh, medP, avgF, avgH };
}

export function computeKeywordStats(allJobs) {
  const byKw = {};
  for (const j of allJobs) {
    for (const kw of j.matchedKeywords || []) {
      if (!byKw[kw]) byKw[kw] = [];
      byKw[kw].push(j);
    }
  }
  const stats = {};
  for (const [kw, jobs] of Object.entries(byKw)) {
    const o = opportunityScore(jobs);
    stats[kw] = {
      keyword: kw,
      group: keywordToGroup(kw),
      totalJobs: jobs.length,
      jobsLast24h: o.n24,
      avgBudgetFixed: o.avgF || null,
      avgRateHourly: o.avgH || null,
      medianProposals: o.medP,
      pctHighBudget: Math.round(o.pctHigh * 10) / 10,
      opportunityScore: o.score,
      sampleConfidence: confidence(jobs.length),
    };
  }
  return stats;
}

export function computeGroupStats(allJobs) {
  const byG = {};
  for (const j of allJobs) {
    const g = j.keywordGroup || "Unknown";
    if (!byG[g]) byG[g] = [];
    byG[g].push(j);
  }
  const stats = {};
  for (const [g, jobs] of Object.entries(byG)) {
    const o = opportunityScore(jobs);
    stats[g] = {
      totalJobs: jobs.length,
      jobsLast24h: o.n24,
      avgBudgetFixed: o.avgF || null,
      avgRateHourly: o.avgH || null,
      medianProposals: o.medP,
      pctHighBudget: Math.round(o.pctHigh * 10) / 10,
      opportunityScore: o.score,
    };
  }
  return stats;
}

export function detectPlatforms(job) {
  const text = `${job.title} ${(job.skills || []).join(" ")} ${(job.matchedKeywords || []).join(" ")}`;
  const found = [];
  for (const [name, re] of PLATFORM_PATTERNS) {
    if (re.test(text)) found.push(name);
  }
  return found;
}

export function computePlatformStats(allJobs) {
  const byP = {};
  for (const p of PLATFORMS) byP[p] = [];
  for (const j of allJobs) {
    for (const p of detectPlatforms(j)) {
      if (!byP[p]) byP[p] = [];
      byP[p].push(j);
    }
  }
  const stats = {};
  for (const [p, jobs] of Object.entries(byP)) {
    if (!jobs.length) {
      stats[p] = {
        jobs: 0,
        recentDemand: 0,
        avgBudgetFixed: null,
        avgRateHourly: null,
        medianProposals: null,
        opportunityScore: 0,
        confidence: "Very Low",
      };
      continue;
    }
    const o = opportunityScore(jobs);
    stats[p] = {
      jobs: jobs.length,
      recentDemand: o.n24,
      avgBudgetFixed: o.avgF || null,
      avgRateHourly: o.avgH || null,
      medianProposals: o.medP,
      opportunityScore: o.score,
      confidence: confidence(jobs.length),
    };
  }
  return stats;
}

export function loadAllJobs() {
  return readJsonl(path.join(DIR, "jobs.jsonl"));
}

export function saveStats(keywordStats, groupStats, platformStats) {
  fs.writeFileSync(path.join(DIR, "keyword-stats.json"), JSON.stringify(keywordStats, null, 2));
  fs.writeFileSync(path.join(DIR, "group-stats.json"), JSON.stringify(groupStats, null, 2));
  fs.writeFileSync(path.join(DIR, "platform-stats.json"), JSON.stringify(platformStats, null, 2));
}

export function keywordsForCycle(cycle) {
  const groups = CYCLES[cycle];
  const kws = new Set();
  for (const g of groups) {
    for (const k of GROUPS[g] || []) kws.add(k);
  }
  return [...kws];
}
