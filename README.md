# Brain Post Paper Sourcing Tool

Automatically surfaces recent PubMed + bioRxiv papers matching each
writer's beat, so nobody has to manually trawl databases every month.
Outputs a single `digest.md` file grouped by beat.

## How it works

- **PubMed**: searched directly via NCBI's E-utilities using each
  beat's keywords, restricted to the last N days (`days_back` in
  `config.yaml`).
- **bioRxiv**: bioRxiv's API doesn't support keyword search, so the
  tool pulls every posting in the date window once, then filters it
  locally against each beat's keywords. This is fetched once and
  reused across all beats, not re-fetched per beat.
- Results from both sources are merged and de-duplicated per beat.
- If you provide an `ANTHROPIC_API_KEY`, each paper also gets a rough
  one-line "why this might matter" draft — a starting point for the
  writer, not a finished line.

## Setup (run it yourself, once)

```bash
git clone <your-repo-url>
cd paper-sourcing-tool
pip install -r requirements.txt
python main.py
```

This creates `digest.md` in the same folder. Open it, skim it, and
use whatever's actually relevant that month.

## Customizing beats

Edit `config.yaml`. Each beat needs:
- `name` — shows as a section header in the digest
- `writer` — whoever owns that beat (or leave as a placeholder)
- `keywords` — phrases searched in title/abstract; add more to widen
  results, remove some to narrow them

Adjust `days_back` and `max_results_per_beat` at the top of the file
to control how far back it looks and how many results per beat.

## Running it automatically every week

The included GitHub Actions workflow (`.github/workflows/weekly_digest.yml`)
runs the tool every Monday and commits the updated `digest.md` back to
the repo, so the team can just check the file rather than running
anything themselves.

To enable it:
1. Push this repo to GitHub.
2. Go to Settings → Secrets and variables → Actions.
3. Add `ANTHROPIC_API_KEY` (optional, for the relevance-note drafts).
4. Add `PUBMED_API_KEY` (optional, raises your NCBI rate limit — get
   one free at https://www.ncbi.nlm.nih.gov/account/).
5. That's it — it'll run on schedule, or you can trigger it manually
   from the Actions tab any time.

## Notes / known limitations

- PubMed indexing lag means very recent papers sometimes don't show
  up for a few days after publication — this is a PubMed limitation,
  not a bug in the tool.
- The bioRxiv keyword filter is a simple substring match, not
  semantic search — if a beat's results look thin, widen the keyword
  phrases in `config.yaml` rather than assuming nothing was posted.
- This surfaces *candidates*, not final picks — it's meant to cut
  down searching time, not replace the judgment of picking which two
  papers are actually worth writing up.
