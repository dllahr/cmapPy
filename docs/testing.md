# Running the tests

cmapPy uses [pytest](https://docs.pytest.org/) as its test runner. Test classes are plain
`unittest.TestCase`s; pytest runs them natively.

## Setup

```bash
pip install -r requirements-dev.txt
```

## Run everything

From the repository root:

```bash
pytest
```

`testpaths` in `setup.cfg` scopes this to `cmapPy/pandasGEXpress/tests`, `cmapPy/math/tests`,
and `cmapPy/set_io/tests`. (`cmapPy/visualization`'s test files and the removed
`clue_api_client` module's tests are not part of this — see note at the bottom.)

## Run a single file or test

```bash
pytest cmapPy/pandasGEXpress/tests/test_parse_gctx.py
pytest cmapPy/pandasGEXpress/tests/test_parse_gctx.py::TestParseGctx::test_parse
```

## Coverage

```bash
pytest --cov=cmapPy --cov-report=term-missing
```

`setup.cfg`'s `[coverage:run]`/`[coverage:report]` sections configure what's measured/excluded.

## Test fixtures

- `cmapPy/pandasGEXpress/mini_gctoo_for_testing.py` builds a small representative `GCToo`
  object used throughout the pandasGEXpress tests.
- `cmapPy/pandasGEXpress/tests/conftest.py` exposes that as pytest fixtures (`mini_gctoo`,
  `mini_gctoo_unconverted`) for new tests written in pytest style. Existing `unittest.TestCase`
  tests just call `mini_gctoo_for_testing.make()` directly (some via a class `setUp`).
- Binary `.gct`/`.gctx` test fixtures live under `cmapPy/pandasGEXpress/tests/functional_tests/`
  and `cmapPy/set_io/tests/functional_tests/`.

## Not currently covered by `pytest`

`cmapPy/visualization/` has its own `test_*.py` files sitting directly in the package
directory (not a `tests/` subpackage), and isn't part of `testpaths`. Wiring it in — and
likely reorganizing it into a `visualization/tests/` subpackage first — is a known gap.
