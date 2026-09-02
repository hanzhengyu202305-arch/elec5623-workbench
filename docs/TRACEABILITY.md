# Requirements traceability matrix

This matrix links requirements to the vertical-slice implementation and tests.
Evidence columns describe what must be retained for the proposal/demo; they are
not completion claims.

| Requirement | Implementation | Verification | Retained evidence / report use |
|---|---|---|---|
| FR-01–02 | `schemas.py` | `test_schemas.py` covers duplicate requirement, evidence, and expected-claim ids plus unknown references/extra fields | Validation transcript; requirements section |
| FR-03 | `segmentation.py`, engine no-claim gate | segmentation, failure-mode, CLI, and API tests | Stable claim ids plus heading/fenced-only fail-closed transcript |
| FR-04–05 | `retrieval.py` | `test_retrieval.py` | Backend and ranked matches; architecture/evaluation |
| FR-06 | `gateway.py`, `engine.py` | `test_gateway.py`, `test_engine.py`, `test_metrics.py` | Five-label report plus mocked compatible-provider contract; method/evaluation |
| FR-07–09 | `validation.py`, `engine.py` | `test_validation.py`; engine regression proves an altered quote overrides a positive gateway decision to `UNSUPPORTED` | Citation and quote failure artifact; trust discussion |
| FR-10 | `retrieval.py` | `test_retrieval.py` | Mapping examples; requirements/evaluation |
| FR-11–12 | `engine.py`, `metrics.py`, `artifacts.py`, `scripts/run_corpus_acceptance.py`, `scripts/run_baseline_study.py` | engine/CLI/API regressions prove non-empty ground truth must cover segmented claim ids exactly before provider/artifacts; metric, Markdown report-contract, corpus-acceptance, and baseline-study tests cover aligned scoring and complete human-readable output | Current-source no-clobber acceptance plus 200 complete human-readable claim audits and multitemplate ablation/error JSON now; frozen-corpus scorecard after approval |
| FR-13 | `artifacts.py` same-directory staging, `fsync`, atomic no-clobber links, final `report.json` commit marker, and stable unaliased report reads | render/write failures, partial-stage interruption, report-marker interruption, publish-order, symlink run/report, and report-identity regressions | No partial or aliased marker becomes readable; distinct run dirs and hashes |
| FR-14 | `artifacts.py` stable review-target checks and durable locked append | `test_artifacts.py`, `test_api.py`, and `test_cli.py` cover two normal appends, short/zero writes, concurrency, unsupported locking, symlink/hard-link targets, and unchanged outside victims | Parseable JSONL records, unchanged report hash, typed alias rejection through service/API/CLI; governance |
| FR-15 | `cli.py`, `api.py`, gateway environment factory | `test_cli.py`, `test_api.py`, `test_gateway.py` cover the default fixture and explicit compatible-provider path | CLI/API transcript; demo script |
| FR-16 | `compare.py` `ComparisonService`; CLI `compare` | `test_compare.py` and `test_cli.py` run ≥2 named gateways on one bundle via `EvaluationService` | Sequential compare transcript; Workbench demo |
| FR-17 | `compare.py` ranking, list-price estimate, `compare.json`/`compare.md` | Divergence test: min-cost vs quality/task-fit select different models; schema-valid compare artifacts | Separate quality, task-fit, time, and estimated-cost columns; no combined index |
| FR-18 | `compare.py` annotation-preferred ranking | Labelled run matches quality-rule preferred model; unlabelled run sets `label_verification_available=false` and does not claim prediction/success | Evaluation section; human-review remains success |
| NFR-01, 02, 07 | schemas, engine, artifacts, `scripts/check_fixture_reproducibility.py` | two fresh processes; schema-validated disk report/input comparison; phantom/corrupted-artifact regressions; canonical report comparison excludes only `run_id` and `created_at`; live store rejects symlink run/report targets, report-id mismatch, and symlink/hard-link review targets; append-only review short-write, zero-progress rollback, unsupported-platform and concurrent-writer regressions | No-clobber normalized-report evidence JSON; parseable unique review JSONL; unchanged alias victims; traceability and audit appendix |
| NFR-03 | evaluation service, corpus acceptance runner | `test_corpus_acceptance.py` verifies `elapsed_seconds <= 60.0` is part of PASS and a slow run fails; repeat after tutor-approved freeze | JSON report records the `<= 60.0` check, Python/platform, corpus/prediction hashes, and run ids |
| NFR-10 | `ComparisonService` wall-clock and fail-closed publish | two-model fixture compare of the sample bundle records `elapsed_seconds <= 60.0`; unavailable-gateway compare writes no `compare.json`/`compare.md` | Comparison latency appendix; incomplete compare must not look finished |
| NFR-04–06 | engine, validation, gateway | `test_failure_modes.py` blocks ordinary/unbroken budget excess and injection; `test_ground_truth_alignment.py` blocks missing/unknown annotations through Engine, CLI validate, and API before provider/artifacts; `test_gateway.py` enforces the compatible-provider failure boundary | Negative-test transcript; risk/ethics section; no real provider call |
| NFR-08–09 | README, project config, locked clean-environment harness | `v7` expected cache-miss FAIL, explicit locked prefetch `v8` PASS, first fully offline replay `v9` PASS, and current-source fully offline replay `v12` PASS; 2026-09-02 Workbench suite `152 passed` at `94.02%` branch coverage | Reproduction appendix and retained manifests; human onboarding timing remains a separate gate |

Before proposal submission, every row must be reconciled against the official
rubric and tutor-approved scope. New claims need a requirement, a test, retained
evidence, and an identified report section.

## Reproducible draft acceptance command

```bash
python scripts/run_corpus_acceptance.py \
  --runs-dir acceptance/runs-YYYYMMDD-HHMMSS \
  --out acceptance/corpus-acceptance-YYYYMMDD-HHMMSS.json
```

The runner uses `FixtureModelGateway` only and requires exactly 20 bundles and
200 claims. It fails the acceptance when any existing threshold is missed:
citation completeness 1.00, five-label macro-F1 0.65, risky precision 0.80,
risky recall 0.75, or requirement-mapping macro-F1 0.70. It refuses to overwrite
the JSON report. NFR-03 is a sixth, upper-bound check: elapsed time must be
`<= 60.0` seconds. Preserve that report together with the referenced run root.

Token-budget preflight does not count whitespace-delimited words. It treats the
canonical input bundle's UTF-8 byte count as a conservative token upper bound,
which ensures long unbroken JSON/Markdown content is blocked before any provider
call when it exceeds the configured budget.

Before any run, the runner rejects duplicate `bundle_id` values and rejects an
expected claim-id sequence that differs from actual segmentation. Regression
tests confirm both failures leave the run root and acceptance report absent.

This command currently evaluates deterministic **draft/unfrozen** synthetic
templates. Its `PASS` is reproducibility evidence, not a tutor-approved corpus,
scope decision, or final reported experiment.

The current retained current-source report is
`acceptance/local-20260804-review-integrity-v2/corpus-acceptance.json`; the matching
five-variant development study is
`acceptance/local-20260803-multitemplate-study-v3/baseline-study.json`. Their
shared corpus SHA-256 is
`45e8a30308ad78be0dcb1ed48d3fa9cf4684bacd3ed348cc3a4c17e25ca09fa9`
and their service prediction SHA-256 is
`8f28dff5ae7d65a817f16de63447f252b187ba6f3f0df7607ff0b8ad4aba804f`.
The full fixture result is macro-F1 `0.8577014177655716`, risky precision
`0.9302325581395349`, risky recall `1.0`, and mapping macro-F1 `0.96`, with
`37` label errors and `12` mapping errors retained for analysis. It remains a
synthetic development result, not frozen or tutor-approved evidence.

## Effectiveness-dimension mapping

Proposal evaluation language reports three effectiveness dimensions separately.
FR-16–18 add a compare shell that still does not invent a combined score.

| Dimension | Existing requirements | What is measured | What it is allowed to predict | What it is not |
|---|---|---|---|---|
| Output quality | FR-06–09, FR-11–12, FR-17; RQ2, RQ3 | Five-label support, citation/quote integrity, risky-claim precision/recall | Independent annotations and later human-review agreement on a frozen set | Model list price, token spend, or a hidden single score |
| Task fit | FR-10–12, FR-17; RQ4 | Requirement-mapping macro-F1 bounded to stated IDs | Independent requirement-mapping annotations | Coverage of an unstated or invented task |
| Efficiency | NFR-03, NFR-04, NFR-05, NFR-10; FR-17; RQ5 | Elapsed time, fail-closed token-budget / unsafe-input behaviour, and estimated list-price cost shown separately | Whether a run stays inside the nominated time and budget without publishing a false report | An invoice, or cheaper-is-worse ranking treated as quality |
| Model comparison | FR-16–18; NFR-10 | Sequential named-gateway runs on one bundle; min-cost vs quality/task-fit selection; optional annotation-preferred match | Whether the two documented policies pick the same labelled model | Auto model-deploy, or a claim that quality ranking predicts deployment success |
| Trace / review join | FR-01–03, FR-13–15; NFR-01, NFR-02, NFR-07; RQ1, RQ6 | Complete traces, immutable artifacts, append-only human review | Reproducibility of the packet a reviewer uses | An automated verdict or hidden composite index |

The only join of the three dimensions is the human-review queue
(`READY_FOR_HUMAN_REVIEW`). A combined effectiveness index is out of scope.
`report.md` now groups the existing metrics under Quality, Task fit, and
Efficiency headings without adding fields to `report.json`. The corpus
acceptance JSON repeats the same grouping and records `token_spend_aud` as
null so spend cannot be mistaken for a passing metric. `compare.md` reports
estimated cost as list-price × conservative token bound, not a bill.
