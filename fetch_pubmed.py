"""
Fetch recent PubMed papers matching a beat's keywords.

Uses NCBI E-utilities (esearch -> esummary). No API key required,
but request one free at https://www.ncbi.nlm.nih.gov/account/ if you
plan to run this often - it raises your rate limit from 3 to 10
requests/second and avoids throttling.
"""

import time
import requests

EUTILS_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"


def _build_term(keywords: list[str]) -> str:
    """OR together keyword phrases, each searched in title/abstract."""
    parts = [f'("{kw}"[Title/Abstract])' for kw in keywords]
    return " OR ".join(parts)


def _get_with_retry(url: str, params: dict, retries: int = 4) -> requests.Response:
    """NCBI rate-limits aggressively without an API key - back off and
    retry on 429 (Too Many Requests) instead of failing immediately."""
    last_exc = None
    for attempt in range(retries):
        resp = requests.get(url, params=params, timeout=20)
        if resp.status_code == 429:
            last_exc = requests.exceptions.HTTPError("429 Too Many Requests")
            time.sleep(2 * (attempt + 1))
            continue
        resp.raise_for_status()
        return resp
    raise last_exc


def search_pubmed(keywords: list[str], days_back: int, max_results: int,
                   api_key: str | None = None) -> list[dict]:
    """Return a list of {title, authors, journal, pub_date, url, source} dicts."""
    term = _build_term(keywords)

    params = {
        "db": "pubmed",
        "term": term,
        "retmax": max_results,
        "datetype": "pdat",
        "reldate": days_back,
        "retmode": "json",
        "sort": "date",
    }
    if api_key:
        params["api_key"] = api_key

    resp = _get_with_retry(f"{EUTILS_BASE}/esearch.fcgi", params)
    id_list = resp.json().get("esearchresult", {}).get("idlist", [])

    if not id_list:
        return []

    time.sleep(1.0)

    summary_params = {
        "db": "pubmed",
        "id": ",".join(id_list),
        "retmode": "json",
    }
    if api_key:
        summary_params["api_key"] = api_key

    resp = _get_with_retry(f"{EUTILS_BASE}/esummary.fcgi", summary_params)
    summaries = resp.json().get("result", {})

    papers = []
    for pmid in id_list:
        doc = summaries.get(pmid)
        if not doc:
            continue
        authors = ", ".join(a.get("name", "") for a in doc.get("authors", [])[:3])
        if len(doc.get("authors", [])) > 3:
            authors += " et al."
        papers.append({
            "title": doc.get("title", "").rstrip("."),
            "authors": authors,
            "journal": doc.get("fulljournalname") or doc.get("source", ""),
            "pub_date": doc.get("pubdate", ""),
            "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
            "source": "PubMed",
        })
    return papers
