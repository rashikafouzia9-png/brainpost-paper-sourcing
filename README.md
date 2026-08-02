# Brain Post Paper Sourcer

Automated PubMed sourcing for [Brain Post](https://thebrainpost.co.uk) writers.

I run paper sourcing for Brain Post — every week someone has to scan journal contents and PubMed for recent neuroscience papers worth writing about, then narrow dozens of hits down to a shortlist. That was taking the team 2-3 hours a week. This script does the search and rank part in under a minute; picking what to actually write about is still a human call.

## Setup

```bash
pip install -r requirements.txt
export NCBI_EMAIL="your@email.com"      # NCBI requires this
export NCBI_API_KEY="..."               # optional, doubles your rate limit
```

## Usage

```bash
python brainpost_sourcer.py --topics "dopamine" "working memory" "sleep consolidation" \
  --days 60 --max-per-topic 5 --open-access-only --out this_weeks_papers.md
```

Or `--interactive` if you just want to try one topic without remembering the flags.

| Flag | Default | What it does |
|---|---|---|
| `--topics` | — | one or more search terms |
| `--days` | 90 | how far back to search |
| `--max-per-topic` | 5 | papers returned per topic |
| `--open-access-only` | False | only papers writers can actually link full-text |
| `--out` | `sourced_papers.md` | output file |

## How ranking works

Not trying to be clever here, it's a transparent point system, editable at the top of the script:

- +3 if it's from a journal on our priority list (Nature Neuroscience, Neuron, eLife, etc. — configurable)
- +1 if open access
- +1 if the abstract is over 100 words, +0.5 more if over 200 — short abstracts are usually not enough to write from

## Known issues

- No citation counts through the free NCBI API, so "impact" is really just a journal prestige proxy, which isn't the same thing and I know it
- Papers less than about a week old sometimes aren't indexed yet, so very fresh work gets missed
- A few journals format abstracts oddly and the output snippet comes out truncated mid sentence — haven't fixed this yet
