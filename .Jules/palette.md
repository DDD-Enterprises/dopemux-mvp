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

## 2026-03-06 - [Contextual Shorthand Indicators]
**Learning:** High-density dashboards often use shorthand status chips (like "[LIVE]" or "[EDGE]") to save space. While visually efficient, they lack context for new users and are inaccessible to keyboard users if they are not focusable. Adding a descriptive Tooltip and `tabIndex={0}` bridges the gap between shorthand brevity and clarity while ensuring accessibility.
**Action:** Always wrap shorthand status indicators in descriptive Tooltips and ensure they have `tabIndex={0}` to be keyboard focusable.

## 2026-03-07 - [Refining Progress and Tooltip Consistency]
**Learning:** In Material UI, `LinearProgress` defaults `aria-valuemin` to 0 and `aria-valuemax` to 100, making explicit attributes redundant. Additionally, consistent use of the `arrow` prop on `Tooltip` components provides a more polished and directed visual cue for users interacting with dense dashboard metrics.
**Action:** Omit redundant ARIA defaults for MUI progress bars and consistently apply the `arrow` prop to Tooltips for improved directional feedback.

## 2026-03-10 - [Metric Card Keyboard Discoverability]
**Learning:** Core dashboard metrics (Energy, Attention, Load) are often purely visual. By adding `tabIndex={0}` and descriptive Tooltips, these cards become accessible to keyboard users and provide "hidden" context that might not fit in the compact visual layout. Using `cursor: 'help'` also signals to mouse users that more info is available.
**Action:** Enhance visual-only metric displays with `tabIndex={0}` and `Tooltip` to support keyboard navigation and provide supplemental context without cluttering the UI.

## 2026-03-11 - [Closing the Task Feedback Loop]
**Learning:** In task-oriented interfaces, failing to provide a clear "success" or "empty" state after finishing a sequence can lead to user confusion or a sense of "unmet expectation." Providing a satisfying "Ritual Complete" visual (like a check icon and positive reinforcement text) creates a distinct sense of closure and progress.
**Action:** Always implement explicit success and empty states for sequential task components to provide closure and guidance when a workflow is completed or empty.

## 2026-03-12 - [Combatting Time Blindness with Aggregate Duration]
**Learning:** For users with ADHD, individual task estimates often fail to provide a clear picture of the "end of the tunnel," leading to "time blindness" or feeling overwhelmed by a list. Providing an aggregate "Total Remaining Duration" that updates in real-time (including the progress of the active task) offers a grounding metric that helps users manage their energy and expectations.
**Action:** In sequential task interfaces, always provide a visible and accessible aggregate duration indicator to help users orient themselves within the overall workflow.
