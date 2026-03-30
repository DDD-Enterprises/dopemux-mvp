# Implementation Plan: Fix Alternate Routing (Gemini/Grok/OpenAI)

## Objective
Fix the Dopemux alternate routing system to allow Claude Code to use external models (Grok, Gemini, OpenAI) through LiteLLM and CCR proxies. This involves fixing bugs in validation, configuration generation, and environment variable handling, as well as adding CLI commands to toggle between routing modes.

## Key Files & Context
1.  `templates/routing.yaml`: Global routing configuration template.
2.  `src/dopemux/routing_config.py`: Logic for loading, validating, and generating proxy configurations.
3.  `src/dopemux/launchd_services.py`: Management of background services (LiteLLM, CCR) and their wrapper scripts.
4.  `src/dopemux/routing_cli.py`: CLI interface for routing management.
5.  `src/dopemux/statusline_integration.py`: Integration with the statusline to show the current routing mode.

## Implementation Steps

### Phase 1: Configuration & Validation Fixes
1.  **Update `templates/routing.yaml`**: Replace the entire file with the new configuration that includes comprehensive model definitions, slots, and fallbacks.
2.  **Update `src/dopemux/routing_config.py`**:
    *   **Change 2a**: Update `validate()` to accept either `model_id` or `litellm_model`.
    *   **Change 2b**: Update `generate_litellm_config()` to use `model_id` or `litellm_model`.
    *   **Change 2c**: Replace `generate_ccr_config()` with a version that properly maps slots and models for the Claude Code Router.

### Phase 2: Service Management Improvements
1.  **Update `src/dopemux/launchd_services.py`**:
    *   **Change 3a**: Update `_generate_litellm_wrapper_script()` to export environment variables from `routing.env`.
    *   **Change 3b**: Update `_generate_ccr_wrapper_script()` to export environment variables.
    *   **Change 3c**: Update `_generate_ccr_config()` to write to the correct path (`~/.claude-code-router/config.json`) and use real key values instead of placeholders.
    *   **Change 3d**: Add the `_read_routing_env()` helper method to read key-value pairs from the environment file.

### Phase 3: CLI & Integration
1.  **Update `src/dopemux/routing_cli.py`**:
    *   **Change 4a**: Add `pathlib.Path` import.
    *   **Change 4b**: Add `_set_routing_mode()` and `_set_claude_base_url()` helper functions.
    *   **Change 4c**: Add `api` and `direct` commands to the `routing` group to allow switching modes.
2.  **Update `src/dopemux/statusline_integration.py`**: Replace the entire file to include routing mode information in the statusline.

## Verification & Testing

### Static Validation
1.  Run the verification script provided in the plan to ensure the routing config loads and validates correctly.
    ```bash
    python -c "
    from dopemux.routing_config import RoutingConfig
    from pathlib import Path
    import yaml
    c = RoutingConfig(config_path=None)
    c.config_path = Path('templates/routing.yaml')
    with open(c.config_path) as f:
        c.config = yaml.safe_load(f)
    c._loaded = True
    c.validate()
    print('Validation OK:', c.config['mode'], len(c.config['models']), 'models')
    "
    ```

### Unit Tests
1.  Run `pytest tests/ -x -q --tb=short` to ensure no regressions in existing functionality.

### CLI Verification
1.  Run `python -m dopemux routing --help` and verify `api` and `direct` commands are listed.
2.  Test `dopemux routing api --no-restart` and verify it updates `routing.yaml` and `~/.claude/settings.json`.
3.  Test `dopemux routing direct` and verify it reverts the changes.

## Rollback Plan
In case of failure:
1.  Revert code changes using `git checkout`.
2.  Manually restore `~/.claude/settings.json` if it was modified (set `baseUrl` back to `https://api.anthropic.com`).
3.  Delete `~/.claude-code-router/config.json` if it was created and is causing issues.
