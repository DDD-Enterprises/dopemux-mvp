---
id: adhd-features-quick-reference
title: Adhd Features Quick Reference
type: how-to
owner: '@hu3mann'
last_review: '2026-02-02'
next_review: '2026-05-03'
---
# ADHD Features Quick Reference Card

**🎯 11 Features for Cognitive Support** | [Full Guide](adhd-features-user-guide.md) | [API Docs](../03-reference/adhd-engine-api.md)

---

## At a Glance

| # | Feature | Use When | API Endpoint |
|---|---------|----------|--------------|
| 1 | Energy Predictor | Start session | `GET /energy-prediction` |
| 2 | Context Preserver | Before breaks | `POST /context/capture` |
| 3 | Attention Calibrator | Detection feels off | `POST /attention/feedback` |
| 4 | Correlation Engine | Weekly review | `GET /correlations/insights` |
| 5 | Voice Assistant | Hands-free needed | `POST /voice/command` |
| 6 | Mobile Push | Away from desk | `POST /notifications/test` |
| 7 | Overwhelm Detector | Feeling stuck | `GET /overwhelm/status` |
| 8 | Hyperfocus Guard | Deep work | `GET /hyperfocus/status` |
| 9 | End-of-Day | Session close | `POST /wind-down` |
| 10 | Weekly Report | Friday | `GET /weekly-report` |
| 11 | Procrastination | Avoiding tasks | `GET /procrastination/status` |

---

## Quick Commands

```bash
# Check energy prediction
curl http://localhost:8095/api/v1/energy-prediction

# Capture context before break
curl -X POST http://localhost:8095/api/v1/context/capture

# Restore context after break
curl http://localhost:8095/api/v1/context/restore

# Provide attention feedback
curl -X POST http://localhost:8095/api/v1/attention/feedback \
  -d '{"predicted": "focused", "actual": "scattered"}'

# Get insights
curl http://localhost:8095/api/v1/correlations/insights

# Voice command
curl -X POST http://localhost:8095/api/v1/voice/command \
  -d '{"command": "how is my focus"}'

# Check overwhelm
curl http://localhost:8095/api/v1/overwhelm/status

# Hyperfocus status
curl http://localhost:8095/api/v1/hyperfocus/status

# Wind down ritual
curl -X POST http://localhost:8095/api/v1/wind-down

# Weekly report
curl http://localhost:8095/api/v1/weekly-report

# Procrastination check
curl http://localhost:8095/api/v1/procrastination/status
```

---

## Configuration

```bash
# ~/.config/dopemux/adhd.env

# Energy & Prediction
ENERGY_PREDICTOR_ENABLED=true

# Hyperfocus Protection
HYPERFOCUS_AUTO_SAVE_INTERVAL=5        # minutes
HYPERFOCUS_GENTLE_REMINDER=90          # minutes
HYPERFOCUS_CRITICAL_THRESHOLD=120      # minutes

# Daily Ritual
END_OF_DAY_HOUR=18                     # 6 PM

# Mobile Push
MOBILE_PUSH_PROVIDER=ntfy              # ntfy (free) | pushover (paid)
MOBILE_PUSH_TOPIC=dopemux-yourusername

# Procrastination Thresholds
PROCRASTINATION_RESEARCH_THRESHOLD=30  # minutes
PROCRASTINATION_SWITCHING_THRESHOLD=5  # switches
PROCRASTINATION_POLISH_THRESHOLD=45    # minutes
```

---

## Overwhelm Levels & Actions

| Level | Signals | Action |
|-------|---------|--------|
| Mild | 1-2 | Gentle check-in |
| Moderate | 2-3 | Simplify task |
| Severe | 3-4 | 15-min forced break |
| Critical | 4-5 | Immediate intervention |

**Signals**: Rapid switching (>10/15min), no progress (>45min), energy mismatch, break resistance, attention overwhelmed

---

## Hyperfocus Phases

| Phase | Duration | Protection |
|-------|----------|------------|
| Building | 15-30min | Start auto-save, block notifications |
| Active | 30-90min | Continue protections |
| Extended | 90-120min | ⏰ Gentle reminder |
| Critical | 120+min | ⚠️ Strong warning |
| Crashed | Post-focus | Recovery protocol |

---

## Procrastination Patterns & Micro-Tasks

| Pattern | Micro-Task Example |
|---------|-------------------|
| Research Rabbit Hole | "Write 3 bullet points" (3min) |
| Productive Procrastination | "Work on priority 5 min" (5min) |
| Task Switching | "Pick ONE, close others" (2min) |
| Perfectionism | "Commit as 'WIP'" (2min) |
| Decision Paralysis | "Flip coin, pick one" (1min) |

**Gamification**: Streaks tracked, badges at 5/25/100 tasks

---

## Privacy

✅ **Collected**: Energy levels, attention states, task switches
❌ **NOT Collected**: Code contents, personal info
🔒 **Storage**: Local only (Redis, ConPort, ML models)
✋ **Control**: All opt-in, export/delete anytime

---

## Troubleshooting

**Energy predictions inaccurate?**
→ Needs 2+ weeks data, retrain weekly

**Context not restoring?**
→ Check ConPort (port 3004) and Serena MCP

**Mobile push not working?**
→ Verify topic subscription, test with `/notifications/test`

**Overwhelm not detecting?**
→ May not meet thresholds, query `/overwhelm/status` manually

---

## Setup Checklist

- [ ] Enable energy predictor (2 weeks to learn)
- [ ] Setup mobile push (ntfy app + topic)
- [ ] Configure end-of-day hour
- [ ] Try voice: "How's my focus?"
- [ ] Complete first micro-task
- [ ] Accept breaks for calibration
- [ ] Run end-of-day tonight
- [ ] Check Friday report
- [ ] Provide attention feedback

---

**Base URL**: `http://localhost:8095/api/v1/`
**Full Docs**: [User Guide](adhd-features-user-guide.md) | [API Reference](../03-reference/adhd-engine-api.md)
**Philosophy**: Consent-first, gentle, transparent, empowering. You're in control. 💙
