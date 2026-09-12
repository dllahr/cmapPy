# Releasing cmapPy

No CI is involved in releases — this is a manual checklist.

1. Bump the version in `cmapPy/__init__.py` (`__version__ = "X.Y.Z"`). This is the single
   source of truth; `pyproject.toml` reads it dynamically, nothing else needs editing.
2. Add a new `## [X.Y.Z] - YYYY-MM-DD` section to the top of `CHANGELOG.md`, moving the
   relevant entries out of `## [Unreleased]`.
3. Run the full test suite and make sure it's clean:
   ```bash
   pip install -r requirements-dev.txt
   pytest
   ```
4. Commit the version bump and changelog update.
5. Tag the release and push the tag (always `vX.Y.Z`, matching the version in step 1):
   ```bash
   git tag vX.Y.Z
   git push origin vX.Y.Z
   ```
6. Build the distributable artifacts from a clean checkout:
   ```bash
   rm -rf dist build cmapPy.egg-info
   python -m pip install --upgrade build twine
   python -m build
   python -m twine check dist/*
   ```
7. Upload to PyPI:
   ```bash
   python -m twine upload dist/*
   ```
8. bioconda's recipe bot picks up the new PyPI release automatically, usually within a day —
   no manual bioconda PR is needed unless dependency constraints changed enough to require a
   recipe edit (check https://github.com/bioconda/bioconda-recipes if a release doesn't show
   up in `conda install cmappy` within a couple of days).
