---
id: adhd-engine-api
title: Adhd Engine Api
type: reference
owner: '@hu3mann'
last_review: '2026-02-02'
next_review: '2026-05-03'
author: '@hu3mann'
date: '2026-02-05'
prelude: Adhd Engine Api (reference) for dopemux documentation and developer workflows.
---
# ADHD Engine API Reference

**Service**: ADHD Engine
**Base URL**: `http://localhost:8095/api/v1/`
**Version**: 2.0
**Last Updated**: 2026-02-02

## Overview

The ADHD Engine provides **15 feature APIs** for cognitive accommodation. All endpoints return JSON unless otherwise specified.

**Feature Categories**:
- Core ML Features (6 endpoints)
- Quick Wins (5 endpoints)
- P1 Priority Features (4 endpoints)

---

## Energy Prediction

### GET /energy-prediction

Get current energy level prediction.

**Response**:
```json
{
  "predicted_level": "high|medium|low",
  "confidence": 0.85,
  "contributing_factors": [
    "Tuesday 10 AM (historically high energy)",
    "25 minutes since last break"
  ],
  "recommendation": "Great time for complex coding tasks"
}
```

### POST /energy-prediction/train

Train ML model on historical data.

**Response**:
```json
{
  "status": "success",
  "samples_trained": 156,
  "model_accuracy": 0.82,
  "model_path": ".models/energy_predictor.pkl"
}
```

---

## Context Management

### POST /context/capture

Capture current development context.

**Request**:
```json
{
  "user_id": "user123",
  "workspace_path": "/Users/user/project"
}
```

**Response**:
```json
{
  "success": true,
  "context_id": "ctx_abc123",
  "active_files": 3,
  "git_status": "2 uncommitted files",
  "timestamp": "2026-02-02T10:30:00Z"
}
```

### GET /context/restore

Restore previously captured context.

**Query Params**:
- `user_id` (required)
- `context_id` (optional, defaults to latest)

**Response**:
```json
{
  "active_files": [
    {"path": "engine.py", "line": 145},
    {"path": "test_engine.py", "line": 67}
  ],
  "recent_symbols": ["handleLogin", "validateToken"],
  "mental_model_summary": "Implementing authentication",
  "next_steps": ["Add tests for edge cases"],
  "git_status": "2 uncommitted files"
}
```

---

## Attention Calibration

### POST /attention/feedback

Provide feedback for calibration.

**Request**:
```json
{
  "user_id": "user123",
  "predicted": "focused",
  "actual": "scattered",
  "context": {
    "time_of_day": 14,
    "energy_level": "low"
  }
}
```

**Response**:
```json
{
  "feedback_recorded": true,
  "total_samples": 6,
  "will_recalibrate": true,
  "message": "Thanks! I'll recalibrate with this feedback."
}
```

### GET /attention/calibration

Get calibration status.

**Query Params**:
- `user_id` (required)

**Response**:
```json
{
  "user_id": "user123",
  "thresholds": {
    "focused_confidence": 0.75,
    "scattered_confidence": 0.60,
    "hyperfocus_duration_min": 40
  },
  "accuracy": 0.87,
  "feedback_samples": 12,
  "recommendation": "Calibration looking good!"
}
```

---

## Correlation Insights

### GET /correlations/insights

Get all correlation insights.

**Response**:
```json
{
  "insights": [
    {
      "insight_type": "task_matching",
      "confidence": 0.82,
      "description": "High energy (9-11 AM) + complex tasks = 2.3x commits",
      "recommendation": "Schedule architecture work for Tuesday/Thursday mornings",
      "source_services": ["energy-tracker", "complexity-coordinator"]
    }
  ]
}
```

### GET /correlations/energy-complexity

Get energy-complexity correlation.

**Response**:
```json
{
  "insight_type": "task_matching",
  "confidence": 0.82,
  "description": "High energy + complex tasks = optimal productivity",
  "recommendation": "Schedule complex work during high-energy windows"
}
```

### GET /correlations/attention-switches

Get attention-switches correlation.

**Response**:
```json
{
  "insight_type": "distraction_pattern",
  "confidence": 0.78,
  "description": "3+ switches in 15 min predicts scattered attention",
  "recommendation": "Set task commitment timer after 2 switches"
}
```

### GET /correlations/break-productivity

Get break-productivity correlation.

**Response**:
```json
{
  "insight_type": "break_optimization",
  "confidence": 0.85,
  "description": "Breaks every 25 min correlate with 40% higher output",
  "recommendation": "Accept more break suggestions"
}
```

---

## Voice Assistant

### POST /voice/command

Process voice command.

**Request**:
```json
{
  "command": "how is my focus"
}
```

**Response**:
```json
{
  "response": "Your attention is focused with 85% confidence. You've been working for 32 minutes. Great job!",
  "spoken": true,
  "command_understood": true
}
```

### GET /voice/status

Get voice assistant status.

**Response**:
```json
{
  "enabled": true,
  "platform": "macos",
  "tts_available": true,
  "rate": 175
}
```

---

## Mobile Push Notifications

### POST /notifications/test

Send test notification.

**Request**:
```json
{
  "user_id": "user123",
  "provider": "ntfy|pushover|happy"
}
```

**Response**:
```json
{
  "success": true,
  "provider": "ntfy",
  "message": "Test notification sent"
}
```

### POST /notifications/break

Send break reminder.

**Request**:
```json
{
  "user_id": "user123",
  "priority": "normal|high",
  "message": "Time for a 5-minute break"
}
```

**Response**:
```json
{
  "success": true,
  "notification_id": "notif_xyz789",
  "sent_at": "2026-02-02T10:45:00Z"
}
```

---

## Overwhelm Detection

### GET /overwhelm/status

Check current overwhelm status.

**Query Params**:
- `user_id` (required)

**Response**:
```json
{
  "overwhelm_detected": true,
  "severity": "moderate|mild|severe|critical",
  "signals": [
    {
      "type": "rapid_switching",
      "confidence": 0.9,
      "evidence": "12 switches in 12 minutes"
    }
  ],
  "circuit_breaker_action": {
    "type": "simplify_task",
    "message": "Let's break this into smaller pieces",
    "suggestion": "Start with writing just one test"
  }
}
```

### POST /overwhelm/reset

Reset overwhelm state after break.

**Request**:
```json
{
  "user_id": "user123"
}
```

**Response**:
```json
{
  "reset": true,
  "message": "Overwhelm state cleared. Fresh start!"
}
```

---

## Hyperfocus Guard

### GET /hyperfocus/status

Get current hyperfocus status.

**Query Params**:
- `user_id` (required)

**Response**:
```json
{
  "hyperfocus_active": true,
  "phase": "active|building|extended|critical|crashed",
  "duration_minutes": 45,
  "protections_applied": 3,
  "actions": ["auto_save", "block_notifications", "gentle_reminder"],
  "recommendation": "Deep work mode active. I'm auto-saving and blocking distractions."
}
```

### GET /hyperfocus/stats

Get hyperfocus session statistics.

**Query Params**:
- `user_id` (required)

**Response**:
```json
{
  "total_sessions": 8,
  "average_duration_minutes": 67,
  "crash_rate": 0.25,
  "total_auto_saves": 124,
  "longest_session_minutes": 145,
  "recommendation": "Healthy pattern. Average 67min sessions."
}
```

---

## End-of-Day Wind Down

### POST /wind-down

Initiate end-of-day ritual.

**Request**:
```json
{
  "user_id": "user123",
  "force": false
}
```

**Response**:
```json
{
  "wind_down_complete": true,
  "summary": "🎉 Wins: 4 tasks, 7 commits, 3.2h focused",
  "quick_wins": [
    "✅ Completed 4 tasks",
    "💻 Made 7 commits",
    "🧠 3.2 hours focused work"
  ],
  "tomorrow_preview": {
    "tasks": [
      "Continue: Authentication refactor",
      "Resolve: JWT vs sessions decision",
      "Warm-up: Review PR comments"
    ],
    "predicted_energy": "medium",
    "context_saved": true
  },
  "recovery": {
    "needed": true,
    "reason": "Energy: low, Focus: 192min",
    "activity": "Rest tonight - avoid screens",
    "bedtime_suggestion": "Earlier than usual"
  },
  "closing_message": "You worked hard today. Your brain needs rest. 💙"
}
```

### GET /wind-down/should-remind

Check if should remind user to wind down.

**Query Params**:
- `user_id` (required)

**Response**:
```json
{
  "should_remind": true,
  "current_hour": 18,
  "message": "🌅 It's about that time. Ready to wrap up for the day?"
}
```

---

## Weekly Pattern Report

### GET /weekly-report

Generate weekly pattern report.

**Query Params**:
- `user_id` (required)
- `force_friday` (optional, default: false)

**Response**:
```json
{
  "report_ready": true,
  "report": "📊 **Weekly Pattern Report**\nWeek of Feb 01 - Feb 05, 2026\n...",
  "visualizations": {
    "focus_by_hour": {"9": 120, "10": 150, "14": 60},
    "energy_by_day": {"Monday": 2.3, "Tuesday": 2.7},
    "break_acceptance": {"accepted": 19, "rejected": 9}
  },
  "action_items": [
    "Schedule important work 09:00-11:00 (best window)",
    "Try accepting more breaks (currently 68%)",
    "Schedule simple tasks at 14:00 (low energy)"
  ]
}
```

### GET /weekly-report/history

Get previous weekly reports.

**Query Params**:
- `user_id` (required)
- `limit` (optional, default: 4)

**Response**:
```json
{
  "reports": [
    {
      "week_start": "2026-01-26",
      "week_end": "2026-01-30",
      "total_focus_minutes": 780,
      "break_acceptance_rate": 0.68
    }
  ]
}
```

---

## Procrastination Detection

### GET /procrastination/status

Check procrastination status.

**Query Params**:
- `user_id` (required)

**Response**:
```json
{
  "procrastination_detected": true,
  "patterns": [
    {
      "type": "research_rabbit_hole|productive_procrastination|task_switching|perfectionism|decision_paralysis",
      "confidence": 0.85,
      "evidence": [
        "Viewed 15 files but edited only 1",
        "Reading for 45 minutes without writing"
      ],
      "duration_minutes": 45
    }
  ],
  "interventions": {
    "awareness_message": "💡 You've been reading for a while without writing...",
    "micro_tasks": [
      {
        "task_id": "micro_123",
        "description": "Write 3 bullet points summarizing what you learned",
        "estimated_minutes": 3
      }
    ],
    "gamification": {
      "current_streak": 3,
      "total_completed": 12,
      "next_milestone": "13 more for Momentum Builder badge"
    },
    "encouragement": "Progress > Perfection. You've got this! 💪"
  }
}
```

### POST /procrastination/complete

Complete a micro-task.

**Request**:
```json
{
  "user_id": "user123",
  "task_id": "micro_123"
}
```

**Response**:
```json
{
  "success": true,
  "task": "Write 3 bullet points summarizing what you learned",
  "streak": 4,
  "total": 13,
  "badge_earned": "🏆 Momentum Builder - 25 micro-tasks!",
  "encouragement": "Nice! One step at a time. 🎯"
}
```

### GET /procrastination/gamification

Get gamification status.

**Query Params**:
- `user_id` (required)

**Response**:
```json
{
  "current_streak": 4,
  "total_completed": 13,
  "next_milestone": "12 more for Momentum Builder badge",
  "badges_earned": [
    "🎖️ Getting Started (5 tasks)"
  ]
}
```

---

## P1 Priority Features

### Task Decomposition

#### POST /task-decomposition/analyze

Analyze task complexity and get decomposition recommendation.

**Request**:
```json
{
  "description": "Migrate authentication to OAuth2",
  "estimated_hours": 4.0,
  "current_energy": "medium"
}
```

**Response**:
```json
{
  "complexity_score": 0.85,
  "complexity_level": "challenging",
  "decomposition_recommended": true,
  "reasoning": "High complexity + multi-hour task = overwhelm risk",
  "estimated_subtasks": 6
}
```

#### POST /task-decomposition/decompose

Decompose task into micro-tasks.

**Request**:
```json
{
  "task_id": "TASK-123",
  "description": "Migrate authentication to OAuth2",
  "estimated_hours": 4.0
}
```

**Response**:
```json
{
  "task_id": "TASK-123",
  "subtasks": [
    {
      "id": "TASK-123-1",
      "title": "Research OAuth2 providers",
      "estimated_minutes": 15,
      "energy_requirement": "medium",
      "order": 1
    }
  ],
  "total_subtasks": 6,
  "pattern_used": "implementation"
}
```

---

### Medication Effectiveness

#### POST /medication/dose

Log medication dose.

**Request**:
```json
{
  "medication_name": "Adderall XR",
  "dosage_mg": 20.0,
  "medication_type": "stimulant_long",
  "notes": "With breakfast"
}
```

**Response**:
```json
{
  "dose_id": "DOSE-123",
  "logged_at": "2026-02-02T08:15:00Z",
  "expected_peak": "2026-02-02T10:15:00Z",
  "expected_duration_hours": 10
}
```

#### POST /medication/side-effect

Log side effect.

**Request**:
```json
{
  "effect": "mild_headache",
  "severity": "mild",
  "notes": "Afternoon, may be dehydration"
}
```

#### GET /medication/report

Generate effectiveness report.

**Query Parameters**:
- `days` (optional): Days to include (default: 30)

**Response**:
```json
{
  "period": "2026-01-03 to 2026-02-02",
  "doses": 28,
  "adherence_rate": 0.93,
  "peak_effectiveness_time": "9:30 AM - 2:00 PM",
  "recommendations": [
    "Consistent peak performance 9:30 AM - 2:00 PM"
  ]
}
```

---

### Social Battery

#### POST /social-battery/interaction

Log social interaction.

**Request**:
```json
{
  "interaction_type": "meeting_large",
  "duration_minutes": 60,
  "masking_level": "high",
  "participants_count": 15,
  "description": "All-hands meeting"
}
```

**Response**:
```json
{
  "drain_amount": 150.0,
  "new_battery_level": 50.0,
  "state": "low",
  "recovery_recommended": true
}
```

#### GET /social-battery/status

Get current battery status.

**Response**:
```json
{
  "battery_level": 50.0,
  "state": "low",
  "recovery_recommendation": {
    "type": "scheduled",
    "description": "Schedule 30min recovery after current meeting"
  }
}
```

#### POST /social-battery/predict

Predict calendar impact.

**Request**:
```json
{
  "upcoming_events": [
    {"type": "meeting_small", "duration": 30, "masking": "medium"}
  ]
}
```

**Response**:
```json
{
  "current_level": 75.0,
  "predicted_end_of_day_level": 25.0,
  "recovery_needed": true
}
```

---

### Working Memory

#### POST /working-memory/capture

Quick thought capture (< 2 seconds).

**Request**:
```json
{
  "content": "TODO: Fix bug in auth.py line 156",
  "priority": "high"
}
```

**Response**:
```json
{
  "thought_id": "TH-1",
  "type": "todo",
  "current_file": "services/adhd_engine/engine.py",
  "current_line": 42
}
```

#### POST /working-memory/breadcrumb

Drop context breadcrumb before interruption.

**Request**:
```json
{
  "description": "Implementing OAuth client",
  "file_path": "auth.py",
  "line_number": 156,
  "goal": "Get OAuth working for production"
}
```

**Response**:
```json
{
  "breadcrumb_id": "BC-5",
  "hints": [
    "Open auth.py",
    "Go to line 156"
  ]
}
```

#### POST /working-memory/interruption

Detect and record interruption.

**Request**:
```json
{
  "interruption_type": "meeting",
  "source": "calendar"
}
```

**Response**:
```json
{
  "interruption_id": "INT-3",
  "context_saved": true,
  "active_thoughts_count": 5
}
```

#### POST /working-memory/restore

Restore context after interruption.

**Response**:
```json
{
  "description": "You were implementing OAuth client in auth.py at line 156",
  "goal": "Get OAuth working for production",
  "hints": ["Open auth.py", "Go to line 156"]
}
```

#### GET /working-memory/thoughts

Get active thoughts.

**Query Parameters**:
- `active_only` (optional): Filter to uncompleted thoughts
- `priority` (optional): Filter by priority

**Response**:
```json
{
  "thoughts": [
    {
      "thought_id": "TH-1",
      "content": "TODO: Fix bug in auth.py line 156",
      "type": "todo",
      "priority": "high",
      "completed": false
    }
  ],
  "total": 8,
  "active": 5
}
```

#### PUT /working-memory/thoughts/{id}

Mark thought as completed.

**Request**:
```json
{
  "completed": true
}
```

#### GET /working-memory/reminder

Get forgotten context reminder.

**Response**:
```json
{
  "reminder": "💭 You have 8 active thoughts...",
  "needs_attention": true
}
```

---

## Error Responses

All endpoints return standard error format:

```json
{
  "error": "Error description",
  "status": 400|404|500,
  "details": "Additional context if available"
}
```

**Common Errors**:
- `400 Bad Request`: Invalid parameters
- `404 Not Found`: User or resource not found
- `500 Internal Server Error`: Server-side error
- `503 Service Unavailable`: Dependency unavailable (Redis, ConPort, etc.)

---

## Rate Limiting

No rate limiting currently implemented. All endpoints are free-form access.

---

## Authentication

Currently no authentication. Future versions will support:
- API key authentication
- JWT tokens
- Session-based auth

---

## Webhooks (Future)

Planned webhook support for:
- Overwhelm detected
- Hyperfocus critical
- End-of-day reminder
- Weekly report ready
- **Social battery critical** (NEW)
- **Medication reminder** (NEW)
- **Context forgotten** (NEW)
- **Task decomposition suggested** (NEW)

---

## SDK Support (Future)

Planned SDKs:
- Python client
- JavaScript/TypeScript client
- CLI tool

---

For implementation details, see individual feature source files in `services/adhd_engine/`.
