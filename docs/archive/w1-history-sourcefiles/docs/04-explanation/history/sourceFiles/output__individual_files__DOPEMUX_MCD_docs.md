Based on the document `DOPEMUX_MCD.md`, here is the extracted information in the required structured format.

### 1. Core Business Goals & User Problems
- **Primary Business Objective:** To centralize and streamline the process of managing multiple marketing campaigns by providing a unified dashboard for performance tracking and analysis.
- **User Pain Points:**
    - Fragmented tooling and lack of a consolidated view of campaign performance.
    - Difficulty in tracking cross-channel campaign metrics effectively.
    - Time-consuming manual data aggregation from various sources.
    - Inability to quickly pivot marketing strategies due to delayed insights.

### 2. Key Actors & Personas
- **Marketing Manager:** Primary user who needs a high-level, aggregated view of campaign performance.
- **Data Analyst:** Secondary user who requires access to granular, raw data and export capabilities for deep analysis.
- **Administrator:** A user role responsible for managing user accounts and access permissions.
- **External Ad Platform:** A system from which data is ingested.

### 3. Functional Requirements & Features
- **Unified Campaign Dashboard:** A central view displaying aggregated performance metrics from all connected platforms.
- **Real-time Performance Metrics:** The system must display key metrics such as clicks, impressions, conversions, and cost-per-acquisition in real-time.
- **Automated Data Ingestion:** The system must automatically pull data from various external ad platforms.
- **Customizable Reporting:** Users must be able to create and export custom reports based on selected metrics and date ranges.
- **User Role Management:** An administrator must be able to manage user roles and permissions to control access to data and features.
- **Data Export:** Data Analysts must be able to export raw performance data in CSV format.

### 4. Non-Functional Requirements (NFRs)
- **Performance:**
    - Dashboard page load time must be less than 3 seconds.
    - API response times must be under 200ms for 95% of requests.
- **Scalability:**
    - The system must support up to 1,000 concurrent users.
    - It must be capable of handling data ingestion from over 50 external ad platforms.
- **Security:**
    - All data must be encrypted at rest and in transit.
    - The system must be compliant with GDPR regulations.
- **Reliability:**
    - The system must have an uptime of 99.9%.

### 5. Technical Constraints & Decisions
- **Mandated Technologies:**
    - **Backend:** Python (FastAPI framework)
    - **Frontend:** TypeScript, React
    - **Database:** PostgreSQL
- **Existing Systems Integration:**
    - Must integrate with the company's existing single sign-on (SSO) solution, Okta.
- **Architectural Decisions:**
    - The system must be built using a microservices architecture.
    - Data ingestion must be handled asynchronously via a message queue (RabbitMQ).
    - The entire solution must be deployed on Amazon Web Services (AWS).

### 6. Data & Integration Points
- **Key Data Entities:**
    - `Campaign`
    - `AdPlatform`
    - `PerformanceMetric`
    - `User`
- **Inputs & Outputs (APIs):**
    - **Input:** An ingestion API endpoint for receiving data from external platforms (`POST /api/v1/ingest`).
    - **Output:** An API endpoint to provide campaign metrics to the frontend (`GET /api/v1/campaigns/{id}/metrics`).