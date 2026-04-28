// Composed cockpit screen. Renders the full 120x40 layout from primitives.

const { useState } = React;

function Cockpit({ size = "120x40" }) {
    const seed = window.SEED;
    const [activeMode] = useState("Services");
    const [activeService] = useState(seed.services.selected);
    const [activeRun] = useState(seed.rte_child_surface.runs[0].run_id);

    return (
        <Frame
            size={size}
            workspace={seed.workspace.id}
            surface="services"
            mode="rich"
            state="STATIC DEMO"
            authority="dopemux"
            domain="cockpit_chrome"
            role="chrome"
            next_action="select_mode"
        >
            <ModeBar modes={seed.top_level_modes} current={activeMode} />

            <div className="cockpit-grid">
                {/* LEFT: Services mode list */}
                <Pane className="services-pane">
                    <PaneHeader
                        title="Services"
                        domain="services_index"
                        authority={seed.services.authority}
                        role="derived"
                        next_action="select_workload"
                    />
                    {seed.services.rows.map((s) => (
                        <ServiceRow
                            key={s.name}
                            active={s.name === activeService}
                            name={s.name}
                            kind={s.kind}
                            status={s.status}
                            src={s.SRC}
                        />
                    ))}
                </Pane>

                {/* CENTER: repo-truth-extractor child/workload surface */}
                <Pane className="center-pane">
                    <PaneHeader
                        title={`Services -> ${activeService}`}
                        domain="services_child_workload"
                        authority={seed.rte_child_surface.authority}
                        role="canonical"
                        next_action="inspect_run_history"
                    />
                    <div className="center-tabs">
                        {seed.rte_child_surface.tabs.map((t, i) => (
                            <span key={t}>
                                <span className={t === seed.rte_child_surface.rendered_tab ? "tab-active" : ""}>{t}</span>
                                {i < seed.rte_child_surface.tabs.length - 1 && <span className="tab-sep"> | </span>}
                            </span>
                        ))}
                    </div>
                    <div className="row row-dim">RUN ID                          REPO · BRANCH        PHASE       ALERTS</div>
                    {seed.rte_child_surface.runs.map((r) => (
                        <RunRow key={r.run_id} active={r.run_id === activeRun} run={r} />
                    ))}
                </Pane>

                {/* RIGHT: Inspector + bridge segregator */}
                <Inspector inspector={seed.services.inspector} />
            </div>

            <CommandRail authority="dopemux" flags="static-demo · no writes · seed-only" />
            <StatusRail
                workspace={seed.workspace.id}
                mode={activeMode}
                render={seed.status_rail.right}
            />
            <HintRail items={seed.hints} />
        </Frame>
    );
}

function App() {
    const [size, setSize] = useState("120x40");
    return (
        <>
            <div className="app-meta">dopemux · cockpit · TUI snapshot · <b>{size}</b></div>
            <div className="controls" role="tablist" aria-label="Snapshot size">
                {["120x40", "100x32", "80x24"].map((s) => (
                    <button
                        key={s}
                        className={size === s ? "active" : ""}
                        onClick={() => setSize(s)}
                        role="tab"
                        aria-selected={size === s}
                    >
                        {s}
                    </button>
                ))}
            </div>
            <Cockpit size={size} />
        </>
    );
}

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(<App />);
