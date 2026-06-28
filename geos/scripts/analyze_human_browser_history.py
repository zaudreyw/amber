"""Analyze browser histories from the human baseline study.

Goal: characterize what each PhD student looked at while authoring the
Buckley-Leverett deck, and contrast with what the agent reads on the
same task.

Outputs a markdown summary at:
    docs/2026-05-04_human-baseline-browser-analysis.md
"""

import csv
import json
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path("/home/matt/sci/repo3")
HUMAN_DIR = ROOT / "data/human_baseline"
OUT_MD = ROOT / "docs/2026-05-04_human-baseline-browser-analysis.md"


def domain_of(url: str) -> str:
    try:
        return urlparse(url).netloc.lower()
    except Exception:
        return "?"


def categorize(url: str, title: str) -> str:
    u = url.lower()
    t = (title or "").lower()
    if "geosx" in u or "geos-dev" in u or "geos.readthedocs" in u or "geosx" in t:
        return "GEOS docs"
    if "github.com/geos" in u:
        return "GEOS source (github)"
    if "stackoverflow.com" in u or "stackexchange.com" in u:
        return "Stack Overflow / SE"
    if "google.com/search" in u or "bing.com/search" in u or "duckduckgo.com" in u:
        return "search engine"
    if "wikipedia.org" in u:
        return "Wikipedia"
    if "youtube.com" in u or "youtu.be" in u:
        return "YouTube"
    if "slack" in u:
        return "Slack"
    if "mail" in u or "gmail" in u or "outlook" in u:
        return "Email"
    if "chatgpt" in u or "openai.com/chat" in u or "claude.ai" in u or "anthropic" in u or "perplexity" in u:
        return "LLM chatbot (DISALLOWED)"
    if "doi.org" in u or ".pdf" in u or "arxiv.org" in u or "researchgate" in u or "sciencedirect" in u or "springer" in u:
        return "scientific paper"
    if "lxml" in u or "xml" in u:
        return "XML reference"
    return "other"


def load_liam() -> list[dict]:
    rows = []
    with open(HUMAN_DIR / "liam_browser_data.csv") as f:
        r = csv.DictReader(f)
        for row in r:
            rows.append(row)
    return rows


def load_sahchit() -> list[dict]:
    return json.load(open(HUMAN_DIR / "sahchit_browser_data.json"))


def liam_during_session(rows: list[dict]) -> list[dict]:
    """Liam's session: ~48 min on 04/24/26. Filter rows to that window.
    The export's date column is 04/24/26 and the rows that look study-related
    span the morning. We use a generous window: any row dated 04/24/26
    after starting the export tooling but before 'finished'.
    """
    relevant = [r for r in rows if r.get("date", "") == "04/24/26"]
    return relevant


def sahchit_during_session(rows: list[dict]) -> list[dict]:
    """Sahchit's JSON has lastVisitTime in epoch ms. The session was around
    04/24/26 (similar timing); we pull entries from a 4-hour window centered
    on that day. To stay robust without exact start time, take the contiguous
    cluster of entries on 04/24 (the largest 1-day cluster)."""
    by_day = defaultdict(list)
    for r in rows:
        ts = r.get("lastVisitTime")
        if ts is None:
            continue
        d = datetime.utcfromtimestamp(ts / 1000.0).strftime("%Y-%m-%d")
        by_day[d].append((ts, r))
    if not by_day:
        return rows
    best_day = max(by_day, key=lambda d: len(by_day[d]))
    return [r for _, r in sorted(by_day[best_day])]


def summarize(rows: list[dict], who: str, url_key: str, title_key: str) -> dict:
    n = len(rows)
    domains = Counter(domain_of(r.get(url_key, "")) for r in rows)
    cats = Counter(categorize(r.get(url_key, ""), r.get(title_key, "")) for r in rows)
    geos_urls = [
        r.get(url_key, "") for r in rows
        if categorize(r.get(url_key, ""), r.get(title_key, "")).startswith("GEOS")
    ]
    return {
        "who": who,
        "n_visits": n,
        "n_unique_domains": len(domains),
        "top_domains": domains.most_common(8),
        "category_counts": dict(cats),
        "geos_url_sample": geos_urls[:15],
    }


def render_md(summaries: list[dict]) -> str:
    out = []
    out.append("# Human baseline — browser-history analysis\n")
    out.append("Buckley-Leverett task. Two geoscience PhD students (Liam, Sahchit), "
               "single 1-hour timeslot each, no internet restrictions enforced "
               "(cf. agent: zero internet, local repo only). Neither finished the "
               "two-file deck; both produced only `buckleyLeverett_base.xml`.\n")

    for s in summaries:
        out.append(f"## {s['who']}\n")
        out.append(f"- visits during session: **{s['n_visits']}**")
        out.append(f"- unique domains: **{s['n_unique_domains']}**\n")
        out.append("**Top domains**:\n")
        for d, c in s["top_domains"]:
            out.append(f"  - `{d}` — {c}")
        out.append("\n**Category counts**:\n")
        for c, n in sorted(s["category_counts"].items(), key=lambda kv: -kv[1]):
            out.append(f"  - {c}: {n}")
        if s["geos_url_sample"]:
            out.append("\n**Sample GEOS-doc URLs visited**:\n")
            for u in s["geos_url_sample"]:
                out.append(f"  - {u}")
        out.append("\n")
    return "\n".join(out) + "\n"


def main() -> None:
    liam_all = load_liam()
    sahchit_all = load_sahchit()

    liam_session = liam_during_session(liam_all)
    sahchit_session = sahchit_during_session(sahchit_all)

    summaries = [
        summarize(liam_session, "Liam (CSV; 04/24/26 entries)", "url", "title"),
        summarize(sahchit_session, "Sahchit (JSON; largest single-day cluster)",
                  "url", "title"),
    ]
    md = render_md(summaries)
    OUT_MD.write_text(md)
    print(md)


if __name__ == "__main__":
    main()
