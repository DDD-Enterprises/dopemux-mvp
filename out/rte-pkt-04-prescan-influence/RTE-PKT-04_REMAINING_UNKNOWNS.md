# RTE-PKT-04 Remaining Unknowns

- Live extraction was not run by design. Runtime label emission was validated through local unit/integration paths, not a full live provider-backed extraction.
- The proof contract schema was not changed. Downstream proof-contract consumers may still need RTE-PKT-10 to make these labels mandatory across generated proof bundles.
- The centralized risk dashboard was not implemented. RTE-PKT-11 can consume the new labels but still needs its own dashboard work.
- Compression hint text is still used in the runtime prompt context when compression is applied. This packet redacts/omits hint text from proof labels; it does not redesign the existing compression behavior.
- `advisory_only` retains the RTE-PKT-03 meaning for accepted imports/local prescan: accepted routers may influence execution. Individual labels carry `advisory_model_derived=true` so operators can distinguish prescan-derived hints from observed source truth.
- Existing pytest configuration still emits `PytestConfigWarning: Unknown config option: asyncio_mode`.
