"""
Fetch recent bioRxiv papers matching a beat's keywords.

bioRxiv's public API (https://api.biorxiv.org) doesn't support keyword
search directly - it only lists all papers in a date range, paginated
100 at a time. So we pull the recent window once (shared across all
beats to avoid re-fetching) and filter locally by keyword match on
title + abstract.
"""

import datetime as dt
import time
import requests

BIORXIV_BASE = "https://api.biorxiv.org/details/biorxiv"


def _get_with_retry(url: str, timeout: int = 60, retries: int = 3) -> requests.Response:
    """bioRxiv's API can be slow under load - retry a couple of times
    with a longer timeout before giving up."""
    last_exc = None
    for attempt in range(retries):
        try:
            return requests.get(url, timeout=timeout)
        except requests.exceptions.ReadTimeout as exc:
            last_exc = exc
            time.sleep(3 * (attempt + 1))
    raise last_exc


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
        resp = _get_with_retry(url, timeout=60, retries=3)
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
