# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Startup idea prior-art engine — a founder types an idea; the system retrieves
the most relevant YC companies, shows a per-facet **alignment** grid (same vs.
different), and computes unoccupied **whitespace** in that neighborhood. This
is a retrieval-and-evaluation study with a UI, not a scored "validator" —
there is no crowdedness score, only differences and computed whitespace. See
`CONTEXT.md` for the full glossary (relevance/alignment/idea facet/cohort
signal/whitespace) and `docs/adr/` for decisions once written.

Full implementation plan: `~/.claude/plans/you-are-a-software-tingly-pearl.md`.

Two deliberate scope exclusions:
- **a16z is out of v1** — its portfolio page has no company descriptions, only
  name/logo/exit-status, so it can't be made comparable to YC without
  inventing prior art. Documented as a limitation, not silently dropped.
- **No crowdedness score, no verdict** — a scalar "validation score" is
  unfalsifiable; the product surfaces facet-level differences instead.

## Architecture

Python backend serving a pre-built React/TypeScript SPA from a single
container (one `Dockerfile`, one URL, no CORS) — chosen because local
open-weights embeddings (~130MB–1.3GB) can't run in Vercel serverless, so a
persistent Python container is required regardless.

```
/
├── CONTEXT.md          glossary
├── docs/adr/           architecture decisions
├── data/
│   ├── yc-snapshot-<date>.json   pinned corpus, committed (not live-fetched)
│   ├── facets.json               extracted idea facets, committed
│   └── embeddings.npy            committed vectors
├── pipeline/           offline: fetch → extract → cluster → embed
├── api/                FastAPI: retrieval, alignment, whitespace
├── eval/                harness, metrics, ablation runner
└── web/                Vite + React + TS SPA
```

**Data**: pinned snapshot from [yc-oss/api](https://github.com/yc-oss/api)
(6,189 companies), regenerated via `python -m pipeline.refresh`. The corpus is
never fetched live at query time — reproducibility of the eval numbers
depends on the corpus being fixed.

**Idea facets** (`customer`, `problem`, `mechanism`, `wedge`,
`business_model`): controlled enum + free-text span each, extracted offline
via `claude-opus-5` Batch API and committed to `data/facets.json`. This is the
project's only API dependency — embeddings, retrieval, alignment, and
whitespace are all local/offline. Only a live typed query needs a Claude call
at request time (facet-extracting the user's idea); canned examples avoid
even that.

**Retrieval**: local open-weights embeddings (`bge-small`/`bge-large` via
`sentence-transformers`) + BM25, fused with Reciprocal Rank Fusion, then a
facet-aware rerank of the top 50 down to the displayed top 12.

**Alignment vs. cohort signals**: the alignment grid only compares bilateral
idea facets (both idea and company have them). Stage/status/batch/team_size
are cohort signals — unilateral, corpus-only — shown as neighborhood
statistics, never as a per-company grid column or an interpretive verdict.

## Build/test commands

Setup: `python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`

- `python -m eval.leave_one_out` — dense-retrieval eval, 300 sampled queries, `bge-small`. Flags: `--n`, `--model {bge-small,bge-large}`, `--full` (every company as a query), `--seed`.
- `python -m pipeline.refresh --dry-run` — verify the live snapshot source still fetches.

Not yet added: `pytest eval/`, `python -m eval.ablate` (full ablation table), Dockerfile.

## Status

Build-order step 2 done: dense-only retrieval (`api/corpus.py`, `api/retrieval.py`)
plus the leave-one-out harness (`eval/leave_one_out.py`). First number, `bge-small`,
300 sampled queries, weak labels = same `subindustry`:

- nDCG@10: 0.247
- MRR: 0.449
- Recall@10: 0.024

Recall@10 reads low in isolation but is not a retrieval failure — it's the
noisy-weak-label effect the plan's Q6 tradeoff table anticipated. Subindustry
groups range from 18 to 629 companies (median 73), so Recall@10 is capped near
10/73 ≈ 0.14 for a *perfect* retriever on a typical query, and near 10/629 ≈
0.016 for anything landing in the huge "B2B" bucket — checked against the
actual group-size distribution, not assumed. nDCG@10 and MRR are the fairer
reads since they aren't penalized the same way by group size. Qualitative
spot-check (Airbnb → FlightCar/Tab/Hipmunk; Coinbase → Bitstack/Coin/Bitaccess;
DoorDash → Heyfood/Cache) confirms the embeddings are finding real competitors.

Not yet started: BM25 + RRF fusion, facet extraction, alignment/whitespace
logic, golden set, LLM-judge, API, frontend.
