---
id: COMPONENT_7_ENVIRONMENTAL_INTERRUPTION_SHIELD
title: Component_7_Environmental_Interruption_Shield
type: explanation
owner: '@hu3mann'
last_review: '2025-11-10'
next_review: '2026-02-08'
---
# Component 7: Environmental Interruption Shield - Technical Specification

**Version**: 1.0.0
**Status**: Design Phase
**Author**: Dopemux Architecture Team
**Date**: 2025-10-20
**Related Decision**: ConPort Decision #188
**Tags**: `component-7`, `adhd-interruption-prevention`, `external-interruptions`, `architecture-3.0`

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Architecture Overview](#architecture-overview)
3. [System Components](#system-components)
4. [Data Models](#data-models)
5. [API Integrations](#api-integrations)
6. [Urgency Scoring Algorithm](#urgency-scoring-algorithm)
7. [Integration Points](#integration-points)
8. [Privacy & Security](#privacy--security)
9. [Testing Strategy](#testing-strategy)
10. [Deployment Plan](#deployment-plan)
11. [Performance Targets](#performance-targets)
12. [Monitoring & Metrics](#monitoring--metrics)

---

## Executive Summary

### Problem Statement

Dopemux has excellent internal interruption handling (hyperfocus protection, context switch recovery, false-start detection) but **ZERO coverage of external interruptions** (Slack, meetings, notifications). ADHD developers lose 15-25 minutes per external interruption rebuilding mental models.

### Solution

Environmental Interruption Shield: A three-layer defense system that automatically activates based on ADHD Engine attention state to prevent, filter, and recover from external interruptions.

### Key Metrics

| Metric | Baseline | Target | Improvement |
|--------|----------|--------|-------------|
| External interruptions/day | ~20 | <8 | 60% reduction |
| Context recovery time | 15-25 min | <2 sec | 98% reduction |
| Task completion rate | 85% | 92% | +7% |
| Focus session duration | 25 min | 35 min | +40% |

### Implementation Timeline

- **Phase 1** (4 weeks): macOS + Slack MVP
- **Phase 2** (3 weeks): Calendar integration, notification batching
- **Phase 3** (4 weeks): Multi-platform expansion

---

## Architecture Overview

### Three-Layer Defense System

```
┌─────────────────────────────────────────────────────────────┐
│                    Layer 1: Predictive Prevention            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  Auto-DND    │  │   Meeting    │  │    Smart     │      │
│  │  Activation  │  │    Buffers   │  │  Scheduling  │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    Layer 2: Active Filtering                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Urgency    │  │   Message    │  │ Notification │      │
│  │   Scoring    │  │   Queuing    │  │   Batching   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    Layer 3: Rapid Recovery                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  Component 6 │  │   Desktop    │  │   ConPort    │      │
│  │   Recovery   │  │  Commander   │  │   Context    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

### High-Level Component Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                        ADHD Engine                               │
│                  (Attention State Detection)                     │
└────────────────────────┬─────────────────────────────────────────┘
                         │ attention_state_changed event
                         ↓
┌──────────────────────────────────────────────────────────────────┐
│                  InterruptionShield Service                      │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  ShieldCoordinator                                         │ │
│  │  - monitor_attention_state()                               │ │
│  │  - activate_shields()                                      │ │
│  │  - deactivate_shields()                                    │ │
│  └────────────────────────────────────────────────────────────┘ │
│  ┌────────────────┐  ┌────────────────┐  ┌─────────────────┐  │
│  │ DNDManager     │  │ MessageTriage  │  │ NotificationMgr │  │
│  │ - macOS Focus  │  │ - Urgency      │  │ - Batch         │  │
│  │ - Slack Status │  │ - Queue        │  │ - Filter        │  │
│  └────────────────┘  └────────────────┘  └─────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
                         ↓
┌──────────────────────────────────────────────────────────────────┐
│                    External Integrations                         │
│  ┌────────────┐  ┌──────────────┐  ┌────────────────────────┐  │
│  │ Slack API  │  │ Calendar API │  │ macOS Notification Ctr │  │
│  └────────────┘  └──────────────┘  └────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
```

---

## System Components

### 1. ShieldCoordinator (Core Orchestration)

**Responsibility**: Monitor ADHD Engine attention state and coordinate shield activation/deactivation.

**Location**: `services/adhd_engine/domains/interruption-shield/core/coordinator.py`

```python
class ShieldCoordinator:
    """
    Coordinates interruption shield activation based on ADHD Engine state.

    Subscribes to ADHD Engine attention state changes and activates/deactivates
    shields across all integrated services (macOS, Slack, notifications).
    """

    def __init__(
        self,
        adhd_engine_client: ADHDEngineClient,
        dnd_manager: DNDManager,
        message_triage: MessageTriage,
        notification_manager: NotificationManager,
        config: ShieldConfig
    ):
        self.adhd_engine = adhd_engine_client
        self.dnd = dnd_manager
        self.triage = message_triage
        self.notifications = notification_manager
        self.config = config

        # State tracking
        self.shields_active = False
        self.current_attention_state = None
        self.activation_timestamp = None

    async def start(self):
        """Start monitoring ADHD Engine and coordinating shields."""
        # Subscribe to attention state changes
        await self.adhd_engine.subscribe_attention_state(
            callback=self.on_attention_state_changed
        )

        # Start background monitoring
        asyncio.create_task(self._monitor_productivity())

    async def on_attention_state_changed(
        self,
        new_state: AttentionState,
        user_id: str
    ):
        """
        Handle attention state changes from ADHD Engine.

        FOCUSED/HYPERFOCUS → Activate shields
        SCATTERED/TRANSITIONING → Deactivate shields
        """
        self.current_attention_state = new_state

        if new_state in [AttentionState.FOCUSED, AttentionState.HYPERFOCUS]:
            await self.activate_shields(user_id)
        else:
            await self.deactivate_shields(user_id)

    async def activate_shields(self, user_id: str):
        """Activate all interruption shields."""
        if self.shields_active:
            return  # Already active

        logger.info(f"Activating interruption shields for user {user_id}")

        # Activate in parallel
        await asyncio.gather(
            self.dnd.enable_macos_focus_mode(),
            self.dnd.set_slack_status(
                status="In focus mode",
                until=self._calculate_end_time()
            ),
            self.notifications.enable_batching(),
            self.triage.start_queuing()
        )

        self.shields_active = True
        self.activation_timestamp = datetime.now()

        # Log to ConPort for tracking
        await self._log_to_conport(user_id, "shields_activated")

    async def deactivate_shields(self, user_id: str):
        """Deactivate shields and deliver queued messages."""
        if not self.shields_active:
            return

        logger.info(f"Deactivating interruption shields for user {user_id}")

        # Deactivate and deliver queued content
        await asyncio.gather(
            self.dnd.disable_macos_focus_mode(),
            self.dnd.clear_slack_status(),
            self.notifications.disable_batching_and_deliver(),
            self.triage.stop_queuing_and_deliver()
        )

        self.shields_active = False

        # Show summary of what was queued
        await self._show_queued_summary(user_id)

        # Log to ConPort
        duration = (datetime.now() - self.activation_timestamp).seconds
        await self._log_to_conport(
            user_id,
            "shields_deactivated",
            metadata={"duration_seconds": duration}
        )

    async def _monitor_productivity(self):
        """
        Detect false positive focus states.

        If no code changes in 15 minutes during FOCUSED state,
        downgrade to SCATTERED to prevent blocking communications.
        """
        while True:
            await asyncio.sleep(60)  # Check every minute

            if not self.shields_active:
                continue

            duration = (datetime.now() - self.activation_timestamp).seconds

            if duration > 900:  # 15 minutes
                # Check for productivity indicators
                has_activity = await self._check_code_activity()

                if not has_activity:
                    logger.warning(
                        "No code activity detected in 15min during FOCUSED state. "
                        "Deactivating shields to prevent communication blockage."
                    )
                    await self.deactivate_shields(user_id="current_user")

    async def _check_code_activity(self) -> bool:
        """Check if user has made code changes recently."""
        # Query Serena for recent file modifications
        # Query git for uncommitted changes
        # Return True if any activity detected
        pass

    async def _calculate_end_time(self) -> datetime:
        """Calculate when to auto-deactivate shields (default: 25min)."""
        return datetime.now() + timedelta(minutes=self.config.default_duration)

    async def _show_queued_summary(self, user_id: str):
        """Show user a summary of queued communications."""
        summary = await self.triage.get_queued_summary()

        # Display via Desktop Commander notification
        # "5 messages queued (0 urgent). Summary: Team discussing deploy schedule."
        pass

    async def _log_to_conport(
        self,
        user_id: str,
        event: str,
        metadata: dict = None
    ):
        """Log shield events to ConPort for analytics."""
        # Log to ConPort custom_data for tracking effectiveness
        pass
```

### 2. DNDManager (Do Not Disturb Automation)

**Responsibility**: Manage macOS Focus Mode and Slack status.

**Location**: `services/adhd_engine/domains/interruption-shield/integrations/dnd_manager.py`

```python
class DNDManager:
    """
    Manages Do Not Disturb across macOS and Slack.

    Handles:
    - macOS Focus Mode activation/deactivation
    - Slack status updates ("In focus mode until...")
    - Window management via Desktop Commander
    """

    def __init__(
        self,
        slack_client: SlackClient,
        desktop_commander: DesktopCommanderClient,
        config: DNDConfig
    ):
        self.slack = slack_client
        self.desktop = desktop_commander
        self.config = config

    async def enable_macos_focus_mode(self):
        """Enable macOS Focus Mode via AppleScript."""
        script = """
        tell application "System Events"
            tell process "ControlCenter"
                set focusMode to menu bar item "Focus" of menu bar 1
                click focusMode
                click menu item "Work" of menu 1 of focusMode
            end tell
        end tell
        """

        result = await asyncio.create_subprocess_exec(
            "osascript", "-e", script,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        await result.communicate()

        if result.returncode != 0:
            logger.error("Failed to enable macOS Focus Mode")
            # Fallback: Use Desktop Commander to minimize windows
            await self.desktop.minimize_non_essential_windows()

    async def disable_macos_focus_mode(self):
        """Disable macOS Focus Mode."""
        script = """
        tell application "System Events"
            tell process "ControlCenter"
                set focusMode to menu bar item "Focus" of menu bar 1
                click focusMode
                click menu item "Off" of menu 1 of focusMode
            end tell
        end tell
        """

        await self._run_applescript(script)

    async def set_slack_status(self, status: str, until: datetime):
        """Set Slack status with expiration."""
        expiration_timestamp = int(until.timestamp())

        await self.slack.users_profile_set(
            profile={
                "status_text": status,
                "status_emoji": ":no_entry_sign:",
                "status_expiration": expiration_timestamp
            }
        )

        # Also set presence to "away"
        await self.slack.users_setPresence(presence="away")

    async def clear_slack_status(self):
        """Clear Slack status and set presence to active."""
        await self.slack.users_profile_set(
            profile={
                "status_text": "",
                "status_emoji": "",
                "status_expiration": 0
            }
        )

        await self.slack.users_setPresence(presence="auto")
```

### 3. MessageTriage (Urgency Scoring & Queuing)

**Responsibility**: Score message urgency and queue non-critical communications.

**Location**: `services/adhd_engine/domains/interruption-shield/triage/message_triage.py`

```python
class MessageTriage:
    """
    Urgency-based message filtering and queuing.

    Uses on-device ML model to score urgency (privacy-first).
    Queues non-urgent messages for break-time delivery.
    """

    def __init__(
        self,
        urgency_scorer: UrgencyScorer,
        message_queue: MessageQueue,
        config: TriageConfig
    ):
        self.scorer = urgency_scorer
        self.queue = message_queue
        self.config = config
        self.queuing_active = False

    async def start_queuing(self):
        """Start queuing incoming messages."""
        self.queuing_active = True
        logger.info("Message queuing activated")

    async def stop_queuing_and_deliver(self):
        """Stop queuing and deliver all queued messages."""
        self.queuing_active = False

        # Deliver queued messages with summary
        queued = await self.queue.get_all()
        summary = await self._generate_summary(queued)

        # Show summary via notification
        await self._show_summary_notification(summary)

        # Mark all as delivered
        await self.queue.clear()

    async def handle_incoming_message(self, message: SlackMessage):
        """
        Process incoming Slack message.

        If shields active:
        - Score urgency
        - If CRITICAL → deliver immediately
        - Else → queue for later
        """
        if not self.queuing_active:
            # Shields not active, pass through
            return

        # Score urgency
        urgency = await self.scorer.score(message)

        if urgency == UrgencyLevel.CRITICAL:
            # Allow critical interruptions
            logger.warning(
                f"Critical message from {message.user}: {message.text[:50]}"
            )
            await self._deliver_immediately(message)
        else:
            # Queue for later
            await self.queue.add(message, urgency)
            logger.info(f"Queued {urgency.name} message from {message.user}")

    async def get_queued_summary(self) -> dict:
        """Generate summary of queued messages."""
        queued = await self.queue.get_all()

        return {
            "total_count": len(queued),
            "critical_count": sum(1 for m in queued if m.urgency == UrgencyLevel.CRITICAL),
            "high_count": sum(1 for m in queued if m.urgency == UrgencyLevel.HIGH),
            "channels": list(set(m.channel for m in queued)),
            "top_senders": Counter(m.user for m in queued).most_common(3)
        }

    async def _generate_summary(self, messages: List[QueuedMessage]) -> str:
        """Generate AI summary of queued messages using OpenAI."""
        if len(messages) == 0:
            return "No messages queued during focus session."

        # Batch messages by channel for context
        by_channel = defaultdict(list)
        for msg in messages:
            by_channel[msg.channel].append(msg)

        # Generate summary using OpenAI
        summaries = []
        for channel, msgs in by_channel.items():
            text = "\n".join(f"{m.user}: {m.text}" for m in msgs[:10])

            summary = await openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[{
                    "role": "system",
                    "content": "Summarize this Slack conversation in 1-2 sentences."
                }, {
                    "role": "user",
                    "content": text
                }],
                max_tokens=100
            )

            summaries.append(f"#{channel}: {summary.choices[0].message.content}")

        return "\n".join(summaries)
```

### 4. UrgencyScorer (On-Device ML Model)

**Responsibility**: Score message urgency using privacy-first on-device processing.

**Location**: `services/adhd_engine/domains/interruption-shield/triage/urgency_scorer.py`

```python
from enum import Enum
from typing import List
import re

class UrgencyLevel(Enum):
    """Message urgency levels."""
    CRITICAL = 4  # Production incidents, emergencies (interrupt allowed)
    HIGH = 3      # Important but not urgent (notify at next break)
    MEDIUM = 2    # Standard messages (batch for break)
    LOW = 1       # FYI, can wait (end-of-day summary)

class UrgencyScorer:
    """
    On-device urgency scoring using keyword matching and heuristics.

    Phase 1: Rule-based scoring (privacy-first, no cloud)
    Phase 2: Fine-tuned local ML model
    """

    def __init__(self, config: UrgencyScorerConfig):
        self.config = config

        # User-configurable keywords
        self.critical_keywords = config.critical_keywords or [
            "urgent", "asap", "emergency", "critical", "p0", "sev0",
            "production down", "outage", "incident", "all hands",
            "security breach", "data loss"
        ]

        self.high_keywords = config.high_keywords or [
            "important", "p1", "sev1", "blocker", "high priority",
            "deadline", "today", "this morning", "right now"
        ]

        # User-configurable VIP senders
        self.vip_users = config.vip_users or []  # CEO, manager, oncall

    async def score(self, message: SlackMessage) -> UrgencyLevel:
        """
        Score message urgency using multiple signals.

        Signals:
        1. Keyword matching (configurable)
        2. Sender importance (VIP list)
        3. Time sensitivity (mentions "today", "now")
        4. Channel type (DMs higher urgency than channels)
        5. @mentions (direct mention = higher urgency)
        """
        score = 0

        # Signal 1: Keyword matching
        text_lower = message.text.lower()

        if any(kw in text_lower for kw in self.critical_keywords):
            return UrgencyLevel.CRITICAL  # Immediate interrupt

        if any(kw in text_lower for kw in self.high_keywords):
            score += 2

        # Signal 2: Sender importance
        if message.user in self.vip_users:
            score += 2

        # Signal 3: Time sensitivity
        time_patterns = [r'\btoday\b', r'\bnow\b', r'\basap\b', r'\bthis (morning|afternoon)\b']
        if any(re.search(pattern, text_lower) for pattern in time_patterns):
            score += 1

        # Signal 4: Channel type
        if message.channel_type == "im":  # Direct message
            score += 1

        # Signal 5: @mentions
        if f"<@{self.config.user_id}>" in message.text:
            score += 1

        # Convert score to urgency level
        if score >= 4:
            return UrgencyLevel.HIGH
        elif score >= 2:
            return UrgencyLevel.MEDIUM
        else:
            return UrgencyLevel.LOW

    async def learn_from_feedback(
        self,
        message: SlackMessage,
        actual_urgency: UrgencyLevel,
        user_corrected: bool
    ):
        """
        Learn from user corrections to improve scoring.

        Phase 2: Use this data to fine-tune ML model.
        For now, just log for analysis.
        """
        if user_corrected:
            logger.info(
                f"User corrected urgency: {message.text[:50]} "
                f"-> {actual_urgency.name}"
            )
            # Store in ConPort for future ML training
            await self._log_correction(message, actual_urgency)
```

---

## Data Models

### ShieldState

```python
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

@dataclass
class ShieldState:
    """Current state of interruption shields."""

    user_id: str
    active: bool
    attention_state: AttentionState
    activated_at: Optional[datetime]
    deactivated_at: Optional[datetime]
    duration_seconds: int

    # Metrics
    messages_queued: int
    messages_critical: int
    notifications_batched: int
    interruptions_prevented: int

    # Configuration
    mode: ShieldMode  # ASSIST or ENFORCE
    auto_deactivate_after: int  # minutes

class ShieldMode(Enum):
    """Shield operation modes."""
    ASSIST = "assist"      # Suggestions only, user can override
    ENFORCE = "enforce"    # Strict filtering, limited overrides
```

### QueuedMessage

```python
@dataclass
class QueuedMessage:
    """Message queued during focus session."""

    id: str
    user: str
    channel: str
    channel_type: str  # "channel", "im", "mpim"
    text: str
    timestamp: datetime
    urgency: UrgencyLevel

    # Metadata for summary generation
    thread_ts: Optional[str]
    reactions: List[str]
    attachments: List[dict]

@dataclass
class MessageQueue:
    """In-memory queue of messages (Redis-backed for persistence)."""

    messages: List[QueuedMessage]
    max_size: int = 100

    async def add(self, message: QueuedMessage):
        """Add message to queue."""
        if len(self.messages) >= self.max_size:
            # Remove oldest LOW urgency message
            self.messages = sorted(
                self.messages,
                key=lambda m: (m.urgency.value, m.timestamp)
            )[1:]

        self.messages.append(message)

    async def get_all(self) -> List[QueuedMessage]:
        """Get all queued messages, sorted by urgency."""
        return sorted(
            self.messages,
            key=lambda m: (m.urgency.value, m.timestamp),
            reverse=True
        )

    async def clear(self):
        """Clear all queued messages."""
        self.messages = []
```

### ShieldConfig

```python
@dataclass
class ShieldConfig:
    """User-configurable shield settings."""

    # Shield activation
    auto_activate: bool = True  # Auto-activate on FOCUSED state
    default_duration: int = 25  # minutes

    # Urgency scoring
    critical_keywords: List[str] = field(default_factory=list)
    high_keywords: List[str] = field(default_factory=list)
    vip_users: List[str] = field(default_factory=list)

    # Mode
    mode: ShieldMode = ShieldMode.ASSIST

    # Overrides
    allow_manual_override: bool = True
    override_cooldown: int = 10  # minutes before auto-reactivate

    # Privacy
    enable_ai_summarization: bool = True
    store_message_content: bool = False  # Only store metadata
```

---

## API Integrations

### Slack API

**Required Scopes**:
- `users.profile:write` - Set user status
- `users:write` - Set presence (away/active)
- `channels:read` - Read channel information
- `im:read` - Read direct messages
- `reactions:read` - Read message reactions

**Webhooks**:
- `message.channels` - Incoming channel messages
- `message.im` - Incoming direct messages

**Rate Limits**:
- Tier 3: 50+ requests/minute
- Mitigation: Batch status updates, cache channel metadata

**Implementation**:

```python
from slack_sdk.web.async_client import AsyncWebClient
from slack_sdk.socket_mode.aiohttp import SocketModeClient

class SlackIntegration:
    """Slack API integration for shield system."""

    def __init__(self, bot_token: str, app_token: str):
        self.web_client = AsyncWebClient(token=bot_token)
        self.socket_client = SocketModeClient(
            app_token=app_token,
            web_client=self.web_client
        )

    async def start_listening(self, message_callback):
        """Start listening for incoming messages via Socket Mode."""
        @self.socket_client.on("message")
        async def handle_message(client, req):
            if req.type == "events_api":
                await message_callback(req.payload["event"])
                await client.send_socket_mode_response(
                    SocketModeResponse(envelope_id=req.envelope_id)
                )

        await self.socket_client.connect()

    async def set_status(
        self,
        text: str,
        emoji: str,
        expiration: int
    ):
        """Set Slack status with expiration."""
        await self.web_client.users_profile_set(
            profile={
                "status_text": text,
                "status_emoji": emoji,
                "status_expiration": expiration
            }
        )
```

### Google Calendar API

**Required Scopes**:
- `calendar.events.readonly` - Read calendar events
- `calendar.freebusy` - Check availability

**Features**:
- Detect upcoming meetings (5min warning)
- Block focus time during FOCUSED/HYPERFOCUS
- Suggest meeting times during SCATTERED state

**Implementation**:

```python
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

class CalendarIntegration:
    """Google Calendar integration for meeting buffers."""

    def __init__(self, credentials: Credentials):
        self.service = build('calendar', 'v3', credentials=credentials)

    async def get_upcoming_events(self, minutes_ahead: int = 30):
        """Get upcoming events in next N minutes."""
        now = datetime.utcnow().isoformat() + 'Z'
        later = (datetime.utcnow() + timedelta(minutes=minutes_ahead)).isoformat() + 'Z'

        events = self.service.events().list(
            calendarId='primary',
            timeMin=now,
            timeMax=later,
            singleEvents=True,
            orderBy='startTime'
        ).execute()

        return events.get('items', [])

    async def block_focus_time(self, duration_minutes: int):
        """Create calendar block for focus time."""
        start = datetime.utcnow()
        end = start + timedelta(minutes=duration_minutes)

        event = {
            'summary': '🎯 Focus Time (Dopemux)',
            'description': 'Protected deep work session',
            'start': {'dateTime': start.isoformat(), 'timeZone': 'UTC'},
            'end': {'dateTime': end.isoformat(), 'timeZone': 'UTC'},
            'transparency': 'opaque',  # Show as busy
            'visibility': 'private'
        }

        return self.service.events().insert(
            calendarId='primary',
            body=event
        ).execute()
```

### macOS Notification Center

**Implementation via `pync` library**:

```python
import pync

class NotificationManager:
    """macOS notification batching and filtering."""

    def __init__(self):
        self.batching_active = False
        self.batched_notifications = []

    async def enable_batching(self):
        """Start batching notifications."""
        self.batching_active = True
        self.batched_notifications = []

    async def disable_batching_and_deliver(self):
        """Stop batching and deliver summary."""
        self.batching_active = False

        if len(self.batched_notifications) > 0:
            summary = f"{len(self.batched_notifications)} notifications during focus session"
            pync.notify(summary, title="Dopemux - Focus Session Complete")

        self.batched_notifications = []

    async def handle_notification(self, title: str, message: str):
        """Handle incoming notification."""
        if self.batching_active:
            self.batched_notifications.append({
                'title': title,
                'message': message,
                'timestamp': datetime.now()
            })
        else:
            pync.notify(message, title=title)
```

---

## Urgency Scoring Algorithm

### Phase 1: Rule-Based Scoring

**Scoring Matrix**:

| Signal | Weight | Examples |
|--------|--------|----------|
| Critical keywords | +4 (immediate) | "urgent", "p0", "production down" |
| High keywords | +2 | "important", "deadline", "today" |
| VIP sender | +2 | CEO, manager, oncall rotation |
| Time sensitivity | +1 | "now", "asap", "this morning" |
| Direct message | +1 | vs channel message |
| @mention | +1 | Direct call-out |

**Urgency Levels**:
- **CRITICAL** (4+): Interrupt immediately, show notification
- **HIGH** (3): Notify at next break (within 25min)
- **MEDIUM** (2): Batch for break delivery
- **LOW** (1): End-of-day summary

### Phase 2: ML-Based Scoring

**Training Data**:
- User corrections: "This was actually urgent"
- Historical patterns: Messages marked as read quickly = urgent
- Team-wide patterns: Messages from oncall rotation = high urgency

**Model Architecture**:
```python
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer

class MLUrgencyScorer:
    """ML-based urgency scoring (Phase 2)."""

    def __init__(self):
        self.vectorizer = TfidfVectorizer(max_features=100)
        self.model = RandomForestClassifier(n_estimators=100)

    def train(self, messages: List[SlackMessage], labels: List[UrgencyLevel]):
        """Train on user-corrected data."""
        # Feature extraction
        features = []
        for msg in messages:
            features.append(self._extract_features(msg))

        X = self.vectorizer.fit_transform([f['text'] for f in features])
        y = [label.value for label in labels]

        self.model.fit(X, y)

    def predict(self, message: SlackMessage) -> UrgencyLevel:
        """Predict urgency level."""
        features = self._extract_features(message)
        X = self.vectorizer.transform([features['text']])
        prediction = self.model.predict(X)[0]

        return UrgencyLevel(prediction)

    def _extract_features(self, message: SlackMessage) -> dict:
        """Extract features for ML model."""
        return {
            'text': message.text,
            'sender_is_vip': message.user in self.vip_users,
            'is_dm': message.channel_type == 'im',
            'has_mention': f"<@{self.user_id}>" in message.text,
            'time_of_day': datetime.now().hour,
            'day_of_week': datetime.now().weekday()
        }
```

---

## Integration Points

### ADHD Engine Integration

**Subscribe to Attention State Changes**:

```python
# In ShieldCoordinator.__init__
await self.adhd_engine.subscribe_attention_state(
    callback=self.on_attention_state_changed
)
```

**Attention State Mapping**:
- `FOCUSED` → Activate shields (moderate filtering)
- `HYPERFOCUS` → Activate shields (aggressive filtering)
- `SCATTERED` → Deactivate shields (need flexibility)
- `TRANSITIONING` → Deactivate shields (context switching)
- `FATIGUED` → Deactivate shields (low energy, need support)

### ConPort Integration

**Log Shield Events**:

```python
await conport_client.log_custom_data(
    workspace_id="/Users/hue/code/dopemux-mvp",
    category="shield_events",
    key=f"activation_{timestamp}",
    value={
        "user_id": "current_user",
        "event": "shields_activated",
        "attention_state": "FOCUSED",
        "timestamp": datetime.now().isoformat(),
        "duration_seconds": 0
    }
)
```

**Track Effectiveness Metrics**:

```python
await conport_client.log_custom_data(
    workspace_id="/Users/hue/code/dopemux-mvp",
    category="shield_metrics",
    key=f"session_{session_id}",
    value={
        "messages_queued": 15,
        "messages_critical": 0,
        "interruptions_prevented": 15,
        "focus_duration_seconds": 1500,  # 25 minutes
        "user_satisfaction": 4  # 1-5 scale
    }
)
```

### Component 6 (Context Switch Recovery) Integration

**Pre-Interruption Snapshot**:

```python
# When critical message interrupts focus
await component6_client.create_context_snapshot(
    reason="critical_interruption",
    message_preview=critical_message.text[:100]
)
```

**Post-Interruption Recovery**:

```python
# After handling critical interruption
await component6_client.restore_context(
    snapshot_id=snapshot_id,
    recovery_hint="You were implementing OAuth PKCE, 3 minutes ago"
)
```

### Desktop Commander Integration

**Window Management**:

```python
# On shield activation
await desktop_commander.minimize_non_essential_windows(
    keep_focused=["VS Code", "Terminal", "Chrome (localhost)"]
)

# On shield deactivation
await desktop_commander.restore_windows()
```

**Screenshots for Context**:

```python
# Before critical interruption
screenshot_path = await desktop_commander.screenshot(
    filename=f"/tmp/shield_interrupt_{timestamp}.png"
)

# Log to ConPort with visual evidence
await conport_client.log_decision(
    summary="Handled critical production incident",
    implementation_details=f"Screenshot: {screenshot_path}"
)
```

---

## Privacy & Security

### Privacy-First Design Principles

1. **On-Device Processing**: All urgency scoring happens locally, no cloud message analysis
2. **Minimal Storage**: Store only metadata (sender, timestamp, urgency score), not message content
3. **User Control**: Users configure keywords, VIP lists, shield aggressiveness
4. **Transparent Filtering**: Show exactly what was blocked and why
5. **Opt-In Features**: AI summarization requires explicit consent

### Data Handling

**What We Store**:
```python
{
    "message_id": "1234567890.123456",
    "user": "U1234ABCD",
    "channel": "C5678EFGH",
    "timestamp": "2025-10-20T10:30:00Z",
    "urgency": "MEDIUM",
    "delivered": false
}
```

**What We DON'T Store**:
- ❌ Message content/text
- ❌ Attachments
- ❌ Reaction details
- ❌ Thread context

**Exception**: If AI summarization enabled, messages sent to OpenAI API (user consent required).

### Security Considerations

**API Token Storage**:
- Slack bot token stored in macOS Keychain
- Google OAuth credentials encrypted at rest
- No plaintext tokens in config files

**Rate Limiting**:
- Respect Slack API rate limits (50 req/min)
- Exponential backoff on failures
- Circuit breaker for API outages

**Error Handling**:
- Graceful degradation if Slack API unavailable
- Fallback to Desktop Commander notifications
- Never block critical communications due to system failure

---

## Testing Strategy

### Unit Tests

**Coverage Target**: 85%

**Key Test Cases**:

1. **UrgencyScorer Tests**:
```python
def test_critical_keyword_detection():
    scorer = UrgencyScorer(config)
    message = SlackMessage(text="URGENT: Production down")

    assert scorer.score(message) == UrgencyLevel.CRITICAL

def test_vip_sender_scoring():
    scorer = UrgencyScorer(config)
    message = SlackMessage(user="CEO", text="Quick question")

    assert scorer.score(message) >= UrgencyLevel.HIGH
```

2. **ShieldCoordinator Tests**:
```python
@pytest.mark.asyncio
async def test_shield_activation_on_focused_state():
    coordinator = ShieldCoordinator(mocks...)

    await coordinator.on_attention_state_changed(
        AttentionState.FOCUSED,
        user_id="test_user"
    )

    assert coordinator.shields_active == True
    assert coordinator.dnd.focus_mode_enabled == True
```

3. **MessageQueue Tests**:
```python
@pytest.mark.asyncio
async def test_queue_size_limit():
    queue = MessageQueue(max_size=10)

    # Add 15 messages
    for i in range(15):
        await queue.add(QueuedMessage(...))

    assert len(queue.messages) == 10  # Oldest LOW urgency dropped
```

### Integration Tests

**Slack Integration Test**:
```python
@pytest.mark.integration
async def test_slack_message_queuing_flow():
    """End-to-end test of Slack message handling."""

    # 1. Activate shields
    await coordinator.activate_shields("test_user")

    # 2. Send test message via Slack API
    test_message = await slack.send_message(
        channel="test_channel",
        text="Test message during focus"
    )

    # 3. Verify message was queued, not delivered
    queued = await triage.queue.get_all()
    assert len(queued) == 1
    assert queued[0].id == test_message.id

    # 4. Deactivate shields
    await coordinator.deactivate_shields("test_user")

    # 5. Verify message was delivered
    assert len(await triage.queue.get_all()) == 0
```

**Calendar Integration Test**:
```python
@pytest.mark.integration
async def test_meeting_buffer_zones():
    """Test pre/post meeting buffer creation."""

    # Create test meeting in 10 minutes
    meeting = await calendar.create_event(
        start=datetime.now() + timedelta(minutes=10),
        duration=30,
        title="Test Meeting"
    )

    # Monitor for pre-meeting warning
    warning_received = await wait_for_event(
        "pre_meeting_warning",
        timeout=600  # 10 minutes
    )

    assert warning_received.meeting_id == meeting.id
    assert warning_received.minutes_until == 5
```

### ADHD User Testing

**Beta Testing Protocol**:

**Week 1: Installation & Setup**
- 10-20 ADHD developers recruited
- Install on macOS, configure Slack integration
- Onboarding: Set VIP users, critical keywords

**Week 2: Daily Usage**
- Use shields for normal development work
- Daily feedback surveys:
  - Did auto-DND activate appropriately?
  - Were any important messages incorrectly queued?
  - Was urgency scoring accurate?
  - Anxiety level about missing messages (1-10 scale)

**Week 3: A/B Testing**
- Group A: Aggressive filtering (ENFORCE mode)
- Group B: Gentle filtering (ASSIST mode)
- Compare: Interruption reduction, task completion, user satisfaction

**Week 4: Iteration**
- Implement top user feedback
- Adjust default thresholds based on data
- Prepare for Phase 2

**Metrics Collected**:
- Interruptions prevented per day
- False positive rate (important messages incorrectly queued)
- False negative rate (unimportant messages interrupting)
- User satisfaction (NPS score)
- Would-recommend rate

---

## Deployment Plan

### Phase 1: macOS + Slack MVP (4 weeks)

**Week 1: Core Infrastructure**
- [ ] Create `services/interruption-shield/` directory structure
- [ ] Implement `ShieldCoordinator` class
- [ ] Integrate with ADHD Engine attention monitoring
- [ ] Unit tests for core logic

**Week 2: macOS Integration**
- [ ] Implement `DNDManager` with AppleScript
- [ ] Test Focus Mode activation/deactivation
- [ ] Desktop Commander window management integration
- [ ] Productivity indicator (false positive detection)

**Week 3: Slack Integration**
- [ ] Set up Slack app with required scopes
- [ ] Implement Socket Mode message listener
- [ ] Implement `MessageTriage` and `UrgencyScorer`
- [ ] Test message queuing/delivery flow

**Week 4: Beta Testing**
- [ ] Recruit 10-20 ADHD beta testers
- [ ] Deploy to beta users
- [ ] Daily feedback collection
- [ ] Iterate based on feedback

### Phase 2: Calendar & Notifications (3 weeks)

**Week 5: Google Calendar**
- [ ] OAuth setup for Calendar API
- [ ] Meeting detection and buffer zones
- [ ] Smart scheduling suggestions
- [ ] Pre/post-meeting warnings

**Week 6: Notification Batching**
- [ ] macOS Notification Center integration
- [ ] Batch delivery during breaks
- [ ] Notification summary generation

**Week 7: AI Summarization**
- [ ] OpenAI API integration
- [ ] Privacy consent flow
- [ ] Message summary generation
- [ ] User testing of summaries

### Phase 3: Multi-Platform (4 weeks)

**Week 8-9: Windows & Linux**
- [ ] Windows Focus Assist API
- [ ] Linux DND protocols (GNOME, KDE)
- [ ] Cross-platform testing
- [ ] Platform-specific edge cases

**Week 10-11: Additional Communication Tools**
- [ ] Microsoft Teams integration
- [ ] Discord integration
- [ ] Zoom meeting detection
- [ ] Multi-tool coordination

### Rollout Strategy

**Gradual Release**:
1. **Internal Alpha** (Week 1-2): Dopemux team only
2. **Closed Beta** (Week 3-6): 10-20 ADHD developers
3. **Public Beta** (Week 7-9): Opt-in for all Dopemux users
4. **General Availability** (Week 10+): Enabled by default

**Feature Flags**:
```python
FEATURE_FLAGS = {
    "shield.auto_activate": True,
    "shield.slack_integration": True,
    "shield.calendar_integration": False,  # Phase 2
    "shield.ai_summarization": False,  # Phase 2, requires consent
    "shield.ml_urgency_scoring": False  # Phase 3
}
```

---

## Performance Targets

### Latency Requirements

| Operation | Target | Rationale |
|-----------|--------|-----------|
| Shield activation | <500ms | Avoid disrupting flow |
| Shield deactivation | <1s | User expects immediate response |
| Urgency scoring | <100ms | Real-time message processing |
| Message queuing | <50ms | Slack API responsiveness |
| Summary generation | <3s | Acceptable for break-time delivery |

### Resource Usage

**Memory**: <100MB for shield service
**CPU**: <5% during active monitoring
**Network**: ~10 API calls/hour (Slack status updates, Calendar polling)
**Disk**: <10MB for queued messages (Redis-backed)

### Scalability

**Phase 1 (MVP)**:
- Single user support
- Local storage (Redis)
- No distributed coordination

**Phase 2-3**:
- Multi-user support
- Shared Redis instance
- Horizontal scaling for >100 users

---

## Monitoring & Metrics

### Operational Metrics

**Shield Effectiveness**:
- `shield.activations_per_day` - How often shields activate
- `shield.average_duration_seconds` - Typical focus session length
- `shield.interruptions_prevented` - Messages queued vs delivered immediately
- `shield.false_positive_rate` - Important messages incorrectly queued
- `shield.false_negative_rate` - Unimportant messages interrupting

**User Engagement**:
- `shield.user_override_rate` - How often users manually disable
- `shield.mode_distribution` - ASSIST vs ENFORCE usage
- `shield.satisfaction_score` - NPS from weekly surveys

**System Health**:
- `shield.api_error_rate` - Slack/Calendar API failures
- `shield.urgency_scoring_latency` - P50, P95, P99
- `shield.queue_size` - Current queued message count

### Analytics Dashboard

**Grafana Panels**:

1. **Focus Sessions**:
   - Daily shield activations
   - Average session duration
   - Attention state distribution

2. **Interruption Prevention**:
   - Messages queued vs delivered
   - Urgency level distribution
   - Critical interruptions (allowed)

3. **User Satisfaction**:
   - NPS trend over time
   - Override frequency
   - Feedback sentiment analysis

### Alerting Rules

**Critical Alerts** (PagerDuty):
- `shield.api_error_rate > 10%` for 5 minutes
- `shield.false_positive_rate > 20%` (breaking trust)
- `shield.activation_failure_rate > 5%`

**Warning Alerts** (Slack):
- `shield.average_queue_size > 50` (notification fatigue risk)
- `shield.user_override_rate > 30%` (users fighting system)
- `shield.urgency_scoring_latency > 200ms` (degraded performance)

---

## Appendices

### Appendix A: ADHD Research References

1. **Cleveland Clinic (2025)**: Task completion is primary ADHD management paradigm
2. **CBT Meta-Analysis (2024)**: External reminders + task breakdown = 87% improvement
3. **Digital Interventions (2024)**: Self-guided systems effective (g = −0.32)
4. **Context Switching Cost (2022)**: 15-25 minute recovery time for ADHD developers
5. **Hyperfocus Protection (2023)**: Graduated interventions reduce burnout by 64%

### Appendix B: Configuration Examples

**Conservative Configuration** (ASSIST mode):
```yaml
shield:
  auto_activate: true
  mode: ASSIST
  default_duration: 25

  urgency:
    critical_keywords:
      - "urgent"
      - "p0"
      - "production down"
    vip_users:
      - "U123ABC"  # CEO

  overrides:
    allow_manual: true
    cooldown_minutes: 10
```

**Aggressive Configuration** (ENFORCE mode):
```yaml
shield:
  auto_activate: true
  mode: ENFORCE
  default_duration: 45  # Longer sessions

  urgency:
    critical_keywords:
      - "urgent"
      - "p0"
      - "p1"
      - "blocker"
      - "production"
    vip_users:
      - "U123ABC"  # CEO
      - "U456DEF"  # Manager
      - "U789GHI"  # Tech Lead

  overrides:
    allow_manual: false  # No manual override
    cooldown_minutes: 0
```

### Appendix C: API Endpoints

**Shield Control API**:

```
POST /api/v1/shield/activate
POST /api/v1/shield/deactivate
GET  /api/v1/shield/status
POST /api/v1/shield/override
GET  /api/v1/shield/queued-messages
POST /api/v1/shield/config

POST /api/v1/shield/urgency/feedback
GET  /api/v1/shield/metrics
```

**Example Request**:
```bash
curl -X POST http://localhost:8096/api/v1/shield/activate \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "current_user",
    "duration_minutes": 25,
    "mode": "ASSIST"
  }'
```

**Example Response**:
```json
{
  "status": "active",
  "activated_at": "2025-10-20T10:30:00Z",
  "will_deactivate_at": "2025-10-20T10:55:00Z",
  "mode": "ASSIST",
  "integrations": {
    "macos_focus": true,
    "slack_status": true,
    "notification_batching": true
  }
}
```

---

## Next Steps

1. ✅ **Research & Design**: Complete (ConPort Decision #188)
2. 🔄 **Technical Specification**: Complete (this document)
3. ⏳ **Stakeholder Approval**: Present to team
4. ⏳ **Beta Recruitment**: Find 10-20 ADHD developers
5. ⏳ **Phase 1 Implementation**: 4-week sprint (macOS + Slack MVP)

**Ready for**: Implementation kickoff pending stakeholder approval

---

**Document Status**: Complete
**Next Review**: After Phase 1 MVP deployment
**Feedback**: Submit via ConPort or GitHub Issues
