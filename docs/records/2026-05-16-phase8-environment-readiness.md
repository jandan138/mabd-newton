# Phase 8 Environment Readiness Record

Date: 2026-05-16

## Scope

Phase 8 makes the cloned M-ABD Newton environment auditable and
machine-checkable. It does not install dependencies, mutate the reference
project environment, mutate the ambient DSW Python, or modify the vendored
Newton source tree.

This record is environment evidence only. It does not verify M-ABD solver
behavior, method correctness, scene dynamics, contact, timing, comparative
baselines, rendered outputs, or paper experiments.

## Source And Environment

- repo base commit: `e13529d`
- plan commit: `d5dc58a`
- implementation commit: `d038a75`
- review hardening commit: `b1297d7`
- reference project: `/cpfs/user/zhuzihou/dev/physics-primitive-agent`
- reference environment:
  `/cpfs/user/zhuzihou/conda-managed/envs/physics-primitive-newton-py310`
- cloned M-ABD environment:
  `/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310`
- canonical Python:
  `/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python`
- vendored Newton import path required:
  `vendor/newton/newton/__init__.py`

## TDD Evidence

RED command:

```bash
PYTHONPATH=src:vendor/newton \
  /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python \
  -m unittest tests.test_environment_readiness
```

RED result:

```text
ModuleNotFoundError: No module named 'mabd_reproduction.environment'
FAILED (errors=1)
```

Focused GREEN command:

```bash
PYTHONPATH=src:vendor/newton \
  /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python \
  -m unittest tests.test_environment_readiness
```

Focused GREEN result:

```text
Ran 5 tests in 5.671s
OK
```

## Readiness Contract

The readiness command:

```bash
PYTHONPATH=src:vendor/newton \
  /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python \
  scripts/env/readiness_check.py
```

Required checks:

- interpreter exists under the cloned M-ABD env root;
- interpreter is not under the reference
  `physics-primitive-newton-py310` environment;
- interpreter is not the ambient `/usr/bin` or Isaac/DSW Python;
- `newton` imports from this repository's `vendor/newton` tree;
- required runtime packages `yaml` and `warp` import;
- optional JSON output is written only under caller-selected output paths.

Generated readiness reports belong under
`reports/generated/environment-readiness/local/` and are not committed.

## Implementation Verification

Commands run before the implementation commit:

```bash
/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check src/mabd_reproduction/environment.py scripts/env/readiness_check.py tests/test_environment_readiness.py tests/test_phase0_bootstrap.py scripts/validate_docs.py
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/env/readiness_check.py
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_environment_readiness tests.test_phase0_bootstrap
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests
git diff --check
```

Observed results:

```text
ruff: All checks passed!
readiness: "status": "smoke_passed"
docs: Phase 0/1/2/3/4/5/6/7/8 docs/provenance validation passed
focused tests: Ran 16 tests in 13.760s, OK
full tests: Ran 67 tests in 13.577s, OK
git diff --check: exit 0
```

Docs validation after backfilling the implementation commit:

```text
Phase 0/1/2/3/4/5/6/7/8 docs/provenance validation passed
```

Required status: all commands exit `0`, readiness JSON reports `status:
smoke_passed`, and docs validation prints
`Phase 0/1/2/3/4/5/6/7/8 docs/provenance validation passed`.

## Review Hardening

Independent review found two readiness false positives:

- `scripts/env/readiness_check.py` could be launched by ambient Python while
  probing the canonical cloned Python and still report `smoke_passed`.
- required packages were only checked for importability, so project-local
  `yaml.py` or `warp.py` shadows could satisfy the gate.

Hardening added regression tests and implementation checks that:

- the current `sys.executable` resolves to the same cloned environment Python
  as the probe interpreter;
- ambient and reference current interpreters fail with `configuration_error`;
- required package module paths must resolve under the cloned env root;
- project-root package shadows are classified as `shadowed` and force
  `dependency_gap`.

Focused review-hardening command:

```bash
PYTHONPATH=src:vendor/newton \
  /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python \
  -m unittest tests.test_environment_readiness
```

Focused review-hardening result:

```text
Ran 7 tests in 6.140s
OK
```

Review-hardening verification:

```text
ruff: All checks passed!
readiness: "status": "smoke_passed"; package paths from cloned env
docs: Phase 0/1/2/3/4/5/6/7/8 docs/provenance validation passed
focused tests: Ran 18 tests in 14.293s, OK
full tests: Ran 69 tests in 13.893s, OK
git diff --check: exit 0
```

## Claim Impact

No `paper-claims.yaml` method or experiment claim changes in this phase. The
claim-boundary update is limited to environment readiness evidence and explicit
non-claims.
