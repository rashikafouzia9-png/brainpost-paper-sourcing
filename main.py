"""
Brain Post paper-sourcing tool.

Reads config.yaml (one block per writer/beat), pulls recent PubMed +
bioRxiv papers matching each beat's keywords, and writes a single
markdown digest (digest.md) grouped by beat - ready to skim or drop
into a shared doc for the team.

Usage:
    pip install -r requirements.txt
    python main.py

Optional: set PUBMED_API_KEY as an environment variable to raise your
NCBI rate limit (free, from https://www.ncbi.nlm.nih.gov/account/).

Optional: set ANTHROPIC_API_KEY to also generate a rough one-line
"why this might matter" draft for each paper via Claude. Without it,
the tool still works - that field is just left blank.
"""

import os
import time
import datetime as dt
import yaml

from fetch_pubmed import search_pubmed
from fetch_biorxiv import fetch_recent_biorxiv, filter_biorxiv

try:
    import anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False


def draft_relevance_note(client, title: str) -> str:
    """Ask Claude for a single-sentence 'why this might matter' draft.
    This is a rough starting point for the writer, not a final line."""
    try:
        msg = client.messages.create(
            model="claude-sonnet-5",
            max_tokens=60,
            messages=[{
                "role": "user",
                "content": (
                    "In one plain-English sentence (under 25 words), suggest why "
                    f"this neuroscience paper might matter to a general reader. "
                    f"Title: {title}"
                ),
            }],
        )
        return msg.content[0].text.strip()
    except Exception:
        return ""


def dedupe(papers: list[dict]) -> list[dict]:
    seen = set()
    unique = []
    for p in papers:
        key = p["title"].strip().lower()
        if key and key not in seen:
            seen.add(key)
            unique.append(p)
    return unique


def main():
    with open("config.yaml") as f:
        config = yaml.safe_load(f)

    days_back = config.get("days_back", 30)
    max_results = config.get("max_results_per_beat", 12)
    beats = config.get("beats", [])

    pubmed_api_key = os.environ.get("PUBMED_API_KEY")
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
    client = None
    if HAS_ANTHROPIC and anthropic_key:
        client = anthropic.Anthropic(api_key=anthropic_key)

    # bioRxiv has no keyword search - pull the recent window ONCE and
    # filter it per beat locally, rather than re-fetching per beat.
    print(f"Fetching bioRxiv postings from the last {days_back} days...")
    biorxiv_pool = fetch_recent_biorxiv(days_back)
    print(f"  -> {len(biorxiv_pool)} bioRxiv postings pulled, filtering per beat.")

    sections = []
    for beat in beats:
        name = beat["name"]
        writer = beat.get("writer", "")
        keywords = beat["keywords"]
        print(f"Searching beat: {name} ...") 
        time.sleep(1.5)

        pubmed_results = search_pubmed(keywords, days_back, max_results, pubmed_api_key)
        biorxiv_results = filter_biorxiv(biorxiv_pool, keywords, max_results)

        combined = dedupe(pubmed_results + biorxiv_results)

        lines = [f"## {name}  \n*Writer: {writer}*\n"]
        if not combined:
            lines.append("_No matches this window - try widening the keywords in config.yaml._\n")
        for p in combined:
            note = ""
            if client:
                note = draft_relevance_note(client, p["title"])
            lines.append(f"- **{p['title']}**")
            lines.append(f"  - {p['authors']} — *{p['journal']}*, {p['pub_date']}")
            lines.append(f"  - {p['url']}")
            if note:
                lines.append(f"  - _Possible angle: {note}_")
        sections.append("\n".join(lines))

    today = dt.date.today().isoformat()
    header = f"# Brain Post — Paper Digest ({today})\n\nCovers the last {days_back} days.\n"
    output = header + "\n\n".join(sections)

    with open("digest.md", "w") as f:
        f.write(output)

    print("\nDone. See digest.md")


if __name__ == "__main__":
    main()
