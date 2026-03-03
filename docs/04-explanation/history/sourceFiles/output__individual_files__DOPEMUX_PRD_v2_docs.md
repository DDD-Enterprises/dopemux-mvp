Based on the document provided, here is the extracted information in the required structured format.

### 1. Core Business Goals & User Problems
-   **Primary Business Objective:** To reduce the time and engineering effort required to launch new marketing campaigns and A/B tests.
-   **User Pain Points:**
    -   Launching simple tests requires a full code deployment cycle, leading to slow turnaround times (up to two weeks).
    -   Non-technical users are highly dependent on the engineering team to make simple configuration changes.
    -   Manual configuration changes in code are prone to human error, causing production incidents.

### 2. Key Actors & Personas
-   **Marketing Manager (Maria):** A non-technical user who needs to quickly launch and modify promotional campaigns.
-   **Product Manager (Paul):** Defines and runs A/B tests by targeting different user segments with feature flags.
-   **Software Engineer (Devon):** Consumes the configuration via an API to implement features in other applications.
-   **System Administrator (Admin):** Manages user permissions for the system.

### 3. Functional Requirements & Features
-   **FS-01:** As a Marketing Manager, I want to create a new "Dope" configuration with a unique name, so I can manage a new campaign.
-   **FS-02:** As a Marketing Manager, I want to define key-value pairs within a Dope, so I can control the content of my campaign.
-   **FS-03:** As a Product Manager, I want to add targeting rules to a Dope based on user attributes, so I can run targeted A/B tests.
-   **FS-04:** As a Software Engineer, I want to fetch a Dope configuration via a REST API endpoint using its unique name, so my application can display the correct content.
-   **FS-05:** As a System Administrator, I want to grant "Editor" or "Viewer" permissions to users for specific Dopes, so I can control who can make changes.
-   **FS-06:** As any user, I want to see a version history for a Dope, so I can track changes and revert to a previous version if needed.

### 4. Non-Functional Requirements (NFRs)
-   **Performance:** The P99 latency for the primary `GET /api/v1/dope/{name}` endpoint must be under 50ms.
-   **Scalability:** The service should be horizontally scalable.
-   **Security:** All API endpoints must be authenticated via JWT tokens issued by `AuthService`. No PII is to be stored in the system. The system must comply with internal data handling policies.
-   **Reliability:** The service must have an uptime of 99.95% and have no single point of failure.

### 5. Technical Constraints & Decisions
-   **Mandated Technologies:**
    -   **Language:** Go
    -   **Database:** PostgreSQL (company's shared instance)
    -   **Deployment:** AWS on the existing Kubernetes cluster
-   **Existing System Integrations:**
    -   Must integrate with the existing `AuthService` via gRPC for user authentication and authorization.
-   **Architectural Decisions:**
    -   The system must expose a RESTful API.

### 6. Data & Integration Points
-   **Key Data Entities:**
    -   **Dope:** Represents a configuration, containing `id`, `name`, `project_id`, `created_at`, `updated_at`.
    -   **DopeVersion:** Represents a specific version of a Dope, containing `id`, `dope_id`, `version_number`, `config_payload` (JSONB), `targeting_rules` (JSONB), `created_by_user_id`, `created_at`.
-   **Inputs & Outputs (APIs):**
    -   **Input:** `GET /api/v1/dope/{name}` - Fetches the active configuration.
    -   **Output:** A JSON object representing the `config_payload`.
    -   **Input:** `POST /api/v1/dope` - Creates a new Dope configuration.
    -   **Output:** A JSON object with the newly created Dope's metadata.