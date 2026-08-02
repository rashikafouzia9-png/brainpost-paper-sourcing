"""
Unit tests for score_paper() and rank_papers() in brainpost_sourcer.py

Run with: pytest tests/test_scoring.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from brainpost_sourcer import score_paper, rank_papers


def make_paper(priority=False, open_access=False, abstract_words=50):
    return {
        "pmid": "12345",
        "title": "Test paper",
        "authors": "Doe J",
        "journal": "Test Journal",
        "year": "2026",
        "abstract": " ".join(["word"] * abstract_words),
        "doi": "",
        "pmc_id": "PMC123" if open_access else "",
        "open_access": open_access,
        "priority": priority,
    }


def test_priority_journal_scores_higher():
    priority_paper = make_paper(priority=True)
    regular_paper = make_paper(priority=False)
    assert score_paper(priority_paper) > score_paper(regular_paper)


def test_open_access_adds_one_point():
    oa_paper = make_paper(open_access=True)
    closed_paper = make_paper(open_access=False)
    assert score_paper(oa_paper) - score_paper(closed_paper) == 1.0


def test_long_abstract_scores_higher_than_short():
    long_paper = make_paper(abstract_words=250)
    short_paper = make_paper(abstract_words=20)
    assert score_paper(long_paper) > score_paper(short_paper)


def test_rank_papers_sorts_descending():
    papers = [
        make_paper(priority=False, open_access=False),
        make_paper(priority=True, open_access=True, abstract_words=250),
        make_paper(priority=False, open_access=True),
    ]
    ranked = rank_papers(papers)
    scores = [score_paper(p) for p in ranked]
    assert scores == sorted(scores, reverse=True)


def test_max_possible_score():
    best_paper = make_paper(priority=True, open_access=True, abstract_words=250)
    assert score_paper(best_paper) == 5.5  # 3.0 + 1.0 + 1.0 + 0.5
