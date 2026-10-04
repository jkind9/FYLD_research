---
id: "26"
title: Export self contained shareable offline viewers
status: closed
priority: MED
type: infra
blocked_by: []
blocks: []
verification_test: experiments/shared/tests/test_share.py
plan_reviewed: 2026-10-03 PASS
files:
  - experiments/shared/share.py
  - experiments/shared/visualization.py
  - experiments/shared/tests/test_share.py
  - experiments/shared/tests/test_share_browser.py
docs:
  - experiments/shared/README.md
  - README.md
  - task_list/README.md
baseline_metric:
  source: experiments/shared/viewer.html:5
  field: portable interactive viewer files
  baseline_value: "0 self-contained shareable viewers"
  target: "2 standalone files: surface and camera; 0 external resource dependencies"
created: 2026-10-03
last_updated: 2026-10-03
superseded_by: null
---

# Task 26: Export self contained shareable offline viewers

## In plain English

Make a viewer that can be sent as one file and opened without the project. Include reduced-size pictures and the existing interactive scene. Preserve the original measurements and make clear that the shared pictures are display previews.

## What

Add a CPU-only export CLI and tests. Extract a reusable pure renderer from write_viewer and reuse the existing HTML/JavaScript assets without changing the drawing implementation. Export existing stage03 and stage04 inspected runs into sibling runs/shareable folders, outside each completed run.

## Why

Current HTML includes scene geometry and JavaScript, but images and provenance/review links are relative to the source run. Copying viewer.html alone loses these resources.

## How

### Reuse evidence

| Claim | Existing owner | Callers/consumers | Evidence |
|---|---|---|---|
| Viewer serialization already escapes embedded scene JSON | write_viewer | saved inspection | experiments/shared/visualization.py:139 |
| Projection and frame controls already work offline | viewer assets | browser | experiments/shared/viewer.js:1 |
| Source completion/hash validation exists | verify_run | exporter | experiments/shared/runs.py:59 |
| Atomic publication pattern exists | write_json | exported file | experiments/shared/runs.py:28 |

1. Test one-file export with a verified tiny fixture; copied-file browser test blocks all external resources and checks images, frame stepping, orbit/zoom/reference controls and console errors.
2. share.py reads the saved display scene from a complete verified run. Only use contained relative image paths included in its manifest. Embed resized RGB PNG previews as data URIs; preserve depth display colours using nearest-neighbour resizing. Set both image path and preview link to the embedded URI, with raw_label="Reduced display preview". Never embed raw depth/arrays or call thumbnails original raw measurements.
3. Preserve existing display geometry and sampling counts. Keep only the viewer scene fields and captions needed for inspection; omit raw artifact paths, roles inventories, machine paths, Git/source snapshots and dataset payloads. Embed source run identifier, manifest hash and explicit display conversion in the standalone page. Carry manifest-listed per-image legends into captions so independently scaled distance images remain interpretable; reject images that require a missing legend.
4. Extract render_viewer(scene) in visualization.py; normal write_viewer remains compatible. Exporter uses this renderer with embedded image paths and reduced-preview links, removes local review/provenance navigation, and adds a share notice. Escape all user-visible source/title text.
5. Validate output .html outside source. Build fully before same-directory temporary-file atomic replace; verify source again before publication. Source damage, missing images, path escape, invalid dimensions or write failures cannot publish success or damage an existing output. No numerical rerun, GPU or new point sampling.
6. Publish both existing inspected controls, measure bytes, and test moved copies with networking blocked. Update declared READMEs and task receipts; keep the remaining approved plan tasks unstarted.

## Invariants and recovery

| Producer/owner | Consumer | Representation | Survives restart? | Evidence |
|---|---|---|---|---|
| Verified completed run | exporter | manifest-listed scene and image artifacts; original hashes unchanged | yes | experiments/shared/runs.py:59 |
| Scene display geometry | standalone browser | unchanged XYZ/RGB, camera frusta, units, role captions and sample counts | embedded JSON | experiments/shared/visualization.py:139 |
| Exporter | recipient | one HTML with data-URI previews and inline drawing code | atomic published file | experiments/shared/runs.py:28 |

Source of truth is the verified source inventory. Output is a lossy display edition, not a numerical run. Export stays outside the source directory, including resolved symlink paths. Crash before replacement leaves old output intact and a disposable .part; failed ordinary calls clean their temporary files. Fresh deployment uses pinned shared requirements and acquired complete inspection runs. Recipient only needs a JavaScript-enabled browser; no server/network or repository. Normal viewers and completed runs remain readable.

## Hyperparameters

hyperparameters n/a: visual publication only; no inference, scoring or new geometry sampling. Inherit source display samples unchanged. Images use a documented 320-pixel maximum edge (the existing viewer's displayed image width, viewer.html:3), PNG output, nearest-neighbour resizing to avoid interpolating missing-depth colours. This display choice does not enter numerical measurements.

## Verification

Contract tests reject incomplete/tampered sources, escaped/absolute/missing image paths, invalid preview bounds and output inside source. Reduced images keep their aspect ratio and labels; decoded scene geometry equals the original. HTML escapes script-closing text and has 0 local/external href/src dependencies. Injected atomic replacement failure preserves previous output. Browser tests open a moved file with networking blocked, exercise controls and assert every image is loaded with 0 script errors. Changed implementation coverage at least 80%; shared and surface regression checks pass. Before 0, target 2 portable files.

## Receipts

| Field | Value |
|---|---|
| Closing commit | Implemented in working tree; no commit requested |
| Files changed | share.py; pure rendering extraction in visualization.py; test_share.py and test_share_browser.py; shared/root/task READMEs; standalone HTML exports outside original runs |
| Test status | 20 red-first tests failed for missing exporter; final shared/surface suite 102 passed; share.py and visualization.py each 95% statement coverage; Ruff and explicit-package-bases mypy pass; actual moved 9/30-frame files load all images offline with 0 errors/external requests |
| Before measurement | 0 self-contained shareable viewers |
| After measurement | 2 standalone viewers: surface 8,347,434 bytes, camera 12,758,417 bytes; 0 external dependencies; source run inventories still verify |
| Delta | +2 portable interactive viewers; 0 numerical reruns |
| Decision-gate outcome | PASS: plan review, Python review and finished-diff review; no unresolved findings or follow-ups |

Original source runs: surface 20261002T195928.219822Z_55d2d0bfa455453eb2289a5e717490c1 and camera 20261002T195923.778722Z_8bcaf965d8dc496192563205df59d85c. Outputs reside in their stage's ignored runs/shareable directory, outside each source run. A ZIP containing both HTML files was also created and its CRCs verified (13,909,157 bytes). Recipients can instead receive either individual HTML file.

Finished-diff finding DR-1 was fixed: independently scaled distance previews now include their source bounds, units and encoding; required missing legends reject publication. Python review also identified inherited placeholder substitution corruption; one-pass template substitution now preserves literal tokens in captions/title. Regression fixtures cover both. Reviewers re-read the final changes and returned PASS/Approve.

Windows sandbox-created pytest temporary directories were inaccessible. Tests and actual offline-browser checks passed through authorised execution with normal external temporary-directory access. No test caches were added to the repository. Existing dirty tracking code remained untouched. Task13 was explicitly handed off to Task26 with the journalled --take command and retains its unfinished full-sequence work after this task closes. The owner's preceding "all good" closes planning Task15 and approves the outline of Tasks16 to 25, while their numerical protocol and implementation reviews remain required.
