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

(To be filled in as they're added — expected: `pytest eval/`,
`python -m eval.ablate`, `python -m pipeline.refresh --dry-run`,
`docker build . && docker run -p 8000:8000`.)

## Status

Scaffolding in progress. Done so far: `CONTEXT.md` glossary,
`data/yc-snapshot-2026-08-22.json` (pinned, 6,189 companies),
`pipeline/refresh.py`. Not yet started: retrieval, facet extraction,
alignment/whitespace logic, eval harness, API, frontend.
