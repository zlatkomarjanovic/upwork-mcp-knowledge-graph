#!/usr/bin/env node
import fs from 'fs';
import path from 'path';
const dir = path.join(process.cwd(), 'upwork-intelligence/chunks');
const out = path.join(process.cwd(), 'upwork-intelligence/run-batch.json');
if (!fs.existsSync(dir)) {
  console.error('no chunks dir');
  process.exit(1);
}
const searches = [];
for (const f of fs.readdirSync(dir).sort()) {
  if (!f.endsWith('.json')) continue;
  const chunk = JSON.parse(fs.readFileSync(path.join(dir, f), 'utf8'));
  if (Array.isArray(chunk)) searches.push(...chunk);
  else if (chunk.searches) searches.push(...chunk.searches);
  else searches.push(chunk);
}
fs.mkdirSync(path.dirname(out), { recursive: true });
fs.writeFileSync(out, JSON.stringify({ searches }, null, 2));
console.log('searches:', searches.length);
