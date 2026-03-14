Leantime (v3.7.2, ref 555803d3d, AGPL-3.0) is a PHP/Laravel 11 PM system with 57 domain modules, 30 database tables, and 48 service classes exposing 241+ methods via JSON-RPC 2.0.
Active integration surfaces: JSON-RPC API (primary, stable), event/filter hooks (unstable names), plugin system (folder+PHAR), CLI (17 commands), MCP endpoint (early-stage, no custom tools registered).
Domain model confidence: HIGH — all 30 entities documented with exact table schemas, model properties, and service methods; canvas system provides 16 strategic planning variants.
Workflow/gating confidence: HIGH — confirmed NO state machine exists; ticket transitions are unrestricted (any→any); no dependency enforcement; no auto-close; Task Orchestrator should own all workflow rules.
Plugin/API confidence: HIGH — JSON-RPC routing verified via Jsonrpc.php reflection-based dispatch; plugin Registration API documented; 3 auth guards (web/sanctum/jsonRpc) confirmed.
Memory-boundary confidence: MEDIUM-HIGH — operational data clearly separable from contextual/strategic data; all rich-text fields require HTML normalization before memory promotion.
Biggest drift findings: TinyMCE fully replaced by Tiptap (docs stale), version 3.6.2→3.7.2, MCP+AI packages (prism/neuron-ai/qdrant) completely undocumented, 21 total drift items identified.
Recommended integration shape: External MCP gateway over JSON-RPC for reads/writes + optional Leantime plugin for event hooks and UI injection; phased rollout starting read-only.
Leantime's lack of workflow enforcement is an opportunity — Task Orchestrator becomes sole workflow authority with zero conflict; Leantime provides the PM data store.
RECOMMENDATION: HYBRID_PLUGIN_AND_ADAPTER
