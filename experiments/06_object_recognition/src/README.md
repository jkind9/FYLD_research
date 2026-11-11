# Identity store

This folder holds the database that records which object ID each checked observation received. It belongs to [experiment 06, object recognition](../README.md).

| File | What it does |
|---|---|
| `identity_store.py` | `IdentityStore(database_path)` keeps objects and observations in an SQLite file. `record_observation(...)` stores one decision, which is `new`, `matched` or `unresolved`, and returns an `ObservationResult`. `count_objects(...)` and `count_observations(...)` give totals. `IdentityStoreError` is raised for any request that breaks the rules. |

The store enforces these rules:

- A `new` decision needs a non-empty label. A `matched` decision needs an object ID and no label. An `unresolved` decision has neither.
- Each call is one atomic write. Sending the same session, source and observation key again with the same payload returns the stored result. The same key with a different payload or decision raises an error.
- A `matched` observation must belong to an object in the same session, world and segment, so objects from different coordinate worlds never merge.

`04_geometry_identity/persistence.py` uses the store, loading it with `importlib.import_module("identity_store")`, so this folder must be on the import path. `tests/test_identity_store.py` in the parent folder tests it.

## How to run it

There is no command line. Run its tests from the repository root:

```text
.venv/Scripts/python.exe -B -m pytest experiments/06_object_recognition/tests/test_identity_store.py -p no:cacheprovider
```

## Where results are recorded

The store's role in the identity chain is described in the [experiment 06 README](../README.md).
