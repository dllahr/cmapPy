# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project is

cmapPy is a Python library for reading, writing, and manipulating `.gct` and `.gctx` genomic data files from the Broad Institute's Connectivity Map (CMap) project. It also provides math utilities.

## Commands

**Install for development:**
```bash
pip install -r requirements-dev.txt
pip install -e .
```
Package metadata is single-sourced in `pyproject.toml` (PEP 621); `cmapPy/__init__.py`'s
`__version__` is the one place the version string lives. `setup.py` is now just a thin
`setup()` shim kept for tools that still invoke it directly.

**Run the full test suite (pytest, from repo root):**
```bash
pytest
```
`testpaths` in `setup.cfg` scopes this to `pandasGEXpress/tests`, `math/tests`, and `set_io/tests`. Test classes are plain `unittest.TestCase`s; pytest runs them natively, no rewrite needed.

**Run with coverage:**
```bash
pytest --cov=cmapPy --cov-report=term-missing
```

**Run a single test file/case:**
```bash
pytest cmapPy/pandasGEXpress/tests/test_parse_gctx.py
pytest cmapPy/pandasGEXpress/tests/test_parse_gctx.py::TestParseGctx::test_parse
```

**CLI entry points (installed via `[project.scripts]` in `pyproject.toml`):**
```bash
gctx2gct <input.gctx> <output.gct>
gct2gctx <input.gct> <output.gctx>
concat ...
subset ...
```

## Architecture

### Core data structure: `GCToo`

`cmapPy/pandasGEXpress/GCToo.py` defines the central `GCToo` class. Every parsed file becomes a GCToo instance with three pandas DataFrames:
- `data_df` — the numeric matrix (rows = probes/genes, columns = samples)
- `row_metadata_df` — annotations for each row (indexed by `rid`)
- `col_metadata_df` — annotations for each column (indexed by `cid`)

GCToo enforces that index values are unique and that row/col IDs match across all three DataFrames via `__setattr__` validation. An optional `multi_index_df` combines all three into a single pandas MultiIndex DataFrame.

**CMap null convention:** `-666` is used as the null/NA sentinel in metadata fields (not `NaN`). Parsers accept a `convert_neg_666=True` parameter to convert these to `numpy.nan` on load; writers accept `convert_back_to_neg_666=True` to reverse this.

### File I/O layer

- `parse.py` — unified entry point; dispatches to `parse_gct.py` or `parse_gctx.py` based on file extension
- `parse_gct.py` — parses text-based GCT v1.2 and v1.3 files
- `parse_gctx.py` — parses binary GCTX v1.0 files (HDF5 via h5py); supports partial loading via `rid`/`cid`/`ridx`/`cidx` parameters
- `write_gct.py` — writes GCToo to text GCT format
- `write_gctx.py` — writes GCToo to HDF5 GCTX format; supports `matrix_dtype` and `data_compression_level` parameters

GCTX HDF5 layout: `/0/META/ROW/`, `/0/META/COL/`, `/0/DATA/0/matrix`

### Submodules

| Module | Purpose |
|---|---|
| `pandasGEXpress/` | GCT/GCTX file I/O, GCToo class, concat/subset/transform utilities |
| `math/` | Vectorized numpy operations: `fast_corr`, `fast_cov`, `robust_zscore`, `agg_wt_avg` |
| `set_io/` | Read/write `.gmt` (gene set) and `.grp` (list) files |

### Test structure

pandasGEXpress tests live under `pandasGEXpress/tests/`. Test fixtures (`.gct`, `.gctx` files) live in `tests/functional_tests/`.

The helper `mini_gctoo_for_testing.py` creates a small representative GCToo object for use in unit tests; `pandasGEXpress/tests/conftest.py` exposes it as pytest fixtures (`mini_gctoo`, `mini_gctoo_unconverted`) for new pytest-style tests. Existing `unittest.TestCase` tests that need one just call `mini_gctoo_for_testing.make()` directly (or via a class `setUp`).
