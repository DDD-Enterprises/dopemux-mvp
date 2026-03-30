Based on the document at `/Users/hue/code/dmpx/research/findings/leantime.md`, here is the extracted information:

### 1. Core Business Goals & User Problems
- **Primary business objective:** To help small teams and startups manage their projects from idea to delivery by blending traditional project management with design thinking and lean startup methodologies. The system aims to keep business goals in focus throughout the project lifecycle.
- **Specific user pain points or needs:** The document implies a need for a unified system that supports not just task execution but also the initial phases of a project, such as idea management, validation (using tools like business model canvases and SWOT analysis), and strategic roadmap planning.

### 2. Key Actors & Personas
- **Client:** Can view project progress and comment on tasks.
- **Team Member:** Can create/manage tasks, track time, and participate in discussions.
- **Project Manager:** Has full control over assigned projects, including managing team members, milestones, and budgets.
- **Administrator:** Has system-level access to manage users, system settings, and plugins.
- **External Systems:** Can interact with the application via a REST API.

### 3. Functional Requirements & Features
- **Idea Management:** Provide a dedicated board for capturing and discussing new ideas.
- **Research Boards:** Integrate tools like the Business Model Canvas and SWOT analysis to validate ideas.
- **Roadmap Planning:** Offer visual timelines (Gantt charts) for planning milestones and releases.
- **Task Management:** Support Kanban boards and to-do lists for daily execution.
- **Time Tracking:** Allow users to track time spent on tasks.
- **Reporting:** Generate project status reports and timesheet summaries.

### 4. Non-Functional Requirements (NFRs)
- **Performance:** Not mentioned.
- **Scalability:** The system is described as being for "small teams and startups."
- **Security:**
    - Authentication is handled via a username/password system with session management.
    - Future enhancements mentioned include implementing two-factor authentication (2FA) and stricter Content Security Policies (CSP).
    - For self-hosted instances, the administrator is responsible for securing the server and database.
- **Reliability:** Not mentioned.

### 5. Technical Constraints & Decisions
- **Specific technologies:**
    - **Backend:** PHP 8+
    - **Database:** MySQL 5.7+ or MariaDB 10.2+
    - **Frontend:** Vanilla JavaScript, Twig templates
- **Existing systems integrations:** Not mentioned.
- **Architectural decisions:**
    - The system is a monolithic web application.
    - It is designed to run on a standard LAMP/LEMP stack.
    - A Docker Compose file is provided as a deployment option.

### 6. Data & Integration Points
- **Key data entities:** Projects, Milestones, To-Dos, Users, and Timesheets.
- **Inputs and outputs:** The system provides a REST API for integrations, allowing external systems to interact with projects, tasks, and users.