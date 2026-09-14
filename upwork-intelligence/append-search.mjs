import fs from 'fs';
const p = new URL('./search-raw.json', import.meta.url).pathname;
const d = JSON.parse(fs.readFileSync(p, 'utf8'));
const adds = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
d.searches.push(...adds);
if (process.argv[3]) d.errors.push(...JSON.parse(process.argv[3]));
fs.writeFileSync(p, JSON.stringify(d));
