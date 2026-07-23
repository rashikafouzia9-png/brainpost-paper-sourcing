"""
Fetch recent bioRxiv papers matching a beat's keywords.

bioRxiv's public API (https://api.biorxiv.org) doesn't support keyword
search directly - it only lists all papers in a date range, paginated
100 at a time. So we pull the recent window once (shared across all
beats to avoid re-fetching) and filter locally by keyword match on
title + abstract.
"""

import datetime as dt
import requests

BIORXIV_BASE = "https://api.biorxiv.org/details/biorxiv"


def fetch_recent_biorxiv(days_back: int, max_pages: int = 5) -> list[dict]:
    """Pull all bioRxiv postings in the last `days_back` days.

    max_pages caps how many 100-result pages we fetch, as a safety
    limit (bioRxiv posts hundreds of papers a day across all fields).
    """
    end = dt.date.today()
    start = end - dt.timedelta(days=days_back)
    date_range = f"{start.isoformat()}/{end.isoformat()}"

all_papers = []
    cursor = 0
    for _ in range(max_pages):
        url = f"{BIORXIV_BASE}/{date_range}/{cursor}/json"
        resp = requests.get(url, timeout=20)
        resp.raise_for_status()
        data = resp.json()
        collection = data.get("collection", [])
        if not collection:
            break
        all_papers.extend(collection)
        cursor += 100
        total = int(data.get("messages", [{}])[0].get("total", 0))
        if cursor >= total:
            break

    return all_papers 

def filter_biorxiv(all_papers: list[dict], keywords: list[str], max_results: int) -> list[dict]:
    """Keep only papers whose title or abstract mentions a keyword."""
    keywords_lower = [kw.lower() for kw in keywords]
    matches = []
    for p in all_papers:
        text = f"{p.get('title', '')} {p.get('abstract', '')}".lower()
        if any(kw in text for kw in keywords_lower):
            matches.append({
                "title": p.get("title", "").rstrip("."),
                "authors": p.get("authors", ""),
                "journal": "bioRxiv (preprint)",
                "pub_date": p.get("date", ""),
                "url": f"https://doi.org/{p.get('doi', '')}",
                "source": "bioRxiv",
            })
        if len(matches) >= max_results:
            break
    return matches
