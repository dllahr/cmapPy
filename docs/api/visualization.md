# visualization

Plotting utilities for summarizing CMap analysis results. These depend on `matplotlib`,
`seaborn`, and (for `cohort_view`) `IPython.display` — none of which are core cmapPy
dependencies, so install them separately if you use this module.

- `cmapPy.visualization.cohort_view.cohort_view_table` /
  `display_cohort_stats_table` — build and display a table of counts/percentages of flagged
  subsets, stratified by category (e.g. how many compounds in each selectivity bucket passed a
  given threshold).
- `cmapPy.visualization.stratogram.stratogram` — a grid of histograms of several metrics,
  stratified by category, with optional reproducibility/recall annotations.
- `cmapPy.visualization.scattergram.scattergram` — a grid of pairwise scatterplots for a set of
  (normalized, 0-1) columns against each other.
