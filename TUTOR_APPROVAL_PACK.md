# Tutor approval request and checklist

Status: **request prepared; no tutor approval claimed**  
Student/team details: **to be supplied by the actual group**  
Official approval requirement: **lab tutor approval before 2026-09-08 23:59**  
Cover evidence required: **tutor name, approval date, brief approval statement**

## Still blocked (human gates)

This pack records remaining gates. It does not fill them.

**Student-only tonight (this repository will not send mail):** copy §1, replace
the tutor name and the sign-off line with real names, attach
`PRIOR_WORK_DISCLOSURE.md` if the mail client allows, and send it yourself.
Leave `GroupXX` out of the send unless Canvas already issued a real number.

- Whole-group agreement on the Workbench direction (not yet recorded).
- Tutor written approval of extending the Inspector single-model audit to
  multi-model effectiveness comparison.
- After those two: fill the actual Canvas group number and confirmed member
  names/SIDs (keep `GroupXX` until then).
- Then Canvas upload of the unblocked PDF. Do not submit this draft.
- Do not send this email from automation. Do not invent approval quotes.

Latest live guidance checked `2026-08-30`: Ed course `38814`, threads
`3504074` and `3476276`. Staff asks groups to send Proposal drafts early for
detailed, potentially multi-round feedback/rebuttal and to communicate with the
lab tutor during labs rather than waiting until the deadline. No draft send,
email receipt, feedback round, tutor interaction, or approval is claimed here.

This pack separates the request, the decisions needed, and the evidence that
would close each gate. Sending a message, attending a discussion, or receiving
general encouragement is not the same as scope approval unless the tutor's
wording actually answers the decision.

## 1. Short request for email or Ed

Subject: `ELEC5623 Track B written approval request: Model Effectiveness Evaluation Workbench`

> Dear [Tutor/Coordinator name],
>
> Our group requests written approval of a Track B direction change: extending
> the Inspector single-model audit (FR-01 to FR-15) to a **Model Effectiveness
> Evaluation Workbench** that compares at least two named models on the same
> evidence-backed bundle (FR-16 to FR-18). This is one product and one
> repository, not two.
>
> On the same lab-write-up style bundle the Workbench sequentially runs named
> gateways through the existing Inspector engine, then reports quality, task
> fit, latency, and estimated list-price cost separately. It contrasts a
> min-cost rule with a documented quality/task-fit rule. There is no combined
> effectiveness index and no auto model-deploy. Every automated success remains
> `READY_FOR_HUMAN_REVIEW`. Estimated cost is a published list price times a
> conservative token bound, not an invoice. Without complete labels the compare
> report is comparison only and does not claim prediction or success.
>
> Course evaluation practice is related to effectiveness-beyond-price questions.
> This product is independent coursework and does not claim that Constantinople
> / ESIPS Pound for Pound is complete. We are not proposing a credit-policy
> retrieval product or a conversational banking front door.
>
> First-month scope uses Python 3.11, FastAPI, Pydantic v2, scikit-learn, and
> pytest. It is limited to English JSON/Markdown and local synthetic evidence,
> with no PDF/OCR, web retrieval, database, frontend framework, or live
> commercial compare APIs this week. We propose 18 functional requirements, ten
> measurable NFRs, and a 20-bundle/200-claim synthetic Inspector evaluation
> plan plus two-model fixture compare.
>
> We are also proactively disclosing that the high-level idea was informed by
> earlier personal exploration called AegisOps. The ELEC5623 product has an
> independent problem statement, codebase, schemas, data, tests, metrics,
> report, and demo; no AegisOps or ELEC5308 code, data, figures, results, prose,
> or demo artifacts will be reused. The attached prior-work disclosure gives the
> full boundary.
>
> Could you please confirm in writing whether (1) this Workbench direction is
> acceptable for Track B, (2) extending the Inspector audit to multi-model
> effectiveness comparison is in scope, (3) the proposed Must/Should/Won't
> boundary is appropriate, (4) the prior-work disclosure and independence
> controls are sufficient, and (5) the proposed synthetic evaluation and
> compare method is acceptable? We would also appreciate any required changes
> and confirmation of the live team rule and any additional AI/reference
> guidance not stated in the hashed Proposal brief.
>
> Kind regards,  
> [Confirmed student names, group number, and contact]

Do not send the template with unfilled tutor-name, group-number, or member
fields. Do not invent GroupXX as a real number.

### 1.1 Draft-feedback workflow

The current compressed PDF is deliberately blocked, so the editable working
draft/candidate can be reviewed first. Before any email is sent, the student
must confirm the real recipients, group identity, approved attachment, and that
every placeholder is appropriate for a draft. Sending is an external action and
requires explicit interactive user confirmation.

For each real feedback round, retain:

```text
Sent date/time and sender:
Recipient/channel:
Exact draft hash/version:
Comments/questions received:
Group rebuttal or clarification:
Revision and requirement/test/report impacts:
Open disagreement or required follow-up:
Second-person check:
```

An email sent is not tutor approval; feedback and rebuttal may require several
revision rounds, and only the bounded approval record closes the approval gate.

## 2. One-page approval summary

### Proposed decision-support product

```text
requirements + supplied evidence + AI-generated Markdown
  -> Inspector engine (FR-01-15): validate, retrieve, classify, enforce, review
  -> Workbench compare (FR-16-18): sequential named models on the same bundle
  -> quality, task fit, latency, estimated cost reported separately
  -> min-cost vs quality/task-fit selection; human review remains success
```

Effectiveness is reported as separate dimensions. Spend is an estimated
list-price bound, not a verdict. The product is not a credit-policy retriever
or a conversational banking front door. Constantinople / ESIPS Pound for Pound
is not claimed complete.

### Public contract

```text
CLI: validate, evaluate, compare, review
API: GET /health
     POST /v1/evaluations
     GET /v1/evaluations/{run_id}
     POST /v1/evaluations/{run_id}/reviews
```

### Proposed first-month constraints

- Python `>=3.11,<3.12`; FastAPI; Pydantic v2; scikit-learn; pytest.
- English JSON and Markdown only; supplied local evidence only.
- `FixtureModelGateway` for deterministic CI.
- Optional compatible model gateway only after rules/privacy approval.
- No PDF/image/OCR, web retrieval, database, or frontend framework.
- No autonomous approval, merge, deployment, or external action.

### Current prototype evidence

- 18 draft FRs and ten draft NFRs linked to implementation/tests.
- 138 tests pass with 93.92% branch coverage under CPython 3.11.15.
- Draft multi-template 20-bundle/200-claim fixture run passes current checks in
  0.866994 seconds; macro-F1 is 0.857701, risky precision/recall are
  0.930233/1.0, and mapping macro-F1 is 0.96.
- Any non-empty ground truth must cover every segmented claim ID exactly; drift
  fails before provider use or artifact creation.
- Aliased run/report/review targets fail closed before a human-review append.
- Result is explicitly unfrozen, synthetic, fixture-only, and not
  tutor-approved; 37 label and 12 mapping errors remain, and no external API
  was used.

### Prior-work boundary

AegisOps is high-level inspiration only. The ELEC5623 problem statement,
architecture, source, schemas, synthetic corpus, tests, metrics, charts, report,
and demo are independent. ELEC5308 and research-paper artifacts are also
excluded. Any future import remains blocked until provenance, licence, course
rules, and written tutor approval are recorded.

## 3. Exact decisions requested

Ask for a bounded answer to each item. “Discussed” is not an approval state.

| ID | Decision requested | Acceptable evidence | Current state |
|---|---|---|---|
| TA-01 | Is this Workbench problem acceptable as ELEC5623 Track B? | Written yes/conditions/rejection from authorised tutor/coordinator | `PENDING` |
| TA-02 | Is the first-month Must/Should/Won't boundary appropriate? | Written scope decision and required changes | `PENDING` |
| TA-03 | Are the 18 FRs and ten NFRs suitable as draft requirements? | Marked list or written conditions | `PENDING` |
| TA-04 | Is the prior-work disclosure sufficient, and is AegisOps inspiration permitted under the stated isolation controls? | Written decision referencing the disclosure | `PENDING` |
| TA-05 | Is a new 20-bundle/200-claim synthetic corpus acceptable? | Written evaluation-method decision | `PENDING` |
| TA-06 | Is the proposed annotation/freeze process sufficient? | Written approval or changes | `PENDING` |
| TA-07 | Are the five labels and proposed metric thresholds appropriate? | Written decision; updated definitions/thresholds | `PENDING` |
| TA-08 | May an external compatible model be used, and under what privacy/budget constraints? | Written conditions; otherwise fixture-only | `PENDING` |
| TA-09 | Does the live Canvas team rule agree with Lab 1's maximum five, and how must individual contribution be evidenced? | Canvas citation or authorised answer | `PENDING` |
| TA-10 | Are there additional Proposal, citation, AI-disclosure, or later-deliverable rules beyond the hashed brief? | Saved Canvas/rubric version or authorised answer | `PENDING` |
| TA-11 | Does the revised Proposal adequately cover the Lab 2 use-case, system-boundary, workflow and product-analysis guidance? | Written comments and resulting revision record | `PENDING` |
| TA-12 | Is reporting quality, task fit, latency, and estimated cost as separate dimensions, without a combined price-proxy score, acceptable? | Written evaluation-framing decision | `PENDING` |
| TA-13 | Do you approve in writing the new direction: extending the Inspector single-model audit to multi-model effectiveness comparison (Workbench FR-16–18)? | Written approval of this direction, or required changes | `PENDING` |

If the tutor is not authorised to answer an item, record the escalation contact
instead of interpreting silence as approval.

## 4. Material to show

Use the smallest set that supports the decision:

- `PROPOSAL_DRAFT.md` — full bounded proposal draft;
- `docs/REQUIREMENTS.md` — 18 draft FRs;
- `docs/NFR_CONSTRAINTS.md` — ten draft NFRs and targets;
- `docs/ARCHITECTURE.md` — product boundary and failure behaviour;
- `docs/TRACEABILITY.md` — implementation/test/evidence mapping;
- `PRIOR_WORK_DISCLOSURE.md` — independence controls;
- `TEAM_FORMATION_PITCH_PACK.md` — only if team rules/allocation are discussed;
- `WEEK3_ORAL_PROGRESS_CHECK_PACK.md` — progress evidence, not an approval
  substitute; and
- one fresh fixture demo, if requested.

Do not attach ignored local acceptance directories, credentials, private member
data, or material from AegisOps/ELEC5308/research-paper work.

## 5. Meeting checklist

### Before

- [ ] Confirm the tutor/coordinator name and approved communication channel.
- [ ] Confirm actual team members and group number; otherwise identify the
  request as an individual pre-formation scope check.
- [ ] Save the current official brief/rubric version if available.
- [ ] Read the AI and prior-work rules verbatim; note unresolved wording.
- [ ] Ensure the demo says “draft fixture baseline” and uses synthetic data.
- [ ] Choose one person to ask, one to demo, and one to record exact decisions.
- [ ] Remove bracketed placeholders from any message actually sent.

### During

- [ ] State the human-review boundary before showing model outputs.
- [ ] Ask TA-01 through TA-13 or record which items are deferred.
- [ ] Show the prior-work disclosure explicitly.
- [ ] Ask what evidence counts as formal approval.
- [ ] Record exact required changes, owner, and due date.
- [ ] Ask whether a follow-up written confirmation is needed.

### After

- [ ] Write a factual meeting note; distinguish quotes from paraphrases.
- [ ] Send a concise confirmation message if the decision was verbal.
- [ ] Save the reply/screenshot/link in the private course record.
- [ ] Update requirements and proposal only after checking the exact condition.
- [ ] Update `PRIOR_WORK_DISCLOSURE.md` tutor fields only when TA-04 is answered.
- [ ] Append the decision and any AI assistance to the relevant journals.
- [ ] Do not mark approval if the answer is ambiguous or from an unauthorised
  source.

## 6. Decision record template

Copy this into the private course record after the actual interaction.

```text
Approval record ID:
Date/time and timezone:
Tutor/coordinator name and role:
Channel/location:
Confirmed group number and attendees:
Official brief/rubric version referenced:

TA-01 Track B problem decision:
TA-02 Scope decision:
TA-03 Requirements decision:
TA-04 Prior-work decision:
TA-05 Corpus decision:
TA-06 Annotation/freeze decision:
TA-07 Labels/metrics decision:
TA-08 External model decision:
TA-09 Team-rule answer:
TA-10 Proposal/AI/submission-rule answer:
TA-11 Lab 2 Proposal-strengthening feedback:

Required changes, owner, due date:
Unanswered items and escalation contact:
Exact approval wording or verified paraphrase:
Evidence location (private):
Recorder and second-person check:
```

## 7. Follow-up confirmation template

Subject: `Confirmation of ELEC5623 Track B scope discussion`

> Dear [Name],
>
> Thank you for discussing our proposed Model Effectiveness Evaluation Workbench on
> [date]. To make sure we implement your guidance accurately, our understanding
> is:
>
> - Track B problem decision: [exact bounded wording]
> - Approved Must scope / excluded scope: [wording]
> - Prior-work disclosure decision and conditions: [wording]
> - Corpus, annotation, labels, metrics, and provider conditions: [wording]
> - Required changes and due dates: [wording]
> - Items still requiring coordinator/Canvas confirmation: [wording]
>
> Please correct any point we have misunderstood. We will not treat the pending
> items as approved until they are confirmed.
>
> Kind regards,  
> [Confirmed group]

## 8. Approval closure rules

An item may change from `PENDING` only when the record contains:

1. the authorised decision-maker;
2. exact decision or conditions;
3. date and communication channel;
4. evidence location;
5. resulting scope/document changes; and
6. a human check that the implementation still matches the decision.

General praise, a demo passing, a fixture `PASS`, team agreement, or the absence
of an objection does not satisfy these rules.
