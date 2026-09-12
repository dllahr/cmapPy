[![install with bioconda](https://img.shields.io/badge/install%20with-bioconda-brightgreen.svg?style=flat-square)](http://bioconda.github.io/recipes/cmappy/README.html)
[![PyPI version](https://badge.fury.io/py/cmapPy.svg)](https://badge.fury.io/py/cmapPy)

# cmapPy

Tools for interacting with `.gct` and `.gctx` files, and other Connectivity Map resources.

This repo was originally built by the **Connectivity Map, Broad Institute of MIT and Harvard**.
Recent work (the Python 3.13 upgrade, dropping Python 2 support, GCTX UTF-8 metadata support,
test-suite modernization, and the packaging/release cleanup) was carried out by
[Claude Code](https://claude.com/claude-code), with Dave Lahr supervising and providing
guidance and direction.

For questions or problems, please add an issue to the repository — including code/files that
reproduce your problem helps a lot.

## Installation

```bash
pip install cmapPy
```

or

```bash
conda install -c bioconda cmappy
```

See [docs/installation.md](docs/installation.md) for version details and a development install.

## Modules

| Module | Purpose |
|---|---|
| [`pandasGEXpress`](docs/api/pandasGEXpress.md) | GCT/GCTX file I/O, the `GCToo` class, concat/subset/transform utilities |
| [`math`](docs/api/math.md) | Vectorized numpy operations: `fast_corr`, `fast_cov`, `robust_zscore`, `agg_wt_avg` |
| [`set_io`](docs/api/set_io.md) | Read/write `.gmt` (gene set) and `.grp` (list) files |

Also installs CLI tools: `gctx2gct`, `gct2gctx`, `concat`, `subset` (each takes `-h` for help).

A tutorial notebook is available at
[`tutorials/cmapPy_pandasGEXpress_tutorial.ipynb`](tutorials/cmapPy_pandasGEXpress_tutorial.ipynb).

## Testing

```bash
pip install -r requirements-dev.txt
pytest
```

See [docs/testing.md](docs/testing.md) for details, including coverage reporting.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## Changelog

See [CHANGELOG.md](CHANGELOG.md).

## Citation

If you use cmapPy and/or GCTx for your research, please cite
[Enache et al.](https://academic.oup.com/bioinformatics/article/35/8/1427/5094509)

## License

[BSD 3-Clause](LICENSE.txt)
