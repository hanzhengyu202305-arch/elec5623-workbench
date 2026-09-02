# Model Effectiveness Evaluation Workbench

Public GitHub (anyone with the URL can clone/read; collaborator invites are optional):
https://github.com/hanzhengyu202305-arch/elec5623-workbench

Clone: `git clone https://github.com/hanzhengyu202305-arch/elec5623-workbench.git`

Group members should start with [GROUP_ONBOARDING.md](GROUP_ONBOARDING.md).

Public product: **Model Effectiveness Evaluation Workbench**. The inner engine
is the **Inspector** (FR-01–15). One shell, not two products or repositories.

An independent ELEC5623 Track B vertical slice. On the same evidence-backed
task it runs at least two named models, then reports quality, task fit,
latency, and estimated cost separately and contrasts min-cost versus
quality/task-fit selection. Human review remains the only automated success
state (`READY_FOR_HUMAN_REVIEW`). There is no combined “effectiveness” score
and no auto model-deploy.

The Inspector engine accepts an English JSON bundle containing requirements,
evidence, and AI-generated Markdown; it segments the output into claims,
retrieves local evidence, classifies support, checks exact quotations, maps
requirements, calculates transparent metrics, and creates an immutable run for
human review.

The first daily scene is a student lab write-up. The evaluation question is
which of two models hallucinates less / fits the stated task better, not a
generic document auditor. The tool is not a chat app and does not read PDFs;
you paste notebook text as evidence. This is independent ELEC5623 coursework.

## Current vertical slice

- Pydantic v2 input/output contracts with unknown-field rejection.
- Deterministic claim segmentation and `FixtureModelGateway` for CI.
- Local TF-IDF evidence retrieval with an explicitly reported lexical fallback.
- Five support labels: `SUPPORTED`, `PARTIALLY_SUPPORTED`, `UNSUPPORTED`,
  `CONTRADICTED`, and `INSUFFICIENT_EVIDENCE`.
- Exact citation and quote checks, requirement mapping, classification and
  coverage metrics.
- The human-readable Markdown audit exposes every metric category, then expands
  each claim with its rationale, ranked evidence scores/excerpts, and exact-quote
  result. Untrusted claim, evidence, and provider text is isolated in a
  dynamically sized literal fence so it cannot forge report structure.
- Atomic no-clobber `input.bundle.json`, `report.json`, and `report.md` artifacts:
  each file is fully written and synced under a same-directory staging name,
  then atomically linked to its final name.
- `report.json` is atomically published last as the completed-run commit marker;
  rendering or ordinary writing failure removes only the explicitly known
  incomplete artifacts. An uncatchable process or power loss may leave a run
  directory without that marker, but it cannot expose a partial marker as a
  completed run.
- Append-only `reviews.jsonl`; review actions never mutate an evaluation report.
  Each record is fully written and `fsync`ed while holding a POSIX
  `fcntl.flock`; platforms without that locking primitive reject review writes
  rather than using an unsafe fallback. Read/review operations also require a
  real run directory, one stable unaliased regular `report.json`, matching
  report/run identity, and an unaliased regular review target. Symlink/hard-link
  aliases fail closed without changing their outside target.
- CLI and FastAPI use the same service boundary.
- Token-budget, prompt-injection, provider-timeout, and malformed-response
  failures stop without producing a completed run.
- `expected_claims` is all-or-none ground truth: when any annotation is supplied,
  its ids must cover the segmented claims exactly. Missing or unknown annotation
  ids fail before retrieval, provider execution, metrics, or artifacts.

Token preflight uses the canonical bundle's UTF-8 byte count as a conservative
upper bound: every tokenizer token must consume at least one byte. This is
deliberately not a whitespace-based estimate, so a long unbroken string cannot
bypass the configured token budget.

Heading-only and fenced-code-only Markdown contains no auditable claim. Engine,
CLI, and API requests fail closed instead of reinterpreting ignored structure as
a claim.

The first-month boundary is intentional: English JSON/Markdown only, no PDF
parsing, no web retrieval, no database, no frontend framework, and no live
commercial model APIs in the compare CLI.

## Quick start

Use Python 3.11 exactly. The course runtime is intentionally constrained to
`>=3.11,<3.12`; other Python versions are not an acceptance environment.

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e '.[dev]'
```

One-command local demo (no live model):

```bash
bash scripts/run_workbench_demo.sh
```

Validate, evaluate, compare two fixture models, and append a review:

```bash
evidence-inspector validate examples/daily_lab_writeup.json
evidence-inspector evaluate examples/daily_lab_writeup.json --out runs/
evidence-inspector compare examples/daily_lab_writeup.json --out runs/ --models fixture,fixture-b
evidence-inspector review RUN_ID examples/daily_lab_review.json --runs runs/
```

The lab example catches a copied current that is right, a stall current that
contradicts the notebook, a quoted 1.20 A that was never written, a datasheet
citation that was never supplied, and a weather sentence with no lab evidence.
Keep `examples/sample_bundle.json` for the original contract demo.

Validate, evaluate, compare, and append a review on the contract sample:

```bash
evidence-inspector validate examples/sample_bundle.json
evidence-inspector evaluate examples/sample_bundle.json --out runs/
evidence-inspector compare examples/sample_bundle.json --out runs/ --models fixture,fixture-b
evidence-inspector review RUN_ID examples/review.json --runs runs/
```

`compare` sequentially evaluates the same loaded bundle under at least two
unique known names (`fixture`, `fixture-b`). It writes `{out}/compare.json` and
`{out}/compare.md` only when every model succeeds. Estimated cost is published
list price times the conservative UTF-8 token bound, not a bill; `fixture` is
0. Live commercial APIs are out of scope this week.

`validate` is provider-free and creates no artifact. In addition to strict JSON
schema checks, it runs the token/injection preflight, deterministic claim
segmentation, the no-auditable-claim gate, and all-or-none ground-truth
alignment. Its success JSON reports both segmented and ground-truth claim counts.

Each evaluation creates a new directory even when the same bundle is evaluated
twice. Inspect `runs/RUN_ID/report.md` for the claim-evidence audit and its human
review target; append-only decisions are written separately to `reviews.jsonl`.
The Markdown metrics section reports quality, task fit, and efficiency
separately. It does not emit a combined score or treat token spend as quality.

### Explicit model-gateway opt-in

The CLI and API default to `FixtureModelGateway`; merely defining an endpoint or
key does not enable network access. An instructor-approved OpenAI-compatible or
Azure OpenAI-compatible Chat Completions endpoint is selected only when all
required variables and the explicit mode are set:

```bash
export EVIDENCE_INSPECTOR_GATEWAY=openai-compatible
export EVIDENCE_INSPECTOR_MODEL_ENDPOINT='https://APPROVED_HOST/FULL_CHAT_COMPLETIONS_PATH'
export EVIDENCE_INSPECTOR_MODEL_ALLOWED_HOSTS='APPROVED_HOST'
export EVIDENCE_INSPECTOR_MODEL_API_KEY="$COURSE_APPROVED_MODEL_API_KEY"
export EVIDENCE_INSPECTOR_MODEL='APPROVED_MODEL_OR_DEPLOYMENT'
export EVIDENCE_INSPECTOR_MODEL_API_KEY_HEADER=Authorization  # or: api-key for Azure
export EVIDENCE_INSPECTOR_MODEL_TIMEOUT_SECONDS=20
```

Do not paste a real key into shell history, source, screenshots, reports, or the
AI Journal; the variable expansion above assumes an approved secret injection
method has already populated `COURSE_APPROVED_MODEL_API_KEY`. The endpoint must
use HTTPS with a non-root full request path, contain no URL user/password or
fragment, and contain either no query or exactly one non-empty Azure
`api-version` query. Every other query key is rejected. Its canonical hostname
must exactly match one comma-separated entry in
`EVIDENCE_INSPECTOR_MODEL_ALLOWED_HOSTS`; an Azure private endpoint is permitted
only when it is explicitly named there. Redirects are refused so authentication
cannot follow a changed host or a TLS downgrade. Only `Authorization`
(Bearer) and `api-key` headers are accepted. Model/key/header/timeout fields are
validated before use, both endpoint and key are excluded from configuration
`repr`, domain errors do not echo them, and malformed, deeply nested, or larger
than 64 KiB provider responses fail closed. Tests replace the no-redirect opener
with local fakes; this repository has not contacted a real provider.

Return to the deterministic default by unsetting `EVIDENCE_INSPECTOR_GATEWAY`
or setting it to `fixture`. CLI gateway selection occurs only for `evaluate`;
API selection occurs when `create_app` constructs its service at startup.

Start the API:

```bash
EVIDENCE_INSPECTOR_RUNS=runs uvicorn evidence_inspector.api:app --reload
```

The four public endpoints are:

```text
GET  /health
POST /v1/evaluations
GET  /v1/evaluations/{run_id}
POST /v1/evaluations/{run_id}/reviews
```

The OpenAPI page is available at `http://127.0.0.1:8000/docs`. Local HTTP is
appropriate for this development server; configured external model endpoints
must use HTTPS because they carry credentials.

## Verification

Current bounded local verification uses CPython `3.11.15`: `149` tests pass at
`94.02%` branch coverage. The current no-clobber development reports are:

- `acceptance/local-20260804-review-integrity-v2/corpus-acceptance.json`;
- `acceptance/local-20260803-multitemplate-study-v3/baseline-study.json`; and
- `acceptance/clean-env-offline-replay-20260804-v12/manifest.json`.

The 20-bundle/200-claim fixture development result has citation completeness
`1.0`, five-label macro-F1 `0.8577014177655716`, risky precision
`0.9302325581395349`, risky recall `1.0`, and requirement-mapping macro-F1
`0.96`. Its corpus SHA-256 is
`45e8a30308ad78be0dcb1ed48d3fa9cf4684bacd3ed348cc3a4c17e25ca09fa9`;
its service prediction SHA-256 is
`8f28dff5ae7d65a817f16de63447f252b187ba6f3f0df7607ff0b8ad4aba804f`.
The full fixture replay retains `37` label errors and `12` mapping errors, so a
passing aggregate is not presented as perfect performance. The corpus remains
synthetic, development-only, unfrozen, and not tutor-approved.

For clean-environment evidence, `v7` is the retained expected offline cache-miss
failure, `v8` is the explicit public-PyPI locked-dependency prefetch followed by
offline project execution, and `v9` is the first fully offline cache replay.
Current-source `v12` is a fresh, non-editable fully offline replay that includes
the complete Markdown claim-audit renderer, semantic ground-truth validation,
and the review-target integrity implementation;
its two reports expose all 22 sample claims. No model provider was called in any
of these runs. See
`docs/CLEAN_ENVIRONMENT_REPRODUCTION.md` for the exact boundary.

```bash
pytest
pytest --cov=evidence_inspector --cov-report=term-missing
python scripts/generate_synthetic_corpus.py --check-only
python scripts/check_fixture_reproducibility.py examples/sample_bundle.json \
  --runs-root acceptance/repro-runs-YYYYMMDD-HHMMSS \
  --out acceptance/fixture-repro-YYYYMMDD-HHMMSS.json
python scripts/check_proposal_structure.py
```

### Proposal candidate PDF

The compressed source and rendered output remain visibly blocked drafts until
real group and tutor facts replace every sentinel:

```text
PROPOSAL_CANDIDATE_NOT_FOR_SUBMISSION.md
output/pdf/ELEC5623_GroupXX_Proposal_DRAFT_NOT_FOR_SUBMISSION.pdf
PDF_QA_REPORT.md
```

Build with the bundled workspace Python, which carries the isolated PDF tooling:

```bash
/Users/hanzhengyu/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 \
  scripts/build_proposal_pdf.py --force
```

The builder defaults to no-clobber; `--force` replaces only an existing regular
draft after source/output alias, hard-link, final-symlink, suffix, and identity
checks. The source identity and SHA-256 are captured from a stable descriptor
and rechecked immediately before publication; a previously absent output uses
an atomic same-directory no-clobber link. The builder validates the exact
candidate H1/12-section structure outside fenced code, substantive per-section
floors, one-page cover, 8-10 rendered body pages, reference-only final pages,
section-bound draft/external-gate markers, adaptive source-content anchors,
near-blank pages, page-count agreement, reachable invisible text rendering
modes, and exact source/PDF token-sequence equality after deterministic page
chrome is removed. ReportLab invariant mode makes equal source and renderer
inputs byte-reproducible. Raster inspection remains a separate required gate.

Run the PDF-boundary regression suite separately from the coursework runtime:

```bash
/Users/hanzhengyu/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 \
  scripts/test_proposal_pdf_builder.py
```

The builder does not close team, tutor, stakeholder, policy, frozen-result,
member-review, or Canvas gates. Every changed PDF must also be rendered and
inspected page by page; see `PDF_QA_REPORT.md`.

The corpus generator deterministically checks the planned 20-bundle/200-claim
evaluation shape without borrowing data from any prior project. Freeze a corpus
only after tutor approval:

```bash
python scripts/generate_synthetic_corpus.py --out corpus/v1
```

The generator refuses to overwrite any existing bundle.

### Draft corpus acceptance evidence

Run the fixture-only 20-bundle/200-claim acceptance with explicit artifact and
report paths:

```bash
python scripts/run_corpus_acceptance.py \
  --runs-dir acceptance/runs-YYYYMMDD-HHMMSS \
  --out acceptance/corpus-acceptance-YYYYMMDD-HHMMSS.json
```

To evaluate previously materialized draft bundles, also pass
`--corpus-dir corpus/v1`. The command aggregates citation completeness,
five-label macro-F1, risky precision/recall, requirement-mapping macro-F1, and
elapsed time across all 200 claims. `PASS` also requires elapsed time `<= 60.0`
seconds (NFR-03). It records input and prediction hashes,
runtime details, and the 20 immutable run ids.

Before the first run, all 20 `bundle_id` values must be globally unique and each
expected claim-id sequence must exactly match deterministic segmentation.
Duplicate ids or annotation drift exit without run artifacts or an acceptance
report.

Both output surfaces are no-clobber: choose a new `--out` path for every run;
an existing report causes an error. The report explicitly records
`DRAFT_UNFROZEN_NOT_TUTOR_APPROVED` and `tutor_approval_claimed: false`. A local
`PASS` is baseline engineering evidence only—not tutor approval, final corpus
freeze, or a performance claim about future data.

The normalized reproducibility command evaluates the same bundle in two fresh
Python interpreter processes and separate fixture-only artifact roots. It then
re-reads and schema-validates both persisted `report.json` and
`input.bundle.json` files. It removes exactly `run_id` and `created_at` from the
reports, compares canonical JSON bytes, verifies each report's input hash against
the persisted and requested bundle, records raw artifact hashes and runtime, and
refuses to reuse either output path. It does not prove a clean checkout,
live-provider reproducibility, or corpus generalization.

## Project truth surfaces

- [Group onboarding (read first)](GROUP_ONBOARDING.md)
- [Current status and verified gates](STATUS.md)
- [Functional requirements](docs/REQUIREMENTS.md)
- [NFRs and constraints](docs/NFR_CONSTRAINTS.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Requirements traceability](docs/TRACEABILITY.md)
- [Official 12-section Proposal working draft](PROPOSAL_DRAFT.md)
- [Compressed blocked Proposal candidate](PROPOSAL_CANDIDATE_NOT_FOR_SUBMISSION.md)
- [Candidate PDF builder](scripts/build_proposal_pdf.py)
- [Candidate PDF boundary regression](scripts/test_proposal_pdf_builder.py)
- [Candidate PDF visual/automated QA](PDF_QA_REPORT.md)
- [Draft baseline, ablation, and error study](docs/BASELINE_ABLATION_STUDY.md)
- [Proposal outline/navigation](PROPOSAL_OUTLINE.md)
- [Official brief provenance and compliance](ASSIGNMENT_REQUIREMENTS_MATRIX.md)
- [Verified reference register](REFERENCES_REGISTER.md)
- [Team formation and pitch](TEAM_FORMATION_PITCH_PACK.md)
- [Tutor approval request/checklist](TUTOR_APPROVAL_PACK.md)
- [Week 3 oral progress check](WEEK3_ORAL_PROGRESS_CHECK_PACK.md)
- [Week 1 attendance, AI-use, approval, and assessment controls](WEEK1_COURSE_CONTROL.md)
- [Lab 1 completion pack](LAB1_COMPLETION_PACK.md)
- [Prior-work disclosure](PRIOR_WORK_DISCLOSURE.md)
- [AI journal](AI_JOURNAL.md)

The official Proposal brief was captured and hashed on `2026-08-02`: the 10%
group PDF is due through Canvas on `2026-09-08 23:59`, with mandatory lab tutor
approval recorded on the cover. Live Canvas revisions and tutor decisions
override this working repository. The current development corpus passes the
proposed engineering thresholds, but those values remain proposed rather than
course-mandated and are not a frozen-corpus or generalisation claim.

## CI location

This dedicated public repository is
https://github.com/hanzhengyu202305-arch/elec5623-workbench (`main`). A local
`.github/workflows/ci.yml` template exists on disk but is not pushed: the
current `gh` token lacks the `workflow` scope, so GitHub Actions is not
enabled. Fixture CI has not run on GitHub. Human review remains the only
automated success state; there is no auto-deploy.
