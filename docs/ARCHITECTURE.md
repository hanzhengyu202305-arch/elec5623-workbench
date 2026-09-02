# Architecture and data flow

```text
English JSON bundle
  -> Pydantic schema + uniqueness validation
  -> token-budget and prompt-injection preflight
  -> deterministic Markdown claim segmentation
  -> all-or-none expected-claim alignment (when ground truth is supplied)
  -> local evidence retrieval (TF-IDF / reported lexical fallback)
  -> ModelGateway support classification
  -> citation + exact-quote checks
  -> requirement mapping + transparent metrics
  -> no-clobber JSON/Markdown run artifacts
  -> append-only human review queue

Workbench compare (FR-16-18), same bundle:
  -> sequential EvaluationService calls, one named gateway each
  -> per-model quality, task fit, elapsed time, estimated list-price cost
  -> min-cost vs quality/task-fit selection (no combined index)
  -> optional annotation-preferred match when expected_claims are complete
  -> compare.json + compare.md only if every model succeeds
```

The CLI `validate`/`evaluate`/`review` and FastAPI adapter both call
`EvaluationService`; CLI `compare` calls `ComparisonService`, which only
orchestrates those same evaluations. Neither adapter implements evaluation
rules independently. `ModelGateway` cannot write files. The default
fixture gateway makes CI reproducible. `OpenAICompatibleModelGateway` is an
optional outbound boundary selected only by
`EVIDENCE_INSPECTOR_GATEWAY=openai-compatible`. CLI `evaluate` and API
`create_app` use the same environment factory; absent that exact opt-in, they
construct `FixtureModelGateway` even when other provider variables exist.

The compatible configuration rejects non-HTTPS, root-only or malformed URLs,
embedded URL credentials, fragments, every query except one non-empty Azure
`api-version`, unsupported key headers, empty/control-bearing model or key values,
and non-finite or out-of-range timeouts. The canonical endpoint hostname must
exactly match the explicit approved-host allowlist; private Azure hostnames or IPs
remain possible only through that same explicit decision. Only Bearer
`Authorization` and Azure `api-key` authentication are supported. Endpoint and
key are excluded from configuration representation, and domain errors echo
neither. The adapter sends only the current claim and bounded retrieved evidence,
requests strict JSON, refuses redirects so credentials cannot follow a new
destination, caps the response at 64 KiB, validates it as `GatewayDecision`, and
maps timeout, HTTP/transport, malformed, deeply nested and oversized responses to
typed fail-closed errors. Provider tests use a local fake at the no-redirect
opener boundary; no live credential or endpoint is needed.

Failure is atomic at the product boundary: a run directory is reserved only
after all claims have valid decisions and metrics. Successful automated runs
remain `READY_FOR_HUMAN_REVIEW`; no component can approve a merge, deployment,
or external action.

`report.json` is the full machine contract. `report.md` exposes every metric
category, grouped under quality, task fit, and efficiency rather than one
score, and expands each claim into the original text, decision rationale,
ranked evidence score/excerpt, requirement mapping, and exact-quote outcome so a
reviewer does not need to infer the decision from a summary label. Claim text,
evidence excerpts, quotations, and provider rationale are untrusted; each is
rendered in a literal fence longer than any backtick run in that value, so the
value cannot create a forged heading or table in the audit. The final section
identifies the run's append-only human-review target without claiming approval.

Each artifact is completely staged and `fsync`ed in its destination directory,
then atomically hard-linked without overwrite to the final name. `report.json` is
the completed-run commit marker and is published last, after the fully rendered
input JSON and Markdown report. A render/ordinary write exception removes only
`input.bundle.json`, `report.md`, and `report.json` from that failed run, then
removes the empty directory. An uncatchable termination can leave fully published
pre-marker files, but cannot expose a partial `report.json`; `get_report` therefore
cannot return `READY_FOR_HUMAN_REVIEW` from an incomplete publish.

Read and review paths add an independent identity gate. A run name must resolve
to a real directory under the configured root, `report.json` must be one stable
unaliased regular file, and its embedded `run_id` must match the requested
directory. `reviews.jsonl` must likewise be one regular file with a single link;
the append open refuses final symlinks and rechecks file identity before the
exclusive lock and write. Symlink run/report targets, hard-linked or symlinked
review targets, and report-id drift raise `ArtifactIntegrityError`. The service,
CLI, and API therefore refuse the review without changing the outside target.

The normalized fixture checker starts two separate Python interpreters with an
explicit `FixtureModelGateway`, then re-reads both persisted reports and input
bundles. It schema-validates them, checks requested/persisted/report input hashes,
and only then compares canonical reports after excluding `run_id` and
`created_at`. In-memory service return values are not the reproducibility truth
surface.

Markdown headings and fenced code are non-claim structure. If segmentation finds
no prose or list-item claims, `EvaluationService` raises `NoAuditableClaims`
before retrieval, provider execution, or artifact publication.

`EvaluationService.validate` is the provider-free semantic boundary shared by
CLI `validate` and `evaluate`. After preflight and segmentation, an empty
`expected_claims` list means “not scored”; a non-empty list must contain exactly
the segmented claim ids. Missing annotations or unknown ids raise
`GroundTruthAlignmentError` before retrieval, provider execution, metric
calculation, or artifact publication. This prevents annotation drift from being
reported as model performance.
