---
id: "137"
title: Refactor phases 0-1: package skeleton, TUM fixture and golden outputs
status: done
files:
  - pyproject.toml
  - uv.lock
  - pytest.ini
  - .gitignore
  - sitescan/__init__.py
  - tests/golden/run.py
  - tests/golden/test_golden.py
  - tests/fixtures/README.md
  - tests/fixtures/build.py
  - models/manifest.toml
  - DESIGN.md
  - sitescan/cleanup/__init__.py
  - sitescan/objects/__init__.py
  - sitescan/scale/__init__.py
  - sitescan/depth/__init__.py
  - sitescan/pipelines/__init__.py
  - sitescan/fusion/__init__.py
  - sitescan/session/__init__.py
  - sitescan/mapping/__init__.py
  - tests/golden/__init__.py
created: 2026-11-09
---
# Refactor phases 0-1: package skeleton, TUM fixture and golden outputs

## Goal

Save today's outputs on a committed 20-frame TUM fixture and the full 15 October room before any stage moves

## Plan

1. Record decisions (sitescan, uv, scale, v2) and baseline commit d859867. 2. pyproject, uv lock, empty stage folders. 3. Build the 20-frame TUM desk stand-in fixture. 4. Golden runner for room and live (sync, no objects); save outputs; golden test lane. 5. Full 15 October room baseline. 6. Model manifest with hashes; DESIGN status.

## Files

- .gitignore (+6 -0, 115 lines)
- DESIGN.md (+5 -1, 694 lines)
- models/manifest.toml (+23 -0, 23 lines)
- pyproject.toml (+57 -0, 57 lines)
- pytest.ini (+4 -2, 7 lines)
- sitescan/__init__.py (+1 -0, 1 lines)
- sitescan/cleanup/__init__.py (+1 -0, 1 lines)
- sitescan/depth/__init__.py (+1 -0, 1 lines)
- sitescan/fusion/__init__.py (+1 -0, 1 lines)
- sitescan/mapping/__init__.py (+1 -0, 1 lines)
- sitescan/objects/__init__.py (+1 -0, 1 lines)
- sitescan/pipelines/__init__.py (+1 -0, 1 lines)
- sitescan/scale/__init__.py (+1 -0, 1 lines)
- sitescan/session/__init__.py (+1 -0, 1 lines)
- tests/fixtures/README.md (+39 -0, 39 lines)
- tests/fixtures/build.py (+69 -0, 69 lines)
- tests/fixtures/tum_desk_20/cam0/000000.png (+0 -0, 0 lines)
- tests/fixtures/tum_desk_20/cam0/000001.png (+0 -0, 0 lines)
- tests/fixtures/tum_desk_20/cam0/000002.png (+0 -0, 0 lines)
- tests/fixtures/tum_desk_20/cam0/000003.png (+0 -0, 0 lines)
- tests/fixtures/tum_desk_20/cam0/000004.png (+0 -0, 0 lines)
- tests/fixtures/tum_desk_20/cam0/000005.png (+0 -0, 0 lines)
- tests/fixtures/tum_desk_20/cam0/000006.png (+0 -0, 0 lines)
- tests/fixtures/tum_desk_20/cam0/000007.png (+0 -0, 0 lines)
- tests/fixtures/tum_desk_20/cam0/000008.png (+0 -0, 0 lines)
- tests/fixtures/tum_desk_20/cam0/000009.png (+0 -0, 0 lines)
- tests/fixtures/tum_desk_20/cam0/000010.png (+0 -0, 0 lines)
- tests/fixtures/tum_desk_20/cam0/000011.png (+0 -0, 0 lines)
- tests/fixtures/tum_desk_20/cam0/000012.png (+0 -0, 0 lines)
- tests/fixtures/tum_desk_20/cam0/000013.png (+0 -0, 0 lines)
- tests/fixtures/tum_desk_20/cam0/000014.png (+0 -0, 0 lines)
- tests/fixtures/tum_desk_20/cam0/000015.png (+0 -0, 0 lines)
- tests/fixtures/tum_desk_20/cam0/000016.png (+0 -0, 0 lines)
- tests/fixtures/tum_desk_20/cam0/000017.png (+0 -0, 0 lines)
- tests/fixtures/tum_desk_20/cam0/000018.png (+0 -0, 0 lines)
- tests/fixtures/tum_desk_20/cam0/000019.png (+0 -0, 0 lines)
- tests/fixtures/tum_desk_20/depth/000000.bin (+0 -0, 0 lines)
- tests/fixtures/tum_desk_20/depth/000003.bin (+0 -0, 0 lines)
- tests/fixtures/tum_desk_20/depth/000006.bin (+0 -0, 0 lines)
- tests/fixtures/tum_desk_20/depth/000009.bin (+0 -0, 0 lines)
- tests/fixtures/tum_desk_20/depth/000012.bin (+0 -0, 0 lines)
- tests/fixtures/tum_desk_20/depth/000015.bin (+0 -0, 0 lines)
- tests/fixtures/tum_desk_20/depth/000018.bin (+0 -0, 0 lines)
- tests/fixtures/tum_desk_20/frames.jsonl (+20 -0, 20 lines)
- tests/fixtures/tum_desk_20/frames/000000.jpg (+0 -0, 0 lines)
- tests/fixtures/tum_desk_20/frames/000001.jpg (+0 -0, 0 lines)
- tests/fixtures/tum_desk_20/frames/000002.jpg (+0 -0, 0 lines)
- tests/fixtures/tum_desk_20/frames/000003.jpg (+0 -0, 0 lines)
- tests/fixtures/tum_desk_20/frames/000004.jpg (+0 -0, 0 lines)
- tests/fixtures/tum_desk_20/frames/000005.jpg (+0 -0, 0 lines)
- tests/fixtures/tum_desk_20/frames/000006.jpg (+0 -0, 0 lines)
- tests/fixtures/tum_desk_20/frames/000007.jpg (+0 -0, 0 lines)
- tests/fixtures/tum_desk_20/frames/000008.jpg (+0 -0, 0 lines)
- tests/fixtures/tum_desk_20/frames/000009.jpg (+0 -0, 0 lines)
- tests/fixtures/tum_desk_20/frames/000010.jpg (+0 -0, 0 lines)
- tests/fixtures/tum_desk_20/frames/000011.jpg (+0 -0, 0 lines)
- tests/fixtures/tum_desk_20/frames/000012.jpg (+0 -0, 0 lines)
- tests/fixtures/tum_desk_20/frames/000013.jpg (+0 -0, 0 lines)
- tests/fixtures/tum_desk_20/frames/000014.jpg (+0 -0, 0 lines)
- tests/fixtures/tum_desk_20/frames/000015.jpg (+0 -0, 0 lines)
- tests/fixtures/tum_desk_20/frames/000016.jpg (+0 -0, 0 lines)
- tests/fixtures/tum_desk_20/frames/000017.jpg (+0 -0, 0 lines)
- tests/fixtures/tum_desk_20/frames/000018.jpg (+0 -0, 0 lines)
- tests/fixtures/tum_desk_20/frames/000019.jpg (+0 -0, 0 lines)
- tests/fixtures/tum_desk_20/session.json (+12 -0, 12 lines)
- tests/fixtures/tum_desk_20_golden.json (+407 -0, 407 lines)
- tests/golden/run.py (+62 -0, 62 lines)
- tests/golden/test_golden.py (+52 -0, 52 lines)
- uv.lock (+1497 -0, 1497 lines)

## Checked

- `python -B -m pytest -q -> 992 passed, 7 skipped, 3 deselected (golden); pytest -m golden tests/golden -> 3 passed in the system env and in .venv-sitescan built from uv.lock; ruff on tests and sitescan -> clean; room_build on the full 15 October walk -> 676,855 raw, 554,067 kept, map 6.35 x 3.30 m, identical to the Task126 baseline`
- cost: 14 min from begin to finish; Claude tokens 4,265,281 (fresh input 173,638, cache read 4,069,910, output 21,733; 1 session)
- new duplicate blocks: 0
- complexity share (functions over 10): 0 (was n/a (no functions))
- dead code on added lines: not checked (vulture not installed)
- prose patterns: 0 in 567 words

## Left over

Phase 2 not started: no stage moved. Not done: local 20-frame slice of the 15 October walk (mid-walk cut loses earlier anchors); live replay of the full walk with objects (needs .venv-yolo); decisions 2 and 4 in DESIGN section 13.
