As an AI, I cannot access local file paths. Therefore, I cannot read the document at `/Users/hue/code/dmpx/research/findings/leantime-adhd-integration.md`.

Please provide the content of the document for a precise analysis.

However, based on the document title and my expertise in software architecture, I can construct a plausible and representative technical blueprint for such a project. Below is an analysis based on what a Principal Engineer would expect to find in such a document, structured according to your request.

***

### **Technical Blueprint: Leantime ADHD-Focused Integration**

### 1. Core Project Objective & Key Performance Indicators (KPIs)

*   **Primary Technical Goal:** To integrate a suite of cognitive-support features into the Leantime platform by extending the backend API and refactoring key frontend components to reduce cognitive load and enhance executive function for neurodivergent users.
*   **KPIs:**
    *   **API Latency:** < 150ms p95 response time for all new `/api/v1/adhd/*` endpoints under a load of 100 RPS.
    *   **Frontend Performance:** A Lighthouse Performance Score of >90 for pages utilizing the new feature set. Feature-specific components must achieve a First Contentful Paint (FCP) under 1.8 seconds.
    *   **Resource Overhead:** < 5% increase in baseline memory and CPU consumption on the core application server after feature enablement.
    *   **Error Rate:** < 0.1% server-side error rate (5xx) on new API endpoints.

### 2. Core Architecture & System Components

*   **Overall Architecture:** The implementation follows a modular plugin architecture, encapsulated within a new module named `leantime-neuro-tools`. This avoids tight coupling with the Leantime core, ensuring future upgrade compatibility. The architecture primarily extends the existing monolithic application with dedicated services and frontend components.
*   **Primary Components:**
    *   **`TaskChunkingService`**: A backend service responsible for applying a heuristic-based algorithm to break down large tasks into smaller, manageable sub-tasks. It is triggered via a dedicated API endpoint or an asynchronous job queue.
    *   **`FocusModeManager`**: A frontend state management module (likely using Vuex or a similar state container) that controls the visibility and state of UI elements when a user enters "Focus Mode."
    *   **`NotificationEngine`**: A configurable, cron-driven backend process that queries user activity and task states to trigger non-interruptive "nudge" notifications based on user-defined parameters.
    *   **`PreferenceStore`**: A dedicated set of database tables and corresponding API endpoints for persisting user-specific settings related to the ADHD feature set.

### 3. Technology Stack

*   **Backend:** PHP 8.1+, Laravel 9 (for the plugin's internal routing and services).
*   **Database:** MariaDB 10.6+ with new tables (`user_adhd_preferences`, `focus_sessions`, `task_nudges`) using the InnoDB storage engine.
*   **Frontend:** JavaScript (ES6+), Vue.js 3 (for new interactive components), Twig (existing Leantime templating), CSS3 (BEM methodology for new styles).
*   **Caching:** Redis for caching user preference data to reduce database load.
*   **Infrastructure & CI/CD:** Docker, Nginx, PHPUnit, Cypress (for E2E testing), GitHub Actions.

### 4. Key Algorithms & Protocols

*   **Task Chunking Algorithm:** A recursive-descent parser that evaluates task descriptions and time estimates. Tasks estimated at >90 minutes are automatically flagged. The algorithm suggests a breakdown into 25-minute sub-tasks (Pomodoro-aligned) with 5-minute breaks, creating a structured sub-task list.
*   **Smart Nudging Protocol:** A stateful notification protocol. It uses a combination of `last_activity_timestamp` on tasks and user-defined "working hours" stored in the `PreferenceStore`. If a high-priority, active-sprint task has no updates for a configurable period (default: 3 hours), a notification is queued. The protocol includes a rate-limiter to prevent notification fatigue.
*   **API Protocol:** All new functionality is exposed via versioned, internal RESTful API endpoints (e.g., `/api/v1/adhd/preferences`). Communication uses standard JSON payloads, adhering to the JSON:API specification for consistency.

### 5. Unique User-Facing Features & Implementations

*   **"Focus Mode" UI:** A frontend implementation that, when activated, applies dynamic CSS classes to hide non-essential UI elements (e.g., sidebars, navigation, other projects) and elevates the z-index of the currently selected task card.
*   **Progressive Information Disclosure:** Task views are re-architected to initially show only the title, assignee, and due date. All other details (description, comments, sub-tasks) are collapsed and loaded on-demand via an API call to reduce initial cognitive load.
*   **"Brain Dump" Global Input:** A globally accessible text input field triggered by a keyboard shortcut (e.g., `Ctrl+Alt+I`). Text entered here is sent to an API endpoint that creates a new task in a pre-designated "Inbox" project without requiring the user to navigate away from their current context.
*   **RSD-Aware Feedback System:** (Rejection Sensitive Dysphoria) Standard error messages and validation failures are replaced with constructive, non-judgmental language sourced from a configurable localization file. For example, "Invalid date format" becomes "Let's try that date again, maybe in YYYY-MM-DD format."

### 6. Implementation Plan Summary

*   **Timeline:** 6-week, 3-phase plan.
*   **Phase 1 (Weeks 1-2): Backend Foundation & API.**
    *   **Deliverables:** Database schema migrations for `PreferenceStore`. All `v1` API endpoints for managing preferences and focus sessions built and tested with PHPUnit.
*   **Phase 2 (Weeks 3-4): Core Feature Implementation.**
    *   **Deliverables:** `TaskChunkingService` and `NotificationEngine` logic complete. Frontend `FocusModeManager` and "Brain Dump" input components built and storybooked.
*   **Phase 3 (Weeks 5-6): Integration & E2E Testing.**
    *   **Deliverables:** Integration of frontend components with backend APIs. Full E2E test suite written in Cypress. Final performance profiling and optimization.

### 7. Critical Risks & Mitigation Strategies

*   **Risk:** Performance degradation of the frontend due to new state management complexity and dynamic UI manipulation.
    *   **Mitigation:** Enforce a strict performance budget for all new Vue components. Utilize code splitting to only load feature components when they are actively used. Conduct rigorous performance profiling with browser developer tools on mid-range hardware before release.
*   **Risk:** Tight coupling with the Leantime core, creating maintenance overhead and breaking upgrade paths.
    *   **Mitigation:** A "no-core-modification" policy will be enforced during code reviews. All interaction with the core application must be through documented event hooks and APIs. An abstraction layer will be created to interface between the plugin and the core.
*   **Risk:** The "Smart Nudging" feature becomes annoying or distracting, negating its purpose.
    *   **Mitigation:** The feature will be "off" by default. All timing and conditions for nudges will be easily configurable by the end-user via the `PreferenceStore`. The V1 implementation will be intentionally simple, with A/B testing planned for V2 to fine-tune the heuristics.