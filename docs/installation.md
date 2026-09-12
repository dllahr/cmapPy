# Installation

cmapPy requires Python 3.8 or later.

## Option 1 (recommended): conda

```bash
conda create --name my_cmapPy_env -c bioconda python=3.13 numpy=2.3.1 pandas=2.3.3 h5py=3.14.0 cmappy
source activate my_cmapPy_env
```

`-c bioconda` tells conda to look in the bioconda channel, where cmapPy is published.

To update an existing environment: `conda update cmappy`

## Option 2: pip

```bash
pip install cmapPy
```

For other virtualenvs, `requirements.txt` in the repo lists the dependency versions cmapPy is
tested against.

## Option 3: development install

Clone the repository, then from the repo's top-level directory:

```bash
pip install -r requirements-dev.txt
pip install -e .
```

This installs cmapPy in editable mode (changes to the source take effect immediately) plus
`pytest`/`pytest-cov` for running the test suite (see [testing.md](testing.md)).

## Verifying your install

```bash
python -c "import cmapPy.pandasGEXpress.parse_gct as pg"
```

The command-line tools (`gctx2gct`, `gct2gctx`, `concat`, `subset`) should also be on your `PATH`
after any of the options above.
