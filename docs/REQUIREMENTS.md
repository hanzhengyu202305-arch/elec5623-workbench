# Functional requirements (scope candidate)

These 18 functional requirements are written for tutor review. Their `Draft`
status must be changed only after explicit scope approval. FR-01–15 are the
single-model Inspector engine. FR-16–18 are the Workbench compare shell around
that engine. They are one product, not two repositories.

| ID | Requirement | Acceptance evidence | Status |
|---|---|---|---|
| FR-01 | Validate a versioned English JSON bundle against strict schemas. | Invalid or extra fields return a validation error and create no run. | Draft |
| FR-02 | Reject duplicate requirement, evidence, and expected-claim identifiers. | Schema tests cover each duplicate category. | Draft |
| FR-03 | Segment English Markdown prose and lists into stable claim identifiers. | The same input produces the same ordered `cNNN` sequence. | Draft |
| FR-04 | Retrieve the top local evidence candidates for every claim. | Report contains ranked evidence ids, excerpts, and bounded scores. | Draft |
| FR-05 | Use TF-IDF retrieval and explicitly identify any fallback backend. | Run report records `sklearn-tfidf` or `lexical-fallback`. | Draft |
| FR-06 | Classify each claim into exactly one of five support labels. | Every assessment validates against the five-label enum. | Draft |
| FR-07 | Extract evidence citations from every segmented claim. | Citation ids appear in each claim assessment. | Draft |
| FR-08 | Reject positive support when a cited evidence id is unknown. | Unknown citation test returns `UNSUPPORTED`. | Draft |
| FR-09 | Validate quoted spans exactly against cited evidence. | Altered quote test returns a failed `QuoteCheck` and `UNSUPPORTED`. | Draft |
| FR-10 | Map claims to the most relevant stated requirements. | Assessment contains bounded requirement ids from the bundle only. | Draft |
| FR-11 | Calculate citation, quotation, requirement-coverage, and label-count metrics. | `report.json` and `report.md` expose the same metrics. | Draft |
| FR-12 | Score frozen expected labels and mappings when complete ground truth is supplied. | Ground truth is all-or-none: a non-empty list must cover every segmented claim id exactly before any provider call or artifact; aligned input populates macro-F1 and risky precision/recall. | Draft |
| FR-13 | Export input, machine-readable report, and Markdown audit without clobbering. | Repeated evaluation creates distinct run directories; a completed report is read only from a real, unaliased run directory and regular `report.json` whose embedded run id matches its directory. | Draft |
| FR-14 | Append a human decision to an existing run without changing prior artifacts. | Two reviews produce two JSONL records and preserve the report hash; symlink/hard-link review targets fail closed without changing the aliased file. | Draft |
| FR-15 | Expose validation/evaluation/review via CLI and evaluation/retrieval/review via four HTTP endpoints. | CLI and API contract tests use the same service. | Draft |
| FR-16 | On the same loaded bundle, sequentially run at least two named gateways. | Each gateway produces an independent Inspector run through `EvaluationService`; CLI `compare` accepts comma-separated unique known names. | Draft |
| FR-17 | Publish a comparison report with per-model quality, task-fit, elapsed time, and estimated cost, plus two named selections. | `compare.json` / `compare.md` report min-cost versus a documented quality/task-fit rule; no hidden composite index. | Draft |
| FR-18 | When complete `expected_claims` exist, report whether each policy’s selected model matches the annotation-preferred model. | Annotation-preferred uses the same ranking keys as quality/task-fit. Without labels: comparison only; do not claim prediction or success. | Draft |

## Official minimum and proposed team allocation

The `2026-08-02` official Proposal brief requires at least three functional
requirements per person. Lab 1 says to form a group of maximum five in
accordance with the Canvas group-size rule. Eighteen FRs still allow at least
three per person for a confirmed group of no more than five.

For five confirmed members, the neutral draft is FR-01-03, FR-04-06, FR-07-09,
FR-10-12, and FR-13-18. For fewer members, redistribute all 18 while preserving
at least three per person and explicit integration/review duties. No member,
group size, or ownership is currently claimed. Ownership never removes
whole-team responsibility for integration, testing, demo, or report accuracy.
