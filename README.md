# job-finder

A free daily digest of internships, co-ops, and sophomore programs that fit me: Software, Data, and Design & UX roles, US only, no fall terms, spring only if remote, undergrad level. It shows **only what is new since yesterday**, so anything I already acted on drops off.

Tracking stays in my Google Doc. This tool only finds.

## How it works

1. `sources.py` pulls 8 community lists (Simplify, vanshb03, speedyapply, zshah101, two underclassmen lists) plus company job boards for design roles (Greenhouse, Lever, Ashby public APIs).
2. `filters.py` keeps what fits and ranks it (sophomore programs, closing soon, NYC, remote rise to the top).
3. `main.py` compares against `state/seen.json` and writes:
   - `docs/index.html`: the page I check every morning (GitHub Pages)
   - `digest/latest.md` and a dated copy
   - `data/new_today.csv` (everything new, not capped) and `data/all_current.csv`
4. GitHub Actions runs it every morning at 7am Central and commits the results.

## Change what it finds

Everything is in `config.py`: keywords, the design company watchlist, term rules, ranking boosts. Add a company by its careers URL slug, for example `jobs.ashbyhq.com/linear` is `("ashby", "linear", "Linear")`.

## Run locally

```
python main.py --dry-run   # preview without marking anything as seen
```

No dependencies beyond Python 3.10+.

## Known limits

- Graduation-year eligibility is not checked. No source lists it, so a few junior-only roles will show up.
- Repo data is only as fresh as the repos. Some "active" rows are stale.
- Sophomore program lists mix in old entries with unknown status. Check the official page before planning around one.
