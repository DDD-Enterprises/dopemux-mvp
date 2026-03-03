from pathlib import Path
from dopemux.instance_manager import InstanceManager

def test_get_instance_env_vars_offsets():
    workspace_root = Path("/tmp/dopemux-test")
    manager = InstanceManager(workspace_root)
    
    # Test Instance A (Port Base 3000)
    env_a = manager.get_instance_env_vars("A", 3000, workspace_root)
    assert env_a["DOPEMUX_PORT_BASE"] == "3000"
    assert env_a["DOPECON_BRIDGE_PORT"] == "3000"
    assert env_a["PAL_PORT"] == "3003"
    assert env_a["CONPORT_HTTP_PORT"] == "3004"
    assert env_a["CONPORT_MCP_PORT"] == "3005"
    assert env_a["SERENA_PORT"] == "3006"
    assert env_a["GPT_RESEARCHER_PORT"] == "3009"
    assert env_a["DOPE_CONTEXT_PORT"] == "3010"
    assert env_a["EXA_PORT"] == "3011"
    assert env_a["DESKTOP_COMMANDER_PORT"] == "3012"
    assert env_a["TASK_ORCHESTRATOR_PORT"] == "3014"
    assert env_a["LEANTIME_BRIDGE_PORT"] == "3015"
    assert env_a["DOPE_MEMORY_PORT"] == "3020"
    assert env_a["ADHD_ENGINE_PORT"] == "3025"

    # Test Instance B (Port Base 3030)
    env_b = manager.get_instance_env_vars("B", 3030, workspace_root)
    assert env_b["DOPEMUX_PORT_BASE"] == "3030"
    assert env_b["DOPECON_BRIDGE_PORT"] == "3030"
    assert env_b["CONPORT_HTTP_PORT"] == "3034"
    assert env_b["CONPORT_MCP_PORT"] == "3035"
    assert env_b["TASK_ORCHESTRATOR_PORT"] == "3044"
