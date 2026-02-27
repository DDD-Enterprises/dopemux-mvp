## 2025-05-14 - [Accessible Progress Indicators]
**Learning:** MUI LinearProgress components are often used to display critical metrics (like cognitive load or team progress) but are invisible to screen readers without explicit ARIA attributes. Providing both an `aria-label` (to name the metric) and `aria-valuetext` (to provide a rounded percentage) significantly improves accessibility.
**Action:** Always include `aria-label` and `aria-valuetext` when using progress components to ensure metrics are accessible.

## 2025-05-14 - [Indeterminate Loading Feedback]
**Learning:** When a dashboard panel depends on asynchronous data (like AI predictions), a static "Loading..." text is less reassuring than an indeterminate progress bar. The visual movement signals active background work.
**Action:** Prefer indeterminate progress bars or skeletons over static text for panels with unpredictable loading times.

## 2025-05-15 - [ADHD-Aware Feedback Loops]
**Learning:** For users with ADHD, static timers can sometimes be overlooked ("time blindness"). Adding a subtle, non-distracting animation (like a slow pulse) to an active timer provides a continuous "live" signal that the session is ongoing, reducing the chance of losing focus on the current task.
**Action:** Use subtle animations or pulsing effects for active status indicators and timers to maintain user engagement without being intrusive.

## 2026-02-25 - [Timer Accessibility Pluralization]
**Learning:** For ADHD-focused dashboards, timers are critical components that require accurate screen reader feedback. Using pluralization logic in ARIA labels (e.g., '1 minute' vs '2 minutes') ensures the UI is accessible and professional for users relying on assistive technology.
**Action:** Always implement a helper like `getTimerAriaLabel` for any duration-based displays and apply it to components with `role="timer"`.

## 2025-05-17 - [Contextual Shorthand Indicators]
**Learning:** High-density dashboards often use shorthand status chips (like "[LIVE]" or "[EDGE]") to save space. While visually efficient, they lack context for new users and are inaccessible to keyboard users if they are not focusable. Adding a descriptive Tooltip and `tabIndex={0}` bridges the gap between shorthand brevity and clarity while ensuring accessibility.
**Action:** Always wrap shorthand status indicators in descriptive Tooltips and ensure they have `tabIndex={0}` to be keyboard focusable.
