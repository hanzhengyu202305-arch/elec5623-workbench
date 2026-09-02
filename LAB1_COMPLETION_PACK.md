# Lab 1 completion pack

Status: **partial private Azure/model/tool evidence reconciled; group, tutor,
screenshot and corrected Run 2 remain open**  
Official Lab 1 source checked: `2026-08-02`  
Work mode: Part A group; Part B individual or pairs  
Lab format: three-hour practical

Private local evidence checked on `2026-08-24`:

- `/Users/hanzhengyu/Documents/elec5623/lab01_azure_record.md`, dated
  `2026-08-12`, SHA-256
  `955cf7a811950815af3701f5755f20d03d2442cb4e812a9d030059eef15adc65`;
- `/Users/hanzhengyu/Documents/elec5623/azure_foundry_prompt.py`, SHA-256
  `5d0258de155cdb8e93fb48dbae4fdeedfaaa8713cde5d2c56906466a5c74bb1d`.

These records are private working evidence, not a tutor-approved completion or
Canvas submission. A targeted text audit found no credential value; the script
contains only a documented `your-key` placeholder. Preserve the records and add
missing evidence rather than rewriting the original model outputs.

The official Lab 1 goal is to form the project team, launch the 10% Group
Business Proposal, configure a safe and reproducible GenAI environment, confirm
access to cloud and IDE-based AI tools, and explore how model/interface/settings
affect output. This pack tells the student what to do and what evidence to keep;
it does not access or invent student accounts.

## 1. Part A - group formation and Proposal launch

### Official actions

1. Form a group of **maximum five**, in accordance with the group-size rule
   published on Canvas.
2. Read the Group Business Proposal brief.
3. Start the Proposal and discuss the initial idea with the lab tutor to confirm
   next steps.

The Proposal is due `2026-09-08 23:59`. The final core idea needs lab tutor
approval before submission and cannot be materially changed after approval
without teaching-team approval.

### Part A evidence record

| Item | Required evidence | Current state | Student action |
|---|---|---|---|
| Canvas group-size rule | Saved rule/version | `BLOCKED` | Open live Canvas and verify it agrees with max five |
| Group registration | Group number and confirmed members | `BLOCKED` | Form/register the group through Canvas |
| Member identity | Full names and SIDs in private course record | `BLOCKED` | Enter only after each member agrees |
| Proposal brief | Saved PDF and hash | `COMPLETE` | Already captured in compliance matrix |
| Selected direction | Track B on draft cover | `DRAFT` | Group confirms before tutor discussion |
| One-minute pitch | Pitch every member understands | `DRAFT` | Rehearse `TEAM_FORMATION_PITCH_PACK.md` |
| Initial tutor discussion | Questions and next steps | `BLOCKED` | Attend lab/discuss with tutor |
| Final tutor approval | Name, date, brief statement on cover | `BLOCKED` | Obtain before deadline; retain evidence |

Do not put private SIDs or tutor correspondence into a public repository unless
the assessment submission requires them in the final private PDF.

## 2. Part B - cloud and AI development environment

### 2.1 Azure for Students

This is the required starting point in Lab 1.

- [x] Sign in to Azure for Students with the university student email — recorded
      without the email address.
- [x] Activate or verify the student subscription — recorded as available.
- [x] Enter the Azure portal — resource creation and policy correction recorded.
- [x] Locate Microsoft Foundry, a model catalogue, a playground, or a
      course-approved endpoint.
- [x] Record subscription status without exposing identifiers or credentials.
- [x] Record region.
- [ ] Record available credit at the time checked.
- [x] Record selected model/deployment name.
- [x] Record the access method.
- [ ] Capture a playground screenshot with all secrets and personal identifiers
      excluded or redacted.

Current state: **PARTIAL / USER_EVIDENCE_REQUIRED**. The private record covers
account route, subscription status, allowed region, Foundry resources,
deployment and access route. Azure credit and a redacted screenshot remain
missing; no current live account state was rechecked on 2026-08-24.

### 2.2 At least one AI coding assistant

Choose and configure at least one of the official options: OpenAI Codex,
Continue, or GitHub Copilot.

| Evidence field | Record after the real setup |
|---|---|
| Assistant selected | OpenAI Codex desktop app — locally recorded |
| IDE / CLI and version | Codex desktop app; exact version `MISSING` |
| Extension / assistant version | `MISSING` |
| Sign-in method (never a credential) | Existing ChatGPT/Codex account session — locally recorded |
| Model or access route | Codex desktop app with browser control — locally recorded |
| Exact prompt used | Azure resource/prompt/script work described, but exact Codex prompt `MISSING` |
| Output/diff reviewed | Resource names, policy, deployment state, prompts, model outputs and script handling recorded as reviewed |
| One issue checked, corrected, or rejected | Default `East US` rejected after `RequestDisallowedByAzure`; allowed `Japan West` selected |
| Human reviewer and date | Record dated 2026-08-12; named human review/sign-off `MISSING` |

The private record closes only the listed local facts. Exact client/version and
prompt metadata, named human review/sign-off, second-person verification, and
any tutor-required evidence remain open.

## 3. Required model exploration

### 3.1 First run

In Azure playground or another instructor-approved model interface, run this
exact prompt:

> Explain in no more than 120 words how generative AI could assist with
> wind-turbine monitoring without replacing the responsible engineer.

Record:

- exact model/deployment ID;
- interface/access route;
- region where relevant;
- system prompt, temperature, top-p, maximum output/token limit, seed, and other
  visible settings (use `not exposed` rather than guessing);
- date/time and timezone;
- exact output; and
- a screenshot with no secrets.

### 3.2 Controlled second run

Change **only the target audience**, rerun, and record:

- the exact changed prompt;
- confirmation that model/deployment and all visible settings stayed constant;
- exact second output; and
- observed differences in terminology, explanation depth, examples, caution,
  and length.

Do not claim that audience caused every difference if the interface does not
offer deterministic generation. Record that limitation.

Automation cannot log into Azure. For the required rerun, keep the **exact**
Run 2 prompt and the same model/settings, paste the new Playground output into
a local text file, and check:

```bash
python scripts/count_lab1_words.py path/to/run2.txt
```

The command prints the whitespace-delimited word count and exits `1` if the
count is above 120. Do not file a generated substitute as the Lab 1 output.

### 3.3 Comparison record

| Field | Run 1 | Run 2 |
|---|---|---|
| Model/deployment | `gpt-oss-120b` / Global Standard, locally recorded | same, locally recorded |
| Target audience | default prompt wording | non-technical wind-farm manager |
| Other settings | locally recorded in private record | record states unchanged; no corroborating screenshot and no deterministic seed exposed |
| Exact output | retained in private record | retained in private record |
| Word count | `113` whitespace-delimited words in the retained private record | `143` whitespace-delimited words — exceeds `<=120` and requires rerun |
| Main observed change | n/a | less technical, more operational wording; locally recorded analysis |
| Screenshot | `MISSING` | `MISSING` |

## 4. Minimal approved-endpoint coding task

Use the configured coding assistant to create or explain a minimal Python script
that sends a prompt to an approved endpoint.

### Safety and reproducibility checklist

- [ ] Endpoint is instructor-approved and uses the required secure protocol —
      HTTPS is used, but instructor approval was not retained.
- [x] API key/token is read from an environment variable or approved secret
      store, never hard-coded.
- [x] Targeted text audit found no credential value in the source or retained
      record; screenshots remain absent.
- [x] Model/deployment, endpoint shape, timeout, and relevant settings are
      explicit.
- [ ] Request and response formats require final provider/course review.
- [x] Network/provider exceptions are handled without publishing a false
      success.
- [ ] Named human review/sign-off for the resource choices and source is missing;
      the retained record describes one correction but is not a signed review.
- [x] At least one issue checked, corrected, or rejected is recorded.
- [ ] Only non-confidential, non-secure-assessment test content is sent.

The existing `OpenAICompatibleModelGateway` may be explained as an example of a
narrow HTTPS boundary, but it does not prove the Lab 1 endpoint task ran. No live
provider, credential, deployment, or successful response is claimed here.

### Manual review record

```text
Date/time and reviewer:
Coding assistant, client/version, model/access route:
Exact prompt:
Generated file or explanation:
Approved endpoint/provider documentation checked:
Credential-handling method:
Commands/diff reviewed before execution:
Issue identified:
Correction or rejection:
Run command and exit status:
Redacted evidence location:
Remaining limitation:
```

## 5. Evidence retention layout

Keep account and screenshot evidence in a private course location, not the
public product repository. A suggested private record is:

```text
ELEC5623_Lab1_Private/
  group-registration-record
  environment-checklist
  azure-redacted-screenshot
  model-run-1-settings-and-output
  model-run-2-settings-and-output
  coding-assistant-version-and-interaction
  manual-review-record
```

The labels describe evidence categories, not files created by Codex. Follow any
official filename or submission-location rule once known.

## 6. Lab 1 completion checklist

### Part A

- [ ] Canvas group-size rule checked live.
- [ ] Group of no more than five formed and registered.
- [ ] Actual group number, names, and SIDs recorded privately.
- [x] Proposal brief saved and reviewed.
- [ ] Track B idea agreed by the actual group.
- [ ] One-minute pitch understood by every member.
- [ ] Initial idea discussed with lab tutor; questions/next steps retained.

### Part B

- [x] Azure for Students subscription activated or verified in the dated local record.
- [ ] Subscription status, region, credit, model/deployment, and access route
  recorded — all except credit are present.
- [ ] Secret-free playground screenshot retained.
- [x] At least one official AI coding assistant configured — Codex locally recorded.
- [ ] IDE/CLI, assistant version, sign-in method, and model/access route recorded.
- [ ] Exact wind-turbine prompt run in an instructor-approved interface — local
      Playground run exists; instructor approval evidence and screenshots are missing.
- [ ] Exact model/deployment, settings, output, and secret-free screenshot kept —
      textual facts exist; screenshots are missing.
- [ ] Only target audience changed for run two; difference analysed — process is
      recorded, but Run 2 exceeds 120 words and must be repeated.
- [ ] Minimal endpoint script is created/explained, but named human review/sign-off
      and the course decision on successful live API execution remain open.
- [x] At least one generated issue checked, corrected, or rejected and recorded.
- [x] No confidential or secure-assessment data is present in the retained record/script.

### Handoff

- [x] Existing textual environment evidence is private and locatable by absolute
      path; screenshots and the remaining fields are still missing.
- [x] Material AI use and the 2026-08-24 evidence reconciliation are appended to
      `AI_JOURNAL.md`.
- [ ] Any tutor-required correction is mapped into the Proposal and matrix.
- [x] No unchecked item is described as complete by this pack.

## 7. Completion record

```text
Lab/date/tutor:
Group registration evidence:
Part A completed by:
Part B completed individually or in pair with:
Azure evidence location:
Coding-assistant evidence location:
Model exploration evidence location:
Manual correction/rejection evidence:
Tutor questions or follow-up:
Incomplete items and owner:
Second-person verification:
```

Current completion state remains **PARTIAL / USER_ACTION_REQUIRED** until the
account-dependent and in-person items above have real evidence.
