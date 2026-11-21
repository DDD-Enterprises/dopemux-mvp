# Off-repo custody

Originals kept outside the public repo, set read-only when this bundle was built:

| File | What | sha256 |
|---|---|---|
| `~/.local/share/dopemux/evidence/pr1521/r1/custody/cli-20261119_200940.log` | AGY CLI log, unredacted | `6998bbf054f00708153f122cc1af24fb6b46fc0f4e444d6c66c34b5ca2b36c32` |
| `~/.local/share/dopemux/evidence/pr1521/r1/custody/fe89e363-4bab-47da-88ef-05dee1a81345.db` | AGY conversation store | `b4e591aa8360c761180d225bd8f223372779b1a4fc41fb50e3de57701b0fe06f` |
| `~/.local/share/dopemux/evidence/pr1521/r1/validation/base_run4.xml` | JUnit report behind the base counts in LOCAL_VALIDATION.txt | `eb296a480dde47aa1e583b604555350f259ca512f25feb6d2bf690d713ea56e5` |
| `~/.local/share/dopemux/evidence/pr1521/r1/validation/base_run4_full.log` | pytest output of that base run | `fd07b8fe4ff59b6de00c3f06e4890cb46af2bb0b858ce4a49d85870672ac3b42` |

The sealed-run dir (`r1/agy`) held only `AUDIT_PROMPT.txt` (same sha256 as this bundle's copy).
The script that built this bundle is `~/.local/share/dopemux/evidence/pr1521/r1/build_bundle.py`.
