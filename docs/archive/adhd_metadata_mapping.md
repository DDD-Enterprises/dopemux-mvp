---
id: adhd_metadata_mapping
title: Adhd_Metadata_Mapping
type: explanation
owner: '@hu3mann'
last_review: '2026-02-02'
next_review: '2026-05-03'
author: '@hu3mann'
date: '2026-02-05'
prelude: Adhd_Metadata_Mapping (explanation) for dopemux documentation and developer
  workflows.
---
# ADHD Metadata Mapping Specification

## Overview

This specification defines the mapping between Dopemux's ADHD metadata fields and task-orchestrator's task model. The goal is to preserve cognitive load semantics, energy levels, session tracking, and other ADHD-related data during integration.

## Dopemux ADHD Data Structure

### Core Fields
- **cognitive_load** (float, 0.0-1.0): Overall cognitive complexity score
- **energy_level** (str): "low", "medium", "high" - Current user energy state
- **session_duration_minutes** (int): Current session length in minutes
- **focus_session_active** (bool): Whether 25-minute focus session is active
- **break_recommended** (bool): Whether break is recommended
- **context_switches_count** (int): Number of context switches in session

### Derived Fields
- **task_priority** (str): Derived from cognitive_load and energy_level
- **recommended_duration** (int): Suggested task duration based on complexity
- **interrupt_risk** (float, 0.0-1.0): Risk of interruption based on session state

## Task-Orchestrator Task Model

### Core Fields
- **tags** (list[str]): Arbitrary tags for task categorization
- **priority** (str): "low", "medium", "high" - Task priority
- **complexity** (float, 0.0-1.0): Task complexity score
- **estimated_duration** (int): Estimated task duration in minutes
- **dependencies** (list[str]): List of dependent task IDs
- **custom_metadata** (dict): Custom key-value pairs for additional data

## Mapping Rules

### 1. Cognitive Load Mapping
- Dopemux `cognitive_load` → Task-Orchestrator `complexity` (direct float mapping)
- `cognitive_load <= 0.3` → Add tag "low_cognitive_load"
- `cognitive_load 0.3-0.7` → Add tag "medium_cognitive_load"
- `cognitive_load > 0.7` → Add tag "high_cognitive_load"

### 2. Energy Level Mapping
- Dopemux `energy_level` → Task-Orchestrator `priority` mapping:
  - "high" → "high"
  - "medium" → "medium"
  - "low" → "low"
- Add tag "energy_{energy_level}" for filtering

### 3. Session State Mapping
- Dopemux `session_duration_minutes` → Task-Orchestrator `custom_metadata.session_duration`
- Dopemux `focus_session_active` → Task-Orchestrator `custom_metadata.focus_active`
- Dopemux `break_recommended` → Task-Orchestrator `custom_metadata.break_needed`
- Dopemux `context_switches_count` → Task-Orchestrator `custom_metadata.context_switches`

### 4. Derived Priority Mapping
- Combine cognitive_load and energy_level:
  - High cognitive_load + Low energy → Priority "high" with tag "risky"
  - High cognitive_load + High energy → Priority "medium" with tag "optimal"
  - Low cognitive_load + Low energy → Priority "low" with tag "safe"

### 5. Duration Estimation
- Dopemux `recommended_duration` → Task-Orchestrator `estimated_duration` (direct mapping)
- If not available, calculate: `estimated_duration = 25 * cognitive_load`

### 6. Interrupt Risk
- Dopemux `interrupt_risk` → Task-Orchestrator `custom_metadata.interrupt_risk` (direct mapping)
- Add tag based on threshold: `interrupt_risk > 0.8` → "high_interrupt_risk"

## Validation Framework

### Semantic Preservation Checks
1. **Range Validation**: Ensure complexity stays within 0.0-1.0
2. **Tag Consistency**: Verify tags match calculated values
3. **Priority Logic**: Validate priority matches cognitive_load + energy_level rules
4. **Duration Range**: Estimated duration must be between 5-120 minutes
5. **Session State**: Focus active must match session duration patterns

### Integration Testing
- Test with edge cases (cognitive_load = 0.0, 1.0, 0.5)
- Validate all tags are generated correctly
- Ensure custom_metadata preserves all ADHD data
- Test round-trip mapping (Dopemux → Task-Orchestrator → Dopemux)

## Implementation Notes

### Mapping Function
```python
def map_adhd_to_task(adhd_data):
    task = {
        "complexity": adhd_data["cognitive_load"],
        "priority": map_energy_to_priority(adhd_data["energy_level"]),
        "estimated_duration": adhd_data.get("recommended_duration", calculate_duration(adhd_data)),
        "tags": generate_tags(adhd_data),
        "custom_metadata": {
            "session_duration": adhd_data["session_duration_minutes"],
            "focus_active": adhd_data["focus_session_active"],
            "break_needed": adhd_data["break_recommended"],
            "context_switches": adhd_data["context_switches_count"],
            "interrupt_risk": adhd_data.get("interrupt_risk", 0.0)
        }
    }
    return task

def generate_tags(adhd_data):
    tags = []

    # Cognitive load tags
    if adhd_data["cognitive_load"] <= 0.3:
        tags.append("low_cognitive_load")
    elif adhd_data["cognitive_load"] <= 0.7:
        tags.append("medium_cognitive_load")
    else:
        tags.append("high_cognitive_load")

    # Energy level tags
    tags.append(f"energy_{adhd_data['energy_level']}")

    # Priority tags
    if adhd_data["cognitive_load"] > 0.7 and adhd_data["energy_level"] == "low":
        tags.append("risky")
    elif adhd_data["cognitive_load"] > 0.7 and adhd_data["energy_level"] == "high":
        tags.append("optimal")

    return tags
```

## Validation Rules

1. **Complexity Range**: `0.0 <= complexity <= 1.0`
2. **Priority Values**: `priority in ["low", "medium", "high"]`
3. **Duration Range**: `5 <= estimated_duration <= 120`
4. **Tag Consistency**: Tags must match cognitive_load and energy_level combinations
5. **Metadata Completeness**: All ADHD session data must be preserved

## Error Handling

- **Mapping Errors**: Log and fallback to default values
- **Validation Failures**: Reject invalid mappings with detailed error messages
- **Data Loss**: Ensure all ADHD metadata is preserved even if mapping fails
- **Fallback Strategy**: Use basic mapping if advanced semantic validation fails
