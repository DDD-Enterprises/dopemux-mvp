# Dependency Graph

```mermaid
flowchart TD
  P00["RTE-PKT-00 SOURCE-CLOSURE"]
  P01["RTE-PKT-01 LIVE-GATE"]
  P02["RTE-PKT-02 PAYLOAD-REDACTION"]
  P15["RTE-PKT-15 FAILED-SIDECARS"]

  P03["RTE-PKT-03 PRESCAN-STALE"]
  P04["RTE-PKT-04 PRESCAN-INFLUENCE"]
  P05["RTE-PKT-05 PROVENANCE-FIELDS"]
  P06["RTE-PKT-06 TRUTH-LABELS"]
  P07["RTE-PKT-07 XAI-METADATA"]
  P08["RTE-PKT-08 XAI-BATCH-STATIC"]
  P09["RTE-PKT-09 LIVE-VALIDATION-PLAN"]
  P10["RTE-PKT-10 PROOF-CONTRACT"]
  P11["RTE-PKT-11 RISK-DASHBOARD"]
  P12["RTE-PKT-12 OPENROUTER-XAI"]
  P13["RTE-PKT-13 ROUTE-FINGERPRINT"]
  P14["RTE-PKT-14 PRICING-VISIBILITY"]
  P16["RTE-PKT-16 CLI-LEGACY-UX"]

  P00 --> P03
  P01 --> P09
  P02 --> P09
  P15 --> P11

  P03 --> P04
  P05 --> P06
  P07 --> P13
  P07 --> P09
  P07 --> P12
  P08 --> P09
  P13 --> P12

  P01 --> P11
  P02 --> P11
  P03 --> P11
  P04 --> P11
  P05 --> P11
  P06 --> P11
  P07 --> P11
  P08 --> P11
  P10 --> P11
  P12 --> P11
  P13 --> P11

  P11 --> P14
  P11 --> P16
```

## Dependency Table

| Packet | Direct dependencies | Execution posture |
| --- | --- | --- |
| `RTE-PKT-03` | accepted baseline | serialized implementation |
| `RTE-PKT-05` | accepted baseline | serialized implementation |
| `RTE-PKT-07` | accepted baseline | serialized implementation |
| `RTE-PKT-08` | accepted baseline | Subwave 1A with `RTE-PKT-10` |
| `RTE-PKT-10` | accepted baseline | Subwave 1A with `RTE-PKT-08` |
| `RTE-PKT-04` | `RTE-PKT-03` | wait |
| `RTE-PKT-06` | `RTE-PKT-05` | wait |
| `RTE-PKT-13` | `RTE-PKT-07` | wait |
| `RTE-PKT-12` | `RTE-PKT-07`, `RTE-PKT-13` | wait |
| `RTE-PKT-09` | `RTE-PKT-01`, `RTE-PKT-02`, `RTE-PKT-07`, `RTE-PKT-08` | plan-only |
| `RTE-PKT-11` | `RTE-PKT-01/02/03/04/05/06/07/08/10/12/13/15` | aggregation after dependencies |
| `RTE-PKT-14` | `RTE-PKT-11` | polish after dashboard |
| `RTE-PKT-16` | `RTE-PKT-11` | plan-only until source resolved |
