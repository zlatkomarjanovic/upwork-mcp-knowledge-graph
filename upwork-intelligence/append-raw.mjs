import fs from 'fs';
const p = new URL('./raw-searches.json', import.meta.url).pathname;
const entries = JSON.parse(process.argv[2] || '[]');
let a = [];
try { a = JSON.parse(fs.readFileSync(p, 'utf8')); } catch {}
a.push(...entries);
fs.writeFileSync(p, JSON.stringify(a));
