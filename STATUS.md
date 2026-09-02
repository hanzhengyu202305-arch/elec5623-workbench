# ELEC5623 Project Status

Updated: `2026-09-02`

State: `DRAFT_VERTICAL_SLICE_COMPLETE / WORKBENCH_COMPARE_LAYER / LAB1_PARTIAL / LAB2_AND_ORAL_RESULTS_UNKNOWN / TEAM_AND_TUTOR_APPROVAL_PENDING`

## Still blocked (human gates)

Automation cannot close these. Keep `GroupXX` and empty approval quotes.

- Whole-group agreement on the Workbench direction.
- Tutor written approval of extending the Inspector single-model audit to
  multi-model effectiveness comparison.
- Then fill the actual Canvas group number and confirmed members.
- Then Canvas upload. Do not submit this `GroupXX` draft.
- Do not send the tutor email from this repository. Do not invent approval
  wording.

Ordered student actions remaining: (1) confirm the group agrees; (2) fill
tutor name plus real member names in `TUTOR_APPROVAL_PACK.md` §1 and send it
yourself; (3) paste the Lab 1 Run 2 Playground output into a file and check
`python scripts/count_lab1_words.py`; (4) keep secret-free Azure screenshots
and credit privately; (5) run Lab 2 LoRA in the authorised runtime; (6)
rebuild/submit the PDF only after written approval and a real group number.

## 2026-09-02 Model Effectiveness Evaluation Workbench

Public product name is now **Model Effectiveness Evaluation Workbench**. The
inner engine remains the Inspector (FR-01–15). FR-16–18 add a sequential
named-model compare shell: quality, task fit, latency, and estimated list-price
cost are reported separately; min-cost is contrasted with a documented
quality/task-fit rule; human review remains `READY_FOR_HUMAN_REVIEW`. No
combined effectiveness index.

The blocked candidate PDF remains `DRAFT_NOT_FOR_SUBMISSION` with `GroupXX`.
A local Workbench demo command is `bash scripts/run_workbench_demo.sh`.
Canvas submission, group identity, tutor name/date/statement, Lab 1 remaining
evidence, Lab 2 execution, and Week 3/4 oral results are still human gates.

## Implemented baseline

- Independent Track B product: **Model Effectiveness Evaluation Workbench**
  (Inspector engine FR-01–15; compare shell FR-16–18).
- Strict English JSON/Markdown schemas, deterministic claim segmentation,
  local TF-IDF retrieval, five support labels, exact-quote validation,
  requirement mapping, metrics, immutable run artifacts, and append-only review.
- Human-readable reports expose all metric categories and a complete per-claim
  audit: original text, rationale, ranked evidence scores/excerpts, exact-quote
  outcomes, and the append-only review target. Dynamic literal fences prevent
  untrusted claim/evidence/provider text from forging report structure.
- Shared service behind CLI `validate`, `evaluate`, `review`, and `compare`,
  plus four FastAPI routes.
- Exact Python runtime `>=3.11,<3.12`; local `.venv` is CPython `3.11.15`.
- `FixtureModelGateway` is the test/CI truth surface; no external model or secret
  was used for the retained draft acceptance.
- CLI `evaluate` and API `create_app` now share an explicit environment factory
  for the optional OpenAI/Azure-compatible gateway. Fixture remains the default;
  live mode additionally requires an exact approved-host allowlist. No real
  provider, credential, or network request was used in verification.
- 18 draft functional requirements, ten draft NFRs, prior-work disclosure,
  official 12-section Proposal working draft, source-hash compliance matrix,
  verified reference register, team/tutor/oral/Lab 1 packs, traceability matrix,
  and append-only AI Journal exist.
- A compressed blocked Proposal candidate, deterministic ReportLab builder and
  rendered `DRAFT_NOT_FOR_SUBMISSION` PDF now exist; they retain every external
  gate rather than inventing cover or approval facts.
- The six-page Proposal brief and seven-page Lab 1 PDF captured from Canvas were
  hashed, fully text-extracted, and visually checked on `2026-08-02`.
- The 44-page Week 1 lecture was captured and hashed on `2026-08-03`; pages
  31-41 were visually checked and reconciled into an operational control for
  attendance/group formation, tutor approval, secure no-AI assessments, and the
  semester assessment timeline.

## Verified evidence

- 2026-09-02 Workbench follow-up: local demo script, Lab 1 word-count helper,
  architecture/compare CLI wording, and Proposal test-count reconciliation.
  Group/tutor/Canvas sentinels unchanged. See the journal append for this date.

- The `2026-08-31` course-logistics reconciliation converted authenticated Ed
  thread `3542678` into a dated source-to-action/evidence gate without changing
  any product, Proposal, oral-result, approval or submission claim. Thread time
  is `2026-08-30 21:21:58 AEST`; the announced class date is Wednesday
  `2026-09-02`. The source says the class is online, strongly recommends not
  coming to campus, and says the meeting link will be posted on Ed on the class
  day; the staff reply confirms that **both** the lecture and tutorial are
  covered. The link and participation remain unknown and must be checked by the
  student on Ed before the scheduled sessions. Post-edit bounded checks passed:
  Proposal heading order, `22/22` PDF-builder regressions, and
  `uv lock --check --offline`. The Proposal source/PDF was not rebuilt.
- Independent 2026-08-30 rerun after the new-source reconciliation:
  `PYTHONPATH=. .venv/bin/pytest` passed `138` tests on CPython `3.11.15`
  with `93.92%` branch coverage; system Ruff passed; compileall passed;
  `uv lock --check --offline` passed; corpus shape remained `20 bundles / 200
  claims`; Proposal heading order passed; and Proposal builder regressions
  passed `22/22`. A first bare pytest invocation failed collection because the
  repository root was absent from `PYTHONPATH`, and `.venv/bin/ruff` was not
  installed; the bounded rerun used the documented root path and system Ruff.
  No provider, model notebook, Canvas, email, submission, commit, or push was
  used. The compressed Proposal candidate/PDF was not rebuilt; Lab 2 use-case
  and context-boundary content is present only in the full working draft, so
  candidate reconciliation and final visual QA remain open.
- Independent 2026-08-24 rerun: `138 passed` on CPython `3.11.15`, branch
  coverage `93.92%`, system Ruff `0.12.0` PASS, compileall PASS,
  `uv lock --check --offline` PASS, corpus shape `20 bundles / 200 claims`
  valid, Proposal structure PASS, and Proposal builder regressions `22/22`
  PASS. The current PDF remained `1` cover + `8` body + `1` references,
  `5,032` source tokens with `100%` extracted-token coverage, SHA-256
  `50adb2eb3771d03d185fb6586d04418223361f7f17b90561060bd85085167bab`.
  This run did not repeat page-by-page visual inspection; the latest visual QA
  remains the 2026-08-07 evidence.
- Independent 2026-08-07 rerun: `138 passed` on CPython `3.11.15`, branch
  coverage `93.92%`, Ruff PASS, compileall PASS, Proposal heading-order PASS,
  and Proposal builder regressions `22/22` PASS. The current 10-page A4 draft
  was rendered at 120 DPI and every page was visually checked again with no
  clipping, overlap, blank page, broken glyph, unreadable URL/table, or
  watermark obstruction. This verification changed no group, tutor, freeze,
  Canvas, or submission gate.
- `138 passed` under CPython `3.11.15`, including ground-truth alignment,
  review-target integrity, mocked compatible-provider contracts, and a local
  Proposal heading-order check against the captured official 12-section brief.
- Branch coverage: `93.92%` (configured minimum `80%`); the expanded gateway is
  `96%` and the artifact store is `88%`.
- Retained Proposal candidate PDF: `10` A4 pages = `1` cover + `8` Sections
  2-11 body pages + `1` reference-only page. Builder validation PASS;
  extracted-text coverage `100.00%`. The last complete rendered-page visual
  inspection is the dated evidence in `PDF_QA_REPORT.md`, not a new 2026-08-24
  inspection.
- Proposal PDF boundary: `22/22` dedicated regression tests PASS. They cover
  same-file/hard-link/symlink protection, atomic no-clobber publication,
  source-identity/SHA recheck, exact draft/section structure outside code
  fences, one/two/trigram and exact token-sequence loss, chrome-only or
  invisible-text pages, nested Form XObjects, explicit overwrite, and
  byte-identical invariant rebuilds.
- Visual QA found no clipping, overlap, blank page, broken glyph, unreadable URL
  or table, and the pale draft watermark does not obscure content. Exact hashes
  and page-by-page evidence are in `PDF_QA_REPORT.md`.
- CLI `validate`, `evaluate`, and `review`: PASS.
- API `health`, create, fetch, and append-review routes: `200/201` as specified.
- Two appended reviews left `report.json` SHA-256 unchanged. Review JSONL now
  holds an exclusive `fcntl.flock` across complete short-write handling and
  `fsync`; a stalled partial append rolls back, concurrent writers retain
  complete unique parseable records, and platforms without `fcntl` fail closed.
- Read/review targets must be real and unaliased: symlink run directories,
  symlink reports, report/directory identity drift, and symlink or hard-linked
  review targets raise a typed error. Service, API, and CLI regressions prove
  the outside target remains byte-for-byte unchanged.
- Markdown report-contract regressions require all classification counts and
  every claim's rationale, ranked evidence excerpt/score, exact-quote result,
  and review target. A collision test proves embedded triple-backtick provider
  text is contained by a longer literal fence.
- Any non-empty `expected_claims` list must cover every segmented claim ID
  exactly. Missing or ghost IDs fail before retrieval/provider work and before
  any completed artifact; empty ground truth remains a valid unscored run.
- Current draft development corpus: `20 bundles / 200 claims`, five synthetic
  template families and four Markdown layouts, fixture-only. The current-source
  acceptance retained at
  `acceptance/local-20260804-review-integrity-v2/corpus-acceptance.json` passes all six
  checks: citation completeness `1.0`, five-label macro-F1
  `0.8577014177655716`, risky precision `0.9302325581395349`, risky recall
  `1.0`, requirement-mapping macro-F1 `0.96`, and elapsed
  `0.8669942080741748 s <= 60.0 s` on the recorded local machine. Its 20
  Markdown reports contain complete audit sections for all 200 claims.
- The matching ablation/error study is retained at
  `acceptance/local-20260803-multitemplate-study-v3/baseline-study.json`. The
  full fixture replay contains `37` label errors and `12` mapping errors across
  `41` affected claims; the error rows are retained rather than hidden by the
  passing aggregates.
- The current corpus hash is
  `45e8a30308ad78be0dcb1ed48d3fa9cf4684bacd3ed348cc3a4c17e25ca09fa9`
  and the service prediction hash is
  `8f28dff5ae7d65a817f16de63447f252b187ba6f3f0df7607ff0b8ad4aba804f`.
- Reusing an acceptance report path returns exit code `2` and preserves the
  existing report hash.
- Prompt-injection, conservative token-budget, long unbroken input, and provider
  timeout tests fail before a completed run is created.
- Mocked OpenAI Bearer and Azure `api-key` requests validate URL/header/payload,
  strict response parsing and CLI/API selection. Live configuration requires an
  exact approved hostname, rejects every query except one valid Azure
  `api-version`, and excludes endpoint/key/allowlist from configuration `repr`.
  Unsafe endpoint/config values, HTTP/transport failures, malformed, deeply
  nested or oversized JSON, and provider timeouts expose no credential and
  create no completed run. A focused regression proves the outbound opener
  refuses redirects, preventing credentials from following a changed destination
  or TLS downgrade. No live endpoint was called.
- Schema regressions now cover duplicate requirement, evidence, and
  expected-claim ids; an engine regression proves an altered exact quote forces
  a positive gateway decision to `UNSUPPORTED`.
- Duplicate corpus bundle ids and expected/segmented claim-id misalignment now
  fail before the first run. Artifacts are fully staged and synced before atomic
  no-clobber publication, with `report.json` last; simulated ordinary failures,
  partial writes, and marker interruptions leave no readable commit marker.
  Heading/code-only output raises typed `NoAuditableClaims` in Engine, CLI, and
  API paths.
- CommonMark backtick/tilde code fences plus ATX/Setext headings are excluded
  from auditable claims; an ignored-only document fails closed.
- A Python 3.11 fixture workflow definition is placed at the real study
  repository root:
  `/Users/hanzhengyu/Documents/study/.github/workflows/elec5623-fixture-ci.yml`.
  It is uncommitted and has not run on GitHub; activation requires deliberate
  commit/push. The nested workflow is labelled as a future standalone-repository
  template.

Current corpus and ablation evidence is under ignored paths
`acceptance/local-20260804-review-integrity-v2/` and
`acceptance/local-20260803-multitemplate-study-v3/`. It is explicitly
`DRAFT_UNFROZEN_NOT_TUTOR_APPROVED` / `DRAFT_DEV_UNFROZEN_NOT_TUTOR_APPROVED`
and is not a final course result.
The superseding fixture-only normalized-report check is retained under
`acceptance/local-20260803-normalized-repro-v3/`: two fresh Python processes and
independent artifact roots produced the same persisted normalized SHA-256
`37973bedb55ae695e82948752076548dba53aa68bd584d8c13dff3098ee691c1`
after excluding only `run_id` and `created_at`. Both disk input bundles were
schema-validated and had raw SHA-256
`ffb2952a4d28d3551ce3196dcfbbce8fd07ae25f033930636db12fdd6e157456`;
each report input hash matched the requested bundle. This is local persisted-
artifact reproducibility evidence, not a clean-checkout or tutor-approved result.

The clean-environment sequence is retained without overwriting any attempt.
Version `v7` is an expected fail-closed cache-miss at
`acceptance/clean-env-offline-replay-20260803-v7/`: the locked offline install
stopped before project build because `hatchling==1.31.0` was absent, and no
dependency or provider request was made. Version `v8` at
`acceptance/clean-env-public-pypi-20260803-v8/` explicitly allowed only the
locked dependency prefetch from public PyPI; that network step excluded the
project, passed, and was followed by an offline project install and fixture
check. Version `v9` at
`acceptance/clean-env-offline-replay-20260803-v9/` then reconstructed a fresh
non-editable CPython `3.11.15` environment entirely from the populated cache;
all four bounded steps exited `0`. Historical `v10` repeated that replay after
the Markdown audit change. Historical `v11` repeated the replay after the
ground-truth alignment gate. Current-source `v12` at
`acceptance/clean-env-offline-replay-20260804-v12/` repeated the fully offline,
non-editable reconstruction after the review-target integrity change. All four
commands again exited `0`; CLI validation exercised the semantic gate, both
retained reports expose the complete 11-claim audit and human-review target,
and the normalized SHA-256 remained
`37973bedb55ae695e82948752076548dba53aa68bd584d8c13dff3098ee691c1`.
The `v12` manifest SHA-256 is
`482aed6343ff29797b8774cdaa385cdbc30c7a5f7f45ace49d605d3b877134fb`.
This proves the retained current-source single-bundle locked/offline replay,
including the append lock and report renderer. It does not prove an
empty-machine bootstrap,
OS-level packet isolation, live-provider compatibility, frozen-corpus
generalization, GitHub CI, tutor approval, or submission.

The original Python 3.14 development environment was preserved, not deleted, as
`.venv-py314-backup-20260802`; it is not an acceptance environment.

## Canvas refresh

- `2026-08-03`: the downloaded Week 1 lecture
  `Canvas_2026_S2/ELEC5623/ELEC5623_wk1_2026.pdf` has SHA-256
  `bb04c4671f1d4f5319028c55430b2a8db03e6a32202ad5f8e65f1f4231b1c6b3`.
  Its assessment pages add course-wide controls without replacing the more
  specific Proposal brief or live Canvas deadline: attend the enrolled lab;
  groups form in the first lab with at most five members; tutor approval is
  required before assessed project start and before Proposal submission; AI is
  prohibited during early-feedback/interactive orals, the mid-term test,
  project Q&A, and the final exam. `WEEK1_COURSE_CONTROL.md` retains the complete
  overview timeline and fail-closed operating rule.
- `2026-08-07`: a fresh Canvas refresh attempt reached University SSO and did
  not yield an authenticated course page. No new assessment, rubric, file, or
  deadline was captured, so the 2026-08-03 authenticated sources remain the
  latest usable course evidence and no 24-hour matrix update was triggered.
- `2026-08-08`: a direct request for the ELEC5623 Modules page again redirected
  to University SSO. No authenticated assessment, rubric, file, deadline or Ed
  post was captured. The 2026-08-03 sources therefore remain the latest usable
  course evidence, and no new 24-hour requirement-to-implementation matrix row
  was triggered. One Chrome sign-in handoff was retained for the student.
- `2026-08-24`: the previously loaded course page was refreshed and reached the
  University of Sydney sign-in page. No authenticated current module,
  assessment, rubric, Ed post, group record, deadline, or submission state was
  captured. This does not prove that the live course is unchanged; the browser
  handoff remains blocked on UniKey/MFA and no 24-hour matrix row was invented.
- `2026-08-30`: four new course-branded local downloads dated `2026-08-26`
  were ingested without live-Canvas inference: Lab 2 SHA-256
  `200e7f06...b641` (9 pages), its LoRA notebook `3019e28a...db7` (19
  cells, zero executed/output cells), Week 2 `e11f9023...3b35` (34 pages),
  and Week 3 `7b16273c...4502` (32 pages). All PDF text/pages were checked;
  the current live Canvas versions remain unknown. Duplicate Lab 1 and Week 1
  downloads matched the previously retained hashes exactly.

## Local course-source scan - 2026-08-31

A filename/date scan of Downloads after `2026-08-30 18:23 AEST` found no new
file explicitly labelled ELEC5623, Proposal, rubric, assignment, oral, lab,
week or notebook. The only unresolved opaque-name PDF was text/metadata checked:
`/Users/hanzhengyu/Downloads/4ED4A49AA46A11F18A9AC58E29055865.pdf`,
SHA-256 `8ed422afd8de9d6ccff46280e11515beb3ca69deef0890b0bb8e58cc20b13701`.
It is a private course-result history, not an ELEC5623 brief or assessment
source, and no personal result content was copied into this project. This scan
does not establish that live Canvas is unchanged.

## Live Ed refresh - 2026-08-30

Authenticated read-only Ed course `38814` evidence now adds three urgent
controls without establishing any attendance, result, send, feedback, or
approval fact:

- thread `3519404` says the Week 4 oral is assessed, individual/random, covers
  Week 1-3 lecture/lab concepts, and emphasises clear own-words understanding;
  its ten focus topics are captured in
  `WEEK4_ASSESSED_ORAL_PREP_CONTROL.md`;
- thread `3476276` says Week 3 early feedback is group-based and 0%, while
  assessed interactive orals total 10% in scheduled labs in Weeks 4, 6, 8, 10
  and 12; AI is prohibited during both; and the Proposal idea needs lab-tutor
  approval before submission; and
- thread `3504074` asks groups to send Proposal drafts early for a potentially
  multi-round feedback/rebuttal process. No message was sent by this run.

Accepted staff answer in thread `3530952` says Lab 03 is not required for the
Week 4 oral. Week 3 and Week 4 completion/result states remain
`COMPLETION_UNKNOWN / USER_VERIFICATION_REQUIRED`.

## Live Ed delivery refresh - 2026-08-31

Authenticated read-only Ed course `38814`, pinned thread `3542678`,
`Wednesday 2 September Class Moved Online`, was posted by staff member Linghan
Huang at `2026-08-30T11:21:58.184Z` (`2026-08-30 21:21:58 AEST`). The retained
operational facts are:

- the Wednesday `2026-09-02` class has moved online;
- students are strongly recommended not to come to campus;
- the online meeting link will be posted on Ed on the class day; and
- in a staff reply to whether the change covers only the tutorial or also the
  lecture, the answer is `both, due to strike :(`.

No meeting link, exact session time, attendance, result or participation fact
was present or inferred. `WEEK1_COURSE_CONTROL.md` and the compliance matrix
now require a user-only Ed recheck before both scheduled sessions on
`2026-09-02`; only the staff-posted link may close that logistics gate. This
one-day delivery change does not relax the no-AI boundary for any secure
assessment that may occur, and no assessed activity is inferred from the post.

## Lab 1 evidence reconciliation — 2026-08-24

The private local record
`/Users/hanzhengyu/Documents/elec5623/lab01_azure_record.md` (dated
2026-08-12, SHA-256
`955cf7a811950815af3701f5755f20d03d2442cb4e812a9d030059eef15adc65`;
supersedes the 2026-08-24 hash after a 2026-09-02 rerun-kit append that does
not claim a new Azure run)
and the companion secret-free script
`/Users/hanzhengyu/Documents/elec5623/azure_foundry_prompt.py` (SHA-256
`5d0258de155cdb8e93fb48dbae4fdeedfaaa8713cde5d2c56906466a5c74bb1d`)
now provide partial Lab 1 evidence. They record an available Azure for Students
subscription, an allowed-region correction, Foundry resources, model/settings,
two exact Playground prompts and outputs, Codex use, environment-variable key
handling, and a manual rejection/correction. The script compiles and exits
fail-closed when `AZURE_FOUNDRY_API_KEY` is absent. A targeted text audit found
no credential value in either retained text source; the script contains only a
documented `your-key` placeholder.

This is not a complete Lab 1 record. No redacted screenshot, Azure credit,
exact Codex/IDE/CLI version, exact run time/timezone, named human review
sign-off, or successful live API execution evidence exists locally. Run 1 is
approximately `110` words, while Run 2 is approximately `133` words and exceeds
the prompt's `<=120` word constraint. The original output remains failure
evidence; Run 2 must be repeated in the approved interface with only the
audience changed and the missing evidence retained before Lab 1 can be
described as complete.

## External gates

- On `2026-09-02`, do not travel to campus for ELEC5623; recheck Ed before the
  scheduled lecture and tutorial, obtain the staff-posted meeting link, and
  retain private participation evidence if required. The link is not yet
  captured, and this automation cannot attend for the student.
- Outside the dated `2026-09-02` online exception, attend the enrolled in-person
  lab or obtain an authorised alternative through the teaching/timetable
  process. Recheck the live Canvas group rule, then
  form/register no more than five members and record group number, names/SIDs,
  and at least three FRs per person.
- Show `PRIOR_WORK_DISCLOSURE.md` and the proposed scope to the tutor.
- Record tutor name, approval date, exact wording, and evidence location.
- Recheck Canvas/AI guidance for revisions; replace every cover/allocation/
  approval sentinel with verified facts, reconcile the resulting content, then
  rebuild and visually re-QA the final 8-10 body-page candidate. The current
  blocked draft (SHA-256
  `b02f49d538474f22508af731e8ff6558c55e260028c2890f014575506031fab4`)
  proves layout feasibility and the Workbench wording only.
  Do not upload the `GroupXX` file to Canvas.
- Complete the remaining Lab 1 evidence: record Azure credit, exact client
  versions and run times, retain secret-free screenshots, repeat Run 2 within
  the 120-word limit with only the audience changed, and record whether the
  course requires a successful live endpoint call. The existing local record
  is partial evidence, not Lab completion.
- Complete the Lab 2 LoRA notebook in the authorised student runtime and retain
  adapter/configuration/logs/baseline/tuned outputs/metrics/manual review and
  evidence ZIP. The downloaded notebook is unexecuted source, not completion.
- Prepare for and independently complete the Week 4 assessed oral. Close Codex
  and all AI tools before the assessment; no attendance or result is claimed.
- With explicit interactive user confirmation, send the actual group Proposal
  draft early enough for the staff's iterative feedback/rebuttal cycle. This
  automation prepared/reconciled drafts but did not send email or claim
  feedback.
- Freeze corpus/labels only after the annotation protocol and tutor-approved
  scope are agreed.
- Student/group performs the oral progress check and final submission.
- Establish a deliberate course repository/history after the group and tutor
  workflow is confirmed. The enclosing `study` repository currently has zero
  commits and this project has zero tracked files, so the working tree cannot
  yet provide an immutable drift/recovery baseline.
- Student/group closes all AI tools and does not consult AI-generated material
  during early-feedback/interactive orals, the mid-term test, project Q&A, or
  the final written exam.

No approval, team membership, oral participation/result, Proposal-draft send or
feedback, proposal submission, Lab 2 completion, or final product completion is
claimed by this status.
