import fs from 'fs';
import path from 'path';
const DIR = path.dirname(new URL(import.meta.url).pathname);
const rawPath = path.join(DIR, 'raw-searches.json');
const inPath = process.argv[2];
const batch = JSON.parse(fs.readFileSync(inPath, 'utf8'));
let a = [];
try { a = JSON.parse(fs.readFileSync(rawPath, 'utf8')); } catch {}
a.push(...batch);
fs.writeFileSync(rawPath, JSON.stringify(a));
