# Clean-environment fixture reproduction

## Scope

`scripts/run_clean_environment_reproduction.py` retains auditable evidence for
one narrow claim: a fresh Python 3.11 environment can be installed from the
current unchanged `uv.lock`, without network access, and can reproduce the
normalized report for `examples/sample_bundle.json` with the deterministic
`FixtureModelGateway`.

It does not call a real model provider, read an API credential, reuse the
project `.venv`, overwrite an earlier acceptance directory, or claim that the
draft corpus is frozen or tutor-approved.

## Preconditions

- The harness driver needs Python 3.11 or newer for the standard-library TOML
  parser. The environment being evaluated is separately required to be exactly
  Python 3.11 (`3.11.*`).
- `uv` must be on `PATH` and a local Python 3.11 interpreter must already be
  discoverable. `uv` is invoked with `--no-python-downloads`.
- In the default mode, all locked wheels and build requirements must already be
  present in the local `uv` cache. The harness never silently falls back to an
  index. An empty or incomplete cache is an expected hard failure.
- The `--work-root` path must not exist. Use a new timestamped path for every
  attempt, including attempts after a failure.

## Command

From the project root:

```bash
python3 scripts/run_clean_environment_reproduction.py \
  --work-root acceptance/clean-env-YYYYMMDD-HHMMSS
```

If the local cache is incomplete, dependency downloads require a separate,
auditable opt-in and a different new root:

```bash
python3 scripts/run_clean_environment_reproduction.py \
  --allow-dependency-downloads \
  --work-root acceptance/clean-env-public-pypi-YYYYMMDD-HHMMSS
```

That flag permits only a `--no-install-project` dependency-sync step to use the
public `https://pypi.org/simple` index. Every registry and artifact URL, size,
and SHA-256 entry in `uv.lock` is checked before the new root is created. The
project is then installed in a separate offline step. The flag does not pass
index credentials, enable a keyring, permit Python downloads, or select a
model-provider network path. The manifest uses a different scope string and
records that dependency network access was allowed.

The installation step is equivalent to a non-editable `uv sync` with
`--locked`, `--offline`, `--extra dev`, `--python 3.11`,
`--no-python-downloads`, disabled keyring/config discovery, and copy-only cache
linking. Default mode also supplies `--offline`. The copied lock hash is checked
again after installation. The child
environment is reduced to a small non-secret allowlist;
fixture mode and offline mode are forced even if the caller has provider or
index variables configured.

## Retained evidence

The new root contains:

- `checkout/`: the exact allowlisted source snapshot plus its fresh `.venv`;
- `logs/`: separate stdout and stderr for every bounded command;
- `evidence/installed-packages.json`: the installed distribution inventory;
- `evidence/fixture-reproducibility.json` and `fixture-runs/`: the two retained
  fixture runs used by the normalized comparison;
- `manifest.json`: hashes, commands, exit codes, Python and `uv` versions,
  fixture result, environment policy, and explicit limitations.

`manifest.json` is written as `PASS` only after the lock metadata, fresh
installation, Python 3.11 package-origin probe, CLI validation, and fixture
comparison all pass. The fixture gate also requires process isolation,
persisted-artifact verification, and identical input artifacts across the two
runs. A failure after the root is claimed writes a `FAIL`
manifest and exits non-zero. Existing roots are refused before modification.

The current-source retained checkpoint is
`acceptance/clean-env-offline-replay-20260804-v12/`. It used CPython `3.11.15`,
a non-editable install, forced offline/fixture mode, and no copied provider
credentials. All four bounded commands exited `0`; CLI validation included
segmentation, the no-claim gate, and exact all-or-none ground-truth alignment.
The two independent fixture runs retained the normalized report SHA-256
`37973bedb55ae695e82948752076548dba53aa68bd584d8c13dff3098ee691c1`;
both Markdown artifacts expose classification counts, complete detail for all
11 claims, and the append-only human-review target. The manifest SHA-256 is
`482aed6343ff29797b8774cdaa385cdbc30c7a5f7f45ace49d605d3b877134fb`.

## Limits of the evidence

This is an offline-cache reconstruction, not a vendored wheelhouse or a
clean-machine bootstrap. The command-level offline policy is explicit, but no
OS-level packet monitor or network namespace is used. The single synthetic
bundle does not prove corpus generalization, frozen-corpus metrics, production
performance, or live-provider behavior. Runtime, development, and build-backend
dependencies are lock-resolved: `hatchling==1.31.0` is exact-pinned in
`pyproject.toml`, included in the `dev` extra so it is represented in `uv.lock`,
and checked in the retained installed-package inventory. The replay still
depends on the local cache and therefore does not prove a blank-machine
bootstrap or the original provenance of cache contents beyond the lock's
official-PyPI URLs, sizes, and SHA-256 values.
