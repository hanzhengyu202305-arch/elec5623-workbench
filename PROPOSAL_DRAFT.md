# Model Effectiveness Evaluation Workbench

## ELEC5623 Track B proposal draft

Document status: **reviewable working draft; not approved and not submission-ready**  
Prepared and reconciled to official brief: `2026-08-02`  
Latest course-source reconciliation: `2026-08-30` - Lab 2, Week 2/3 and live
Ed oral/Proposal guidance; current live Canvas file version still unknown  
Proposed product: **Model Effectiveness Evaluation Workbench** (Inspector engine)  
Team, group number, tutor, and approval evidence: **not yet confirmed**  
Assessment: **10% (10 marks), group assignment**  
Due: **2026-09-08 23:59 through Canvas**  
Week 3 check: **interactive oral, not graded**  
Approval: **mandatory lab tutor approval before the deadline**

The official brief recommends 8–10 pages excluding the cover and references and
requires one readable, internally consistent PDF per group. This Markdown is a
longer working source with decision gates and evidence notes. The submission
candidate must be compressed, paginated, rendered, and visually checked; no
final page-count claim is made here. It does not claim team formation, tutor
approval, stakeholder validation, commercial performance, complete Lab 1
evidence, or results on a frozen test set.

Official source paths, SHA-256 hashes, requirement-by-requirement status, and
open gates are controlled by `ASSIGNMENT_REQUIREMENTS_MATRIX.md`.

### Claim-status convention

To prevent draft plans from being reported as results, this document uses four
statuses:

- **Implemented**: present in the current source tree.
- **Verified baseline**: reproduced locally with a retained artifact or test
  transcript.
- **Proposed**: a scope, threshold, experiment, or process requiring human or
  tutor confirmation.
- **External gate**: cannot be closed from this repository, such as team
  membership, tutor approval, official rubric interpretation, or submission.

## 1. Cover and group information

The final PDF cover must contain every official field below. Bracketed fields
must be replaced by actual group/tutor evidence; they must not appear in a
submitted PDF.

| Cover field | Submission candidate value | Current gate |
|---|---|---|
| Project title | Model Effectiveness Evaluation Workbench | Draft group confirmation |
| Selected direction | Track B - Product that helps AI work better | Draft group/tutor confirmation |
| Group number | `[REQUIRED: actual Canvas group number]` | `BLOCKED_CANVAS` |
| Full member names and SIDs | `[REQUIRED: actual confirmed members]` | `BLOCKED_USER_ACTION` |
| Lab tutor name | `[REQUIRED: authorised tutor]` | `BLOCKED_TUTOR` |
| Approval date | `[REQUIRED: actual approval date]` | `BLOCKED_TUTOR` |
| Brief approval statement | `[REQUIRED: exact approved wording or verified concise statement]` | `BLOCKED_TUTOR` |
| One-sentence product vision | On the same evidence-backed tasks, run at least two named models; report quality, task-fit, latency, and estimated cost separately; contrast min-cost versus quality/task-fit selection; human review remains success; not auto model-deploy. | Draft tutor confirmation |

Suggested final filename: `ELEC5623_GroupXX_Proposal.pdf`, with `XX` replaced by
the actual group number. The final cover must state Track B explicitly. A
passing test suite or local corpus report is not approval evidence.

## 2. Executive summary

A student can ask two models to turn the same lab notebook into a write-up.
The review question is which model hallucinates less and fits the stated task
better, not whether a cheaper model is automatically worse. Reviewers still
need claim-level evidence, quotations, requirement coverage, and an auditable
decision. Candidate users are students checking write-ups, evidence reviewers,
requirement owners, report authors, and team leads; these roles remain
stakeholder hypotheses.

The proposed **Model Effectiveness Evaluation Workbench** runs at least two
named models on the same English JSON bundle of requirements, evidence, and
AI-generated Markdown. The inner **Inspector** engine (FR-01–15) segments
claims, retrieves local evidence, applies a bounded support classifier,
enforces citations and exact quotations, maps requirements, calculates
metrics, and publishes an immutable run. The Workbench shell (FR-16–18)
compares those independent runs and reports quality, task fit, latency, and
estimated list-price cost separately. Two documented selection results are
published: **min-cost** versus a **quality/task-fit rule**. There is no hidden
composite index and no auto model-deploy. Every success remains
`READY_FOR_HUMAN_REVIEW`.

This is independent ELEC5623 Track B coursework. Estimated cost is a published
list price times a conservative token bound, not an invoice. Without complete
`expected_claims`, comparison is reported without a prediction or success claim.

The first-month Track B scope is Python 3.11 with FastAPI, Pydantic v2,
scikit-learn, and pytest; English JSON/Markdown and local synthetic evidence
only. Live commercial APIs are out of the compare CLI this week. The current
vertical slice has 18 draft FRs, ten draft NFRs, a passing test suite, and
branch coverage above the proposed 80% floor. Its multi-template
20-bundle/200-claim Inspector result is fixture-only development evidence with
retained errors, explicitly unfrozen and not tutor-approved - not a
generalisation claim.

Submission still requires the actual group and allocation, stakeholder/source
validation, an approved annotation/freeze protocol, mandatory lab tutor
approval of this Workbench direction (including the prior-work boundary),
final page compression, member review, and Canvas submission.

## 3. Introduction and background

### 3.1 Application and research context

This project sits in AI engineering evaluation: it examines how a generated
output uses a bounded set of evidence and addresses stated requirements. A
whole-document judgement can conceal mixed support. FActScore motivates
fine-grained assessment by observing that long-form generations may combine
supported and unsupported information and by decomposing text into atomic facts
checked against a source [4]. This proposal adopts only the general motivation
for claim-level inspection; it does not implement FActScore, use its data, or
reproduce its experiments.

Evaluation also has multiple dimensions. RAGAs distinguishes retrieval
relevance, faithful use of retrieved passages, and generation quality [5]. The
Inspector therefore keeps retrieval matches, support labels, citation/quote
checks, requirement mappings, and human decisions separate rather than hiding
them behind one score. Token spend and model list price are likewise not
treated as quality or task-fit proxies. It does not implement or claim
compatibility with the RAGAs metric suite.

### 3.2 Current practice and alternative solutions

The assumed current workflow is manual: read an output, identify its claims,
search supplied evidence, cross-check citations/quotes, compare requirements,
and record comments. This is a hypothesis to validate with a permitted
stakeholder or tutor; no measured time, cost, error, or market claim is made.

Existing alternative classes include unstructured manual review, document
search, generic LLM critique prompts, RAG evaluation frameworks, and
domain-specific factuality tools. Manual review preserves authority but may
lack a reproducible structure. Generic prompts are easy to run but do not
guarantee stable schemas, immutable evidence, or fail-closed behaviour. Research
frameworks such as FActScore and RAGAs inform the evaluation context, but this
course product has its own requirements, labels, data, tests, and human-review
contract.

Credible evidence for the final background section is tracked in
`REFERENCES_REGISTER.md`. Stakeholder evidence remains an open gate; no
interview participant or organisation is fabricated.

## 4. Problem statement and motivation

### 4.1 Decision to be improved

The target decision is: **given the same stated requirements, supplied
evidence, and AI-generated outputs from at least two named models, which
model hallucinates less / fits the task better for a human reviewer, and
should cost or quality/task-fit drive that choice?** The product improves the
information available for that decision. It does not deploy a model and does
not make the final decision.

A related failure mode is treating model price or token spend as
effectiveness. Absent quality, task-fit, and efficiency evidence, usage
policy is set by budget rather than by reviewable measures. This Workbench
contrasts **min-cost** with a documented **quality/task-fit** rule and does
not hide them in one score. Estimated cost is a list-price upper bound, not
an organisational saving. The product does not claim that the quality rule
predicts deployment success.

A traceable review still needs at least six linked facts:

1. the exact input and its hash;
2. the stable claim being assessed;
3. the cited and retrieved evidence;
4. the support label and rationale;
5. the mapped requirements and calculated metrics; and
6. the subsequent human review record.

The Inspector engine supplies that packet per model. The Workbench adds
per-model quality, task-fit, latency, and estimated cost, plus whether each
named policy matches an annotation-preferred model when complete labels exist.

GenAI is appropriate for the bounded classification component because varied
claim and evidence language may require contextual interpretation. It is not
used for schema, citation, quote, artifact, comparison ranking, or approval
rules, which remain deterministic. The present problem statement is a design
hypothesis, not a measured claim about a particular organisation. No
time-saving percentage, financial benefit, market size, or error rate is
asserted in this draft.

## 5. Stakeholders and requirements engineering

### 5.1 Candidate stakeholders and needs

The following stakeholder roles are proposed for validation. They are
role archetypes, not confirmed interview participants.

| Stakeholder role | Decision or need | Potential value | Risk if poorly designed |
|---|---|---|---|
| Student checking an AI lab write-up | Catch invented numbers, bad quotes, and fake citations against their notebook | Daily, bounded use of the same audit packet | Treating the label as a mark |
| Evidence reviewer | Locate support and challenge weak claims | One auditable queue instead of an unstructured prose review | Automation bias or missed context |
| Requirement owner | See which requirements have claim-level coverage | Explicit mapping and gaps | Lexical mapping may overstate semantic coverage |
| Report author | Correct unsupported or misquoted statements | Actionable claim-level feedback | May optimise for the tool rather than accuracy |
| Team lead or assessor | Reproduce how a result was produced | Immutable inputs, reports, hashes, and reviews | False confidence in synthetic metrics |
| System administrator | Operate the evaluation boundary safely | Fail-closed provider and credential boundary | Data leakage or provider outage |

### 5.2 Stakeholder-validation plan

Validate which manual step consumes most attention, whether missed weak claims
or false escalations are costlier, and which trace fields a reviewer needs.
Record the permitted method, consent, findings, and resulting requirement
changes. Private or identifiable notes remain outside the public repository. A
tutor-approved alternative is required if stakeholder contact is not permitted.

### 5.3 Stakeholder-level success definition

Value is defined as **review quality and reproducibility**, not automated
approval or raw model fluency. The proposed product is successful if it can:

- preserve a complete claim-to-evidence-to-requirement trace;
- surface risky `UNSUPPORTED` and `CONTRADICTED` cases with the proposed
  precision and recall thresholds;
- fail without publishing a completed run when input or provider behaviour is
  unsafe;
- allow human decisions to be appended without rewriting machine evidence; and
- be reproduced by a new team member in the nominated course environment.

Any benefit beyond these measurable product outcomes remains a hypothesis to be
validated rather than a proposal claim.

### 5.4 Proposed scope and priorities

One local versioned bundle produces one immutable run and optional append-only
reviews. Proposed priority is:

| Priority | Boundary |
|---|---|
| Must | strict schema/IDs; stable claims; local retrieval; five labels; citation/quote enforcement; mapping/metrics; no-clobber artifacts; append-only review; CLI/API parity; sequential named-model compare with min-cost vs quality/task-fit; fail-closed CI |
| Should | frozen-set error analysis; clean-checkout and timed review rehearsal |
| Could | lightweight report visualisation, recorded retrieval configuration, second synthetic domain |
| Won't (first month) | PDF/image/OCR, web search, database/frontend, live commercial compare APIs, autonomous approval/action, or cross-project assessed artifacts |

### 5.5 Functional requirements and acceptance criteria

All 18 requirements are **Draft** until the tutor confirms the problem, scope,
priorities, and allocation. Their full acceptance wording is controlled by
`docs/REQUIREMENTS.md`. The official minimum is at least three FRs per person.
Eighteen FRs still allow at least three per person after the actual group is
confirmed at no more than five members; no member or allocation is claimed here.

| ID | Required behaviour | Current implementation and verification handle |
|---|---|---|
| FR-01 | Validate a versioned English JSON bundle against strict schemas | `schemas.py`; invalid/extra-field tests |
| FR-02 | Reject duplicate requirement, evidence, and expected-claim IDs | `schemas.py`; duplicate-category tests |
| FR-03 | Segment English Markdown prose/lists into stable claim IDs | `segmentation.py`; deterministic and no-claim tests |
| FR-04 | Retrieve ranked local evidence for every claim | `retrieval.py`; bounded score/excerpt tests |
| FR-05 | Use TF-IDF and name any lexical fallback | `retrieval.py`; backend contract tests |
| FR-06 | Produce exactly one of five support labels | `gateway.py`, `engine.py`; schema/engine tests |
| FR-07 | Extract evidence citations per claim | `validation.py`; citation tests |
| FR-08 | Prevent positive support for an unknown citation | `engine.py`; unknown-citation test |
| FR-09 | Verify quoted spans exactly against cited evidence | `validation.py`; altered-quote test |
| FR-10 | Map claims to bounded requirement IDs | `retrieval.py`; mapping tests |
| FR-11 | Calculate citation, quotation, coverage, and label metrics | `metrics.py`; JSON/Markdown contract tests |
| FR-12 | Score labels and mappings only when supplied truth is complete | `engine.py` requires a non-empty `expected_claims` list to cover every segmented claim ID exactly before provider use or artifact creation; aligned truth is scored by `metrics.py` and the acceptance runner |
| FR-13 | Export and read no-clobber input/report artifacts | `artifacts.py`; distinct-run, failure, symlink-run/report, and report-identity tests |
| FR-14 | Append human review without mutating evaluation artifacts | `artifacts.py`; JSONL/hash, short-write, concurrency, and symlink/hard-link target tests through service/API/CLI |
| FR-15 | Expose the agreed CLI and HTTP contracts through one service | `cli.py`, `api.py`; CLI/API contract tests |
| FR-16 | Sequentially run ≥2 named gateways on the same bundle | `compare.py`; each model uses `EvaluationService` |
| FR-17 | Report quality, task-fit, time, estimated cost, and two named selections | `compare.json`/`compare.md`; no combined index |
| FR-18 | If complete labels exist, check policy vs annotation-preferred | Same ranking keys as quality/task-fit; unlabelled = comparison only |

The five support labels are `SUPPORTED`, `PARTIALLY_SUPPORTED`, `UNSUPPORTED`,
`CONTRADICTED`, and `INSUFFICIENT_EVIDENCE`. Their final operational definitions
and annotation examples must be frozen before final test labels are produced.

The most important Must acceptance criteria are testable:

| Requirement | Acceptance criterion | Current evidence / final gate |
|---|---|---|
| FR-01-03 input/claims | Invalid/duplicate input or non-auditable output creates no run; repeated prose keeps ordered IDs | Schema/segmentation/failure tests pass |
| FR-06-09 evidence decision | Exactly one valid label per claim; unknown citations or altered quotes cannot retain positive support | Engine/validation tests pass; frozen error analysis pending |
| FR-11-14 metrics/artifacts/review | Reports agree; partial/mismatched ground truth and aliased run/report/review targets fail closed; each run is no-clobber; two reviews preserve report hash | Ground-truth, metric, artifact-integrity, API, and CLI tests pass; final corpus not frozen |
| FR-15 interfaces | Validate, evaluate, and review CLI plus four HTTP endpoints use the same Inspector service | CLI/API tests pass |
| FR-16-18 compare | Two named models produce independent runs and a complete compare report, or fail closed with no `compare.json` | Compare/CLI tests pass |

### 5.6 Non-functional requirements, assumptions, and constraints

The ten NFR candidates are controlled by `docs/NFR_CONSTRAINTS.md`.

| ID | Quality | Proposed measurable criterion |
|---|---|---|
| NFR-01 | Traceability | 100% of serialized assessments contain the required trace fields |
| NFR-02 | Reproducibility | Normalised fixture reports are byte-equivalent across two runs |
| NFR-03 | Performance | 200 frozen claims complete in no more than 60.0 s on the nominated lab machine |
| NFR-04 | Token budget | Conservative canonical UTF-8 byte bound is checked before provider use |
| NFR-05 | Fail closed | Unsafe input/provider failure produces no completed `report.json` |
| NFR-06 | Privacy | Only the minimum configured payload crosses an approved provider boundary |
| NFR-07 | Auditability | Runs are no-clobber and reviews are append-only |
| NFR-08 | Onboarding | A new member reproduces the README flow within 20 minutes |
| NFR-09 | Maintainability | Core package branch coverage remains at or above 80% |
| NFR-10 | Comparison latency | Two-model fixture compare of the sample/daily bundle finishes in ≤60.0 s; a model fail-closed publishes no complete compare report |

The 60-second limit, token-budget strategy, onboarding time, and coverage target
are proposed engineering criteria, not marking thresholds specified by the
brief. They must be changed if the tutor requires different measures.

The explicit design constraints exceed the official minimum of three:

| ID | Constraint | Consequence |
|---|---|---|
| C-01 | Python `>=3.11,<3.12`; fixed first-month libraries | One bounded CI/reproduction toolchain |
| C-02 | English JSON/Markdown only | No PDF/image/OCR/other language |
| C-03 | Supplied local evidence only | No web retrieval or database |
| C-04 | Fixture gateway is CI truth surface | Live results cannot replace reproducibility |
| C-05 | Synthetic data until provenance/privacy/licence/tutor approval | Private/copied data is blocked |
| C-06 | Runs stop at human review | No truth, merge, deployment, or external-action approval |

Assumptions requiring validation are: the intended reviewer can provide a
bounded requirement/evidence bundle; English text is sufficient for the first
milestone; the nominated lab environment can run Python 3.11; and a synthetic
corpus is acceptable to the tutor. A failed assumption triggers scope review,
not silent expansion.

### 5.7 Public interface requirements

The CLI contract is:

```text
evidence-inspector validate bundle.json
evidence-inspector evaluate bundle.json --out runs/
evidence-inspector compare bundle.json --out runs/ --models fixture,fixture-b
evidence-inspector review RUN_ID review.json --runs runs/
```

The HTTP contract is:

```text
GET  /health
POST /v1/evaluations
GET  /v1/evaluations/{run_id}
POST /v1/evaluations/{run_id}/reviews
```

Both adapters call `EvaluationService`; they do not implement separate
classification or artifact rules. This is important for testability and avoids
different answers from the CLI and API paths.

## 6. Proposed product and innovation

The public product is the **Model Effectiveness Evaluation Workbench**. The
inner engine is the Inspector (FR-01–15); the compare shell is FR-16–18. One
pipeline, not two products. A user validates one input bundle, evaluates each
named model, inspects retained reports, compares min-cost versus
quality/task-fit, and appends human review. Major engine features remain
strict input contracts, stable claims, ranked evidence, five support labels,
exact citation and quote checks, requirement coverage, transparent metrics,
immutable runs, and append-only decisions.

The proposed AI contribution is deliberately narrow: a replaceable
`ModelGateway` interprets claim/evidence relationships. Deterministic components
own validation, safety preflight, segmentation, retrieval provenance,
quote/citation enforcement, metrics, artifact integrity, and review history.
This hybrid boundary makes the AI component testable and prevents a provider
response from authorising an action.

The expected engineering contribution is the linkage of five surfaces in one
reproducible contract: `claim -> evidence -> support decision -> requirement ->
human review`. The distinction from a generic LLM wrapper is observable:

| Generic critique prompt | Proposed Inspector |
|---|---|
| Free-form request/response | Versioned strict input and output schemas |
| Conversation-level judgement | Stable claim-level records |
| Evidence use may be implicit | Citations, quotes, ranked matches, and input hash retained |
| No required requirement trace | Bounded requirement IDs and coverage metrics |
| Provider may return malformed prose | Strict decision schema plus deterministic enforcement |
| History can be edited or lost | No-clobber runs and append-only reviews |
| “Looks correct” success | Explicit metrics, failure tests, and human-only decision |

The product is also separate from existing research tools. FActScore and RAGAs
provide referenced evaluation context [4], [5], but their code, data, metrics,
results, and diagrams are not reused. This ELEC5623 product is independent new
work; see `PRIOR_WORK_DISCLOSURE.md`. Tutor approval of scope remains pending.

## 7. Proposed methodology and system design

### 7.1 Development method and editable data flow

Development follows requirement-led vertical slices: define a measurable
requirement and acceptance criterion, implement it behind the shared service,
add positive and negative tests with the selected pytest framework [7], retain
the evidence handle, and update the
traceability/proposal impact. Scope changes are reviewed against the approved
Must/Should/Won't boundary before code changes. The text diagram below is the
editable source diagram for the working draft; the final PDF may restyle it but
must preserve the same nodes and boundaries.

```text
English JSON bundle
  -> Pydantic schema and uniqueness validation
  -> token-budget and prompt-injection preflight
  -> deterministic Markdown claim segmentation
  -> local evidence retrieval (TF-IDF or named lexical fallback)
  -> ModelGateway support classification
  -> citation and exact-quote enforcement
  -> requirement mapping and metrics
  -> no-clobber input/report artifacts
  -> append-only human review
```

Pydantic rejects unknown/invalid fields; preflight applies the conservative
canonical UTF-8 budget and tested injection guard; segmentation excludes
headings/fences and rejects an output with no auditable prose. Retrieval records
`sklearn-tfidf` or `lexical-fallback`; scikit-learn documents TF-IDF feature
conversion [6], while local tests establish project behaviour. The fixture
gateway is deterministic; the optional compatible HTTPS gateway validates a
strict decision schema. After classification, deterministic rules force
unknown citations, false quotations, or uncited positive decisions to
`UNSUPPORTED`, so a provider cannot bypass evidence integrity.

Lab 2 requires the context/container view to name more than the model. Evidence
reviewers use the CLI or HTTP interface; `EvaluationService` owns application
orchestration; the local run store retains immutable inputs, reports and
reviews; the optional compatible model endpoint is the only external system;
and the deployment boundary is one Python 3.11 process plus its artifact root.
The `ModelGateway` is one marked AI component. Validation, output enforcement,
safety preflight, logging/audit fields and human oversight remain outside it.

### 7.2 Primary written use case

| Field | Draft content |
|---|---|
| Actor and goal | Evidence reviewer obtains a traceable decision packet for one bounded bundle. |
| Trigger and preconditions | Reviewer invokes evaluation with schema-valid English requirements/evidence/output; an approved fixture or model configuration exists and the run root is writable. |
| Main success flow | Validate IDs/schema; segment claims; retrieve/classify evidence; enforce citations/quotes; map requirements and compute metrics; atomically publish the run; retrieve it and append a human decision. |
| Alternate/exception flows | Invalid input, injection, budget excess, provider failure, mismatched truth or aliased artifacts fail before a completed report; insufficient evidence remains explicit; disagreement is appended without rewriting machine evidence. |
| Postcondition | Canonical input/report remain immutable, reviews are append-only, and no external action is authorised. |
| Linked requirements | FR-01-15; especially FR-06-09, FR-11-15 and NFR-01, NFR-05, NFR-07. |

This is a draft use case for group/tutor review, not stakeholder-validation
evidence.

### 7.3 Data, models, integrations, and artifact integrity

Data is new synthetic English JSON/Markdown. Fixture mode supports CI; the only
optional model integration stays disabled unless endpoint, deployment,
settings, budget, privacy, and tutor conditions are recorded. FastAPI and CLI
adapt one service; the local filesystem is the first-month store.

Each successful evaluation writes a distinct run directory. The canonical
input and Markdown report are rendered before `report.json`; `report.json` is
the completed-run commit marker. If rendering or a write fails, only the known
incomplete files for that reserved run are removed, and `get_report` cannot
return a partial run as successful.

Human decisions append to `reviews.jsonl` without rewriting prior reviews or
the report; automated status remains `READY_FOR_HUMAN_REVIEW`. Before a read or
append, the store requires a real run directory, a stable unaliased regular
report whose embedded run id matches the directory, and an unaliased regular
review target. Symlink/hard-link aliases raise a typed error without changing
the outside target.

### 7.4 Trust boundaries and failure response

| Boundary or failure | Control | Observable outcome |
|---|---|---|
| Malformed or extra input | Strict Pydantic models | Validation error; no run |
| Duplicate IDs/reference drift | Schema and corpus pre-run invariants | Evaluation/acceptance stops |
| Prompt injection in untrusted fields | Preflight guard | Typed failure before provider use |
| Oversized input | Conservative byte upper bound | Token-budget failure; no run |
| Provider timeout/unavailable/invalid JSON | Typed gateway failures | No completed report |
| Unknown citation or false quotation | Deterministic post-gateway checks | Claim forced to `UNSUPPORTED` |
| Heading/code-only output | No-auditable-claims gate | No retrieval, provider call, or run |
| Partial artifact write | Final commit marker and explicit cleanup | Partial run is not readable as complete |
| Human disagreement | Append-only review | Machine evidence remains unchanged |

Known limitations include lexical rather than semantic retrieval in the local
baseline, English-only segmentation, exact-string quotation checking, synthetic
data, no authentication layer, local filesystem concurrency assumptions, and
no evidence that fixture results generalise to unseen natural documents. These
limitations are part of the evaluation, not details to conceal.

## 8. Business and product analysis

### 8.1 Value proposition and intended users

The value proposition is **a reproducible review packet and a named-model
comparison, not an automated verdict or auto model-deploy**. Candidate users
are students checking an AI lab write-up, evidence reviewers, requirement
owners, report authors, team leads, and system administrators. For them, the
expected benefit is a stable claim-level queue plus an explicit contrast of
min-cost versus quality/task-fit on the same bundle. Price is shown as an
estimated list-price bound, not as a quality substitute. These are user
hypotheses; a permitted interview or tutor review must establish whether the
workflow is relevant and which trace fields matter most.

### 8.2 Alternatives and differentiation

| Alternative | Advantage | Limitation for the proposed need | Workbench response |
|---|---|---|---|
| Manual review | Human context and authority | Structure and evidence retention may vary | Preserve human authority while standardising the packet |
| Document search | Fast evidence lookup | Does not classify claims or map requirements | Add claim-level audit and mapping |
| Generic LLM critique | Low setup effort | Free-form, non-reproducible, may invent evidence | Strict schemas, supplied evidence, deterministic enforcement |
| Research evaluation framework | Established methods | May target a different task/data/metric and not human workflow | Cite conceptual context; implement independent course requirements |
| Commercial governance platform | Broad operational features | Could be inaccessible, opaque, or too broad for one semester | Narrow transparent vertical slice and synthetic evaluation |
| Token or model-price comparison | Easy to collect | Says nothing about output quality or task fit; can mislead selection | Keep quality, task fit, time, and estimated cost separate; contrast two named policies |

No commercial product feature, price, market share, or customer claim is made
without a checked primary source. The current comparison is category-level and
must be refined if the tutor requires named competitors.

### 8.3 Feasibility, benefits, costs, and operations

Technical feasibility is supported by the current Python 3.11 vertical slice,
tests, CLI/API contracts, and deterministic 20/200 baseline. Semester
feasibility depends on retaining the narrow input/data/interface boundary and
cutting Should/Could work before weakening Must tests. Team feasibility remains
blocked until actual members, skills, lab attendance, and allocation are known.

The main expected costs are team engineering/review time, annotation time,
course-approved cloud/model usage if enabled, and CI/runtime resources. No
currency amount or Azure credit is claimed. A dated private Lab 1 record covers
some subscription/model facts, but credit, screenshots, exact versions/times
and completion sign-off remain missing. Fixture mode has no external model call,
but that does not make total development cost zero.

Operational considerations include Python 3.11 onboarding, secrets outside
source/artifacts, HTTPS for external credentials, no-clobber storage growth,
retention of hashes/configuration, provider outage, and human queue ownership.
A production deployment, support model, authentication design, and commercial
business case are outside the first-month scope.

### 8.4 Business-validation gate

Before final submission, the group must validate at least the target workflow,
highest-cost review step, acceptable false-positive/false-negative trade-off,
required trace fields, and willingness to perform human review. If course rules
do not allow stakeholder contact, record the tutor-approved alternative. No
invented interview, survey, cost saving, or market estimate may close this gate.

## 9. Evaluation plan

### 9.1 Research questions

The proposed evaluation asks:

- **RQ1 Trace completeness (precondition):** does every auditable claim retain a
  valid citation path and the fields required to reproduce its assessment?
- **RQ2 Support classification (quality):** can the chosen gateway distinguish
  all five support labels on a frozen synthetic corpus?
- **RQ3 Risk detection (quality):** does the system identify `UNSUPPORTED` and
  `CONTRADICTED` claims with sufficient precision and recall for a human queue?
- **RQ4 Requirement mapping (task fit):** can claims be mapped to the correct
  stated requirements without inventing IDs?
- **RQ5 Operational safety (efficiency / fail-closed):** do prompt injection,
  budget excess, provider failure, schema drift, and artifact failure stop
  closed?
- **RQ6 Reproducibility and usability (validation / operations):** can a clean
  environment reproduce the fixture result and can a new member complete the
  documented flow?
- **RQ7 Named-model comparison (Workbench):** on one bundle, do min-cost and
  quality/task-fit select the same model, and does either match
  annotation-preferred when labels exist?

These questions are not combined into a single effectiveness index. A combined
score would hide the mixed support the product exists to expose and would
repeat the failure mode of measuring only what is easy to measure. The only
join of quality, task fit, and efficiency is the human-review queue.

Workbench comparison (RQ7) asks, on the same bundle: which named model the
min-cost rule selects, which the quality/task-fit rule selects, and—when
complete labels exist—whether each matches annotation-preferred. Without
labels the compare report is comparison only and must not claim prediction or
success. Estimated cost is list price times the conservative token bound.

**What the measures are claimed to predict.** On a tutor-approved frozen
corpus, quality and task-fit scores are accepted only if they predict the
independent annotations and, if permitted, a later human-review decision.
They are not claimed to predict production model selection, token spend, or
financial outcome. The current fixture result is regression evidence only.

### 9.2 Corpus and annotation protocol

The planned corpus size is 20 bundles and 200 claims. Each bundle contains only
new synthetic requirements, evidence, generated text, expected labels, and
expected requirement mappings created for ELEC5623. The corpus and product
are independent of prior personal or other-unit work.

Before final evaluation, obtain tutor approval; define labels, ambiguity and
mapping rules without final predictions; use two permitted annotators or an
approved alternative; resolve disagreement independently of model output; hash
and freeze bundles/labels; and prohibit tuning on final labels. The current
generator/fixture is regression evidence, not independent annotation or
external validity.

### 9.3 Metrics and thresholds

For each class, precision is `TP / (TP + FP)`, recall is
`TP / (TP + FN)`, and F1 is their harmonic mean. Five-label macro-F1 is the
unweighted mean of the five per-label F1 values. Risky precision and recall
treat `UNSUPPORTED` and `CONTRADICTED` as the combined positive set.
Requirement-mapping macro-F1 is calculated per requirement and averaged.
Citation completeness is the proportion of claims with at least one citation
where all cited IDs exist in the bundle.

| Measure | Proposed acceptance target | Reason for inclusion |
|---|---:|---|
| Citation completeness | 1.00 | A positive evidence audit needs an explicit valid path |
| Five-label macro-F1 | at least 0.65 | Avoid hiding weak minority classes behind accuracy |
| Risky precision | at least 0.80 | Limit unnecessary escalations in the review queue |
| Risky recall | at least 0.75 | Reduce missed unsupported/contradicted claims |
| Requirement-mapping macro-F1 | at least 0.70 | Measure per-requirement mapping rather than raw coverage |
| Elapsed time | no more than 60.0 s for 200 claims | Bound the nominated first-month workflow |
| Two-model compare time | no more than 60.0 s for the sample/daily bundle | Same order as NFR-03; incomplete compares must not publish |

Elapsed time and the conservative token-budget preflight are the efficiency
measures. They bound waste and prevent an over-budget call from publishing a
false completed report. They are not AUD-per-token accounting and are not
used to rank models by price.

These thresholds are proposed engineering criteria. The team must justify or
replace them after tutor feedback and the official rubric review; they are not
presented as course-mandated thresholds.

### 9.4 Baselines, comparisons, test scenarios, and failure tests

| Baseline | State and control |
|---|---|
| B0 trivial constant/frequency reference | Proposed; fit on development data only; not scored |
| B1 TF-IDF + fixture + deterministic enforcement | Implemented Inspector regression baseline (cost 0) |
| B1b gold-label fixture-b | Implemented Workbench contrast with published mock list price > 0 |
| B2 one compatible model | Conditional on privacy/course approval; out of compare CLI this week |

Proposed same-input ablations remove TF-IDF, deterministic evidence enforcement,
or the normal mapping signal. Negative scenarios cover schema/ID/claim drift,
missing or unknown ground-truth claim IDs, citations/quotes, injection/budget,
provider failure, no-claim Markdown, partial/reused or aliased artifacts, and
append-only review.

### 9.5 Current verified baseline and interpretation

The current reproducibility surfaces are
`acceptance/local-20260804-review-integrity-v2/corpus-acceptance.json` and
`acceptance/local-20260803-multitemplate-study-v3/baseline-study.json`.

| Item | Verified baseline | Interpretation boundary |
|---|---:|---|
| Runtime | CPython 3.11.15 | Exact local environment, not yet nominated by the course |
| Automated tests | 152 passed | Includes compare-layer, ground-truth and review-target integrity through Engine, CLI, and API plus the local official-brief heading-order check |
| Branch coverage | 94.02% | Above proposed 80%; not a rubric score |
| Corpus size | 20 bundles / 200 claims | Five synthetic templates and four Markdown layouts |
| Citation completeness | 1.0 | Fixture corpus only |
| Five-label macro-F1 | 0.857701 | Fixture corpus only; 37 label errors retained |
| Risky precision / recall | 0.930233 / 1.0 | Fixture corpus only |
| Requirement mapping macro-F1 | 0.96 | Twelve mapping errors retained |
| Elapsed time | 0.866994 s | Recorded local Mac, fixture gateway, no network |

The retained report records corpus/prediction hashes and status
`DRAFT_UNFROZEN_NOT_TUTOR_APPROVED`;
`tutor_approval_claimed` is false, and no external API was used. A final report
must show the frozen-corpus result separately and must not overwrite this
baseline.

### 9.6 Qualitative/expert evaluation and threats to validity

If course rules and availability permit, at least one reviewer who did not
author the assessed bundle should complete a timed task: locate a weak claim,
inspect its evidence/requirement trace, append a decision, and explain whether
the packet was sufficient. Record task completion, decision correctness against
the frozen annotation, time, missing trace fields, and a short usefulness/trust
rating. Participant identity and comments remain private. If no reviewer is
available, obtain the tutor-approved qualitative alternative rather than
inventing user feedback.

The validation target is annotator and reviewer agreement, not external
business metrics. Retained fixture errors (37 label, 12 mapping) are kept so
passing aggregates cannot conceal misses. Ablations that remove retrieval,
deterministic enforcement, or the mapping signal test whether each dimension
is doing work rather than riding a single hidden score.

- **Construct:** lexical overlap/exact quotes are proxies; inspect semantic errors.
- **Internal:** generator/fixture alignment requires independent frozen labels.
- **External:** 20 English synthetic bundles do not represent other domains or providers.
- **Conclusion:** passing aggregates still require per-class/confusion/error reporting.
- **Reproducibility:** record runtime, hardware, load, gateway, and command.

## 10. Risks, ethics and responsible AI

### 10.1 Human authority and automation bias

NIST AI RMF frames AI risk work through `GOVERN`, `MAP`, `MEASURE`, and
`MANAGE` and treats accountability/transparency as cross-cutting
trustworthiness concerns [1]. Its GenAI Profile identifies risks including
confabulation, privacy, human-AI configuration/automation bias, information
integrity, and information security [2]. These sources guide the risk questions;
they do not establish compliance or safety for this prototype.

The main ethical risk is treating a support label as truth. The interface and
report therefore keep `READY_FOR_HUMAN_REVIEW` as the only successful automated
state, expose evidence and rationale, and append human decisions separately.
The demo must include at least one case where a human challenges the automated
assessment.

False support may cause a weak claim to pass unnoticed; false escalation may
waste review effort or unfairly undermine a valid claim. The evaluation reports
both risky precision and recall rather than optimising one invisibly.

### 10.2 Privacy, security, safety, bias, legal, and adoption risk

Synthetic data remains default until provenance, consent, licence, retention,
and approval are recorded. Secrets stay outside source/evidence; external model
traffic requires HTTPS. No authentication, tenancy, or production-readiness is
claimed. OWASP describes direct/indirect prompt injection and layered controls
including output validation, least privilege, untrusted-content segregation,
adversarial tests, and human approval [3]. The current pattern guard is not
foolproof; the stronger boundary prevents the gateway writing artifacts or
acting externally.

Bias can enter labels, domains, annotation, and per-claim performance; report
per-label errors. Data rights, licence, privacy, provider terms, and assessment
rules remain legal gates. Queue ownership, over-reliance, and onboarding are
adoption risks. With no physical output in scope, safety requires uncertainty
visibility and no autonomous action.

### 10.3 Academic integrity and prior work

This ELEC5623 product is independent new work and does not copy prior personal
or other-unit code, data, or figures. `PRIOR_WORK_DISCLOSURE.md` records that
boundary. Show it to the tutor and retain the exact decision. Do not claim
approval until a written reply exists.

OpenAI Codex was materially used on `2026-08-02` to scaffold and review the
independent prototype, tests, evaluation tooling, and this proposal working
draft. Its outputs were revised and checked with local tests, source
provenance, and independent review; they do not establish stakeholder facts,
tutor approval, team authorship, or final-course compliance. The submitted
group remains responsible for every claim, citation, requirement, engineering
decision, and permitted-use declaration. `AI_JOURNAL.md` retains the detailed
interaction record, but that external record does not replace this direct
acknowledgement. Before submission, the group must reconcile this paragraph
with the current course/University AI guidance and accurately record any later
AI use and human review.

### 10.4 Risk register

| Risk | Likelihood / impact | Preventive control | Trigger and response | Owner |
|---|---|---|---|---|
| Tutor/Canvas or prior-work decision conflicts with scope | Unknown / high | Hashed matrix, disclosure, early approval | Stop freeze; revise and reconfirm | Unassigned |
| Team/role availability differs | Unknown / high | Formation pack and allocation record | Replan; never invent members | Student action |
| Synthetic corpus overfits fixture rules | High / high | Independent protocol and frozen labels | Report limitation; redesign before final evaluation | Unassigned |
| Provider leaks data or becomes unavailable | Medium / high if enabled | Synthetic data, HTTPS, minimal payload, fixture CI | Fail closed and revert to approved fixture path | Unassigned |
| Automation bias | Medium / high | Human-only final decision and challenge case | Record disagreement and revise presentation | Whole team |
| Requirement or artifact drift | Medium / medium | Traceability matrix, hashes, no-clobber runs | Block report/demo until versions match | Unassigned |
| Schedule compression | Medium / medium | Weekly gate review and vertical slices | Cut Should/Could before weakening Must tests | Unassigned |

Likelihood and ownership must be confirmed by the actual team. The table does
not assign responsibility to people who have not agreed to join.

## 11. Semester plan and team responsibilities

### 11.1 Milestones and dependencies

| Period | Intended outcome | Exit evidence | External dependency |
|---|---|---|---|
| 03–09 Aug | Team formation, pitch, schema, 18 FRs, disclosure | Team record; tutor questions; current vertical slice | Team members |
| 10–16 Aug | Lab 1 environment and single-bundle vertical slice | Clean setup and CLI/API transcript | Course environment |
| 17–23 Aug | Week 3 oral progress check and scope freeze | Oral pack, feedback log, decision record | Tutor feedback |
| 24–30 Aug | Corpus protocol, baselines, failure tests, evaluation | Versioned draft artifacts and risk analysis | Protocol approval |
| 31 Aug–07 Sep | Tutor approval and 8–10 page proposal reconciliation | Written approval, final matrix, AI audit | Tutor and Canvas rubric |
| 08 Sep 23:59 | Student performs final submission | Canvas confirmation retained privately | Student action |
| From 09 Sep | Demonstrable product, frozen test set, final report work | Tagged versions and weekly rubric delta | Future assessments |

As of `2026-08-30`, this table remains an intended plan rather than a completion
record. `ASSIGNMENT_REQUIREMENTS_MATRIX.md` controls actual status: Lab 1 is
partial; Lab 2 and Week 3 completion are unknown; group formation, tutor
feedback/approval, and authenticated current-Canvas verification remain
unconfirmed. Live Ed requests early iterative draft feedback, but no send or
feedback round is claimed.

The date and submission requirements were checked on `2026-08-02` and must be
reconfirmed against live Canvas before final production.
Only the student/group can perform the final submission.

### 11.2 Conditional team allocation

For five confirmed members, the neutral template gives each the official
minimum of three FRs; Slot E also takes the compare shell. For fewer members,
redistribute all 18:

| Role slot | Candidate primary FRs | Cross-team duty |
|---|---|---|
| Slot A | FR-01–03 | Schema/segmentation integration review |
| Slot B | FR-04–06 | Retrieval/gateway evaluation review |
| Slot C | FR-07–09 | Evidence-integrity and negative tests |
| Slot D | FR-10–12 | Mapping, metrics, corpus protocol |
| Slot E | FR-13–18 | Artifacts, CLI/API, Workbench compare, demo |

These are placeholders. Record actual names/SIDs, group number, availability,
deliverables, and reviewers only after agreement. Every member remains
responsible for the complete submission.

### 11.3 Working method and change control

- Log each requirement change with source, owner, and test/evidence/report impact.
- A feature needs matching acceptance evidence and independent review where possible.
- Demo, report, AI journal, and commit must describe one version.
- Must defects outrank Should/Could work; private course data stays private.

### 11.4 Approval request and conclusion

The vertical slice supports feasibility, contracts, failure modes, and
reproduction, but stakeholders, frozen-corpus validity, team allocation, and
approval remain open. The group requests tutor decisions on Track B fit, the
Workbench direction (extending the Inspector single-model audit to named-model
effectiveness comparison), scope, prior-work independence, separate quality /
task-fit / time / estimated-cost reporting with no combined price proxy,
synthetic
evaluation/thresholds, and any additional team/AI/later-deliverable rules.
Only the recorded decision closes a gate.

## 12. References

### 12.1 Verified external references

The numbered citations below were opened and metadata-checked on `2026-08-02`.
`REFERENCES_REGISTER.md` records source hashes, claim mappings, and limitations.

[1] National Institute of Standards and Technology, *Artificial Intelligence
Risk Management Framework (AI RMF 1.0)*, NIST AI 100-1, Jan. 2023,
doi: `10.6028/NIST.AI.100-1`.

[2] National Institute of Standards and Technology, *Artificial Intelligence
Risk Management Framework: Generative Artificial Intelligence Profile*, NIST
AI 600-1, July 2024, doi: `10.6028/NIST.AI.600-1`.

[3] OWASP Gen AI Security Project, “LLM01:2025 Prompt Injection,” accessed Aug.
2, 2026. `https://genai.owasp.org/llmrisk/llm01-prompt-injection/`.

[4] S. Min, K. Krishna, X. Lyu, M. Lewis, W.-t. Yih, P. Koh, M. Iyyer,
L. Zettlemoyer, and H. Hajishirzi, “FActScore: Fine-grained Atomic Evaluation of
Factual Precision in Long Form Text Generation,” in *Proceedings of EMNLP
2023*, pp. 12076-12100, 2023, doi: `10.18653/v1/2023.emnlp-main.741`.

[5] S. Es, J. James, L. Espinosa Anke, and S. Schockaert, “RAGAs: Automated
Evaluation of Retrieval Augmented Generation,” in *Proceedings of the 18th EACL:
System Demonstrations*, pp. 150-158, 2024,
doi: `10.18653/v1/2024.eacl-demo.16`.

[6] scikit-learn developers, “`TfidfVectorizer`,” *scikit-learn API Reference*,
accessed Aug. 2, 2026.
`https://scikit-learn.org/stable/modules/generated/sklearn.feature_extraction.text.TfidfVectorizer.html`.

[7] pytest developers, “pytest documentation,” accessed Aug. 2, 2026.
`https://docs.pytest.org/en/stable/`.

The final group must apply one citation style consistently and recheck every
reference. These sources motivate design/evaluation choices; they do not prove
the project's implementation, performance, safety, or compliance.

### 12.2 Current repository truth surfaces

Implementation and local-result claims are grounded in versioned project files:

- `README.md` — product boundary, commands, and reproduction instructions;
- `docs/REQUIREMENTS.md` — 15 draft FRs;
- `docs/NFR_CONSTRAINTS.md` — ten draft NFRs, constraints, and targets;
- `docs/ARCHITECTURE.md` — data flow and failure boundary;
- `docs/TRACEABILITY.md` — requirement-to-code-to-test-to-evidence mapping;
- `PRIOR_WORK_DISCLOSURE.md` — prior-work and independence boundary;
- `AI_JOURNAL.md` — material AI assistance and human verification duties;
- `STATUS.md` — bounded current results and open gates; and
- `acceptance/local-20260804-review-integrity-v2/corpus-acceptance.json` — ignored local
  baseline evidence, not a proposed public artifact.

The official course sources and their SHA-256 provenance are recorded in
`ASSIGNMENT_REQUIREMENTS_MATRIX.md`. Links do not replace required Proposal
content.

## Proposal completion gates

### Production records outside the Proposal by default

The official brief does not require appendices or say that appendices are
excluded from the 8-10-page recommendation. Therefore the submission candidate
must not assume an appendix allowance. Keep the full reconciliation matrix,
approval evidence, team allocation record, traceability details, corpus and
prediction hashes, extended failure analysis, privacy/provenance record,
prior-work decision, and AI journal as private production records unless the
live Canvas instructions or tutor explicitly require selected material in the
single PDF. Any material included beyond cover and references must be counted
conservatively in rendered-page QA.

### Submission page and word budget

This working source intentionally retains decision gates, evidence boundaries,
and review notes. The submission candidate should target the following body
budget before layout; tables/diagrams also consume pages.

Current working body Sections 2-11 contain approximately **5,192 words** before
final member/tutor edits. This is above the target range below, so compression
and rendered-page QA remain explicitly open.

| Body section | Target words for PDF candidate |
|---|---:|
| 2 Executive summary | 180-220 |
| 3 Introduction/background | 250-320 |
| 4 Problem/motivation | 180-250 |
| 5 Stakeholders/requirements | 650-750 |
| 6 Product/innovation | 250-320 |
| 7 Method/system design | 400-500 |
| 8 Business/product analysis | 250-320 |
| 9 Evaluation plan | 550-700 |
| 10 Risks/ethics/responsible AI | 350-450 |
| 11 Semester/team | 200-280 |
| **Target body total** | **3260-4110** |

Cover and references are excluded from the official 8-10 page recommendation;
no other exclusion is stated. Keep extended provenance, traceability, raw
evidence, approval records, and checklists as private production evidence unless
the current instructions explicitly require them in the PDF. Final compliance
requires generating the single PDF, inspecting every rendered page for
overflow/legibility, and confirming 8-10 body pages; Markdown word count alone
cannot close this gate.

### Gate checklist

- [x] Official Proposal and Lab 1 PDFs saved, hashed, visually checked, and
  mapped in `ASSIGNMENT_REQUIREMENTS_MATRIX.md` on `2026-08-02`.
- [ ] Live Canvas is rechecked while authenticated for any later brief, group,
  submission, or AI policy revision before final production; the 2026-08-24
  attempt stopped at University SSO.
- [ ] The direct Codex disclosure is reconciled with the final permitted-use
  guidance and every later material AI interaction/human decision is recorded.
- [ ] Team members, group number, individual responsibilities, and review
  partners confirmed.
- [ ] Tutor has approved the Track B problem and scope in writing.
- [ ] `PRIOR_WORK_DISCLOSURE.md` shown to tutor; exact decision retained.
- [ ] Stakeholder and business hypotheses validated or explicitly bounded.
- [ ] FR/NFR and thresholds reconciled against official requirements.
- [ ] Annotation protocol approved before the final corpus/labels are frozen.
- [ ] Every quantitative result has a no-clobber retained artifact and runtime.
- [ ] Final references have been opened and verified; no placeholder citations.
- [ ] Proposal, code, tests, demo, AI journal, and final commit describe one
  consistent version.
- [ ] Student/group completes the final review and submission action.
