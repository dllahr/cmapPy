# set_io

Reads and writes two simple gene-set file formats used by the Connectivity Map. Further
details on the formats: <https://clue.io/connectopedia/grp_gmt_gmx_format>.

- **GRP** — a single set of things (e.g. one gene set), one entry per line.
  - `cmapPy.set_io.grp.read` / `cmapPy.set_io.grp.write`
- **GMT** — multiple named sets of things (e.g. several gene sets) in one file.
  - `cmapPy.set_io.gmt.read` / `cmapPy.set_io.gmt.write`
  - `cmapPy.set_io.gmt.verify_gmt_integrity` — sanity-checks a parsed GMT structure.
