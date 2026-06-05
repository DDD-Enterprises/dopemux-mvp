# COMMAND_LOG — TP-DCP-MCP-RO-0003 (Inspect Dopemux Init Registry Contract)

Read-only static inspection. Run from worktree .worktrees/chatgpt-mcp-ro-0003 (branch reset onto merged main 59b309f27).

## $ git rev-parse --show-toplevel && git branch --show-current && git rev-parse HEAD
/Users/hue/code/dopemux-mvp/.worktrees/chatgpt-mcp-ro-0003
dcp/chatgpt-mcp-ro-0003-inspect-dopemux-init-registry-co
59b309f27ab745a76dee2dfe7c1e6c0c2e0e36fd

## Evidence — dopemux init (cli.py / project_init.py)
204:from .project_init import init_project
725:def init(
770:            f"[warning]⚠️  Project already initialized (.dopemux/ exists)[/warning]"
780:    success = init_project(workspace, profile, force)
38:        self.dopemux_dir = self.workspace / ".dopemux"
114:                self.dopemux_dir = self.workspace / ".dopemux"
167:        self.dopemux_dir.mkdir(exist_ok=True)
168:        (self.dopemux_dir / "databases").mkdir(exist_ok=True)
174:        # Step 4: Create config.yaml (optional project overrides)
175:        config_file = self.dopemux_dir / "config.yaml"
178:            console.logger.info(f"   Created: .dopemux/config.yaml")
188:        console.logger.info(f"  3. (Optional) Edit: [text.dim].dopemux/config.yaml[/text.dim]")
265:def init_project(workspace: Path, profile: Optional[str], force: bool) -> bool:

## Evidence — workspace detection
11:2. git rev-parse --show-toplevel (works for worktrees AND main repo!)
82:def get_workspace_root(start_path: Optional[Path] = None) -> Path:
129:    # git rev-parse --show-toplevel returns:
135:            ["git", "rev-parse", "--show-toplevel"],
184:def export_workspace_env(workspace_path: Optional[Path] = None) -> dict[str, str]:
222:def validate_workspace(workspace_path: Path) -> tuple[bool, Optional[str]]:
272:def get_workspace_info(workspace_path: Optional[Path] = None) -> dict[str, any]:

## Evidence — registries
24:GLOBAL_CONFIG_PATH = CONFIG_DIR / "config.json"
37:        "default_workspace": None,
45:    if not GLOBAL_CONFIG_PATH.exists():
49:        with GLOBAL_CONFIG_PATH.open("r", encoding="utf-8") as fh:
55:            data.setdefault("default_workspace", None)
63:    with GLOBAL_CONFIG_PATH.open("w", encoding="utf-8") as fh:
93:def register_workspace(workspace_path: Path) -> WorkspaceEntry:
127:def set_default_workspace(workspace_path: Path) -> None:
130:    config["default_workspace"] = str(workspace_path)
135:def get_default_workspace() -> Optional[Path]:

## Evidence — repo-root markers (existence + tracking)
EXISTS .repo_id
EXISTS .dopetaskroot
ABSENT .n
EXISTS .dopemux
.dopetaskroot
.repo_id

## Evidence — .repo_id content
project=dopemux-mvp
owner=hu3mann
intent=Primary dopemux workspace. Task packets must refuse if repo_id mismatches.

## Evidence — repo_marker CONFLICT
141:            "repo_marker": ".dopetaskroot",
18:    "repo_root_marker",
95:      "description": "Repository identifier from .repo_id marker."
97:    "repo_root_marker": {

## Validation — no runtime/service/config changed (expect empty)
(none)

## Validation — diff within allowlist
docs/03-reference/dcp/chatgpt-mcp-readonly/DOPEMUX_INIT_REGISTRY_DISCOVERY.md
docs/03-reference/dcp/chatgpt-mcp-readonly/MULTI_PROJECT_REGISTRY_CONTRACT.md
