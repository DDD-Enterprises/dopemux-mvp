import inspect, pathlib
from dopemux.pcp.bridge import fastapi_bridge as fb
_PCP = pathlib.Path(fb.__file__).resolve().parents[1]
_FORBIDDEN = ("queue_drain", "batch_resolve_and_merge", "pr_merge_specialist")
def test_no_forbidden_writer_wiring_in_pcp():
    for path in _PCP.rglob("*.py"):
        text = path.read_text()
        for tok in _FORBIDDEN:
            assert tok not in text, f"Red Line #15: forbidden token {tok!r} in {path}"
def test_bridge_factories_default_no_writer():
    for fn in (fb.create_bridge_router, fb.create_bridge_app):
        assert inspect.signature(fn).parameters["writer_registry"].default is None
def test_execute_without_writer_is_rejected():
    res = fb.route_mutation({"operation_ref": "op1", "target_surface": "s"}, live_write_ready=None, execute=True)
    assert res["executed"] is False and res["permitted"] is False
