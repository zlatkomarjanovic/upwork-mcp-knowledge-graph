import fs from 'fs';
import path from 'path';
const file = path.join(path.dirname(new URL(import.meta.url).pathname), 'search-batch.json');
const batch = JSON.parse(fs.readFileSync(file, 'utf8'));
batch.push(JSON.parse(process.argv[2]));
fs.writeFileSync(file, JSON.stringify(batch));
