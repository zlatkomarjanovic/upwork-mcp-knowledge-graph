#!/usr/bin/env python3
"""Helper to merge search results - MCP calls done externally."""
import json
import sys
from datetime import datetime, timezone

KEYWORDS = [
    ("Core Web Dev", "web development"),
    ("Core Web Dev", "website development"),
    ("Core Web Dev", "web developer"),
    ("Core Web Dev", "custom website"),
    ("Core Web Dev", "website builder"),
    ("Core Web Dev", "frontend developer"),
    ("Core Web Dev", "full stack developer"),
    ("Core Web Dev", "website project"),
    ("Web Design", "web design"),
    ("Web Design", "website design"),
    ("Web Design", "website redesign"),
    ("Web Design", "landing page design"),
    ("Web Design", "UI UX website"),
    ("Web Design", "responsive web design"),
    ("Web Design", "homepage redesign"),
    ("Web Design", "one page website"),
    ("WordPress", "wordpress"),
    ("WordPress", "wordpress developer"),
    ("WordPress", "wordpress website"),
    ("WordPress", "wordpress development"),
    ("WordPress", "wordpress redesign"),
    ("WordPress", "wordpress customization"),
    ("WordPress", "wordpress migration"),
    ("WordPress", "wordpress speed optimization"),
    ("WordPress", "wordpress maintenance"),
    ("WordPress", "woocommerce"),
    ("WordPress", "elementor developer"),
    ("WordPress", "bricks builder"),
    ("WordPress", "headless wordpress"),
    ("Webflow/Framer", "webflow"),
    ("Webflow/Framer", "webflow developer"),
    ("Webflow/Framer", "webflow website"),
    ("Webflow/Framer", "webflow redesign"),
    ("Webflow/Framer", "figma to webflow"),
    ("Webflow/Framer", "webflow CMS"),
    ("Webflow/Framer", "framer"),
    ("Webflow/Framer", "framer developer"),
    ("Webflow/Framer", "framer website"),
    ("Webflow/Framer", "framer redesign"),
    ("Webflow/Framer", "figma to framer"),
    ("Webflow/Framer", "framer CMS"),
]

if __name__ == "__main__":
    print(len(KEYWORDS))
