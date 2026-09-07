import os
import re
import html
import hashlib
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime
from email.utils import parsedate_to_datetime

MEDIUM_USERNAME = os.environ["MEDIUM_USERNAME"]
OUTPUT_DIR = "content/posts"

FEED_URL = f"https://medium.com/feed/@{MEDIUM_USERNAME}"

os.makedirs(OUTPUT_DIR, exist_ok=True)

# Medium RSS namespaces
NS = {
    "content": "http://purl.org/rss/1.0/modules/content/",
    "dc": "http://purl.org/dc/elements/1.1/",
}

print(f"Fetching {FEED_URL}")

with urllib.request.urlopen(FEED_URL) as response:
    data = response.read()

root = ET.fromstring(data)

for item in root.findall("./channel/item"):
    title = item.findtext("title", "").strip()
    link = item.findtext("link", "").strip()
    pub_date = item.findtext("pubDate", "").strip()
    description = item.findtext("description", "").strip()

    if not title or not link:
        continue

    # Create a stable filename from the Medium URL
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")

    if not slug:
        slug = hashlib.md5(link.encode()).hexdigest()[:12]

    filename = os.path.join(OUTPUT_DIR, f"{slug}.md")

    # Parse date
    try:
        date = parsedate_to_datetime(pub_date).strftime("%Y-%m-%dT%H:%M:%S%z")
    except Exception:
        date = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S+00:00")

    # Strip HTML from description
    description_text = re.sub("<[^>]+>", "", description)
    description_text = html.unescape(description_text)
    description_text = re.sub(r"\s+", " ", description_text).strip()

    # Escape YAML
    safe_title = title.replace('"', '\\"')
    safe_description = description_text.replace('"', '\\"')

    content = f"""---
title: "{safe_title}"
date: {date}
description: "{safe_description}"
draft: false
externalUrl: "{link}"
ShowReadingTime: false
ShowShareButtons: false
---

This article was originally published on [Medium]({link}).

**[Read the full article on Medium →]({link})**
"""

    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"Synced: {title}")
