// Cockpit primitives — TUI rendering as React components.
// Every component renders character-positioned text; no layout flex/grid
// hides behind the scenes — what you see is what the framebuffer draws.

const { useState, useMemo } = React;

/* ── Closed chip set. Do not extend. ─────────────────────────────────── */
const CHIP_STYLES = {
    LIVE:      "chip-live",
    BLOCKER:   "chip-blocker",
    OVERRIDE:  "chip-override",
    LOGGED:    "chip-logged",
    AFTERCARE: "chip-aftercare",
    EDGE:      "chip-edge",
};

const PANE_ROLES = new Set(["canonical", "derived", "mirrored", "proxied", "authoring", "chrome"]);

function Chip({ kind }) {
    const cls = CHIP_STYLES[kind];
    if (!cls) throw new Error(`forbidden chip: ${kind}`);
    return <span className={`chip ${cls}`}>[{kind}]</span>;
}

/* ── SRC tag: provenance, not authority.
 *   Chrome does not carry SRC.
 *   Each logical data/provenance record carries SRC once.
 * ───────────────────────────────────────────────────────────────────── */
function Src({ value }) {
    if (!value || value === "UNKNOWN") throw new Error("SRC requires known service provenance");
    return <span className="src">SRC={value}</span>;
}

/* ── Selector arrow in column 0. ─────────────────────────────────────── */
function Selector({ active }) {
    return <span className="sel">{active ? ">" : " "}</span>;
}

/* ── Pane: a region inside the protected grid. ───────────────────────── */
function Pane({ children, className = "" }) {
    return <div className={`pane ${className}`}>{children}</div>;
}

/* ── PaneHeader: declares the required four-field pane contract. ─────── */
function PaneHeader({
    title,
    domain,
    authority,
    role = "canonical",
    next_action,
    accent = "cyan",
}) {
    if (!PANE_ROLES.has(role)) throw new Error(`forbidden pane role: ${role}`);
    return (
        <div className={`pane-header pane-header-${accent}`}>
            <span className="pane-title">{title}</span>
            <span className="pane-domain"> domain: {domain}</span>
            <span className="pane-auth"> authority: {authority}</span>
            <span className="pane-role"> role: {role}</span>
            <span className="pane-next"> next_action: {next_action}</span>
        </div>
    );
}

/* ── Rule: a horizontal protected divider. ───────────────────────────── */
function Rule({ width = 56 }) {
    return <div className="rule">{"─".repeat(width)}</div>;
}

/* ── Row: one line of content. ───────────────────────────────────────── */
function Row({ active, src, chip, children, dim }) {
    return (
        <div className={`row ${active ? "row-active" : ""} ${dim ? "row-dim" : ""}`}>
            <Selector active={active} /> {src && <><Src value={src} /> </>}
            {chip && <><Chip kind={chip} /> </>}
            {children}
        </div>
    );
}

/* ── ServiceRow: a service in the left pane. ─────────────────────────── */
function ServiceRow({ active, name, kind, status, src }) {
    return (
        <Row active={active} src={src} chip={status}>
            <span className="row-name">{name}</span>
            <span className="row-kind"> {kind}</span>
        </Row>
    );
}

/* ── RunRow: two-line run row in the center pane. ────────────────────── */
function RunRow({ active, run }) {
    return (
        <>
            <Row active={active} src={run.src} chip={run.status}>
                <span className="row-name">{run.runId}</span>
            </Row>
            <Row dim>
                <span>phase={run.phase} repo={run.repo} alerts={run.alerts}</span>
            </Row>
        </>
    );
}

/* ── ModeBar: top-level modes with key affordances.
 *   Chrome — never carries SRC=. Authority is declared by the surface header,
 *   not by the mode bar.
 * ──────────────────────────────────────────────────────────────────────── */
function ModeBar({ modes, current }) {
    return (
        <div className="modebar">
            {modes.map((m, i) => {
                const sel = m === current;
                return (
                    <span key={m} className={`mode ${sel ? "mode-active" : ""}`}>
                        {i + 1} {sel ? "*" : " "}{m}
                        {i < modes.length - 1 && <span className="modesep"> | </span>}
                    </span>
                );
            })}
        </div>
    );
}

/* ── Inspector: subject + provenance + bridge segregator. ────────────── */
function Inspector({ inspector }) {
    return (
        <Pane className="inspector">
            <PaneHeader
                title="Inspector"
                domain="services_child_detail"
                authority={inspector.authority}
                role="derived"
                next_action="inspect_workload"
            />
            <div className="row">subject <Src value={inspector.authority} /> {inspector.subject}</div>
            <div className="row">provenance={inspector.provenance} <Src value={inspector.authority} /></div>
            {inspector.rows.map((r, i) => (
                <div key={i} className="row row-dim">
                    {r.src && <><Src value={r.src} /> </>}{r.label}={r.value}
                </div>
            ))}
            <Rule width={34} />
            <div className="bridge-header">Bridge adapter/proxy: dopecon-bridge</div>
            <div className="row"><Src value="dopecon-bridge" /> <Chip kind="EDGE" /> adapter-only segregated</div>
            <div className="row row-dim">ADAPTER -&gt; &lt;service&gt; : &lt;action&gt;</div>
            {inspector.bridge.actions.map((a, i) => (
                <div key={i} className="row row-dim"><Src value={a.src} /> {a.label}</div>
            ))}
            <div className="row row-muted">{inspector.bridge.footer}</div>
        </Pane>
    );
}

/* ── CommandRail / StatusRail: protected bottom rows.
 *   Chrome — communicates surface state, not data provenance. Never SRC=.
 * ──────────────────────────────────────────────────────────────────────── */
function CommandRail({ authority = "dopemux", flags = "static-demo · no writes" }) {
    return (
        <div className="rail rail-command">
            <span className="rail-cell">domain: commands</span>
            <span className="rail-cell">authority: {authority}</span>
            <span className="rail-cell">role: chrome</span>
            <span className="rail-cell">next_action: operator_shortcut</span>
            <span className="rail-cell">{flags}</span>
        </div>
    );
}

function StatusRail({ workspace, mode, render }) {
    return (
        <div className="rail rail-status">
            <span className="rail-cell">workspace {workspace}</span>
            <span className="rail-cell">mode {mode}</span>
            <span className="rail-cell">render {render}</span>
            <span className="rail-cell">domain: status</span>
            <span className="rail-cell">authority: dopemux</span>
            <span className="rail-cell">role: chrome</span>
            <span className="rail-cell">next_action: observe_state</span>
        </div>
    );
}

/* ── HintRail: keybind hints (not a mouse menu). ─────────────────────── */
function HintRail({ items }) {
    return (
        <div className="hintrail">
            {items.map((h, i) => (
                <span key={i} className="hint"><span className="hint-key">{h.key}</span> {h.label}{i < items.length - 1 ? "  · " : ""}</span>
            ))}
        </div>
    );
}

/* ── Frame: the outer cockpit shell.
 *   Chrome row — declares workspace, surface, mode, render mode, command
 *   authority, role, flags, and snapshot size. Never carries SRC=.
 *   Data carries provenance; chrome does not. */
function Frame({
    size = "120x40",
    workspace = "/users/hu3/code/dopemux-mvp",
    surface = "services",
    mode = "rich",
    state = "STATIC DEMO",
    authority = "dopemux",
    role = "chrome",
    domain = "cockpit_chrome",
    next_action = "select_mode",
    children,
}) {
    return (
        <div className={`frame frame-${size.replace("x", "-")}`}>
            <div className="frame-header">
                <span className="frame-title">dopemux cockpit</span>
                <span className="frame-meta">workspace {workspace}</span>
                <span className="frame-meta">surface {surface}</span>
                <span className="frame-meta">mode {mode}</span>
                <span className="frame-meta">domain: {domain}</span>
                <span className="frame-meta">authority: {authority}</span>
                <span className="frame-meta">role: {role}</span>
                <span className="frame-meta">next_action: {next_action}</span>
                <span className="frame-meta frame-state">{state}</span>
                <span className="frame-meta">snapshot {size}</span>
            </div>
            <div className="frame-body">{children}</div>
        </div>
    );
}

Object.assign(window, {
    Chip, Src, Selector, Pane, PaneHeader, Rule, Row,
    ServiceRow, RunRow, ModeBar, Inspector,
    CommandRail, StatusRail, HintRail, Frame,
});
