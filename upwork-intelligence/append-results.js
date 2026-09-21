#!/usr/bin/env node
const fs = require('fs');
const path = require('path');
const file = path.join(__dirname, 'run-input.json');
const runStartedAt = '2026-09-21T00:34:05.412Z';
let data = { searchResults: [], runStartedAt, errors: [] };
if (fs.existsSync(file)) data = JSON.parse(fs.readFileSync(file, 'utf8'));
const chunk = JSON.parse(fs.readFileSync(0, 'utf8'));
for (const item of chunk) {
  if (item.response?.status === 'error') {
    data.errors.push(item.keyword);
  }
  data.searchResults.push(item);
}
fs.writeFileSync(file, JSON.stringify(data));
