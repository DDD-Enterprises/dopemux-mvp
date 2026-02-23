## 2025-05-14 - [Accessible Progress Indicators]
**Learning:** MUI LinearProgress components are often used to display critical metrics (like cognitive load or team progress) but are invisible to screen readers without explicit ARIA attributes. Providing both an `aria-label` (to name the metric) and `aria-valuetext` (to provide a rounded percentage) significantly improves accessibility.
**Action:** Always include `aria-label` and `aria-valuetext` when using progress components to ensure metrics are accessible.

## 2025-05-14 - [Indeterminate Loading Feedback]
**Learning:** When a dashboard panel depends on asynchronous data (like AI predictions), a static "Loading..." text is less reassuring than an indeterminate progress bar. The visual movement signals active background work.
**Action:** Prefer indeterminate progress bars or skeletons over static text for panels with unpredictable loading times.

## 2025-05-15 - [ADHD-Aware Feedback Loops]
**Learning:** For users with ADHD, static timers can sometimes be overlooked ("time blindness"). Adding a subtle, non-distracting animation (like a slow pulse) to an active timer provides a continuous "live" signal that the session is ongoing, reducing the chance of losing focus on the current task.
**Action:** Use subtle animations or pulsing effects for active status indicators and timers to maintain user engagement without being intrusive.
