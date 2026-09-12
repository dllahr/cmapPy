# pandasGEXpress

Reads, writes, and manipulates `.gct` and `.gctx` files, integrated with
[pandas](https://pandas.pydata.org/). `.gctx` (HDF5-backed) is more performant than the
text-based `.gct` and is the recommended format for anything but small files.

This page is a map of the module's public entry points; see each function's docstring in the
source for full parameter details.

## The `GCToo` class

`cmapPy.pandasGEXpress.GCToo.GCToo` is the central data structure. Every parsed file becomes a
`GCToo` instance holding three pandas DataFrames — `data_df` (the numeric matrix),
`row_metadata_df`, and `col_metadata_df` — kept consistent with each other (same rid/cid values)
by validation in `GCToo.__setattr__`.

## Parsing

- `cmapPy.pandasGEXpress.parse.parse` — unified entry point; dispatches to `parse_gct.parse` or
  `parse_gctx.parse` based on the file extension.
- `cmapPy.pandasGEXpress.parse_gct.parse` — parses GCT v1.2/v1.3 text files (including gzipped).
- `cmapPy.pandasGEXpress.parse_gctx.parse` — parses GCTX (HDF5) files; supports partial loading
  via `rid`/`cid`/`ridx`/`cidx`, and `cmapPy.pandasGEXpress.parse_gctx.get_row_metadata` /
  `get_column_metadata` for metadata-only reads.

## Writing

- `cmapPy.pandasGEXpress.write_gct.write` — writes a `GCToo` to text GCT format.
- `cmapPy.pandasGEXpress.write_gctx.write` — writes a `GCToo` to HDF5 GCTX format; supports
  `matrix_dtype` and `data_compression_level`. Metadata strings are written as UTF-8 (see
  `write_gctx.write_string_dataset`), and the encoding is recorded per-dataset in the file so
  `parse_gctx` can auto-detect it on read.

## Concatenating

`cmapPy.pandasGEXpress.concat` — `hstack` (concatenate columns/samples) and `vstack`
(concatenate rows/features) combine multiple `GCToo` objects, reconciling shared metadata
fields; also usable as a CLI (`concat`).

## Subsetting

- `cmapPy.pandasGEXpress.subset_gctoo.subset_gctoo` — subset a `GCToo` by row/column ids,
  indices, or boolean masks.
- `cmapPy.pandasGEXpress.random_slice.make_specified_size_gctoo` — take a random slice of a
  given size along one dimension (handy for building small test fixtures).
- `cmapPy.pandasGEXpress.subset` — CLI wrapper (`subset`) around `subset_gctoo`.

## Other transforms

- `cmapPy.pandasGEXpress.transform_gctoo.transpose` — transpose a `GCToo` (swap rows/columns).
- `cmapPy.pandasGEXpress.diff_gctoo.diff_gctoo` — compute a plate- or group-control-normalized
  difference for a `GCToo`.

## Converting `.gct` <-> `.gctx`

- `cmapPy.pandasGEXpress.gct2gctx` — CLI (`gct2gctx`) and `gct2gctx_main`.
- `cmapPy.pandasGEXpress.gctx2gct` — CLI (`gctx2gct`) and `gctx2gct_main`.

## CMap null convention

`-666` is used as the null/NA sentinel in metadata fields (not `NaN`), for historical CMap
reasons. Parsers accept `convert_neg_666=True` to convert these to `numpy.nan` on load; writers
accept `convert_back_to_neg_666=True` to convert back on write.
