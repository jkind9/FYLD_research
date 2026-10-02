# FYLD scene-mapping research

This repository studies whether phone captures can produce useful, measurable maps of visible work areas and identify distinct objects across repeated views. Work is organised into six independent experiments so each stage can be tested before connecting the pipeline.

Start with the [experiment plan](experiments/README.md). It explains the six pieces, their inputs and outputs, independent controls and the role of the Samsung S23 and Redmi Note 11 Pro. The [dataset guide](experiments/datasets/README.md) explains how to test the later stages without phone capture. The [task list](task_list/README.md) records priorities and completion evidence.

The [research reading guide](research/sources/README.md) links the individual source summaries covering phone depth, reconstruction, tracking, evaluation datasets and construction-site use.

The [background explanation](research/sources/00_start_here.md) introduces the pipeline. The [research index](research/README.md) links the comparison table, bibliography, dataset catalogue and permission checks.

The [Task 00 prototype](archive/task00_prototype/README.md) preserves preliminary desktop runs and their limitations. [Shared src](src/README.md) is ready to build incrementally. No experiment has yet established performance on either phone or on construction sites.

The active folders are `experiments/`, `research/`, `src/`, `data/` and `task_list/`. `archive/` holds earlier work. Local virtual environments and fetched reference repositories are ignored runtime resources.

## Starting point

Verify geometry conventions in task 03, then test reconstruction with supplied depth and camera poses in task 04. Check camera access on both phones alongside that work in task 08. Task 09 adds object recognition and persistent identities, so returning to an object does not automatically increase its count. Tracking remains independently testable in task 05; estimated poses and depth replace reference inputs one at a time.

The first intended result is a measured reconstruction with a verifiable object inventory. No phone performance or construction-site accuracy has been established. Processing placement remains a comparison between the phone, a local edge computer and a backend.

## Repository contents

Git includes research summaries, plans, task receipts, first-party source and tests, and dataset acquisition/calibration records. Raw datasets, downloaded reference repositories, model weights, virtual environments, caches, generated geometry and raw assistant transcripts remain local. The historical prototype is retained as an archive, with unfinished validation stated explicitly.

A fresh clone does not contain benchmark images or reference surfaces. Follow [dataset acquisition and verification](data/README.md) before running data-dependent work. Environment observations in the archive are historical records, not a current installation guarantee. Raw session evidence referenced by the recovery review is also local-only; the reviewed summaries and source inventory are included.
