#!/usr/bin/env python3
import argparse
import csv
from pathlib import Path
from collections import Counter, defaultdict


def load_tsv(path: Path):
    if not path.exists():
        return []
    rows = []
    with path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            rows.append(row)
    return rows


def coalesce_empty(val):
    return (val or "").strip()


def main():
    parser = argparse.ArgumentParser(description="Generate summary dashboard from registry TSVs")
    parser.add_argument("--input", required=True, help="Directory containing TSVs (features.tsv, components.tsv, subsystems.tsv, research.tsv, evidence_links.tsv)")
    args = parser.parse_args()

    base = Path(args.input)
    features = load_tsv(base / "features.tsv")
    components = load_tsv(base / "components.tsv")
    subsystems = load_tsv(base / "subsystems.tsv")
    research = load_tsv(base / "research.tsv")

    # Evidence density (stream counts)
    evidence_file = base / "evidence_links.tsv"
    evidence_to_counts = Counter()
    evidence_from_counts = Counter()
    if evidence_file.exists():
        with evidence_file.open("r", encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter="\t")
            for row in reader:
                evidence_to_counts[coalesce_empty(row.get("to_id"))] += 1
                evidence_from_counts[coalesce_empty(row.get("from_id"))] += 1

    # Metrics
    totals = {
        "features": len(features),
        "components": len(components),
        "subsystems": len(subsystems),
        "research": len(research),
        "evidence_links": sum(evidence_to_counts.values()),
    }

    # SLO coverage (components)
    slo_missing = 0
    for c in components:
        if not coalesce_empty(c.get("slo_availability")) or not coalesce_empty(c.get("slo_latency")):
            slo_missing += 1
    slo_missing_pct = (slo_missing / max(len(components), 1)) * 100.0

    # Security coverage (components)
    security_present = 0
    for c in components:
        if coalesce_empty(c.get("security_notes")) or coalesce_empty(c.get("threat_model_refs")):
            security_present += 1
    security_present_pct = (security_present / max(len(components), 1)) * 100.0

    # ADR linkage
    comp_with_adr = sum(1 for c in components if coalesce_empty(c.get("adr_ids")))
    feat_with_adr = sum(1 for f in features if coalesce_empty(f.get("adr_ids")))

    # Research quality & recency
    quality_counts = Counter(coalesce_empty(r.get("source_quality")) for r in research)
    recency_buckets = Counter()
    total_conf = 0.0
    conf_count = 0
    for r in research:
        try:
            rec = int(float(coalesce_empty(r.get("recency_days")) or 0))
        except Exception:
            rec = 0
        if rec <= 30:
            recency_buckets["<=30d"] += 1
        elif rec <= 90:
            recency_buckets["31-90d"] += 1
        elif rec <= 180:
            recency_buckets["91-180d"] += 1
        else:
            recency_buckets[">180d"] += 1

        try:
            conf = float(coalesce_empty(r.get("confidence")) or 0.0)
            total_conf += conf
            conf_count += 1
        except Exception:
            pass
    avg_conf = (total_conf / conf_count) if conf_count else 0.0

    # Top subsystems by component count
    subsys_name_by_id = {coalesce_empty(s.get("subsystem_id")): coalesce_empty(s.get("name")) for s in subsystems}
    comp_per_subsys = Counter(coalesce_empty(c.get("subsystem_id")) for c in components)
    top_subsys = comp_per_subsys.most_common(10)

    # Evidence density samples
    top_components_by_evidence = []
    for c in components:
        cid = coalesce_empty(c.get("component_id"))
        cnt = evidence_to_counts.get(cid, 0)
        top_components_by_evidence.append((cnt, cid, coalesce_empty(c.get("name"))))
    top_components_by_evidence.sort(reverse=True)
    top_components_by_evidence = top_components_by_evidence[:10]

    # Prepare output
    out_dir = base / "reports"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_md = out_dir / "SUMMARY_DASHBOARD.md"
    with out_md.open("w", encoding="utf-8") as f:
        f.write("# Documentation Registries – Summary Dashboard\n")
        f.write("\n")
        f.write("## Totals\n")
        for k, v in totals.items():
            f.write(f"- {k}: {v}\n")

        f.write("\n## SLO Coverage (Components)\n")
        f.write(f"- Missing any SLO: {slo_missing}/{max(len(components),1)} ({slo_missing_pct:.1f}%)\n")

        f.write("\n## Security Coverage (Components)\n")
        f.write(f"- Has security notes or threat model refs: {security_present}/{max(len(components),1)} ({security_present_pct:.1f}%)\n")

        f.write("\n## ADR Linkage\n")
        f.write(f"- Components with ADR refs: {comp_with_adr}\n")
        f.write(f"- Features with ADR refs: {feat_with_adr}\n")

        f.write("\n## Research Quality\n")
        for q, c in quality_counts.items():
            label = q or "(unknown)"
            f.write(f"- {label}: {c}\n")

        f.write("\n## Research Recency\n")
        for b, c in recency_buckets.items():
            f.write(f"- {b}: {c}\n")
        f.write(f"- Avg confidence: {avg_conf:.2f}\n")

        f.write("\n## Top Subsystems by Components\n")
        for sid, cnt in top_subsys:
            name = subsys_name_by_id.get(sid, sid)
            f.write(f"- {name} ({sid}): {cnt}\n")

        f.write("\n## Top Components by Evidence Incoming\n")
        for cnt, cid, name in top_components_by_evidence:
            f.write(f"- {name} ({cid}): {cnt}\n")

    print(f"✅ Wrote dashboard: {out_md}")


if __name__ == "__main__":
    main()

