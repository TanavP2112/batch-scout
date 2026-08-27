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

- `python -m eval.leave_one_out` — retrieval eval, 300 sampled queries, `bge-small`. Flags: `--n`, `--model {bge-small,bge-large}`, `--method {dense,lexical,fusion,facet-rerank}`, `--full` (every company as a query), `--seed`.
- `python -m pipeline.refresh --dry-run` — verify the live snapshot source still fetches.
- `python -m pipeline.extract_facets submit [--n N]` then `python -m pipeline.extract_facets poll [--watch] [batch_id]` — submits/collects the facet-extraction Batch job. Requires `ANTHROPIC_API_KEY`; costs real money (measured $0.10 for a 20-company sample, so ≈$30 projected for the full ~6,132-company corpus — in line with the plan's ~$27 estimate) and is not run in CI. `--watch` polls every 30s instead of a single check.
- `python -m pipeline.cluster_problems [--k 40]` — clusters `data/facets_raw.json`'s normalized `problem` labels into the bottom-up `problem` enum (naming clusters by embedding medoid, locally — no API key needed) and writes committed `data/facets.json`. Requires `data/facets_raw.json` to already exist.
- `python -m eval.golden_set` — retrieval eval against `data/golden_set.json`'s 30 hand-labeled founder-voice ideas. Flags: `--model {bge-small,bge-large}`, `--method {dense,lexical,fusion,facet-rerank}` (default `fusion`). No API key needed — local embeddings only (`facet-rerank` reads committed `data/golden_set_facets.json`, no live call).
- `python -m pipeline.extract_golden_set_facets submit` then `poll [--watch] [batch_id]` — one-off batch classifying `data/golden_set.json`'s 30 ideas into the five facets (using the corpus's already-derived `problem` enum, so results are comparable to `data/facets.json`). Requires `ANTHROPIC_API_KEY`; already run once, ~$0.18 measured. Writes `data/golden_set_facets.json` (committed).
- `python -m eval.llm_judge submit` then `python -m eval.llm_judge poll [--watch] [batch_id]` — judges the fusion retriever's golden-set top-10 (300 pairs) for relevance via a Batches job (`claude-sonnet-5`). Requires `ANTHROPIC_API_KEY`; not run in CI.

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

Build-order step 3 done: BM25 lexical retrieval (`api/lexical.py`, via
`rank-bm25`, already pinned in requirements.txt) plus RRF fusion
(`api/fusion.py`, k=60, standard Cormack et al. constant) combining dense and
lexical ranks by reciprocal rank rather than raw score, since BM25 scores and
cosine similarities aren't on comparable scales. `eval.leave_one_out` now
takes `--method {dense,lexical,fusion}`. Same 300-query harness, `bge-small`.

**Numbers corrected 2026-08-24** (see the facet-rerank section below for how
this was caught): the dense/lexical/fusion numbers below were re-measured
and differ from what this section originally reported
(0.247/0.223/0.275 nDCG@10). Root cause: the original numbers predate a
re-run against the current corpus — `company_text`/`load_corpus` had a
whitespace-fallback bug (fixed in the commit that introduced this test
suite) that changed which 3 companies' text was usable, which shifts every
downstream index and therefore the seeded 300-query sample, even for
lexical (BM25, fully deterministic — confirmed via a fresh re-run, which is
what proved this wasn't run-to-run embedding noise). The fix predates this
session; the recorded numbers just never got regenerated after it landed.
Current, accurate:

- dense:   nDCG@10 0.233 | MRR 0.452 | Recall@10 0.021
- lexical: nDCG@10 0.210 | MRR 0.418 | Recall@10 0.017
- fusion:  nDCG@10 0.258 | MRR 0.463 | Recall@10 0.023

Fusion beats dense-only on all three metrics — lexical alone is weaker, but
it catches sharp keyword/name overlaps dense embeddings blur past, so
combining ranks (not scores) nets a gain rather than diluting the signal.

Build-order step 4 done: facet extraction pipeline, run against the full
corpus. `api/facets.py` holds the five-facet schema — controlled enums for
`customer`/`mechanism`/`wedge`/`business_model` (hand-authored per the plan)
plus a structured-output JSON schema built from them. `problem` deliberately
has no enum in that schema; `pipeline/extract_facets.py` submits/polls a
Message Batches job (`claude-opus-5`, structured outputs) that returns both
a short 3-6 word normalized `problem` label (`value`) and a longer free-text
supporting quote (`span`) per company, alongside the four enum values.
`pipeline/cluster_problems.py` embeds the normalized `value` labels
(`bge-small`), k-means clusters them, and names each cluster after its
**medoid** — the member label closest to the cluster's embedding centroid,
computed locally with plain numpy, no LLM call — then merges the result
into committed `data/facets.json`. This is the bottom-up derivation the plan
calls for, so a hand-authored problem taxonomy never has to be guessed
upfront, and (after an initial version used a Claude call to name clusters)
it now needs zero API calls at all — cost-conscious per user request. Both
scripts split into pure, unit-tested functions (request building,
batch-result parsing, medoid/slugify naming, label merging) and thin I/O
wrappers, so the logic is tested without hitting any API.
`pipeline.extract_facets poll --watch` polls the batch every 30s until it
ends rather than requiring a manual rerun.

A 20-company sample batch ran clean first (measured cost $0.10; enum values
and `problem` labels spot-checked as well-grounded in the source text), then
the full 6,132-company batch ran clean too: 6,132/6,132 succeeded, 0 errors,
written to `data/facets_raw.json`.

Enum revision pass (the plan's rule: flag any value that swallows >30% of
the corpus): `wedge=novel-capability` (56.8%) and
`business_model=subscription` (51.2%) both cross the threshold.
**Decision: accept as-is, do not split.** Spot-checking the spans behind
each shows this isn't a taxonomy failure — `novel-capability` is correctly
catching everything that isn't cheaper/faster/unbundling/regulatory-
arbitrage/distribution-hack (AI-agent products, deep-tech, novel
data/hardware capabilities all genuinely belong there), and `subscription`
dominance reflects that the YC corpus itself is SaaS/AI-heavy, not a
mislabeling. Splitting either would mean inventing sub-categories not
grounded in a real gap and re-spending ~$27 on a re-run for a taxonomy
change that wouldn't sharpen the alignment grid.

`pipeline.cluster_problems` ran clean against the medoid-naming rewrite:
40 clusters, clean readable labels (`clinical-documentation-automation`,
`runtime-infrastructure-for-ai-agents`, `on-demand-food-delivery`, sizes
71-291, no dominant outlier), zero API cost. `data/facets.json` is written —
**build-order step 4 is fully done.** (Earlier attempt hit the org's API
usage limit on the cluster-naming call before the local-naming rewrite;
moot now, but the underlying limit — resets 2026-09-01 00:00 UTC — still
applies to any other Claude call, e.g. `eval.llm_judge`.) Along the way,
caught and fixed a real bug: the first working version clustered on
`problem.span` (the long free-text supporting quote) instead of
`problem.value` (the short normalized label `extract_facets`'s prompt
produces specifically for downstream clustering) — the symptom was
run-on, sentence-fragment cluster names instead of clean short ones.

Build-order step 5 done: alignment grid (`api/alignment.py`) and whitespace
arithmetic (`api/whitespace.py`), both built test-first (red→green, one seam
at a time — see the `tdd` skill). `build_alignment_grid(idea_facets,
company_facets)` returns per-facet `{idea_value, company_value, same}` for
display; `find_whitespace(cohort_facets, facet_name, enum_values)` returns
enum values with zero occupants across a retrieved cohort, in the caller's
enum order. Both are pure functions over facet dicts — no dependency on
`data/facets.json` actually existing yet, so they're fully tested against
synthetic fixtures ahead of the real extraction run.

Build-order step 7 (golden set) done: `data/golden_set.json` — 30 hand-labeled
founder-voice ideas (deliberately messy paragraphs, not YC's polished
marketing copy, per the plan's distribution-mismatch fix), each with
manually-judged `relevant_company_ids` against the real corpus. Candidates
were pooled from both dense and lexical top-25 (reduces bias toward
whichever method the pool came from) and hand-judged by reading the actual
company descriptions. 7 of the 30 ideas have zero relevant companies —
a legitimate "no real prior art in this corpus" label, not a labeling gap.
`eval/golden_set.py` mirrors `eval/leave_one_out.py`'s `build_qrels`/
`build_run` shape (query text is `idea_text` directly; no `exclude_index`
since the idea isn't a corpus row), tested per the `tdd` skill. Results,
`bge-small`:

- dense:   nDCG@10 0.343 | RR 0.374 | R@10 0.494
- lexical: nDCG@10 0.320 | RR 0.351 | R@10 0.431
- fusion:  nDCG@10 0.448 | RR 0.413 | R@10 0.639

Fusion wins on all three metrics again, consistent with the leave-one-out
result — corroborating evidence from an independently-labeled, distribution-
matched eval set rather than a repeat of the same weak-label story.

LLM-judge (coverage check) scaffolded, not yet run: `eval/llm_judge.py`
submits/polls a Batches job (`claude-sonnet-5` — cheaper than Opus 5 per
token, appropriate for a classification task; see decision below —
structured output `{relevant: bool, reason: str}`) judging the fusion
retriever's golden-set top-10 per idea (300 pairs total — confirmed locally,
no API needed to build the pairs). `coverage_report` flags judged-relevant
pairs absent from `eval.golden_set`'s qrels — the whole point of running a
judge alongside hand labels, since those are the candidate false negatives
a small single-labeler golden set is expected to miss. Blocked on the same
org API usage limit as `pipeline.cluster_problems` (resets 2026-09-01
00:00 UTC) — not run against the real API yet.

**Decision (2026-08-23): stay on Claude, not open-weights.** Considered
swapping `llm_judge` (and, briefly, the not-yet-built query-time facet
extraction path) to a local open-weights model over cost concerns. Priced
both: query-time facet extraction on `claude-sonnet-5` runs ~$0.003-0.009
per typed idea (2,200-6,700 queries/month before threatening a $20/month
budget, before the plan's own hash-cache/rate-limit protections even
kick in), and the full 300-pair `llm_judge` batch runs ~$0.30-1.20
depending on model. Neither was ever a dollar-cost problem — both blocked
calls hit the org's usage *quota*, not a price ceiling, and no model swap
fixes a quota. Rejected local inference because: (1) it would introduce
classifier drift between corpus-side facets (Claude-labeled) and
query-time facets (differently-labeled), corrupting the alignment grid's
same/different comparisons: the two sides of every comparison need a
consistent classifier; (2) a weaker, unvalidated judge undermines the one
thing `llm_judge` exists to do — catch subtle false negatives the
automatic metrics miss; (3) hosting a 7-8B local model in the deployed
container shifts cost to hosting/latency, which likely nets out worse than
a sub-cent Claude call. Fine-tuning was floated and dropped — no real
training dataset exists (the 300 golden-set pairs are needed for
*evaluating* a judge, not training one).

`pipeline/extract_facets.py` and `eval/llm_judge.py` share a batch-job
module, `api/anthropic_batch.py` (submit/poll/watch/parse/collect), instead
of each hand-rolling the same Message Batches lifecycle. This fixed a real
bug caught in review: the two hand-copied versions had drifted, and
`eval.llm_judge`'s `poll` didn't actually support `--watch` despite its own
docstring claiming it did. `build_judge_pairs` also dropped a redundant
re-sort — `eval.golden_set.build_run`'s dict is already in rank order by
construction (dict insertion order + already-sorted input), so re-deriving
that order was dead work hiding an undocumented cross-module contract.

`api/fusion.py` also gained `build_retriever(companies, method, model_key="bge-small") -> Retriever`,
replacing the dense/lexical/fusion construction branch that had been
copy-pasted three times across `eval/leave_one_out.py`, `eval/golden_set.py`,
and `eval/llm_judge.py` — it now owns the shared-companies invariant
`FusionRetriever`'s docstring warns about (dense and lexical must be built
over the same list) as a single constructor instead of three comments.
Re-running `eval.golden_set --method fusion` after the rewire reproduced
the exact same numbers (nDCG@10 0.448, RR 0.413, R@10 0.639), confirming
the refactor is behavior-preserving.

Not yet started: alignment/whitespace wiring into the LLM-judge and
facet-aware rerank, API, frontend. Also queued from architecture review: a
validated `Facets` load boundary at `data/facets.json` (`api/facets.py`'s
`validate_facets` exists but is currently dead code, never called by the
pipeline that produces the file it's meant to validate) — deferred until
an API layer exists to consume it, since the seam's shape is underdetermined
until then.

Build-order step 6 done: facet-aware rerank, `api/rerank.py`. Within the
fused top-50, `rerank_by_facets` stable-sorts by descending
`facet_match_count` (0-5 shared enum values) against the query's own
facets, keeping RRF order as the tiebreak — a plain count, not a tuned
weighted blend, matching CONTEXT.md's "alignment is never a scalar" spirit.
`FacetRerankRetriever` wraps any Retriever and satisfies the same protocol,
so it drops into `eval.leave_one_out.build_run` unchanged. It gets the
query's own facets via `exclude_index` — in leave-one-out the query *is*
corpus row `exclude_index`, and that row's facets are already committed in
`data/facets.json`, so this ablation needed zero new API calls.

**Bug caught and fixed:** the first working version reordered the
`(index, score)` list but left the *old* retrieval score attached to each
entry. `ir_measures.calc_aggregate` ranks purely off the numeric score
field — confirmed directly by feeding it a tiny hand-built run where the
"first" doc has the lowest score, and it ranked last, regardless of dict/
list order — so a reorder that doesn't rewrite the score is silently a
no-op for every metric. It was caught because two independent ablation
rows (this one and golden-set's, below) came back suspiciously identical
to their respective plain-fusion baselines. Fix: `rerank_by_facets` now
assigns a synthetic score that directly encodes the new order (descending
by final rank position), with every reranked entry scoring above every
untouched tail entry. TDD'd, 12 tests total in `tests/test_rerank.py`.
`eval.leave_one_out` and `eval.golden_set` both take `--method
facet-rerank`. Same 300-query harness, `bge-small` (post the baseline
correction above):

- dense:        nDCG@10 0.233 | MRR 0.452 | Recall@10 0.021
- lexical:      nDCG@10 0.210 | MRR 0.418 | Recall@10 0.017
- fusion:       nDCG@10 0.258 | MRR 0.463 | Recall@10 0.023
- facet-rerank: nDCG@10 0.298 | MRR 0.508 | Recall@10 0.026

A real win this time, on all three metrics — unlike the pre-fix numbers,
which happened to be measuring plain fusion twice.

The golden-set version of this row is no longer blocked: `data/
golden_set_facets.json` (all 30 ideas, extracted via
`pipeline/extract_golden_set_facets.py` against the corpus's already-derived
40-value `problem` enum — see below) exists now. `eval.golden_set
--method facet-rerank`:

- fusion (baseline):  nDCG@10 0.448 | MRR 0.413 | Recall@10 0.639
- facet-rerank:        nDCG@10 0.353 | MRR 0.343 | Recall@10 0.561

A decline here, reported honestly rather than cherry-picked — the two
harnesses disagree. Plausible reading: leave-one-out's weak subindustry
labels happen to correlate with the five idea facets (both are coarse
industry-shaped categories), so facet-match promotion helps there; the
golden set's 30 hand-labeled qrels are true relevance judgments with very
few positives per idea (many ideas have 0-2 relevant companies total), so
promoting by raw facet-match count has more room to bump a facet-similar
but not-actually-relevant company above the one or two real hits. Facet
rerank is not a documented unconditional win — worth carrying into the
final ablation table as a real, mixed result rather than picking whichever
harness looks better.

`pipeline/extract_golden_set_facets.py`: a one-off batch (not part of the
regular corpus pipeline) that classifies each golden idea into the five
facets, passing the corpus's already-derived `problem` enum
(`api/facets.extraction_schema(problem_enum=...)`, a new optional param) so
idea-side and corpus-side `problem` values are directly comparable — the
free-text version would have produced fresh labels that could never match
any corpus company's `problem` value, silently zeroing that facet's
contribution to every match count. Cost: measured exactly from real batch
`usage` (not estimated) — $0.176 total for all 30 ideas on `claude-opus-5`
Batch API (1,058 fresh + 1,917 cached input tokens, 13,858 output tokens).
Note `count_tokens` badly overestimates cost for schema-heavy structured-
output requests (it counted the full JSON schema as ~1,952 tokens/request
of literal prompt text; real billed input was ~99 tokens/request) — trust
real batch `usage`, not `count_tokens`, for anything with a nontrivial
`output_config.format` schema.

Build-order step 8 started: the FastAPI query-time path. `api/query.py`
holds `build_query_result` — the pure core (rank → facet-rerank the top 50
via the same `rerank_by_facets` step 6 introduced → attach an
`build_alignment_grid` per displayed company → compute `find_whitespace`
per facet over the displayed cohort), unit-tested against synthetic
fixtures with no corpus or API dependency, per the `tdd` skill. Its
`enum_values_for` helper closes a real gap: `problem` has no hand-authored
enum (see step 4), so whitespace for that facet is computed against every
distinct value observed across the *full* corpus, not just the 12
displayed companies — tested explicitly (`test_problem_whitespace_enum_
universe_is_the_full_corpus_not_just_the_displayed_cohort`) so a value
absent from the top 12 but present elsewhere in the corpus doesn't get
misreported as true whitespace.

`api/extract_idea.py` is the query-time facet-extraction call — a single
synchronous `client.messages.create`, not the Batches API, since a founder
typing an idea can't wait for batch turnaround. Reuses
`pipeline.extract_facets`'s `MODEL`/`SYSTEM_PROMPT` and passes the corpus's
own `problem` enum (same reasoning as `extract_golden_set_facets.py`, so
a live idea's `problem` value is directly comparable to a company's).
Split into pure request/response functions (tested with a hand-built fake
message object, mirroring `tests/test_anthropic_batch.py`'s pattern) and a
thin `extract_idea_facets` I/O wrapper.

`api/app.py` wires it together: `handle_query` (extract → `validate_facets`
→ `build_query_result`, tested with a fake extractor and fake retriever —
no corpus, no live call) is the seam; `create_app()` is the thin FastAPI
factory that loads the corpus, builds the fusion retriever, and loads
committed `data/facets.json` once at process startup rather than
per-request, then exposes `POST /query`. This is also the load-bearing
call site `api/facets.py`'s `validate_facets` was waiting on — it was dead
code until now (see step 5's note); it now guards every live extraction
before the pure core ever sees it. Verified the app boots end-to-end
(`create_app()` loads the real corpus/retriever/facets with no errors) —
the live `/query` call itself is untested against the real API, still
blocked by the same org usage quota (resets 2026-09-01 00:00 UTC) noted in
steps 4 and 7. `fastapi`/`uvicorn` added to `requirements.txt`.

Rate limiting and the normalized-hash query cache are done. `api/cache.py`'s
`QueryCache` keys on `normalize_query` (lowercase, collapsed whitespace) so
"A Marketplace for Used Textbooks" and "a marketplace  for used textbooks"
hit the same entry and skip both the Claude call and the ranking pass
entirely — `api/app.py`'s `handle_query` checks it before extraction and
populates it after, tested by asserting the fake `extract` is called
exactly once across two near-identical queries. `api/ratelimit.py`'s
`RateLimiter` tracks two in-memory sliding windows (per-IP per-hour,
shared daily cap across all IPs) with an injectable clock, tested without
real sleeps by advancing a fake `now()`. `api/app.py`'s `check_rate_limit`
is the seam between the two — a pure function from `(limiter, ip)` to
`None` or `DEMO_LIMIT_MESSAGE` — so the "degrade to a message, not an
error" behavior the plan calls for is unit-tested directly, without
booting the app or going through `TestClient` (which would otherwise force
loading the real corpus/embeddings/API client just to check a 2-line
policy). Both are process-local/in-memory, matching the single-container
architecture — not meant to survive a restart or scale past one instance.

Not yet done: canned example ideas, the SPA, and Dockerfile — the rest of
step 8/9.
