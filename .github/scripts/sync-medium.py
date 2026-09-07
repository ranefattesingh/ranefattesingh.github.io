import os
import re
import html
import hashlib
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime
from email.utils import parsedate_to_datetime

MEDIUM_USERNAME = os.environ["MEDIUM_USERNAME"].strip().lstrip("@")
OUTPUT_DIR = "content/posts"

FEED_URL = f"https://medium.com/feed/@{MEDIUM_USERNAME}"

os.makedirs(OUTPUT_DIR, exist_ok=True)

print("=" * 60)
print(f"Medium username: {MEDIUM_USERNAME}")
print(f"Feed URL: {FEED_URL}")
print("=" * 60)

# Use a browser-like User-Agent
request = urllib.request.Request(
    FEED_URL,
    headers={
        "User-Agent": "Mozilla/5.0 (compatible; HugoMediumSync/1.0)"
    }
)

try:
    with urllib.request.urlopen(request, timeout=30) as response:
        data = response.read()

    print(f"Downloaded {len(data)} bytes")

except Exception as e:
    print(f"ERROR fetching Medium RSS feed:")
    print(e)
    raise

# Show beginning of response for diagnostics
print("Response begins with:")
print(data[:200])

try:
    root = ET.fromstring(data)
except ET.ParseError as e:
    print("ERROR: Medium response is not valid XML/RSS.")
    print(e)
    raise

items = root.findall("./channel/item")

print(f"Found {len(items)} Medium posts")

if not items:
    print("WARNING: RSS feed contains no posts.")

for item in items:
    title = item.findtext("title", "").strip()
    link = item.findtext("link", "").strip()
    pub_date = item.findtext("pubDate", "").strip()
    description = item.findtext("description", "").strip()

    if not title or not link:
        print("Skipping item without title or link")
        continue

    slug = re.sub(
        r"[^a-z0-9]+",
        "-",
        title.lower()
    ).strip("-")

    if not slug:
        slug = hashlib.md5(link.encode()).hexdigest()[:12]

    filename = os.path.join(
        OUTPUT_DIR,
        f"{slug}.md"
    )

    try:
        date = parsedate_to_datetime(
            pub_date
        ).strftime("%Y-%m-%dT%H:%M:%S%z")
    except Exception:
        date = datetime.utcnow().strftime(
            "%Y-%m-%dT%H:%M:%S+00:00"
        )

    description_text = re.sub(
        r"<[^>]+>",
        "",
        description
    )

    description_text = html.unescape(
        description_text
    )

    description_text = re.sub(
        r"\s+",
        " ",
        description_text
    ).strip()

    safe_title = title.replace(
        '"',
        '\\"'
    )

    safe_description = description_text.replace(
        '"',
        '\\"'
    )

    content = f"""---
title: "{safe_title}"
date: {date}
description: "{safe_description}"
draft: false
externalUrl: "{link}"
ShowReadingTime: false
ShowShareButtons: false
---

This article was originally published on Medium.

**[Read the full article on Medium →]({link})**
"""

    with open(
        filename,
        "w",
        encoding="utf-8"
    ) as f:
        f.write(content)

    print(f"Synced: {title}")
    print(f"  -> {filename}")

print("=" * 60)
print("Medium sync complete.")
print("=" * 60)
