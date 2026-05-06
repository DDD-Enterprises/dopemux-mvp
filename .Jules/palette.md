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

## 2025-05-20 - [Combatting Time Blindness]
**Learning:** For users with ADHD, seeing a list of tasks without an aggregate "time to finish" can lead to "time blindness" or feeling overwhelmed by an infinite-feeling backlog. Providing a "Total Remaining Duration" counter that updates in real-time creates a "light at the end of the tunnel" effect, making the workload feel finite and manageable.
**Action:** Aggregate and display total remaining estimated duration in sequential task managers to help users maintain perspective on their progress.

## 2026-03-12 - [Cognitive Load & Feed Management]
**Learning:** In high-stimulation environments (like a live signal feed), accumulating notifications can contribute to "cognitive clutter," which is particularly taxing for users with ADHD. Providing a "Clear" button that is only visible when the feed is active allows users to reset their visual field and reduce overwhelm once information has been processed.
**Action:** Always provide a conditional "Clear" or "Reset" mechanism for live data feeds to help users manage cognitive load and maintain a clean workspace.

## 2026-03-25 - [Tooltip Visibility on Disabled Elements]
**Learning:** Material UI Tooltips do not trigger on disabled elements (like buttons) because they don't emit pointer events. Wrapping the disabled element in a `<span>` ensures the tooltip remains accessible, allowing users to understand *why* an action is unavailable.
**Action:** Always wrap disabled buttons in a `<span>` when using `Tooltip` to maintain accessibility and user feedback.

## 2026-03-26 - [Multi-State Connection Indicators]
**Learning:** For systems with asynchronous background services, a binary "Live/Down" connection status is insufficient. Introducing an explicit "Connecting" state with distinct visual (Gold/Secondary) and semantic cues reduces user uncertainty during initialization.
**Action:** Implement three-tier status logic (Connecting, Live, Degraded) for all real-time service indicators.

## 2026-03-26 - [Reducing Screen Reader Noise in Status Chips]
**Learning:** Decorative pulsing animations inside status chips are helpful for sighted users but can be noisy for screen readers if not properly hidden. Since the Chip's `aria-label` already provides the full status context, the internal pulsing element should be marked `aria-hidden="true"`.
**Action:** Always add `aria-hidden="true"` to purely visual status icons or animations when they are part of a larger component that already has a descriptive label.

## 2026-04-24 - [Visual Liveness Indicators]
**Learning:** For users in high-concentration "Flow" states, an empty dashboard panel can be ambiguous—is it broken or just quiet? Adding a subtle, low-contrast pulsing animation (like "Listening..." dots) provides a continuous "system alive" signal that reduces cognitive uncertainty without breaking focus.
**Action:** Implement subtle pulsing animations for "listening" or "waiting" states in real-time feeds to provide passive reassurance.

## 2026-04-25 - [Temporal Context in Event Feeds]
**Learning:** In high-density "live" feeds, notifications without timestamps can cause "temporal confusion" for users, especially when returning to a dashboard after a distraction. Adding a concise `[HH:mm:ss]` timestamp to each event chip provides immediate context on *when* an event occurred relative to the current ritual state.
**Action:** Always include a formatted timestamp in live event or notification chips to ground the user in time and improve the auditability of the signal feed.

## 2026-04-26 - [Dynamic Empty States for Live Feeds]
**Learning:** Static empty state messages like "Waiting for..." can make an application feel unresponsive or "dead" if no data is currently available. Replacing them with an active, animated "Listening..." state provides immediate visual feedback that the system is functioning and monitoring for events.
**Action:** Use subtle animations (like pulsing dots) in empty state messages for real-time feeds to signal active background processes.

## 2026-04-26 - [Semantic Error Severity Alignment]
**Learning:** Using `warning` severity for critical system failures (like WebSocket disconnections or API errors) can lead to user confusion and "warning fatigue." Aligning the visual and semantic severity with `error` ensures users immediately recognize the criticality of the issue and trigger appropriate iconography.
**Action:** Always use the most accurate semantic severity level (error vs warning) to match the criticality of the system state.

## 2026-04-30 - [Mitigating Time Blindness with Absolute Anchors]
**Learning:** For users with ADHD, relative durations (e.g., "45 minutes remaining") can feel abstract and fail to trigger a realistic sense of time ("time blindness"). Providing an absolute completion time (e.g., "Estimated completion: 14:30") grounds the relative effort in the real world, making the remaining workload feel more tangible and manageable.
**Action:** Always supplement relative duration displays with an absolute estimated completion time to provide a concrete temporal anchor.

## 2026-05-14 - [Temporal Grounding for Task Management]
**Learning:** Displaying relative durations (e.g., "45m remaining") is helpful but can still feel abstract to users with ADHD who experience "time blindness." Providing an absolute wall-clock finish estimate (e.g., "Finish at 14:30") grounds the relative duration in real-world time, making the workload feel more concrete and manageable.
**Action:** Supplement relative duration counters with absolute estimated completion times to improve temporal grounding and reduce cognitive load.

## 2026-05-15 - [Safe Destructive Actions with Soft Confirmation]
**Learning:** For ADHD users who may experience impulsivity or accidental clicks, immediate destructive actions (like resetting a hard-won ritual progress) can lead to significant frustration. Implementing a "soft" two-step confirmation (Confirm Reset?) within a short temporal window (3s) provides a safety net without the friction of a modal dialog.
**Action:** Use a two-step confirmation state on buttons for destructive actions that are not easily reversible to prevent accidental progress loss.

## 2026-05-16 - [Hardening Async Micro-interactions]
**Learning:** Hardening asynchronous state transitions in React (like multi-step confirmation buttons) requires defensive timeout management. Always clear existing timeouts before starting new ones and explicitly nullify the timer reference after clearing or firing to maintain deterministic component behavior and avoid race conditions.
**Action:** Add explicit timeout clearing and ref nullification when implementing time-windowed micro-interactions.

## 2026-05-17 - [Visual Reinforcement for Soft Confirmations]
**Learning:** A two-step "soft" confirmation button (e.g., "Confirm Clear?") benefits from subtle visual feedback like a slow pulse animation and a high-contrast color shift (e.g., to `saintGold`). This reinforces that the interface is in a "pending" state and effectively draws the user's attention to the decision point without the abruptness of a modal.
**Action:** Use subtle pulse animations and distinct semantic colors (like gold for warning/confirmation) to visually reinforce temporary confirmation states.
