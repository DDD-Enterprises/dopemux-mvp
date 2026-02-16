---
id: NOTIFICATIONS_UI_MASTER_HISTORY
title: Notifications Ui Master History
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-06'
last_review: '2026-02-06'
next_review: '2026-05-07'
prelude: Notifications Ui Master History (explanation) for dopemux documentation and
  developer workflows.
---
# Notifications & UI Services: Master History & Feature Catalog

**Services**: `adhd-notifier`, `adhd-dashboard`
**Role**: User Interface & Interruption Management
**Status**:
* Notifier: Production
* Dashboard: Production (Port 8097)

---

## 1. Executive Summary

The **Notifications & UI Services** are the "Face" and "Voice" of the system. They are responsible for delivering information to the human in a way that respects their neurodivergent traits—specifically, avoiding "Alarm Fatigue" and interrupting only when necessary.

**Key Feature**: **Context-Aware Notifications**. The system checks the `ADHD Engine` state before sending a ping. If `attention_state="hyperfocus"`, the notification is suppressed or queued, protecting the user's flow.

---

## 2. Feature Catalog

### 🔔 ADHD Notifier (`services/adhd-notifier`)
* **Smart Delivery**: Checks `attention_state` before notifying.
* **Multi-Channel**:
  * **Terminal**: In-band notifications for users living in CLI.
  * **Voice**: "It's time for a break" (TTS).
  * **System**: Native OS notifications.
* **Break Logic**: Enforces Pomodoro-style breaks (25/5) but adapts to flow.

### 📊 ADHD Dashboard (`services/adhd-dashboard`)
* **Visualizer**: Real-time graphs of Energy, Attention, and Cognitive Load.
* **Recommendations**: "Your energy is low. Switch to Documentation tasks."
* **Tech Stack**: FastAPI backend + React frontend (Port 8097).

---

## 3. Architecture Deep Dive

### The Notification Logic
```python
if urgency < HIGH and state == HYPERFOCUS:
    queue_notification()
else:
    deliver_notification()
```

### Integration Points
* **ADHD Engine**: The source of truth for "Can I interrupt?"
* **DopeconBridge**: The transport layer for all notification events (`notification.sent`).

---

## 4. Validated Status (Audit Results)

**✅ Operational:**
* **Notifier**: Health check passing on port 8098.
* **Dashboard**: Validated on port 8097.

**🚧 Future Work:**
* **Wearable Integration**: Sending haptic feedback to watches (planned).

---

*Sources: `adhd-notifier/README.md`, `adhd-dashboard/README.md`.*
