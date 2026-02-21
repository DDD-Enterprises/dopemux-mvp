# Upgrade Pipeline Run Order (v3)

This runbook is authoritative for `UPGRADES/run_extraction_v3.py`.

## Canonical phase folders

Use only canonical phase folder names under `extraction/runs/<run_id>/`.

- `R_arbitration` is canonical.
- `R2_synthesis` is legacy and forbidden.
- The runner now fails fast if a legacy folder is present.

## Provider gate (required before ALL)

Run provider/auth checks before a full sweep.

```bash
python UPGRADES/run_extraction_v3.py --preflight-providers
python UPGRADES/run_extraction_v3.py --doctor-auth --gemini-transport openai_compat_http --gemini-auth-mode auto
```

- `--preflight-providers` writes `extraction/doctor/PROVIDER_PREFLIGHT.json` and blocks `--phase ALL` when providers are not healthy.
- `--doctor-auth` writes `extraction/doctor/AUTH_DOCTOR.json` and `AUTH_DOCTOR.txt` with per-mode results.

## Canonical phase order

```bash
python UPGRADES/run_extraction_v3.py --phase A --resume
python UPGRADES/run_extraction_v3.py --phase H --resume
python UPGRADES/run_extraction_v3.py --phase D --resume
python UPGRADES/run_extraction_v3.py --phase C --resume
python UPGRADES/run_extraction_v3.py --phase E --resume
python UPGRADES/run_extraction_v3.py --phase W --resume
python UPGRADES/run_extraction_v3.py --phase B --resume
python UPGRADES/run_extraction_v3.py --phase G --resume
python UPGRADES/run_extraction_v3.py --phase Q --resume
python UPGRADES/run_extraction_v3.py --phase R --resume
python UPGRADES/run_extraction_v3.py --phase X --resume
python UPGRADES/run_extraction_v3.py --phase T --resume
python UPGRADES/run_extraction_v3.py --phase Z --resume
```

`--phase ALL` executes the same order and now runs provider preflight first.

## Artifact parse fallback order

Artifact payload parsing in `UPGRADES/run_extraction_v3.py` is deterministic and fail-closed:

1. Strict JSON parse of full text.
2. De-fenced parse (` ```json ... ``` ` wrapper stripped).
3. First fenced block only (when multiple fenced blocks are present).
4. Balanced-repair parse only when the decode error is semantic EOF-eligible:
   `trimmed = text.rstrip()`, `error.pos >= len(trimmed)` or `error.pos == len(trimmed) - 1`, and error class is not unterminated string.
5. Return `None` (no fallback beyond these steps).

## Prompt-corpus phase contracts

The table below is the required checklist mapping phase to step flow and expected capstone outputs.

| Phase | Step flow | Required capstone outputs |
|---|---|---|
| A | `A0` inventory/partition -> `A1..A8` surfaces -> `A99` merge/qa | phase-level `*_NORM_MANIFEST.json`, `*_QA.json`, merged repo norm outputs |
| H | `H0` inventory/partition -> `H1..H7` surfaces -> `H9` merge/qa | phase-level `*_NORM_MANIFEST.json`, `*_QA.json`, merged home norm outputs |
| D | `D0` inventory/partition -> `D1..D3` extraction -> `D4` merge/normalize/coverage | phase-level `*_NORM_MANIFEST.json`, `*_QA.json`, merged docs norm outputs |
| C | `C0` inventory/partition -> `C1..C8` surfaces -> `C9` merge/normalize/qa | phase-level `*_NORM_MANIFEST.json`, `*_QA.json`, merged code norm outputs |
| E | `E0` inventory/partition -> `E1..E6` surfaces -> `E9` merge/normalize/qa | phase-level `*_NORM_MANIFEST.json`, `*_QA.json`, merged execution norm outputs |
| W | `W0` inventory/partition -> `W1..W5` surfaces -> `W9` merge/qa | phase-level `*_NORM_MANIFEST.json`, `*_QA.json`, merged workflow norm outputs |
| B | `B0` inventory/partition -> `B1..B3` surfaces -> `B9` merge/qa | phase-level `*_NORM_MANIFEST.json`, `*_QA.json`, merged boundary norm outputs |
| G | `G0` inventory/partition -> `G1..G4` surfaces -> `G9` merge/qa | phase-level `*_NORM_MANIFEST.json`, `*_QA.json`, merged governance norm outputs |
| Q | `Q0` completeness -> `Q1..Q3` drift checks -> `Q9` merge/qa | phase-level `*_NORM_MANIFEST.json`, `*_QA.json`, merged pipeline QA outputs |
| R | `R0..R8` arbitration steps | truth-map and risk artifacts consumed by `X`/`T` |
| X | `X0` inventory/partition -> `X1..X4` feature extraction -> `X9` merge/qa | phase-level `*_NORM_MANIFEST.json`, `*_QA.json`, merged feature index outputs |
| T | `T0..T5` packet generation -> `T9` merge/qa | phase-level `*_NORM_MANIFEST.json`, `*_QA.json`, merged task packet outputs |
| Z | `Z0..Z2` freeze inputs -> `Z9` freeze manifest/checksums | freeze manifest/checksum proof outputs |

## Phase R gate contract

Before Phase R runs, A/H/D/C must provide all required normalized artifacts declared in `R_REQUIRED_ARTIFACT_GROUPS` in `UPGRADES/run_extraction_v3.py`.

Use:

```bash
python UPGRADES/run_extraction_v3.py --coverage-report --phase ALL
```

and review `PROOF_PACK.json` plus `RUN_MANIFEST.json` for missing groups before Phase R.
