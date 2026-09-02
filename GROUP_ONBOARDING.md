# Group onboarding / 组员必读

Read this first. Product names below stay in English.

先读本文。产品正式名、仓库名、命令、FR 编号保持英文。

## What this product is / 这是什么

Public product: **Model Effectiveness Evaluation Workbench**.

Inner engine: **Inspector** (FR-01–15). Compare shell: FR-16–18. **One product, one repo**, not two.

On the same evidence-backed task it runs at least two named models, then reports **quality**, **task fit**, **latency**, and **estimated cost** separately, and contrasts min-cost versus quality/task-fit selection. Human review remains the only automated success state (`READY_FOR_HUMAN_REVIEW`). There is no combined “effectiveness” score and **no auto model-deploy**.

Inspector 接收英文 JSON bundle（requirements + evidence + AI Markdown），切分 claims、检索本地证据、判定支持关系、核对精确引用、映射需求、计算透明指标，并生成不可变 run 供人工审核。

This is **ELEC5623 Track B** coursework, not a public product.

**Do not claim ESIPS P3 complete.** Constantinople / ESIPS Pound-for-Pound is related course evaluation practice, not a completed claim of this repo.

## Repo / 仓库与克隆

- **GitHub (public):** https://github.com/hanzhengyu202305-arch/elec5623-workbench
- **Clone URL:** `https://github.com/hanzhengyu202305-arch/elec5623-workbench.git`
- **Local source of truth (Zhengyu):** `/Users/hanzhengyu/Documents/study/projects/ELEC5623/evidence-inspector`
- **Default branch:** `main`
- **Visibility:** public. Anyone with the URL can clone/read; collaborator invites are optional.

Clone:

```bash
git clone https://github.com/hanzhengyu202305-arch/elec5623-workbench.git
cd elec5623-workbench
```

### Where NOT to look / 不要去这里找产品

Cursor dump `/Users/hanzhengyu/5623` is **course PDFs / Canvas dumps**, not the product. Do not treat it as the assignment repo. Lecture PDFs, Lab 03/04, and week5 mp4 are **not** this Workbench.

## Quick start / 本地运行

**Python 3.11 only** (`>=3.11,<3.12`). Other versions are not an acceptance environment.

```bash
python3.11 -m venv .venv
. .venv/bin/activate
python -m pip install -e '.[dev]'
bash scripts/run_workbench_demo.sh
```

`runs/` and `acceptance/` stay local (gitignored). Do not commit them.

More commands: see `README.md`.

## Track B / Canvas / GroupXX PDF

- Track B. Tutor **written approval** is required **before** any Canvas upload.
- **Do not upload** the `GroupXX` PDF to Canvas.
- The blocked draft is `output/pdf/ELEC5623_GroupXX_Proposal_DRAFT_NOT_FOR_SUBMISSION.pdf`. Filename means what it says: **DRAFT, NOT FOR SUBMISSION**.
- Do not send the tutor email from this repository. Do not invent approval wording.

## Slot A–E FR split / 五人分组（仍共有整份 Proposal）

Official Proposal minimum: at least three FRs per person. Neutral five-person draft:

| Slot | Primary FRs |
|------|-------------|
| A | FR-01–03 (schema and segmentation) |
| B | FR-04–06 (retrieval and classification) |
| C | FR-07–09 (citations and quotations) |
| D | FR-10–12 (mapping and metrics) |
| E | FR-13–18 (artifacts, interfaces, Workbench compare) |

**Everyone still owns the whole proposal.** Primary slots do not remove shared responsibility for integration, tests, report accuracy, demo, and academic integrity. Member names remain `UNCONFIRMED` until the group actually agrees.

Details: `docs/REQUIREMENTS.md`, `TEAM_FORMATION_PITCH_PACK.md`.

## Human gates still open / 仍未关闭的人工关卡

Automation cannot close these:

- Whole-group agreement on the Workbench direction
- Tutor written approval of multi-model effectiveness comparison
- Real Canvas group number and confirmed members
- Canvas upload (only after written approval)
- Lab 1 remaining evidence, Lab 2 execution, Week 3/4 oral results

Keep `GroupXX` and empty approval quotes until those facts exist. See `STATUS.md` and `TUTOR_APPROVAL_PACK.md`.

## Collaborator invites (optional) / 协作者邀请（可选）

The repo is **public**: anyone with the URL can clone/read. Collaborator invites are optional (for write access or GitHub notifications).

If you still want to add a collaborator (replace `USERNAME`; do **not** invent handles):

```bash
gh api -X PUT repos/hanzhengyu202305-arch/elec5623-workbench/collaborators/USERNAME -f permission=pull
```

## Core files to read next / 建议接着读

| File | Why |
|------|-----|
| `README.md` | Product, install, CLI/API |
| `STATUS.md` | Verified gates vs still-blocked humans |
| `docs/REQUIREMENTS.md` | FR-01–18 |
| `docs/NFR_CONSTRAINTS.md` | NFRs |
| `docs/ARCHITECTURE.md` | Workbench + Inspector |
| `docs/TRACEABILITY.md` | FR/NFR → code/tests |
| `PROPOSAL_DRAFT.md` | Official 12-section working draft |
| `PROPOSAL_CANDIDATE_NOT_FOR_SUBMISSION.md` | Compressed blocked candidate |
| `TUTOR_APPROVAL_PACK.md` | Tutor checklist (do not send from repo) |
| `WEEK3_ORAL_PROGRESS_CHECK_PACK.md` | Week 3 oral |
| `TEAM_FORMATION_PITCH_PACK.md` | Pitch + Slot A–E |
| `PRIOR_WORK_DISCLOSURE.md` | Independent coursework disclosure |
| `ASSIGNMENT_REQUIREMENTS_MATRIX.md` | Brief vs repo |
| `AI_JOURNAL.md` | AI-use log |
| `scripts/run_workbench_demo.sh` | One-command demo |
| `scripts/count_lab1_words.py` | Lab 1 word count |

## What this GitHub repo does not contain / 本仓库故意不包含

- Course lecture PDFs, Lab 03/04, week5 mp4, Canvas dumps
- Azure endpoints, keys, screenshots (`lab01_azure_record.md` and similar)
- `.venv/`, `runs/`, `acceptance/`, secrets
- The Cursor dump at `/Users/hanzhengyu/5623`
