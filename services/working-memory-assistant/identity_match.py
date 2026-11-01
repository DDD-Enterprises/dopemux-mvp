"""Shared workspace-identity matching for dope-memory (event intake and writes)."""

# compose.yml ships DOPE_MEMORY_WORKSPACE_ID=${...:-default}; that literal is a
# placeholder, not an identity, so it does not drive the foreign-workspace check.
PLACEHOLDER_WORKSPACE_IDS = frozenset({"default"})


def workspace_matches(own: str, event_ws: str) -> bool:
    """Own id with no "/" (launcher basename) matches the path's last
    component; an own id containing "/" requires an exact match."""
    if "/" in own:
        return event_ws == own
    return event_ws.rstrip("/").rsplit("/", 1)[-1] == own


def write_identity_error(
    workspace_id: str, instance_id: str, own_workspace: str, own_instance: str
) -> "str | None":
    """Error text if a WRITE request's identity is unacceptable, else None.

    Rejects a blank workspace_id, a workspace_id foreign to the server's own
    (own unset/blank/"default" skips this), and an instance_id that differs
    from a set, non-blank own instance id.
    """
    ws = (workspace_id or "").strip()
    if not ws:
        return "identity check failed: workspace_id is required for writes"
    own_ws = (own_workspace or "").strip()
    if own_ws and own_ws not in PLACEHOLDER_WORKSPACE_IDS and not workspace_matches(own_ws, ws):
        return f"identity check failed: workspace_id {ws!r} is not this server's workspace"
    own_inst = (own_instance or "").strip()
    if own_inst and (instance_id or "").strip() != own_inst:
        return "identity check failed: instance_id does not match this server's instance"
    return None
