# Lab 2 completion pack

Status: **official-looking local course files ingested; practical completion
unknown and no run result claimed**  
Source review date: `2026-08-30`  
Student action mode: Part A group; Part B individual or pairs

## Source identities

- Lab 2 PDF:
  `/Users/hanzhengyu/Downloads/ELEC5623_Lab_02.pdf`, SHA-256
  `200e7f06e3504f9d48ac66ee18fb9af3ca146051942f5d5cab85e6150861b641`,
  nine pages, revised-v5 title metadata.
- Companion notebook:
  `/Users/hanzhengyu/Downloads/ELEC5623_Lab_02_LoRA.ipynb`, SHA-256
  `3019e28a2eed5ca7710fe63285e1b3ce3adf68cd20c5c0e9f7223ac790a31db7`,
  19 cells, zero executed cells, zero stored outputs.

Both files were read without execution. Their content and layout were checked,
but the current live Canvas file versions were not re-authenticated in this
run. Do not replace these facts with an assumed submission or completion state.

## Part A - oral and Proposal checkpoint

The source says the early-feedback oral begins five minutes after the lab
starts, groups are called one at a time, each check takes approximately 5-10
minutes, and every member must attend and be ready for questions. The focus is
the Business Proposal: problem, target users, GenAI role, feasibility, current
progress, and next steps. It remains an ungraded early-feedback activity.

Local preparation now includes:

- measurable FR/NFR/acceptance wording;
- one complete written use case;
- an architecture boundary naming users, interfaces, services, stores,
  external systems, AI controls, deployment, logging, and human oversight; and
- bounded business/product analysis that separates evidence from assumptions.

No attendance, contribution, tutor feedback, scope decision, or approval is
available locally. See `WEEK3_ORAL_PROGRESS_CHECK_PACK.md` and
`TUTOR_APPROVAL_PACK.md`.

## Part B - LoRA practical

The provided notebook is designed to:

1. create and verify 48 fictional maintenance-triage records split into 32
   training, eight validation, and eight frozen test cases;
2. record runtime versions, seed, device, and dataset/test fingerprints;
3. evaluate the unchanged `Qwen/Qwen2.5-0.5B-Instruct` baseline;
4. train a LoRA adapter with `r=8`, `lora_alpha=16`, dropout `0.05`, and
   `q_proj`/`v_proj` targets;
5. re-evaluate the same frozen test prompts and compute JSON/task metrics; and
6. retain a manual safety review plus reproducibility evidence.

The source recommends a Colab T4 GPU for the full run. Its CPU branch is only a
two-step dry run. This automation did not install the notebook dependencies,
download a model, use Colab, access an account, or execute any cell.

## Evidence that must be retained privately

- adapter and tokenizer configuration;
- environment, package versions, seed, device/GPU and timing;
- dataset and frozen-test fingerprints;
- trainer logs and configuration;
- unchanged baseline and tuned outputs;
- JSON metric table and comparison rows;
- completed manual safety review with reviewer/date/evidence;
- evidence ZIP and its hash; and
- whether the run was a T4 experiment or CPU dry run.

Automated JSON/category/priority metrics are not a safety certification. Do not
claim improvement unless the retained baseline/tuned evidence supports the
exact metric, and retain regressions or failed cases rather than hiding them.

## Completion gate

```text
Lab/date/tutor:
Part A attendance and feedback evidence:
Part B completed by:
Runtime/device:
Notebook source hash:
Evidence ZIP path and hash:
Baseline/tuned metric summary:
Manual safety reviewer/date:
Failures or regressions retained:
Second-person verification:
```

Current state: `COMPLETION_UNKNOWN / USER_ACTION_REQUIRED`.
