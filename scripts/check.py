#!/usr/bin/env python3
"""Checks data/agents.json.

  python3 scripts/check.py           Validate the data. Exits 1 on any error.
  python3 scripts/check.py --report  Also check links and stale listings, and
                                     print a Markdown review checklist.

Standard library only, so it runs anywhere without installing anything.
"""
import datetime as dt
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data" / "agents.json"
STALE_AFTER_DAYS = 30
PER_WEEK = 4  # keeps the weekly review to about an hour
REQUIRED = ["id", "name", "vendor", "category", "bestFor", "pricing", "pros", "cons", "websiteUrl", "checked"]


def parse_date(value):
    try:
        return dt.date.fromisoformat(value)
    except (TypeError, ValueError):
        return None


def validate(data):
    errors = []
    categories = {c.get("id") for c in data.get("categories", [])}
    methods = data.get("methods", {})
    seen = set()
    for i, a in enumerate(data.get("agents", [])):
        name = a.get("id") or f"agent #{i + 1}"
        for field in REQUIRED:
            if a.get(field) in (None, "", []):
                errors.append(f"{name}: missing '{field}'")
        if a.get("id") in seen:
            errors.append(f"{name}: duplicate id")
        seen.add(a.get("id"))
        if a.get("category") not in categories:
            errors.append(f"{name}: unknown category '{a.get('category')}'")
        if not str(a.get("websiteUrl", "")).startswith("https://"):
            errors.append(f"{name}: websiteUrl must start with https://")
        if a.get("checked") and not parse_date(a["checked"]):
            errors.append(f"{name}: 'checked' is not a YYYY-MM-DD date")
        if not (a.get("pricing") or {}).get("display"):
            errors.append(f"{name}: missing pricing.display")
        b = a.get("benchmark")
        if b:
            if a.get("category") not in methods:
                errors.append(f"{name}: has a benchmark but its category has no method")
            if not isinstance(b.get("score"), (int, float)) or not 0 <= b["score"] <= 100:
                errors.append(f"{name}: benchmark.score must be a number from 0 to 100")
            for field in ("name", "model", "sourceUrl", "checked"):
                if not b.get(field):
                    errors.append(f"{name}: benchmark missing '{field}'")
            if b.get("checked") and not parse_date(b["checked"]):
                errors.append(f"{name}: benchmark.checked is not a YYYY-MM-DD date")
    for c in methods:
        if c not in categories:
            errors.append(f"methods: unknown category '{c}'")
    return errors


def stale(data, today):
    """Agents whose listing or score is older than STALE_AFTER_DAYS, oldest first."""
    out = []
    for a in data.get("agents", []):
        dates = [parse_date(a.get("checked")), parse_date((a.get("benchmark") or {}).get("checked"))]
        oldest = min((d for d in dates if d), default=None)
        if oldest and (today - oldest).days > STALE_AFTER_DAYS:
            out.append((oldest, f"{a['name']} ({a['vendor']}), last checked {oldest.isoformat()}"))
    return [text for _, text in sorted(out)]


def check_url(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; AgentRankingsCheck/1.0)"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status, None
    except urllib.error.HTTPError as e:
        return e.code, None
    except Exception as e:  # DNS, timeout, TLS
        return None, str(e)


def links(data):
    urls = {}
    for a in data.get("agents", []):
        urls.setdefault(a["websiteUrl"], f"{a['name']} website")
        src = (a.get("benchmark") or {}).get("sourceUrl")
        if src:
            urls.setdefault(src, "benchmark source")
    broken, unsure = [], []
    for url, label in urls.items():
        status, err = check_url(url)
        if status and status < 400:
            continue
        if status in (401, 403, 429):
            unsure.append(f"{label}: {url} (HTTP {status}, the site may block automated checks)")
        else:
            broken.append(f"{label}: {url} ({f'HTTP {status}' if status else err})")
    return broken, unsure


def report(data, today):
    broken, unsure = links(data)
    old = stale(data, today)
    lines = [f"Weekly review for {today.isoformat()}. Tick each box as you go; it should take about an hour.", ""]

    lines += ["### 1. Broken links", ""]
    lines += [f"- [ ] {x}" for x in broken] or ["None found."]
    if unsure:
        lines += ["", "Could not be verified automatically (open them by hand):", ""] + [f"- [ ] {x}" for x in unsure]

    lines += ["", "### 2. Re-check these listings", "",
              "Confirm the price, link, strengths and weaknesses, then set `checked` to today's date.", ""]
    lines += [f"- [ ] {x}" for x in old[:PER_WEEK]] or [f"Nothing to re-check. Every listing was checked in the last {STALE_AFTER_DAYS} days."]
    if len(old) > PER_WEEK:
        lines += ["", f"{len(old) - PER_WEEK} more are due; they will come up in the next weeks."]

    lines += ["", "### 3. Benchmarks", ""]
    for cat, m in data.get("methods", {}).items():
        lines.append(f"- [ ] Open the {m['benchmark']} leaderboard ({m['sourceUrl']}) and look for new or better results for the {cat} agents, including those without a score.")

    lines += ["", "### 4. New agents", "",
              "- [ ] Anything new worth adding? Only add an agent you would recommend to a friend.",
              "", "After any change to `data/agents.json`, also update `meta.lastUpdated`."]
    return "\n".join(lines)


def main():
    data = json.loads(DATA.read_text(encoding="utf-8"))
    errors = validate(data)
    if errors:
        print("data/agents.json has problems:\n" + "\n".join(f"  - {e}" for e in errors), file=sys.stderr)
        return 1
    if "--report" in sys.argv:
        print(report(data, dt.date.today()))
    else:
        print(f"OK: {len(data['agents'])} agents in {len(data['categories'])} categories.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
