---
id: "86"
title: ARCore terms check and open-source replacement map
status: done
files:
  - README.md
  - research/phone_ar_platforms/arcore_commercial_terms.md
  - research/phone_ar_platforms/arcore_open_replacement.md
  - research/phone_ar_platforms/README.md
  - learning/11_inside_arcore.md
created: 2026-10-14
---
# ARCore terms check and open-source replacement map

## Goal

Know exactly what ARCore's terms require and which open-source parts could replace each ARCore function, with verified licences, in the project README

## Plan

1. Read the four governing documents clause by clause. 2. Check licences of candidate replacement components from their repositories. 3. Write the replacement map and the split plan (ARCore stream, open stream) into the README, research and learning. 4. Draft next-session prompts.

## Files

- README.md (+49 -10, 399 lines)
- learning/11_inside_arcore.md (+4 -0, 118 lines)
- research/phone_ar_platforms/README.md (+1 -0, 26 lines)
- research/phone_ar_platforms/arcore_commercial_terms.md (+23 -0, 52 lines)
- research/phone_ar_platforms/arcore_open_replacement.md (+46 -0, 46 lines)

## Checked

- `licences read from each project's licence file or GitHub record (22 projects); link check over README and the new notes -> all links resolve`
- cost: 4 min from begin to finish; Claude tokens 7,474,650 (fresh input 32,414, cache read 7,423,764, output 18,472; 1 session)
- new duplicate blocks: 0
- complexity share (functions over 10): n/a (no functions) (was n/a (no functions))
- dead code on added lines: 0
- prose patterns: 1 in 1400 words: bold-labels "5 items"

## Left over

Legal review of ARCore terms and a patent check before launch (owner); Stream A and Stream B sessions
