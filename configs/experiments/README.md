# Experiment Configs

Phase 6 introduces `paper_experiment_matrix.yaml` as the machine-checkable index
for every `experiment.*` paper claim. It records scene IDs, paper source lines,
known paper values, required lanes, asset IDs, metrics, blocking reasons, and
the intended output report path.

The matrix is infrastructure only. It does not verify scene dynamics, timing,
contact, or baseline results. Paper-missing values must be represented as
`unknown_in_source` or `not_applicable`.
