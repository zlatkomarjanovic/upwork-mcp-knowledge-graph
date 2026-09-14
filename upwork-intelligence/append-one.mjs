import fs from 'fs';
const p = new URL('./search-raw.json', import.meta.url).pathname;
const d = JSON.parse(fs.readFileSync(p, 'utf8'));
const keyword = process.argv[2];
const group = process.argv[3];
const jobs = JSON.parse(fs.readFileSync(process.argv[4], 'utf8'));
d.searches.push({ keyword, group, jobs });
fs.writeFileSync(p, JSON.stringify(d));
