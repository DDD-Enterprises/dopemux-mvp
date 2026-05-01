// Demo-state seed mirrors the deterministic cockpit render contract in
// src/dopemux/ui/cockpit/render.py.
window.SEED = {
    workspace: { id: "dopemux-mvp", instance: "local", src: "dopemux" },
    modes: ["PM", "Implementer", "Overview", "Services", "Events"],
    services: {
        authority: "dopemux",
        selected: "repo-truth-extractor",
        rows: [
            { name: "dopemux",              status: "LIVE",      kind: "control",    src: "dopemux" },
            { name: "task-orchestrator",    status: "LIVE",      kind: "workflow",   src: "task-orchestrator" },
            { name: "conport",              status: "LIVE",      kind: "structured", src: "conport" },
            { name: "dope-memory",          status: "LOGGED",    kind: "chronicle",  src: "dope-memory" },
            { name: "dope-context",         status: "LOGGED",    kind: "retrieval",  src: "dope-context" },
            { name: "dopecon-bridge",       status: "OVERRIDE",  kind: "adapter",    src: "dopecon-bridge" },
            { name: "adhd-engine",          status: "LIVE",      kind: "support",    src: "adhd-engine" },
            { name: "repo-truth-extractor", status: "AFTERCARE", kind: "extraction", src: "repo-truth-extractor" },
        ],
        inspector: {
            subject: "repo-truth-extractor",
            authority: "repo-truth-extractor",
            provenance: "EXTRACTED",
            rows: [
                { label: "canonical", value: "services/repo-truth-extractor/run_extraction_v5.py", src: "repo-truth-extractor" },
                { label: "boundary",  value: "workload view not shell owner", src: "dopemux" },
                { label: "state",     value: "seed only no live run", src: "repo-truth-extractor" },
            ],
            bridge: {
                actions: [{ label: "ADAPTER -> dopecon-bridge : replay-event", src: "dopecon-bridge" }],
                footer: "[EDGE] bridge is adapter/proxy only. NEXT: prefer canonical write.",
            },
        },
    },
    rte: {
        authority: "repo-truth-extractor",
        tabs: ["R1 Runs", "R2 Active", "R3 Prescan", "R4 Doctor", "R5 Coverage", "R6 Audit"],
        rendered_tab: "R1 Runs",
        runs: [
            { runId: "v5-2026-04-22T14:32Z-a91c", repo: "dopemux/main",            scope: "services",         status: "LIVE",      phase: "normalize", alerts: 2, src: "repo-truth-extractor" },
            { runId: "v5-2026-04-22T11:04Z-7f18", repo: "dopemux/main",            scope: "rte",              status: "BLOCKER",   phase: "preflight", alerts: 1, src: "repo-truth-extractor" },
            { runId: "v5-2026-04-22T09:51Z-3e2a", repo: "dopemux/feat-bridge",     scope: "dopecon-bridge",   status: "LOGGED",    phase: "verify",    alerts: 1, src: "repo-truth-extractor" },
            { runId: "v5-2026-04-21T22:48Z-1d9b", repo: "dopemux/main",            scope: "docs",             status: "OVERRIDE",  phase: "coverage",  alerts: 6, src: "repo-truth-extractor" },
            { runId: "v5-2026-04-21T18:02Z-ce44", repo: "dopemux/main",            scope: "services",         status: "BLOCKER",   phase: "doctor",    alerts: 0, src: "repo-truth-extractor" },
            { runId: "v5-2026-04-21T09:15Z-f02d", repo: "dopemux/main",            scope: "services/adhd",    status: "LOGGED",    phase: "verify",    alerts: 0, src: "repo-truth-extractor" },
        ],
    },
    statusRail: { left: "workspace dopemux-mvp", middle: "mode Services", right: "rich · seed · no-writes" },
    hints: [
        { key: ")", label: "enter open" },
        { key: "n", label: "new run" },
        { key: "d", label: "doctor" },
        { key: "c", label: "compare" },
        { key: "x", label: "export" },
        { key: "/", label: "filter" },
        { key: "q", label: "quit" },
    ],
};
