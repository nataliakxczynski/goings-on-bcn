#!/usr/bin/env python3
"""Fetch configured cultural RSS feeds and build a compact events.json for the widget."""
import calendar
import datetime as dt
import hashlib
import html
import json
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / "sources.json"
OUTPUT = ROOT / "events.json"
NOW = dt.datetime.now(dt.timezone.utc)
WINDOW_END = NOW + dt.timedelta(days=120)
MAX_EVENTS = 100

def clean(value):
    value = html.unescape(value or "")
    value = re.sub(r"<[^>]+>", " ", value)
    return re.sub(r"\s+", " ", value).strip()

def first_text(node, names):
    for name in names:
        found = node.find(name)
        if found is not None and found.text:
            return found.text.strip()
    return ""

def parse_date(raw):
    if not raw:
        return None
    raw = raw.strip()
    try:
        value = dt.datetime.fromisoformat(raw.replace("Z", "+00:00"))
        if value.tzinfo is None:
            value = value.replace(tzinfo=dt.timezone.utc)
        return value.astimezone(dt.timezone.utc)
    except ValueError:
        pass
    try:
        value = parsedate_to_datetime(raw)
        if value.tzinfo is None:
            value = value.replace(tzinfo=dt.timezone.utc)
        return value.astimezone(dt.timezone.utc)
    except (TypeError, ValueError, OverflowError):
        return None

def child_text(item, local_names):
    for child in list(item):
        tag = child.tag.split("}")[-1].lower()
        if tag in local_names:
            if child.text:
                return child.text.strip()
            # Content may contain nested HTML.
            return "".join(child.itertext()).strip()
    return ""

def parse_feed(url, source_name):
    request = urllib.request.Request(url, headers={"User-Agent": "GoingsOnBarcelona/1.0 (+personal cultural calendar)"})
    with urllib.request.urlopen(request, timeout=30) as response:
        raw = response.read()
    root = ET.fromstring(raw)
    items = [x for x in root.iter() if x.tag.split("}")[-1].lower() in ("item", "entry")]
    events = []
    for item in items:
        title = clean(child_text(item, {"title"}))
        if not title:
            continue
        link = ""
        for child in list(item):
            if child.tag.split("}")[-1].lower() == "link":
                href = child.attrib.get("href")
                if href:
                    link = href
                    break
                if child.text:
                    link = child.text.strip()
                    break
        desc = clean(child_text(item, {"description", "summary", "content", "encoded"}))
        raw_date = child_text(item, {"startdate", "start_date", "dtstart", "pubdate", "published", "updated", "date"})
        # Some feeds use namespaced event dates; inspect all direct children by local name.
        if not raw_date:
            for child in list(item):
                local = child.tag.split("}")[-1].lower()
                if local in {"startdate", "start_date", "dtstart", "pubdate", "published", "updated", "date"}:
                    raw_date = child.text or ""
                    if raw_date:
                        break
        date = parse_date(raw_date)
        # Avoid treating a feed publication date as an event date if no event start is present.
        # Feed-specific dates are preferable; undated items are skipped rather than inventing dates.
        if not date or date < NOW - dt.timedelta(days=1) or date > WINDOW_END:
            continue
        categories = []
        for child in list(item):
            if child.tag.split("}")[-1].lower() == "category":
                term = child.attrib.get("term") or child.text
                if term:
                    categories.append(clean(term))
        venue = child_text(item, {"venue", "location", "place"})
        if not venue:
            # Some feeds include venue as a namespaced element.
            for child in list(item):
                if child.tag.split("}")[-1].lower() in {"venue", "location", "place"} and child.text:
                    venue = clean(child.text)
                    break
        if not venue:
            venue = source_name or "Barcelona"
        identifier = link or title + date.date().isoformat()
        event_id = hashlib.sha1(identifier.encode("utf-8")).hexdigest()[:12]
        events.append({
            "id": event_id,
            "title": title,
            "startDate": date.isoformat(),
            "venue": venue,
            "category": ", ".join(categories),
            "description": desc[:420],
            "detail": desc[:900],
            "url": link,
            "source": source_name
        })
    return events

def main():
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    feeds = [f for f in config.get("feeds", []) if f.get("url") and "PASTE_" not in f["url"]]
    all_events, errors = [], []
    for feed in feeds:
        name = feed.get("name", "Cultural agenda")
        try:
            items = parse_feed(feed["url"], name)
            all_events.extend(items)
            print(f"{name}: {len(items)} future items")
        except Exception as exc:
            errors.append(f"{name}: {type(exc).__name__}: {exc}")
            print(errors[-1], file=sys.stderr)

    # De-duplicate events by URL, otherwise by normalized title and date.
    unique = {}
    for event in all_events:
        key = event["url"] or (event["title"].casefold(), event["startDate"][:10])
        if key not in unique:
            unique[key] = event
    events = sorted(unique.values(), key=lambda e: e["startDate"])[:MAX_EVENTS]
    payload = {
        "generatedAt": NOW.isoformat(),
        "sourceCount": len(feeds),
        "eventCount": len(events),
        "sources": [{"name": f.get("name", "Cultural agenda"), "url": f["url"]} for f in feeds],
        "warnings": errors,
        "events": events
    }
    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(events)} events to {OUTPUT}")
    # Do not fail the workflow for one broken feed if another works.
    if feeds and not events and errors:
        sys.exit(1)

if __name__ == "__main__":
    main()
