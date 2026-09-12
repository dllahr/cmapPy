# Changelog

All notable changes to cmapPy are documented here. Format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

## [4.2.0] - 2026-09-12

### Removed
- Removed `cmapPy.visualization` (`cohort_view`, `scattergram`, `stratogram`) and its tests.
  An audit found no real development since 2019, no other module depending on it, no
  mention in any past documentation, and its `matplotlib`/`seaborn`/`IPython` dependencies
  had never been declared anywhere (so it was never actually installable-and-usable via a
  plain `pip install cmapPy`/`conda install cmappy`). Its tests had also never been
  runnable as-is (broken imports and relative paths); those were fixed in this same window,
  which is what surfaced the module for review in the first place.

## [4.1.0] - 2026-09-12

### Added
- GCTX metadata now supports UTF-8 (and other) string encodings, not just ASCII. The encoding
  is recorded per-dataset in the HDF5 file itself and detected automatically on read, so
  existing ASCII-encoded `.gctx` files continue to read exactly as before. Writing a value that
  can't be encoded raises an error identifying the offending field, row, and value.
- Coverage reporting via `pytest-cov` (`pytest --cov=cmapPy --cov-report=term-missing`).
- `cmapPy/pandasGEXpress/tests/conftest.py` with shared `mini_gctoo`/`mini_gctoo_unconverted`
  pytest fixtures for new tests.
- `pyproject.toml` (PEP 621) as the single source of packaging metadata; `cmapPy/__init__.py`'s
  `__version__` is now the one place the version string lives.
- `RELEASING.md`, a manual release checklist (no CI involved).
- `CONTRIBUTING.md` at the repo root, consolidating what used to be duplicated between
  `README` and the old Sphinx docs.
- A `docs/` folder of plain Markdown pages: `installation.md`, `testing.md`, and per-module
  `api/*.md` overviews (`pandasGEXpress`, `math`, `set_io`, `visualization` — the last two
  didn't have API docs before).
- This changelog.
- Completed and corrected docstrings across `pandasGEXpress`, `math`, `set_io`, and
  `visualization`, following each module's existing docstring convention.
- A note in `README.md` attributing this round of work to Claude Code, under the maintainer's
  supervision and direction.

### Changed
- Adopted `pytest` as the test runner. Existing `unittest.TestCase`-based tests run unchanged;
  `setup.cfg` now configures `testpaths` so a single `pytest` invocation (from the repo root)
  runs the `pandasGEXpress`, `math`, and `set_io` suites together, instead of three separate
  `python -m unittest discover` commands.
- Flattened `cmapPy/pandasGEXpress/tests/python3_tests/` into `cmapPy/pandasGEXpress/tests/`,
  matching the flat layout every other module's test directory already used (the "python3"
  qualifier stopped meaning anything once Python 2 support was dropped).
- Migrated packaging from `setup.py` to `pyproject.toml`; `setup.py` is now a thin
  compatibility shim. Development install is now `pip install -e .` instead of
  `python setup.py develop`.
- Converted all documentation from reStructuredText/Sphinx to plain Markdown (dropping
  ReadTheDocs, which wasn't being kept up to date). `README.md` replaces `README.rst`.
- Fixed real bugs in the packaging config uncovered while verifying the above: `setup.py`'s
  `find_packages` exclude patterns weren't actually excluding test packages (e.g.
  `cmapPy.pandasGEXpress.tests`) from built sdists/wheels, and `MANIFEST.in` had a malformed
  `recursive-include *.gct`/`*.gctx` rule (missing a directory argument) that — once naively
  "fixed" — turned out to instead pull multi-megabyte binary test fixtures into the installed
  wheel. Verified with an actual `python -m build` + `twine check` that the wheel and sdist are
  now free of test code and test fixtures.

### Removed
- Dropped Python 2 support entirely: deleted `cmapPy/pandasGEXpress/tests/python2_tests/` (an
  audit confirmed it was an exact-name subset of the Python 3 suite, so no test coverage was
  lost) and the separate python2/python3 cross-compatibility harness (its still-relevant
  high-precision round-trip test was folded into the main suite as `test_high_precision_roundtrip.py`).
- Removed Travis CI (`.travis.yml`) — no longer used.
- Removed `cmapPy.clue_api_client` (and its tests): the CLUE API it talked to no longer exists,
  and nothing else in cmapPy depended on it. `requests` was dropped from dependencies as a
  result, since it was clue_api_client's only consumer.

### Fixed
- Several test-suite issues surfaced by newer pandas: removed reliance on `pd.util.testing`
  (removed from pandas), deprecated positional `Series` indexing, and a `FutureWarning` from
  `DataFrame.replace()`'s silent downcasting behavior.
- A `SettingWithCopyWarning` in `concat.py`'s metadata-trimming step.
- A stale "Only Python 2.7 supported" comment in `setup.cfg`.
- `diff_gctoo.diff_gctoo`: with `plate_control=False` and `diff_method="median_norm"`, the
  median subtracted was always computed from all samples instead of just the negative
  controls, so vehicle-control median normalization silently behaved identically to
  plate-control normalization. Now correctly uses the negative control samples' median.
- `parse_gctx.check_and_order_id_inputs`: the row-id branch used the `sort_col_meta` flag
  instead of `sort_row_meta` internally, which could silently skip out-of-range validation
  for `ridx` when `sort_row_meta=True` but `sort_col_meta=False`.
- A typo (`logger.errot`) in `visualization/stratogram.py` that would itself raise
  `AttributeError` if that error-handling branch were ever hit.
- `GCToo.check_df` now logs before raising in the "columns not unique" branch, consistent
  with its other validation branches.

## [4.0.0] - 2026-06-02

### Added
- Upgraded to support Python 3.13.

### Changed
- `parse_gctx`/`write_gctx` now preserve HDF5 datatypes when round-tripping data instead of
  forcing conversions (e.g. no longer forces the data matrix to `float32` on parse).
- `pd.to_numeric` conversions of metadata columns now raise on failure instead of silently
  ignoring errors (`errors="raise"` instead of `errors="ignore"`), surfacing bad metadata
  instead of masking it.

## [3.4.1] and earlier

See `git log` for history prior to the Python 3.13 upgrade.
