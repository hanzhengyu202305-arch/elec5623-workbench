# Team formation and pitch pack

Status: **ready to use; no team members or group number confirmed**  
Product: **Model Effectiveness Evaluation Workbench** (Inspector engine)  
Official Lab 1 group cap: **maximum five, subject to the live Canvas group-size rule**  
Proposal due: **2026-09-08 23:59**

Use this pack to explain the project, find compatible teammates, and record an
actual agreement. Do not enter a person's name, student ID, or commitment until
they have agreed. Do not describe the current prototype as tutor-approved.

## 1. Thirty-second team-formation pitch

> We are proposing a Model Effectiveness Evaluation Workbench for ELEC5623
> Track B. On the same evidence-backed tasks it runs at least two named models,
> reports quality, task-fit, latency, and estimated cost separately, and
> contrasts min-cost versus quality/task-fit. Human review remains success; it
> does not auto-deploy a model. The Inspector engine already audits claims
> against a lab notebook. A Python 3.11 vertical slice and deterministic tests
> exist, but the project, team, evaluation protocol, and prior-work disclosure
> still need tutor approval of this Workbench direction. We need teammates who
> want to own well-defined requirements while sharing integration, testing,
> report, and demo responsibility.

## 2. Two-minute technical pitch

### Problem

AI-generated reports may contain supported, partially supported, unsupported,
contradicted, or unevaluable claims. Manual reviewers must connect each claim
to evidence and requirements and keep an auditable decision record. The project
tests whether one constrained product can make that review more traceable
without replacing the reviewer.

### Product flow

```text
requirements + local evidence + AI-generated Markdown
  -> strict validation and safety preflight
  -> stable claim segmentation
  -> local evidence retrieval
  -> five-label support classification
  -> citation and exact-quote enforcement
  -> requirement mapping and metrics
  -> immutable report
  -> append-only human review
```

### First-month boundary

- Python 3.11, FastAPI, Pydantic v2, scikit-learn, pytest.
- English JSON/Markdown and local evidence only.
- CLI and four HTTP endpoints share the same evaluation service.
- Deterministic fixture gateway for CI; compatible live provider is conditional.
- No PDF, OCR, web search, database, frontend framework, or automated approval.

### Current evidence, stated accurately

- 18 draft FRs and ten draft NFRs have implementation/test handles.
- Current CPython 3.11.15 baseline: 138 tests passed, 93.92% branch coverage.
- A draft multi-template 20-bundle/200-claim fixture run passed the six current
  checks in 0.866994 seconds: macro-F1 0.857701, risky precision 0.930233,
  risky recall 1.0, and mapping macro-F1 0.96.
- The corpus is explicitly unfrozen and not tutor-approved; 37 label and 12
  mapping errors remain visible and no generalisation claim is made.
- This ELEC5623 product is independent new work; it does not reuse prior
  personal or other-unit code, data, or figures.

### What the team must still decide

- confirm that the official brief permits this Track B problem;
- agree on the human-review use case and Must/Should/Won't scope;
- show the prior-work disclosure to the tutor;
- define independent annotation and corpus-freeze rules;
- allocate work under the actual team-size and contribution requirements; and
- reconcile proposal, AI disclosure, demo, and later deliverables with Canvas.

## 3. Suggested three-minute walkthrough

| Time | Surface | Message |
|---:|---|---|
| 0:00–0:30 | `examples/sample_bundle.json` | One versioned input contains requirements, evidence, and generated output |
| 0:30–1:00 | `docs/ARCHITECTURE.md` | The gateway is a narrow component; deterministic controls enforce evidence integrity |
| 1:00–1:30 | `report.md` from a fresh sample run | Each claim exposes label, citations, evidence matches, quotes, and requirements |
| 1:30–2:00 | two appended review records | Human decisions append; the report hash does not change |
| 2:00–2:30 | failure test names | Timeout, injection, budget excess, invalid quote, and partial writes fail closed |
| 2:30–3:00 | `PRIOR_WORK_DISCLOSURE.md` | The course project is independent and awaits written tutor approval |

Run a fresh demo in a new temporary output directory; never depend on a stale
run ID. The presenter must say “draft fixture baseline” when showing metrics.

## 4. Team-fit conversation

Ask each prospective teammate the same core questions so the decision is fair
and auditable.

### Availability and constraints

- Can you attend the required labs, Week 3 oral check, tutor approval meeting,
  demo, and any scheduled assessment activity?
- What recurring weekly time can you commit, and what dates are unavailable?
- Does the live Canvas group-size/registration rule agree with the Lab 1 maximum
  of five, and are there stream or timetable constraints?
- Which communication channel and response-time expectation works for you?

### Skills and learning goals

- Which areas do you want to own: schemas/segmentation, retrieval/gateway,
  evidence validation, metrics/evaluation, or artifacts/API?
- Which area do you want a review partner for?
- Are you comfortable running Python 3.11 tests and documenting reproducible
  evidence, or would onboarding support help?
- What do you want to learn from the project beyond completing your own tasks?

### Integrity and product boundary

- Are you willing to keep this ELEC5623 product independent of prior personal
  and other-unit work?
- Will you record material AI assistance and personally verify the output?
- Are you comfortable with a product that supports, but never replaces, the
  human decision?
- Will you disclose any proposed prior-work import before it enters the repo?

## 5. Candidate allocation template

Use this only after the actual group and responsibility rules are confirmed.
The official Proposal minimum is at least three FRs per person. For a
five-person group, three consecutive FRs per slot provide a neutral starting
point; for fewer members, redistribute all 15 while keeping at least three each.
These are not pre-assigned ownership.

| Slot | Candidate primary FRs | Integration/review duty | Member | Agreed evidence |
|---|---|---|---|---|
| A | FR-01–03: schema and segmentation | Review no-claim and schema failure gates | `UNCONFIRMED` | `UNCONFIRMED` |
| B | FR-04–06: retrieval and classification | Review corpus label analysis | `UNCONFIRMED` | `UNCONFIRMED` |
| C | FR-07–09: citations and quotations | Review adversarial/fail-closed tests | `UNCONFIRMED` | `UNCONFIRMED` |
| D | FR-10–12: mapping and metrics | Review freeze/annotation protocol | `UNCONFIRMED` | `UNCONFIRMED` |
| E | FR-13–15: artifacts and interfaces | Review clean-checkout/demo flow | `UNCONFIRMED` | `UNCONFIRMED` |

Primary allocation does not remove whole-team responsibility for integration,
testing, report accuracy, demo readiness, and academic integrity.

## 6. Team decision record

Do not treat a chat reaction or an exploratory conversation as commitment.

| Field | Record only after confirmation |
|---|---|
| Team size rule | Lab 1 says maximum five; live Canvas registration rule still to verify |
| Group number / registration location | `UNCONFIRMED` |
| Member names and student IDs | `UNCONFIRMED` |
| Timetable/lab compatibility | `UNCONFIRMED` |
| FR and cross-review allocation | `UNCONFIRMED` |
| Weekly meeting and async channel | `UNCONFIRMED` |
| Definition of done | `UNCONFIRMED` |
| Missed-deadline escalation path | `UNCONFIRMED` |
| AI-use and prior-work agreement | `UNCONFIRMED` |
| Evidence of each person's agreement | `UNCONFIRMED` |

## 7. Proposed working agreement

Ask every actual member to accept or revise these points.

1. **One source version:** code, tests, report, AI journal, and demo refer to the
   same reviewed revision.
2. **Traceable completion:** a requirement is not complete without its test,
   evidence artifact, and report implication.
3. **Review outside ownership:** where team size permits, someone other than the
   primary author reviews each Must requirement.
4. **Fail visibly:** blockers, absences, course-rule uncertainty, and negative
   results are reported early rather than hidden.
5. **Scope discipline:** Must defects outrank Should/Could features.
6. **Academic boundary:** no cross-course or prior-project code, data,
   experiment, figure, prose, or demo material is imported without documented
   permission and course approval.
7. **AI accountability:** material AI use is journalled; a human checks every
   submitted claim and remains responsible for it.
8. **No false approval:** only actual written tutor evidence closes the scope
   and prior-work approval gates.

## 8. Formation checklist

- [ ] Read the current Canvas team and Track rules together.
- [ ] Confirm the live Canvas rule, maximum-five group, registration method, and
  any stream constraints.
- [ ] Give every candidate the same accurate pitch and limitations.
- [ ] Show `PRIOR_WORK_DISCLOSURE.md`; record questions or objections.
- [ ] Confirm attendance and weekly availability.
- [ ] Agree primary FR slots and cross-review duties.
- [ ] Agree communication, meeting, response, and escalation expectations.
- [ ] Record names/IDs privately where required; do not expose them publicly.
- [ ] Register the actual group through the official channel.
- [ ] Prepare one combined tutor approval request.
- [ ] Append the human decisions and any AI assistance to the appropriate logs.

## 9. Stop conditions

Pause team commitment or scope freeze if:

- the official brief does not allow Track B or this product type;
- a candidate expects reuse of assessed code/data/results from another project;
- the live Canvas group-size/registration or timetable eligibility rule is
  unknown or conflicts with the Lab source;
- contribution expectations cannot be made explicit;
- the prior-work disclosure is rejected or withheld; or
- a tutor condition materially changes the proposed architecture/evaluation.

Record the condition and seek the relevant course decision instead of guessing.
