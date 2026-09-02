# Non-functional requirements and constraints

## NFR candidates

The official Proposal brief requires at least five NFRs; the ten candidates
below exceed that numerical minimum but remain subject to tutor approval.

| ID | Requirement | Measurable acceptance criterion |
|---|---|---|
| NFR-01 Traceability | Every result links to its input hash, claim, citations, evidence matches, requirements, gateway, and retrieval backend. | 100% of serialized assessments contain the required trace fields. |
| NFR-02 Reproducibility | Fixture-mode output is deterministic except run id and creation time. | Normalized reports are byte-equivalent across two clean runs. |
| NFR-03 Performance | A 200-claim corpus completes within 60.0 seconds on the nominated lab machine. | Corpus acceptance includes an `elapsed_seconds <= 60.0` PASS/FAIL check and records machine/runtime details. Repeat after tutor-approved freeze. |
| NFR-04 Token budget | Provider-bound input is checked against a configured budget before any call. | The canonical bundle's UTF-8 byte count is used as a conservative token upper bound; ordinary and long-unbroken over-budget tests create no run directory. |
| NFR-05 Fail closed | Unsafe input, incomplete/mismatched ground truth, timeout, unavailable provider, or invalid provider JSON cannot become a completed run. | Engine, CLI and API failure tests assert that semantic drift is rejected before provider execution and no `report.json` exists. |
| NFR-06 Privacy | Raw input remains local except the minimum claim/evidence payload intentionally sent to a configured model endpoint. | Architecture/data-flow review plus redacted logs. |
| NFR-07 Auditability | Evaluation artifacts are no-clobber and human reviews are append-only. | Report hash remains unchanged; real unaliased run/report/review targets and matching report/run identity are required; review appends hold an exclusive file lock through complete short-write handling and `fsync`; zero-progress writes roll back; concurrent-writer JSONL remains complete, parseable and unique. Symlink/hard-link targets and unsupported locking platforms fail closed. |
| NFR-08 Onboarding | A new team member can install, evaluate the sample, and run tests from the README. | Clean-environment reproduction is completed in 20 minutes. |
| NFR-09 Maintainability | Core package branch coverage is at least 80%. | `pytest --cov` exits successfully at the configured threshold. |
| NFR-10 Comparison latency | A two-model fixture compare of the sample or daily-lab bundle completes within 60.0 seconds, the same order as NFR-03. | `ComparisonService` records wall-clock `elapsed_seconds <= 60.0`; any model fail-closed must not publish `compare.json` or `compare.md`. |

Estimated comparison cost (FR-17) is a published USD-per-million-input-token
list price multiplied by `conservative_token_upper_bound`. It is not an
invoice. Named `fixture` / `fixture-v1` cost is 0; `fixture-b` uses a small
published mock list price so min-cost and quality/task-fit can diverge.
Unknown gateway names fail closed rather than inventing a price. Live
commercial APIs are out of scope this week.

## First-month constraints

The official Proposal brief requires at least three constraints. These six are
explicit design boundaries, not course-wide technology mandates.

| ID | Constraint |
|---|---|
| C-01 | Exact Python runtime `>=3.11,<3.12`, FastAPI, Pydantic v2, scikit-learn, and pytest. |
| C-02 | English JSON and Markdown only; no PDF/image/OCR or other-language ingestion. |
| C-03 | Supplied local evidence only; no web retrieval, browser automation, database, or frontend framework. |
| C-04 | `FixtureModelGateway` is the CI truth surface; any optional live gateway requires an exact approved-host allowlist, a full Azure/OpenAI-compatible Chat Completions HTTPS endpoint with no query except a valid Azure `api-version`, and never exposes endpoint or API key through configuration representation or artifacts. |
| C-05 | Synthetic data only until data provenance, privacy, licensing, and tutor approval are documented. |
| C-06 | No automated deployment/merge/external-action approval and no claim that model output is ground truth. |

## Evaluation targets and current development check

- Citation completeness: 100%.
- Five-label macro-F1: at least 0.65.
- Combined `UNSUPPORTED`/`CONTRADICTED` precision: at least 0.80.
- Combined `UNSUPPORTED`/`CONTRADICTED` recall: at least 0.75.
- Requirement-mapping macro-F1: at least 0.70.

The current synthetic **development** corpus passes these proposed checks:
citation completeness `1.0`, five-label macro-F1 `0.8577014177655716`, risky
precision `0.9302325581395349`, risky recall `1.0`, and requirement-mapping
macro-F1 `0.96`. The current-source report is
`acceptance/local-20260804-review-integrity-v2/corpus-acceptance.json`; its 20
Markdown artifacts expose complete audits for all 200 claims. The matching
multitemplate study retains `37` label errors and `12` mapping errors at
`acceptance/local-20260803-multitemplate-study-v3/baseline-study.json`.

These are not course thresholds or final achieved-product claims. The corpus is
synthetic, development-only, unfrozen, and not tutor-approved. NFR-08 also
remains open as a human onboarding claim: current-source `v12` proves a locked
fully offline technical replay, including semantic ground-truth validation,
after the explicit `v8` cache prefetch and first `v9` replay, not that a new team
member completed the workflow unaided within 20 minutes.
