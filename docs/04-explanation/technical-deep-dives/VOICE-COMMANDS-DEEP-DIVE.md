---
id: VOICE-COMMANDS-DEEP-DIVE
title: Voice Commands Deep Dive
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-09'
last_review: '2026-02-09'
next_review: '2026-05-10'
prelude: Voice Commands Deep Dive (explanation) for dopemux documentation and developer
  workflows.
---
# Voice Commands: Deep Technical Analysis

## SECTION 1: TECHNICAL REPORT

### Executive Summary & Strategic Intent
**Voice Commands** is a cognitive plane service that enables natural language task interactions. It specializes in "task decomposition," taking high-level voice inputs (e.g., "how do I implement auth?") and breaking them down into actionable sub-tasks. It leverages the **Zen MCP** for the heavy lifting of decomposition and stores findings in **ConPort** via **DopeconBridge**.

### Architecture & Core Components (Validated)
The service is a FastAPI-based Python application configured to run as a backend utility.

* **Service Type**: Internal API (Python/FastAPI)
* **Default Port**: 3007
* **Location**: `services/voice-commands`
* **Orchestration**: *Missing* from `docker-compose.master.yml`.
* **Dependencies**:
  * **Zen MCP**: (Default `http://localhost:3003`) for decomposition logic.
  * **DopeconBridge**: (Default `http://localhost:3016`) for data persistence.
  * **ADHD Engine**: (Default `http://localhost:8095`) for attention-state context.

**Core Modules**:
1. **`voice_api.py`**: The entry point. Handles the `/api/v1/decompose-task` POST endpoint.
1. **`voice_task_decomposer.py`**: The logic layer. Extracts task descriptions from strings via regex and coordinates calls to Zen and ADHD Engine.
1. **`bridge_adapter.py`**: Handles pushing the final decomposition into DopeconBridge.

### Failure & Drift Analysis
**Status**: **Not Running / Un-orchestrated**.

**Findings**:
1. **Orchestration Gap**: While a `Dockerfile` exists, the service is not included in the master orchestration. This suggests it is a peripheral feature not currently enabled in the baseline stack.
1. **Missing Documentation**: No `README.md` exists within the service directory.
1. **Hardcoded Defaults**: While it uses environment variables, several internal URLs (like `adhd_engine_url` in `VoiceTaskDecomposer`) have hardcoded `localhost` fallbacks which may cause issues in containerized environments if not correctly overridden.

### Integration Patterns & Data Flow
1. **Input**: Receives `voice_input` and `user_id` via HTTP POST.
1. **Context**: Fetch user attention state from `ADHD Engine`.
1. **Process**: Call `Zen MCP` to perform the actual decomposition based on the task prompt and ADHD context.
1. **Persistence**: Post result back to `DopeconBridge`.
1. **Output**: Returns a structured task breakdown to the caller.

### Testing, Performance, Limitations & Opportunities
* **Testing**: Test coverage is sparse. Internal tests exist in `adhd_engine` (`test_voice_assistant.py`) but not within the component itself.
* **Limitations**:
  * **Synchronous Processing**: The decomposition involves multiple external LLM/MCP calls and could benefit from more robust error handling and task queuing.
* **Opportunities**:
  * **Orchestrate**: Add to standard dev stack.
  * **Extend**: Integrate with other voice-to-text providers or UI-level voice capture utilities.

## SECTION 2: EVIDENCE TRAIL

### Inventory Evidence (Phase 1)
* **Source Code**: `services/voice-commands`.
* **Structure**: Clear separation between API, Decomposer, and Bridge layers.

### Failure & Drift Findings (Phase 2)
* **Orchestration**: Confirmed absence from `docker-compose.master.yml`.
* **Runtime**: No container found under `docker ps -a`.

## SECTION 3: LIVING DOCUMENTATION METADATA
* Last Validated: 2026-02-09
* Confidence Level: 95% (Code is well-structured and easy to read)
* Evidence Quality Score: High
* Evolution Log:
  * 2026-02-09: Initial Deep Dive. Found functional code but lacking orchestration and documentation.
