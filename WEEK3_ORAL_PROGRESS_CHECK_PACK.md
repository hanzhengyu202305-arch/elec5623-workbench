# Week 3 interactive oral progress check pack

Status: **prepared; actual Week 3 attendance, contribution and feedback remain
`COMPLETION_UNKNOWN / USER_VERIFICATION_REQUIRED`**  

> **No-AI assessment boundary:** Week 1 states that AI use is prohibited during
> the early-feedback oral and every interactive oral. This pack is for advance
> human study and rehearsal only. Close Codex and all other AI tools before the
> check; do not consult generated notes or request live answers during it. See
> `WEEK1_COURSE_CONTROL.md` and the Week 1 lecture, pp. 39 and 41.
Assessment status: **early-feedback, interactive, group-based, and 0% / not
graded**  
Latest source checks: `2026-08-30` - Lab 2 PDF SHA-256
`200e7f06e3504f9d48ac66ee18fb9af3ca146051942f5d5cab85e6150861b641`
and live Ed course `38814`, thread `3476276`

The official Proposal brief and later Lab 2/Ed guidance say every group
participates during the Week 3 lab and every member must attend and be ready to
contribute. It begins five minutes after the lab starts; tutors call groups one
at a time and each check takes approximately 5-10 minutes. It covers Proposal
progress/idea, problem, target users, GenAI role, feasibility, current progress,
next steps, and simple Week 1-2 lecture questions. It does not replace the
written proposal, and the teaching team may require the idea to be refined or
narrowed before final approval.

## 1. One-sentence product answer

> We selected **Track B** and propose a **Model Effectiveness Evaluation
> Workbench**: on the same evidence-backed tasks, run at least two named
> models; report quality, task-fit, latency, and estimated cost separately;
> contrast min-cost versus quality/task-fit selection; human review remains
> success; not auto model-deploy. The Inspector engine is FR-01–15; the
> compare shell is FR-16–18.

Every actual team member should be able to explain this sentence in their own
words rather than memorising one speaker's script.

## 2. Required oral topics

The five official topics are mapped to concise answers below.

### 2.1 Track and product

- **Track:** B - Product that helps AI work better.
- **Product:** Model Effectiveness Evaluation Workbench (Inspector engine plus
  compare shell).
- **Human boundary:** every completed machine run is
  `READY_FOR_HUMAN_REVIEW`; no automated truth, approval, or model-deploy.

### 2.2 Problem, users, and why it matters

> A student asks two models to turn a lab notebook into a write-up. The
> Workbench checks both write-ups against the notebook only and asks which
> model hallucinates less / fits the task better. Spend and model price do not
> answer those questions. Quality, task fit, latency, and estimated cost stay
> separate. Candidate users start with students and lab partners; evidence
> reviewers, requirement owners, authors, and team leads remain hypotheses, not
> claimed customers.

Why it matters: a fluent write-up can hide a wrong current, a fake datasheet
citation, or a sentence that has nothing to do with the experiment. The product
improves the evidence available to the person who still has to sign the report.

### 2.3 AI contribution and distinction

> The AI contribution is a bounded `ModelGateway` that classifies claim support
> from supplied evidence. It sits inside a larger engineering workflow with
> strict schemas, deterministic segmentation and retrieval, exact citation and
> quotation enforcement, requirement mapping, metrics, immutable artifacts,
> and append-only human review. It is not a generic chatbot or a thin LLM API
> wrapper because it has versioned inputs, specialised outputs, fail-closed
> rules, measurable evaluation, and no conversational approval path.

### 2.4 At least three core requirements

Use requirements whose acceptance evidence can be shown. Any member should be
ready to explain at least these six:

1. **FR-01 strict validation:** invalid or extra fields return an error and
   create no run.
2. **FR-03 stable segmentation:** the same English Markdown produces the same
   ordered claim IDs; heading/code-only input fails with no run.
3. **FR-09 exact quotations:** a changed quoted span cannot retain positive
   support and is forced to `UNSUPPORTED`.
4. **FR-13 immutable export:** repeated evaluations create distinct runs, and a
   partial write cannot expose a completed `report.json`.
5. **FR-14 append-only review:** two reviews append two JSONL records while the
   evaluation report hash stays unchanged.
6. **FR-16/17 named-model compare:** the same bundle is run under ≥2 gateways;
   quality, task-fit, time, and estimated cost are reported separately; min-cost
   and quality/task-fit are two named policies, not a hidden index.

### 2.5 One major risk

> The largest current validity risk is that the deterministic synthetic corpus
> and fixture rules may be too closely aligned. Perfect fixture scores therefore
> do not demonstrate generalisation. We propose tutor-approved label rules,
> independent annotation or an approved alternative, a hash-frozen test set,
> and no tuning on final labels before reporting final performance.

Alternative major risks the group should understand are automation bias,
provider privacy/outage, rubric-scope mismatch, and prior-work contamination.

### 2.6 Evaluation answer

> We propose 20 new synthetic bundles containing 200 claims for the Inspector
> engine. Quality is citation completeness, five-label macro-F1, and combined
> `UNSUPPORTED`/`CONTRADICTED` precision and recall. Task fit is
> requirement-mapping macro-F1. Efficiency is 200-claim elapsed time and a
> fail-closed token budget. Workbench compare adds estimated list-price cost
> and two named selection rules on the same bundle. We do not combine those
> dimensions into one score. Measures are accepted only against independent
> annotations and later human review, not spend, and not as a claim that the
> quality rule predicts deployment success. Constantinople / ESIPS Pound for
> Pound is not claimed complete. Negative tests cover injection, provider
> failure, budget excess, malformed input, invalid quotations, partial writes,
> incomplete compare, and append-only review.

### 2.7 Feasibility, current progress, and next steps

Bounded feasibility evidence is the Python 3.11 vertical slice, deterministic
fixture path, failure tests, and reproducibility records. It does not establish
team feasibility, tutor approval, stakeholder demand, a frozen result, or live
provider suitability. Current progress is therefore described as a technical
spike plus working Proposal, not an approved semester project.

The next authorised steps are to capture actual group facts, obtain and record
tutor feedback/approval, reconcile the new Lab 2 use-case and architecture
controls, close the Lab 1/2 evidence gaps, and request iterative Proposal-draft
feedback early enough to revise before `2026-09-08 23:59`.

## 3. Five-to-ten-minute group run sheet

The tutor may make the check shorter or interrupt with questions. This is a
coverage plan, not a requirement to deliver a monologue.

| Time | Speaker | Content | Evidence surface |
|---:|---|---|---|
| 0:00-0:30 | `UNASSIGNED` | Track B and one-sentence product | Cover / Section 2 |
| 0:30-1:20 | `UNASSIGNED` | Problem, candidate users, why GenAI is appropriate | Proposal Sections 3-4 |
| 1:20-2:10 | `UNASSIGNED` | Product flow and difference from chatbot | Architecture diagram |
| 2:10-3:10 | `UNASSIGNED` | Three or more FRs and acceptance criteria | Requirements/traceability |
| 3:10-4:00 | `UNASSIGNED` | Evaluation metrics and failure tests | Evaluation table |
| 4:00-4:40 | `UNASSIGNED` | Major risk and mitigation | Risk register |
| 4:40-5:20 | `UNASSIGNED` | Feasibility, current progress, and next steps | Status / Proposal Section 11 |
| 5:20-6:00 | `UNASSIGNED` | Exact tutor decisions and prepared course/assessment questions | Approval pack |

The remaining official window up to approximately ten minutes is tutor-led
questioning, including simple Week 1-2 concepts. This table is a rehearsal aid,
not evidence that the real check used this order or duration.

Assign only confirmed members. Every member must still understand all topics.

## 4. Optional 90-second evidence demo

Use only if the tutor invites a demo. Prefer the daily lab-write-up scene:

```bash
. .venv/bin/activate
bash scripts/run_workbench_demo.sh
```

Or the original contract sample in the exact Python 3.11 environment and a
fresh output path:

```bash
. .venv/bin/activate
evidence-inspector validate examples/sample_bundle.json
evidence-inspector evaluate examples/sample_bundle.json --out runs-week3/
evidence-inspector compare examples/sample_bundle.json --out runs-week3/ --models fixture,fixture-b
```

Then show:

1. input bundle structure;
2. `compare.md` with separate quality, task-fit, time, and estimated-cost
   columns plus the two named selections;
3. a claim with evidence matches, citation/quote checks, and requirement IDs;
4. `READY_FOR_HUMAN_REVIEW` status;
5. an appended human review; and
6. one fail-closed test name.

Do not reuse `runs-week3/` if it already exists for the rehearsal; use a new
explicit path. Do not show credentials or private data.

## 5. Current evidence that may be stated

As of `2026-08-30`, the bounded local baseline is:

- CPython 3.11.15;
- 138 automated tests passed, including ground-truth and review-target
  alignment plus a local heading-order check against the captured official
  Proposal brief;
- 93.92% branch coverage;
- 20 draft synthetic bundles and 200 claims;
- citation completeness 1.0, macro-F1 0.857701, risky precision/recall
  0.930233/1.0, and mapping macro-F1 0.96;
- 37 label errors and 12 mapping errors retained for review;
- elapsed time 0.866994 seconds for the draft fixture run; and
- no external API used.

Required qualification:

> These are deterministic vertical-slice and contract results. The corpus is
> `DRAFT_UNFROZEN_NOT_TUTOR_APPROVED`; no tutor approval, independent
> annotation, frozen-set generalisation, or final assessment result is claimed.

## 6. Likely questions and bounded answers

### Why is this more than a generic chatbot?

It has strict versioned schemas, stable claim-level records, local retrieval,
five specialised labels, deterministic evidence enforcement, measurable
requirements, immutable artifacts, failure gates, and append-only human review.
The model is one replaceable component rather than the product interface.

### Who is the customer?

Candidate users are evidence reviewers, requirement owners, report authors, and
team leads. They have not yet been validated as customers. The proposal defines
a stakeholder-validation plan instead of fabricating demand or commercial data.

### Why GenAI rather than only rules?

Support classification can require interpreting varied claim and evidence
language; the `ModelGateway` tests that AI contribution. Deterministic rules
remain responsible for schema, citations, quotations, artifacts, and safety.
The evaluation will compare against non-model/trivial baselines.

### Why not use AegisOps directly?

AegisOps is disclosed high-level inspiration only. This project has an
independent problem, source tree, schemas, synthetic corpus, tests, metrics,
report, and demo. No cross-project code, data, figures, results, or prose are
used. Written tutor approval of that boundary is still pending.

### Do you treat cheaper models as worse?

No. Cost per token is easy to measure and does not say whether the output was
supported or whether it addressed the stated requirements. We report quality,
task fit, and efficiency separately and stop at human review. We do not rank
models by price and we do not claim a financial saving.

### Why are the fixture metrics perfect?

The current corpus and gateway are deterministic contract fixtures designed to
exercise all labels and interfaces. That makes them useful for regression but
weak evidence of generalisation. The final evaluation requires an approved,
independently governed frozen corpus and explicit limitations.

### What happens when the provider fails?

Timeout, unavailable provider, or invalid provider output raises a typed failure
before a completed report is published. The provider cannot write files or
approve a human action.

### What will you cut if time is limited?

Keep schema, segmentation, evidence retrieval, classification, validation,
mapping, artifacts, review, core interfaces, and failure tests. Cut the external
model comparison and other Should/Could extensions before weakening the Must
traceability and fail-closed behaviour.

## 7. Rehearsal checklist

- [ ] Actual group and group number are confirmed under the Canvas rule.
- [ ] Each member can state Track B and the product in one sentence, including
  quality, task fit, and efficiency as separate measures.
- [ ] Each member can explain problem, users, AI contribution, three FRs, one
  risk, and evaluation.
- [ ] Members can distinguish implemented, verified, proposed, and pending.
- [ ] No one calls draft fixture metrics a final model result.
- [ ] Prior-work disclosure is stated before the tutor has to ask.
- [ ] Demo uses synthetic data, no secrets, and a fresh run path.
- [ ] One member records tutor questions, requested changes, and approval state.
- [ ] Each member can answer simple Week 1-2 concept questions in their own
  words without any AI tool or generated notes during the check.
- [ ] The group knows that this ungraded oral check does not replace the written
  Proposal or mandatory approval.

## 8. Feedback and authorship record

Complete this after the real check; do not prefill attendance or decisions.

```text
Date/time and Week 3 lab:
Tutor:
Group number:
Members present and contribution:

Questions asked:
Requested scope changes:
Requirements/risks/evaluation challenged:
Authorship or understanding concerns:
Approval status after check:
Items requiring coordinator clarification:

Change owner and due date:
Private evidence location:
Recorder and second-person check:
```

## 9. Stop conditions

Do not claim the oral check is complete or the project is approved when:

- any member or attendance fact is unknown;
- the tutor requests a revision that has not been implemented and confirmed;
- prior-work permission remains unanswered;
- the official track/team rule conflicts with the proposal; or
- the only evidence is a passing test/corpus report rather than a tutor decision.

As of `2026-08-30`, no authoritative local attendance, contribution, feedback,
or completion record exists. The correct state is `COMPLETION_UNKNOWN`, not
`completed` and not proof of non-attendance.
