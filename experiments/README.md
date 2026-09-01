# Experiments

File-based experiment records (docs/21). One directory per run:

```
EXP-YYYYMMDD-NNN-<slug>/
    experiment.json   # the docs/21 §7 record (hypothesis, dataset@version +
                      # content_hash, code_commit, config incl. the FULL fill
                      # model and equity convention, metrics, artifacts)
    equity.csv        # mark-to-market equity per decision candle
```

## Artifact convention

- **Reference experiments** (baselines, validated candidates) commit their
  artifacts here: they are the comparison points and must survive as-is.
- **Exploratory runs** write OUTSIDE Git (any scratch directory): the replay
  engine is deterministic and fail-closed, so any run is exactly
  reproducible from `dataset_version` + `content_hash` + `code_commit` +
  `config`.
- Comparisons are only valid between runs whose `config.fill_model` records
  are identical — the fill model is part of the experiment, not a detail.

This convention will be formalized together with the `experiments` database
table in its own phase; until then the JSON record is the registry.
