openapi: 3.0.3
info:
  title: Dopemux API
  description: |
    RESTful API for the Dopemux ADHD-accommodated development platform.

    This API provides comprehensive access to development tools, AI assistance,
    personal automation, and ADHD accommodations. All endpoints are designed
    with cognitive load optimization and context preservation in mind.
  version: "1.0.0"
  contact:
    name: Dopemux API Support
    url: https://docs.dopemux.com
    email: api-support@dopemux.com
  license:
    name: MIT
    url: https://opensource.org/licenses/MIT

servers:
  - url: https://api.dopemux.com/v1
    description: Production server
  - url: https://api-staging.dopemux.com/v1
    description: Staging server
  - url: http://localhost:3000/v1
    description: Local development server

security:
  - OAuth2: []
  - ApiKeyAuth: []

tags:
  - name: Authentication
    description: User authentication and authorization
  - name: Projects
    description: Development project management
  - name: Memory
    description: Context and memory management
  - name: Agents
    description: AI agent orchestration
  - name: Workflows
    description: Automation workflow management
  - name: ADHD
    description: ADHD accommodations and preferences
  - name: Analytics
    description: Usage analytics and insights

paths:
  # Authentication Endpoints
  /auth/login:
    post:
      tags: [Authentication]
      summary: Authenticate user
      description: |
        Authenticate user and obtain access tokens. Supports multiple
        authentication methods including OAuth2, SSO, and API keys.
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                grant_type:
                  type: string
                  enum: [password, authorization_code, refresh_token]
                username:
                  type: string
                  description: User email or username
                password:
                  type: string
                  format: password
                  description: User password (for password grant)
                code:
                  type: string
                  description: Authorization code (for authorization_code grant)
                refresh_token:
                  type: string
                  description: Refresh token (for refresh_token grant)
              required:
                - grant_type
      responses:
        '200':
          description: Authentication successful
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/AuthResponse'
        '401':
          description: Authentication failed
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'

  /auth/logout:
    post:
      tags: [Authentication]
      summary: Logout user
      description: Revoke access tokens and end user session
      security:
        - OAuth2: []
      responses:
        '200':
          description: Logout successful
        '401':
          description: Invalid or expired token

  # Project Management Endpoints
  /projects:
    get:
      tags: [Projects]
      summary: List user projects
      description: |
        Retrieve all projects accessible to the authenticated user.
        Supports filtering, sorting, and pagination.
      parameters:
        - name: filter
          in: query
          description: Filter projects by status, technology, or tags
          schema:
            type: string
        - name: sort
          in: query
          description: Sort order (name, created_at, updated_at)
          schema:
            type: string
            enum: [name, created_at, updated_at, -name, -created_at, -updated_at]
        - name: limit
          in: query
          description: Number of projects to return (max 100)
          schema:
            type: integer
            minimum: 1
            maximum: 100
            default: 20
        - name: offset
          in: query
          description: Number of projects to skip for pagination
          schema:
            type: integer
            minimum: 0
            default: 0
      responses:
        '200':
          description: Projects retrieved successfully
          content:
            application/json:
              schema:
                type: object
                properties:
                  projects:
                    type: array
                    items:
                      $ref: '#/components/schemas/Project'
                  pagination:
                    $ref: '#/components/schemas/PaginationInfo'

    post:
      tags: [Projects]
      summary: Create new project
      description: |
        Create a new development project with ADHD accommodations
        and AI assistance configuration.
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CreateProjectRequest'
      responses:
        '201':
          description: Project created successfully
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Project'
        '400':
          description: Invalid project data
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'

  /projects/{projectId}:
    get:
      tags: [Projects]
      summary: Get project details
      parameters:
        - name: projectId
          in: path
          required: true
          schema:
            type: string
            format: uuid
      responses:
        '200':
          description: Project details retrieved
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Project'
        '404':
          description: Project not found

    put:
      tags: [Projects]
      summary: Update project
      parameters:
        - name: projectId
          in: path
          required: true
          schema:
            type: string
            format: uuid
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/UpdateProjectRequest'
      responses:
        '200':
          description: Project updated successfully
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Project'

    delete:
      tags: [Projects]
      summary: Delete project
      parameters:
        - name: projectId
          in: path
          required: true
          schema:
            type: string
            format: uuid
      responses:
        '204':
          description: Project deleted successfully
        '404':
          description: Project not found

  # Memory Management Endpoints
  /memory/blocks:
    get:
      tags: [Memory]
      summary: Retrieve memory blocks
      description: |
        Get memory blocks based on context, project, or semantic similarity.
        Supports ADHD-optimized retrieval with cognitive load considerations.
      parameters:
        - name: context
          in: query
          description: Context for memory retrieval
          schema:
            type: string
        - name: project_id
          in: query
          description: Filter by project ID
          schema:
            type: string
            format: uuid
        - name: block_type
          in: query
          description: Type of memory block
          schema:
            type: string
            enum: [persona, project_context, decisions, patterns, runbook, lessons]
        - name: similarity_threshold
          in: query
          description: Minimum similarity score for retrieval (0.0-1.0)
          schema:
            type: number
            minimum: 0.0
            maximum: 1.0
            default: 0.7
      responses:
        '200':
          description: Memory blocks retrieved
          content:
            application/json:
              schema:
                type: object
                properties:
                  blocks:
                    type: array
                    items:
                      $ref: '#/components/schemas/MemoryBlock'
                  relevance_scores:
                    type: array
                    items:
                      type: number

    post:
      tags: [Memory]
      summary: Create memory block
      description: Store new information in the memory system
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CreateMemoryBlockRequest'
      responses:
        '201':
          description: Memory block created
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/MemoryBlock'

  # Agent Orchestration Endpoints
  /agents:
    get:
      tags: [Agents]
      summary: List available agents
      description: |
        Retrieve list of AI agents available for orchestration,
        including their capabilities and current status.
      responses:
        '200':
          description: Agents retrieved successfully
          content:
            application/json:
              schema:
                type: object
                properties:
                  agents:
                    type: array
                    items:
                      $ref: '#/components/schemas/Agent'

  /agents/{agentId}/execute:
    post:
      tags: [Agents]
      summary: Execute agent task
      description: |
        Execute a task using a specific AI agent with context
        and ADHD accommodations.
      parameters:
        - name: agentId
          in: path
          required: true
          schema:
            type: string
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/AgentExecutionRequest'
      responses:
        '200':
          description: Task executed successfully
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/AgentExecutionResponse'
        '202':
          description: Task accepted for asynchronous execution
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/AsyncTaskResponse'

  # ADHD Accommodations Endpoints
  /adhd/preferences:
    get:
      tags: [ADHD]
      summary: Get ADHD preferences
      description: Retrieve user's ADHD accommodation preferences and settings
      responses:
        '200':
          description: ADHD preferences retrieved
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ADHDPreferences'

    put:
      tags: [ADHD]
      summary: Update ADHD preferences
      description: Update user's ADHD accommodation settings
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/ADHDPreferences'
      responses:
        '200':
          description: Preferences updated successfully

  /adhd/metrics:
    get:
      tags: [ADHD]
      summary: Get accommodation effectiveness metrics
      description: |
        Retrieve metrics on ADHD accommodation effectiveness,
        including attention patterns and productivity improvements.
      parameters:
        - name: time_range
          in: query
          description: Time range for metrics (1d, 7d, 30d, 90d)
          schema:
            type: string
            enum: [1d, 7d, 30d, 90d]
            default: 7d
      responses:
        '200':
          description: Metrics retrieved successfully
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ADHDMetrics'

components:
  securitySchemes:
    OAuth2:
      type: oauth2
      flows:
        authorizationCode:
          authorizationUrl: https://auth.dopemux.com/oauth/authorize
          tokenUrl: https://auth.dopemux.com/oauth/token
          scopes:
            read_profile: Read user profile and accommodation settings
            write_profile: Modify user profile and preferences
            read_development: Access development project data
            write_development: Modify development projects and code
            read_automation: Access personal automation features
            write_automation: Configure and execute personal automation
            read_memory: Access stored context and memory
            write_memory: Store and modify context and memory
            admin: Administrative access for enterprise features

    ApiKeyAuth:
      type: apiKey
      in: header
      name: X-API-Key

  schemas:
    AuthResponse:
      type: object
      properties:
        access_token:
          type: string
          description: OAuth2 access token
        refresh_token:
          type: string
          description: OAuth2 refresh token
        token_type:
          type: string
          enum: [Bearer]
        expires_in:
          type: integer
          description: Token lifetime in seconds
        scope:
          type: string
          description: Granted scopes
        user:
          $ref: '#/components/schemas/User'

    User:
      type: object
      properties:
        id:
          type: string
          format: uuid
        email:
          type: string
          format: email
        name:
          type: string
        avatar_url:
          type: string
          format: uri
        adhd_profile:
          $ref: '#/components/schemas/ADHDProfile'
        created_at:
          type: string
          format: date-time
        updated_at:
          type: string
          format: date-time

    Project:
      type: object
      properties:
        id:
          type: string
          format: uuid
        name:
          type: string
          maxLength: 100
        description:
          type: string
          maxLength: 500
        status:
          type: string
          enum: [active, paused, completed, archived]
        technology_stack:
          type: array
          items:
            type: string
        adhd_accommodations:
          $ref: '#/components/schemas/ProjectADHDSettings'
        memory_context:
          type: object
          description: Project-specific memory and context
        ai_agents:
          type: array
          items:
            type: string
          description: Associated AI agents
        created_at:
          type: string
          format: date-time
        updated_at:
          type: string
          format: date-time

    CreateProjectRequest:
      type: object
      required:
        - name
        - technology_stack
      properties:
        name:
          type: string
          maxLength: 100
        description:
          type: string
          maxLength: 500
        technology_stack:
          type: array
          items:
            type: string
        adhd_accommodations:
          $ref: '#/components/schemas/ProjectADHDSettings'
        template_id:
          type: string
          format: uuid
          description: Optional project template

    MemoryBlock:
      type: object
      properties:
        id:
          type: string
          format: uuid
        block_type:
          type: string
          enum: [persona, project_context, decisions, patterns, runbook, lessons]
        content:
          type: string
          description: Memory block content
        metadata:
          type: object
          properties:
            project_id:
              type: string
              format: uuid
            tags:
              type: array
              items:
                type: string
            importance:
              type: string
              enum: [low, medium, high, critical]
            access_count:
              type: integer
        embeddings:
          type: array
          items:
            type: number
          description: Vector embeddings for similarity search
        created_at:
          type: string
          format: date-time
        updated_at:
          type: string
          format: date-time

    Agent:
      type: object
      properties:
        id:
          type: string
        name:
          type: string
        description:
          type: string
        capabilities:
          type: array
          items:
            type: string
        status:
          type: string
          enum: [available, busy, offline, error]
        performance_metrics:
          type: object
          properties:
            success_rate:
              type: number
              minimum: 0
              maximum: 1
            average_response_time:
              type: number
              description: Average response time in milliseconds
            current_load:
              type: number
              minimum: 0
              maximum: 1

    ADHDPreferences:
      type: object
      properties:
        attention_tracking:
          type: boolean
          default: true
        break_reminders:
          type: boolean
          default: true
        focus_mode:
          type: string
          enum: [adaptive, deep, scanning, break]
          default: adaptive
        distraction_shield:
          type: boolean
          default: true
        reduced_motion:
          type: boolean
          default: false
        high_contrast:
          type: boolean
          default: false
        notification_preferences:
          type: object
          properties:
            frequency:
              type: string
              enum: [minimal, normal, frequent]
            channels:
              type: array
              items:
                type: string
                enum: [email, push, sms, in_app]

    ADHDProfile:
      type: object
      properties:
        assessment_completed:
          type: boolean
        accommodation_preferences:
          $ref: '#/components/schemas/ADHDPreferences'
        effectiveness_metrics:
          type: object
          properties:
            focus_improvement:
              type: number
              description: Percentage improvement in focus metrics
            task_completion_rate:
              type: number
              description: Task completion rate improvement
            cognitive_load_reduction:
              type: number
              description: Measured cognitive load reduction

    ErrorResponse:
      type: object
      properties:
        error:
          type: string
          description: Error code
        message:
          type: string
          description: Human-readable error message
        details:
          type: object
          description: Additional error context
        request_id:
          type: string
          description: Request ID for debugging

    PaginationInfo:
      type: object
      properties:
        total:
          type: integer
          description: Total number of items
        limit:
          type: integer
          description: Items per page
        offset:
          type: integer
          description: Current offset
        has_more:
          type: boolean
          description: Whether more items are available