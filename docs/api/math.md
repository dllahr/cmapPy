# math

Vectorized numpy operations used across CMap analyses. All operate on numpy arrays or pandas
objects directly (not `GCToo`s). See each function's docstring for full parameter details.

- `cmapPy.math.fast_corr.fast_corr` / `nan_fast_corr` — fast Pearson correlation between the
  columns of one or two matrices; the `nan_*` variant tolerates missing values.
- `cmapPy.math.fast_corr.fast_spearman` / `nan_fast_spearman` — Spearman (rank) correlation,
  built on `fast_corr`.
- `cmapPy.math.fast_cov.fast_cov` / `nan_fast_cov` — fast covariance between the columns of one
  or two matrices; the `nan_*` variant tolerates missing values.
- `cmapPy.math.robust_zscore.robust_zscore` — median/MAD-based ("robust") z-scoring of a
  matrix, optionally against a separate control matrix.
- `cmapPy.math.agg_wt_avg.agg_wt_avg` — aggregate replicate profiles into a single signature via
  a correlation-weighted average (cmapPy's "modz" method); `calculate_weights` and
  `get_upper_triangle` are its building blocks, also usable standalone.
