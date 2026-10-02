---
id: "10"
title: Prepare research repository and publish initial main branch
status: closed
priority: MED
type: infra
blocked_by: []
blocks: []
verification_test: README.md
plan_reviewed: null
files:
  - .gitignore
  - .gitattributes
  - README.md
  - experiments/**/README.md
  - research/**/README.md
  - research/roadmap.md
  - data/README.md
  - archive/**/README.md
  - archive/task00_prototype/.github/workflows/cpu-tests.yml
  - archive/task00_prototype/pyproject.toml
  - research/papers.csv
  - research/session_recovery/source_urls.csv
  - task_list/**
docs:
  - README.md
  - task_list/README.md
created: 2026-10-02
last_updated: 2026-10-02
superseded_by: null
---

# Task 10: Prepare research repository and publish initial main branch

## In plain English

Record the agreed starting point and missing object-recognition work. Publish research, plans and first-party implementation as a Git repository. Leave local environments, downloaded data, caches and raw assistant logs out of the commit.

## What

Update task/experiment/research indexes. Initialise Git, configure the supplied origin, review files, commit and push main without overwriting remote history.

## Why

The workspace has 0 Git commits and the revised direction needs durable tasks. A clone should preserve provenance without disposable environments or dataset payloads.

## How

| Claim | Existing owner | Callers/consumers | Evidence |
|---|---|---|---|
| Environments and payloads already have ignore rules | Root ignore file | Git index | .gitignore:1 |
| Geometry/reconstruction plans exist | Task board | Implementation | task_list/README.md:17 |
| Revisit inventory is part of the brief | Edge review | Recognition plan | research/edge_products/README.md:3 |

1. Retain first-party source/tests, existing documents/plans and task receipts.
2. Add phone and recognition plans; prioritise geometry then supplied-input reconstruction.
3. Retain dataset JSON provenance; exclude raw data, outputs, environments, caches, vendor checkouts and session logs.
4. Review secrets, sizes, generated content, task board and links.
5. Commit and push main; verify remote commit equality.

## Invariants and recovery

No data/environment deletion is needed. Local artifacts remain available. Never force-push. Check remote history first; failed publication leaves the local commit intact for retry.

## Hyperparameters

hyperparameters n/a: repository preparation and plans only; no experiment runs.

## Verification

Before: 0 commits and no remote. Target: reviewed main commit, no generated payloads in the index, valid task links and matching origin/main SHA. Run task lint/audit and publication review. tests n/a: no executable changes; existing code remains historical/unmodified.

## Receipts

| Field | Value |
|---|---|
| Closing commit | a507ae7b04d21aecc5fdeb6be956e1e4b1afe6a2 (initial publication); this receipt is recorded in a subsequent documentation commit |
| Files changed | Plans, task board, research indexes, ignore/line-ending rules and publication notes; first-party executable source unchanged |
| Test status | Acquisition suite: 23 passed in 0.20 s using system Python and fresh Windows TEMP; task lint: 11 tasks, 0 errors/warnings |
| Before measurement | 0 Git commits; no remote |
| After measurement | 119 tracked files, 1,049,127 working-tree bytes at initial commit; main published and origin/main SHA verified equal |
| Delta | Added repository tracking and two implementation plans |
| Outcome | Passed: initial commit pushed with main tracking origin/main; remote SHA matched; no raw payloads, environments, caches, vendor checkouts or assistant logs tracked |

Security-reviewer and diff-reviewer were both invoked but failed at the account usage limit. Independent agent review is explicitly waived for this documentation/initial-publication task; no executable behaviour changed. Manual checks covered staged credential patterns, token-bearing URLs, file sizes, ignore rules, task states/dependencies and local Markdown links. No actual credentials were found; one coverage-badge URL was omitted from the published inventory. Task 09 still requires stateful plan/diff reviews when implemented.

The board audit's oversized-file findings refer to ignored third-party checkouts; those are excluded from the snapshot, so vendor refactoring is outside this task. The constitution remains an unratified draft. Acquisition tests failed under restricted temporary-directory permissions; all 23 passed in a fresh external TEMP directory without source edits. The incomplete archived prototype remains explicitly unvalidated.

No implementation follow-up is required to close this publication task. Tasks 03, 04, 05, 08 and 09 remain open research/implementation plans. Local caches and environments were excluded from Git, not deleted from the working machine.
