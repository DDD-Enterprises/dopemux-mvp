# Test and CI Evidence

## workflows
.github/workflows/gemini-review.yml
name: '🔎 Gemini Review'

on:
  workflow_call:
    inputs:
      additional_context:
        type: 'string'
        description: 'Any additional context from the request'
        required: false

concurrency:
  group: '${{ github.workflow }}-review-${{ github.event_name }}-${{ github.event.pull_request.number || github.event.issue.number }}'
  cancel-in-progress: true

defaults:
  run:
    shell: 'bash'

jobs:
  review:
    runs-on: 'ubuntu-latest'
    timeout-minutes: 7
    # The Gemini CLI hard-fails in headless mode unless the workspace is trusted.
    # Review is gated by gemini-dispatch.yml to OWNER/MEMBER/COLLABORATOR authors
    # only, which bounds the trust to repo collaborators' PRs. Re-added after
    # 4206a2972 removed it (a newer CLI now enforces trusted-folders).
    env:
      GEMINI_CLI_TRUST_WORKSPACE: 'true'
    permissions:
      contents: 'read'
      id-token: 'write'
      issues: 'write'
      pull-requests: 'write'
    steps:
      - name: 'Mint identity token'
        id: 'mint_identity_token'
        if: |-
          ${{ vars.APP_ID }}
        uses: 'actions/create-github-app-token@29824e69f54612133e76f7eaac726eef6c875baf' # ratchet:actions/create-github-app-token@v2
        with:
          app-id: '${{ vars.APP_ID }}'
          private-key: '${{ secrets.APP_PRIVATE_KEY }}'
          permission-contents: 'read'
          permission-issues: 'write'
          permission-pull-requests: 'write'

      - name: 'Checkout repository'
        uses: 'actions/checkout@8e8c483db84b4bee98b60c0593521ed34d9990e8' # ratchet:actions/checkout@v6

      - name: 'Run Gemini pull request review'
        uses: 'google-github-actions/run-gemini-cli@v0' # ratchet:exclude
        id: 'gemini_pr_review'
        env:
          GEMINI_CLI_TRUST_WORKSPACE: 'true'
          GITHUB_TOKEN: '${{ steps.mint_identity_token.outputs.token || secrets.GITHUB_TOKEN || github.token }}'
          ISSUE_TITLE: '${{ github.event.pull_request.title || github.event.issue.title }}'
          ISSUE_BODY: '${{ github.event.pull_request.body || github.event.issue.body }}'
          PULL_REQUEST_NUMBER: '${{ github.event.pull_request.number || github.event.issue.number }}'
          REPOSITORY: '${{ github.repository }}'
          ADDITIONAL_CONTEXT: '${{ inputs.additional_context }}'
        with:
          gcp_location: '${{ vars.GOOGLE_CLOUD_LOCATION }}'
          gcp_project_id: '${{ vars.GOOGLE_CLOUD_PROJECT }}'
          gcp_service_account: '${{ vars.SERVICE_ACCOUNT_EMAIL }}'
          gcp_workload_identity_provider: '${{ vars.GCP_WIF_PROVIDER }}'
          gemini_api_key: '${{ secrets.GEMINI_API_KEY }}'
          gemini_cli_version: '${{ vars.GEMINI_CLI_VERSION }}'
          gemini_debug: '${{ fromJSON(vars.GEMINI_DEBUG || vars.ACTIONS_STEP_DEBUG || false) }}'
          gemini_model: '${{ vars.GEMINI_MODEL }}'
          google_api_key: '${{ secrets.GOOGLE_API_KEY }}'
          use_gemini_code_assist: '${{ vars.GOOGLE_GENAI_USE_GCA }}'
          use_vertex_ai: '${{ vars.GOOGLE_GENAI_USE_VERTEXAI }}'
          upload_artifacts: '${{ vars.UPLOAD_ARTIFACTS }}'
          workflow_name: 'gemini-review'
          settings: |-
            {
              "model": {
                "maxSessionTurns": 100
              },
              "telemetry": {
                "enabled": true,
                "target": "local",
                "outfile": ".gemini/telemetry.log"
              },
              "mcpServers": {
                "github": {
                  "command": "docker",
                  "args": [
                    "run",
                    "-i",
                    "--rm",
                    "-e",
                    "GITHUB_PERSONAL_ACCESS_TOKEN",
                    "ghcr.io/github/github-mcp-server:v0.27.0"
                  ],
                  "includeTools": [
                    "add_comment_to_pending_review",
                    "pull_request_read",
                    "pull_request_review_write"
                  ],
                  "env": {
                    "GITHUB_PERSONAL_ACCESS_TOKEN": "${GITHUB_TOKEN}"
                  }
                }
              },
              "tools": {
                "core": [
                  "run_shell_command(cat)",
                  "run_shell_command(echo)",
                  "run_shell_command(grep)",
                  "run_shell_command(head)",
                  "run_shell_command(tail)"
                ]
              }
            }
          prompt: '/gemini-review'
.github/workflows/security-review.yml
name: 🔒 Security Review with Claude Code

permissions:
  pull-requests: write  # Needed for PR comments
  contents: read
  issues: write         # For issue tracking

on:
  pull_request:
    types: [opened, synchronize, reopened]
  push:
    branches: [main]
  merge_group:
    types: [checks_requested]

jobs:
  security-review:
    name: "🤖 Claude Code Security Analysis"
    runs-on: ubuntu-latest
    timeout-minutes: 25  # ADHD-optimized: 25-minute chunks
    if: github.repository == 'DDD-Enterprises/dopemux-mvp' && (github.event_name != 'pull_request' || github.event.pull_request.head.repo.full_name == github.repository)
    env:
      ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}

    steps:
      - name: 📥 Checkout code
        uses: actions/checkout@v5
        with:
          ref: ${{ github.event.pull_request.head.sha || github.sha }}
          fetch-depth: 2  # Get enough history for diff analysis
      - name: 🔐 ADHD-Optimized Security Review
        if: ${{ env.ANTHROPIC_API_KEY != '' }}
        uses: anthropics/claude-code-security-review@main
        with:
          comment-pr: true
          claude-api-key: ${{ env.ANTHROPIC_API_KEY }}
          upload-results: true

          # ADHD-optimized timeout (25-minute focus sessions)
          claudecode-timeout: "20"

          # Use latest Claude model for best analysis
          claude-model: "claude-opus-4-1-20250805"

          # Custom instructions for memory/intelligence systems
          # Use absolute paths: the upstream composite action chdirs into
          # `github.action_path` before opening these files, so a repo-relative
          # path resolves under the action's checkout instead of the workspace
          # and the customizations silently fall back to defaults.
          custom-security-scan-instructions: ${{ github.workspace }}/.github/security-scan-instructions.txt
          false-positive-filtering-instructions: ${{ github.workspace }}/.github/security-filtering-instructions.txt

          # Exclude test directories and generated files to reduce noise
          exclude-directories: "tests,__pycache__,node_modules,.git,docker/leantime/data"

          # Run on every commit for comprehensive coverage
          run-every-commit: false

  # ADHD-friendly summary for non-technical stakeholders
  security-summary:
    name: "📊 ADHD-Friendly Security Summary"
    runs-on: ubuntu-latest
    needs: security-review
    if: always() && github.event_name == 'pull_request'

    steps:
      - name: 🎯 Generate gentle security report
        run: |
          echo "🧠 **ADHD-Friendly Security Check Complete**" >> $GITHUB_STEP_SUMMARY
          echo "" >> $GITHUB_STEP_SUMMARY

          if [ "${{ needs.security-review.result }}" == "success" ]; then
            echo "✅ **Great news!** Your code changes look secure." >> $GITHUB_STEP_SUMMARY
            echo "" >> $GITHUB_STEP_SUMMARY
            echo "**What this means:**" >> $GITHUB_STEP_SUMMARY
            echo "- No high-severity security issues detected" >> $GITHUB_STEP_SUMMARY
            echo "- Memory system components are safe" >> $GITHUB_STEP_SUMMARY
            echo "- Ready for merge when tests pass!" >> $GITHUB_STEP_SUMMARY
          elif [ "${{ needs.security-review.result }}" == "skipped" ]; then
            echo "⏭️ **Security review skipped** (API key missing or not required)" >> $GITHUB_STEP_SUMMARY
          else
            echo "⚠️ **Security items need attention**" >> $GITHUB_STEP_SUMMARY
            echo "" >> $GITHUB_STEP_SUMMARY
            echo "**Next steps:**" >> $GITHUB_STEP_SUMMARY
            echo "1. Check the detailed findings in the PR comments above" >> $GITHUB_STEP_SUMMARY
            echo "2. Address high-priority items first (marked 🔴)" >> $GITHUB_STEP_SUMMARY
            echo "3. Ask for help if anything is unclear" >> $GITHUB_STEP_SUMMARY
          fi

          echo "" >> $GITHUB_STEP_SUMMARY
          echo "**💡 Remember:** Small, focused security fixes work best!" >> $GITHUB_STEP_SUMMARY
          echo "_Take breaks and tackle one issue at a time._" >> $GITHUB_STEP_SUMMARY
.github/workflows/gemini-dispatch.yml
name: '🔀 Gemini Dispatch'

on:
  pull_request_review_comment:
    types:
      - 'created'
  pull_request_review:
    types:
      - 'submitted'
  pull_request:
    types:
      - 'opened'
  issues:
    types:
      - 'opened'
      - 'reopened'
  issue_comment:
    types:
      - 'created'

defaults:
  run:
    shell: 'bash'

jobs:
  debugger:
    if: |-
      ${{ fromJSON(vars.GEMINI_DEBUG || vars.ACTIONS_STEP_DEBUG || false) }}
    runs-on: 'ubuntu-latest'
    permissions:
      contents: 'read'
    steps:
      - name: 'Print context for debugging'
        env:
          DEBUG_event_name: '${{ github.event_name }}'
          DEBUG_event__action: '${{ github.event.action }}'
          DEBUG_event__comment__author_association: '${{ github.event.comment.author_association }}'
          DEBUG_event__issue__author_association: '${{ github.event.issue.author_association }}'
          DEBUG_event__pull_request__author_association: '${{ github.event.pull_request.author_association }}'
          DEBUG_event__review__author_association: '${{ github.event.review.author_association }}'
          DEBUG_event: '${{ toJSON(github.event) }}'
        run: |-
          env | grep '^DEBUG_'

  dispatch:
    # For PRs: only if not from a fork
    # For issues: only on open/reopen
    # For comments: only if user types @gemini-cli and is OWNER/MEMBER/COLLABORATOR
    if: |-
      (
        github.event_name == 'pull_request' &&
        github.event.pull_request.head.repo.fork == false
      ) || (
        github.event_name == 'issues' &&
        contains(fromJSON('["opened", "reopened"]'), github.event.action)
      ) || (
        github.event.sender.type == 'User' &&
        startsWith(github.event.comment.body || github.event.review.body || github.event.issue.body, '@gemini-cli') &&
        contains(fromJSON('["OWNER", "MEMBER", "COLLABORATOR"]'), github.event.comment.author_association || github.event.review.author_association || github.event.issue.author_association)
      )
    runs-on: 'ubuntu-latest'
    permissions:
      contents: 'read'
      issues: 'write'
      pull-requests: 'write'
    outputs:
      command: '${{ steps.extract_command.outputs.command }}'
      request: '${{ steps.extract_command.outputs.request }}'
      additional_context: '${{ steps.extract_command.outputs.additional_context }}'
      has_gemini_credentials: '${{ steps.detect_gemini_credentials.outputs.available }}'
      issue_number: '${{ github.event.pull_request.number || github.event.issue.number }}'
    steps:
      - name: 'Mint identity token'
        id: 'mint_identity_token'
        if: |-
          ${{ vars.APP_ID }}
        uses: 'actions/create-github-app-token@29824e69f54612133e76f7eaac726eef6c875baf' # ratchet:actions/create-github-app-token@v2
        with:
          app-id: '${{ vars.APP_ID }}'
          private-key: '${{ secrets.APP_PRIVATE_KEY }}'
          permission-contents: 'read'
          permission-issues: 'write'
          permission-pull-requests: 'write'

      - name: 'Extract command'
        id: 'extract_command'
        uses: 'actions/github-script@ed597411d8f924073f98dfc5c65a23a2325f34cd' # ratchet:actions/github-script@v8.0.0
        env:
          EVENT_TYPE: '${{ github.event_name }}.${{ github.event.action }}'
          REQUEST: '${{ github.event.comment.body || github.event.review.body || github.event.issue.body }}'
        with:
          script: |
            const eventType = process.env.EVENT_TYPE;
            const request = process.env.REQUEST;
            core.setOutput('request', request);

            if (eventType === 'pull_request.opened') {
              core.setOutput('command', 'review');
            } else if (['issues.opened', 'issues.reopened'].includes(eventType)) {
              core.setOutput('command', 'triage');
            } else if (request.startsWith("@gemini-cli /review")) {
              core.setOutput('command', 'review');
              const additionalContext = request.replace(/^@gemini-cli \/review/, '').trim();
              core.setOutput('additional_context', additionalContext);
            } else if (request.startsWith("@gemini-cli /triage")) {
              core.setOutput('command', 'triage');
            } else if (request.startsWith("@gemini-cli /approve")) {
              core.setOutput('command', 'approve');
            } else if (request.startsWith("@gemini-cli")) {
              const additionalContext = request.replace(/^@gemini-cli/, '').trim();
              core.setOutput('command', 'invoke');
              core.setOutput('additional_context', additionalContext);
            } else {
              core.setOutput('command', 'fallthrough');
            }

      - name: 'Detect Gemini credentials'
        id: 'detect_gemini_credentials'
        env:
          GEMINI_API_KEY: '${{ secrets.GEMINI_API_KEY }}'
          GOOGLE_API_KEY: '${{ secrets.GOOGLE_API_KEY }}'
          GCP_WIF_PROVIDER: '${{ vars.GCP_WIF_PROVIDER }}'
        run: |-
          if [[ -n "${GEMINI_API_KEY}" || -n "${GOOGLE_API_KEY}" || -n "${GCP_WIF_PROVIDER}" ]]; then
            echo 'available=true' >> "${GITHUB_OUTPUT}"
          else
            echo 'available=false' >> "${GITHUB_OUTPUT}"
          fi

      - name: 'Acknowledge request'
        env:
          GITHUB_TOKEN: '${{ steps.mint_identity_token.outputs.token || secrets.GITHUB_TOKEN || github.token }}'
          ISSUE_NUMBER: '${{ github.event.pull_request.number || github.event.issue.number }}'
          MESSAGE: |-
            🤖 Hi @${{ github.actor }}, I've received your request, and I'm working on it now! You can track my progress [in the logs](${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}) for more details.
          REPOSITORY: '${{ github.repository }}'
        run: |-
          gh issue comment "${ISSUE_NUMBER}" \
            --body "${MESSAGE}" \
            --repo "${REPOSITORY}"

  review:
    needs: 'dispatch'
    if: |-
      ${{ needs.dispatch.outputs.command == 'review' && needs.dispatch.outputs.has_gemini_credentials == 'true' }}
    uses: './.github/workflows/gemini-review.yml'
    permissions:
      contents: 'read'
      id-token: 'write'
      issues: 'write'
      pull-requests: 'write'
    with:
      additional_context: '${{ needs.dispatch.outputs.additional_context }}'
    secrets: 'inherit'

  triage:
    needs: 'dispatch'
    if: |-
      ${{ needs.dispatch.outputs.command == 'triage' && needs.dispatch.outputs.has_gemini_credentials == 'true' }}
    uses: './.github/workflows/gemini-triage.yml'
    permissions:
      contents: 'read'
      id-token: 'write'
      issues: 'write'
      pull-requests: 'write'
    with:
      additional_context: '${{ needs.dispatch.outputs.additional_context }}'
    secrets: 'inherit'

  invoke:
    needs: 'dispatch'
    if: |-
      ${{ needs.dispatch.outputs.command == 'invoke' && needs.dispatch.outputs.has_gemini_credentials == 'true' }}
    uses: './.github/workflows/gemini-invoke.yml'
    permissions:
      contents: 'read'
      id-token: 'write'
      issues: 'write'
      pull-requests: 'write'
    with:
      additional_context: '${{ needs.dispatch.outputs.additional_context }}'
    secrets: 'inherit'

  plan-execute:
    needs: 'dispatch'
    if: |-
      ${{ needs.dispatch.outputs.command == 'approve' && needs.dispatch.outputs.has_gemini_credentials == 'true' }}
    uses: './.github/workflows/gemini-plan-execute.yml'
    permissions:
      contents: 'write'
      id-token: 'write'
      issues: 'write'
      pull-requests: 'write'
    with:
      additional_context: '${{ needs.dispatch.outputs.additional_context }}'
    secrets: 'inherit'

  fallthrough:
    needs:
      - 'dispatch'
      - 'review'
      - 'triage'
      - 'invoke'
      - 'plan-execute'
    if: |-
      ${{ always() && !cancelled() && (failure() || needs.dispatch.outputs.command == 'fallthrough') }}
    runs-on: 'ubuntu-latest'
    permissions:
      contents: 'read'
      issues: 'write'
      pull-requests: 'write'
    steps:
      - name: 'Mint identity token'
        id: 'mint_identity_token'
        if: |-
          ${{ vars.APP_ID }}
        uses: 'actions/create-github-app-token@29824e69f54612133e76f7eaac726eef6c875baf' # ratchet:actions/create-github-app-token@v2
        with:
          app-id: '${{ vars.APP_ID }}'
          private-key: '${{ secrets.APP_PRIVATE_KEY }}'
          permission-contents: 'read'
          permission-issues: 'write'
          permission-pull-requests: 'write'

      - name: 'Send failure comment'
        env:
          GITHUB_TOKEN: '${{ steps.mint_identity_token.outputs.token || secrets.GITHUB_TOKEN || github.token }}'
          ISSUE_NUMBER: '${{ github.event.pull_request.number || github.event.issue.number }}'
          MESSAGE: |-
            🤖 I'm sorry @${{ github.actor }}, but I was unable to process your request. Please [see the logs](${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}) for more details.
          REPOSITORY: '${{ github.repository }}'
        run: |-
          gh issue comment "${ISSUE_NUMBER}" \
            --body "${MESSAGE}" \
            --repo "${REPOSITORY}"
.github/workflows/preflight.yml
name: preflight

on:
  pull_request:
    types: [opened, synchronize, reopened, ready_for_review]
  workflow_dispatch:

jobs:
  preflight:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install uv
        uses: astral-sh/setup-uv@v7
        with:
          enable-cache: true

      - name: Install jq
        run: sudo apt-get update && sudo apt-get install -y jq

      - name: Run preflight
        run: |
          chmod +x ./scripts/preflight.sh
          RUN_MODE=enforce \
          TP_ID=CI-PREFLIGHT \
          ./scripts/preflight.sh
.github/workflows/pr-steward.yml
name: PR Steward

on:
  pull_request:
    types: [opened, synchronize, reopened, ready_for_review]
  workflow_dispatch:
    inputs:
      pr_number:
        description: Pull request number to inspect
        required: true
        type: string

permissions:
  contents: read
  pull-requests: read
  checks: read
  statuses: read
  actions: read
  issues: read

jobs:
  pr-steward:
    name: advisory check-only intake
    runs-on: ubuntu-latest
    env:
      GH_TOKEN: ${{ github.token }}
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Set PR number
        id: pr
        env:
          EVENT_NAME: ${{ github.event_name }}
          EVENT_PR_NUMBER: ${{ github.event.pull_request.number }}
          INPUT_PR_NUMBER: ${{ inputs.pr_number }}
        run: |
          if [ "$EVENT_NAME" = "pull_request" ]; then
            printf 'number=%s\n' "$EVENT_PR_NUMBER" >> "$GITHUB_OUTPUT"
          else
            printf 'number=%s\n' "$INPUT_PR_NUMBER" >> "$GITHUB_OUTPUT"
          fi

      - name: Refresh PR audit proof
        run: |
          python -m scripts.audit.pr_audit_router \
            --dry-run \
            --packet-id TP-DMX-PR-AUDIT-ROUTER-001 \
            --git-sha "${{ github.event.pull_request.head.sha || github.sha }}" \
            --out proof/TP-DMX-PR-AUDIT-ROUTER-001/MULTI_MODEL_PR_AUDIT.json

      - name: Run PR Steward
        id: steward
        continue-on-error: true
        run: |
          set +e
          python -m tools.pr_steward.intake \
            --repo "$GITHUB_REPOSITORY" \
            --pr "${{ steps.pr.outputs.number }}" \
            --out pr-steward-artifacts \
            --strict \
            --format text \
            --proof-path proof/TP-DMX-PR-AUDIT-ROUTER-001/MULTI_MODEL_PR_AUDIT.json
          status=$?
          printf 'exit_code=%s\n' "$status" >> "$GITHUB_OUTPUT"
          exit 0

      - name: Write job summary
        if: always()
        run: |
          {
            printf '## PR Steward advisory result\n\n'
            printf -- '- exit_code: %s\n' '${{ steps.steward.outputs.exit_code }}'
            printf -- '- mutation_performed: false\n\n'
            if [ -f pr-steward-artifacts/PR_STEWARD_SUMMARY.md ]; then
              cat pr-steward-artifacts/PR_STEWARD_SUMMARY.md
            else
              printf 'PR Steward did not emit a summary artifact.\n'
            fi
          } >> "$GITHUB_STEP_SUMMARY"

      - name: Upload PR Steward artifacts
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: pr-steward-${{ steps.pr.outputs.number }}
          path: pr-steward-artifacts/
          if-no-files-found: warn
.github/workflows/gemini-invoke.yml
name: '▶️ Gemini Invoke'

on:
  workflow_call:
    inputs:
      additional_context:
        type: 'string'
        description: 'Any additional context from the request'
        required: false

concurrency:
  group: '${{ github.workflow }}-invoke-${{ github.event_name }}-${{ github.event.pull_request.number || github.event.issue.number }}'
  cancel-in-progress: false

defaults:
  run:
    shell: 'bash'

jobs:
  invoke:
    runs-on: 'ubuntu-latest'
    env:
      GEMINI_CLI_TRUST_WORKSPACE: 'true'
    permissions:
      contents: 'read'
      id-token: 'write'
      issues: 'write'
      pull-requests: 'write'
    steps:
      - name: 'Mint identity token'
        id: 'mint_identity_token'
        if: |-
          ${{ vars.APP_ID }}
        uses: 'actions/create-github-app-token@29824e69f54612133e76f7eaac726eef6c875baf' # ratchet:actions/create-github-app-token@v2
        with:
          app-id: '${{ vars.APP_ID }}'
          private-key: '${{ secrets.APP_PRIVATE_KEY }}'
          permission-contents: 'read'
          permission-issues: 'write'
          permission-pull-requests: 'write'

      - name: 'Checkout Code'
        uses: 'actions/checkout@v4' # ratchet:exclude

      - name: 'Run Gemini CLI'
        id: 'run_gemini'
        uses: 'google-github-actions/run-gemini-cli@v0' # ratchet:exclude
        env:
          TITLE: '${{ github.event.pull_request.title || github.event.issue.title }}'
          DESCRIPTION: '${{ github.event.pull_request.body || github.event.issue.body }}'
          EVENT_NAME: '${{ github.event_name }}'
          GITHUB_TOKEN: '${{ steps.mint_identity_token.outputs.token || secrets.GITHUB_TOKEN || github.token }}'
          IS_PULL_REQUEST: '${{ !!github.event.pull_request }}'
          ISSUE_NUMBER: '${{ github.event.pull_request.number || github.event.issue.number }}'
          REPOSITORY: '${{ github.repository }}'
          ADDITIONAL_CONTEXT: '${{ inputs.additional_context }}'
        with:
          gcp_location: '${{ vars.GOOGLE_CLOUD_LOCATION }}'
          gcp_project_id: '${{ vars.GOOGLE_CLOUD_PROJECT }}'
          gcp_service_account: '${{ vars.SERVICE_ACCOUNT_EMAIL }}'
          gcp_workload_identity_provider: '${{ vars.GCP_WIF_PROVIDER }}'
          gemini_api_key: '${{ secrets.GEMINI_API_KEY }}'
          gemini_cli_version: '${{ vars.GEMINI_CLI_VERSION }}'
          gemini_debug: '${{ fromJSON(vars.GEMINI_DEBUG || vars.ACTIONS_STEP_DEBUG || false) }}'
          gemini_model: '${{ vars.GEMINI_MODEL }}'
          google_api_key: '${{ secrets.GOOGLE_API_KEY }}'
          use_gemini_code_assist: '${{ vars.GOOGLE_GENAI_USE_GCA }}'
          use_vertex_ai: '${{ vars.GOOGLE_GENAI_USE_VERTEXAI }}'
          upload_artifacts: '${{ vars.UPLOAD_ARTIFACTS }}'
          workflow_name: 'gemini-invoke'
          settings: |-
            {
              "model": {
                "maxSessionTurns": 25
              },
              "telemetry": {
                "enabled": true,
                "target": "local",
                "outfile": ".gemini/telemetry.log"
              },
              "mcpServers": {
                "github": {
                  "command": "docker",
                  "args": [
                    "run",
                    "-i",
                    "--rm",
                    "-e",
                    "GITHUB_PERSONAL_ACCESS_TOKEN",
                    "ghcr.io/github/github-mcp-server:v0.27.0"
                  ],
                  "includeTools": [
                    "add_issue_comment",
                    "issue_read",
                    "list_issues",
                    "search_issues",
                    "pull_request_read",
                    "list_pull_requests",
                    "search_pull_requests",
                    "get_commit",
                    "get_file_contents",
                    "list_commits",
                    "search_code"
                  ],
                  "env": {
                    "GITHUB_PERSONAL_ACCESS_TOKEN": "${GITHUB_TOKEN}"
                  }
                }
              },
              "tools": {
                "core": [
                  "run_shell_command(cat)",
                  "run_shell_command(echo)",
                  "run_shell_command(grep)",
                  "run_shell_command(head)",
                  "run_shell_command(tail)"
                ]
              }
            }
          prompt: '/gemini-invoke'
.github/workflows/codeql.yml
name: CodeQL

on:
  push:
    branches:
      - main
  pull_request:
    branches:
      - main
  schedule:
    - cron: "20 5 * * 1"
  workflow_dispatch:

permissions:
  actions: read
  contents: read
  security-events: write

jobs:
  analyze:
    name: Analyze (${{ matrix.language }})
    if: github.event_name != 'dynamic'
    runs-on: ubuntu-latest
    timeout-minutes: 45

    strategy:
      fail-fast: false
      matrix:
        language:
          - ruby
          - python
          - javascript-typescript

    steps:
      - name: Checkout
        uses: actions/checkout@v5

      - name: Initialize CodeQL
        uses: github/codeql-action/init@v3
        with:
          languages: ${{ matrix.language }}

      - name: Perform CodeQL Analysis
        uses: github/codeql-action/analyze@v3
        with:
          category: "/language:${{ matrix.language }}"
.github/workflows/containers.yml
name: Container Build and Publish (GHCR)

on:
  push:
    branches: [main]
    paths:
      - 'Dockerfile'
      - 'services/**/Dockerfile*'
      - 'docker/**/Dockerfile*'
      - '.github/workflows/containers.yml'
  pull_request:
    paths:
      - 'Dockerfile'
      - 'services/**/Dockerfile*'
      - 'docker/**/Dockerfile*'
      - '.github/workflows/containers.yml'

concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

env:
  REGISTRY: ghcr.io
  NAMESPACE: ghcr.io/ddd-enterprises/dopemux-mvp

jobs:
  build:
    name: "Build ${{ matrix.service }}"
    runs-on: ubuntu-latest
    timeout-minutes: 30

    permissions:
      contents: read
      packages: write

    env:
      DHI_TOKEN: ${{ secrets.DHI_TOKEN }}

    strategy:
      fail-fast: false
      matrix:
        include:
          - service: dopemux-backend
            dockerfile: Dockerfile
            context: .
            smoke_test: "false"

          # -- Frontend
          # Removed - ui-dashboard deprecated

          # -- MCP: ConPort
          - service: conport
            dockerfile: docker/mcp-servers-source/conport/Dockerfile
            context: .
            smoke_test: "false"

          # -- MCP: LiteLLM proxy
          - service: litellm
            dockerfile: docker/mcp-servers-source/litellm/Dockerfile
            context: .
            smoke_test: "false"

          # -- Cognitive: Task Orchestrator
          - service: task-orchestrator
            dockerfile: services/task-orchestrator/Dockerfile
            context: .
            smoke_test: "false"
            smoke_port: "8000"
            smoke_path: "/health"

          # -- Cognitive: Claude Brain
          - service: claude-brain
            dockerfile: services/claude_brain/Dockerfile
            context: .
            smoke_test: "false"

          # -- Cognitive: ADHD Engine
          - service: adhd-engine
            dockerfile: services/adhd_engine/Dockerfile
            context: .
            smoke_test: "false"
            smoke_port: "8095"
            smoke_path: "/health"

          # -- Coordination: DopeconBridge
          - service: dopecon-bridge
            dockerfile: services/dopecon-bridge/Dockerfile
            context: .
            smoke_test: "false"

          # -- Integration: Webhook Receiver
          - service: webhook-receiver
            dockerfile: services/webhook_receiver/Dockerfile
            context: .
            smoke_test: "false"

          # -- Memory: Dope Memory
          - service: dope-memory
            dockerfile: services/working-memory-assistant/Dockerfile.dope-memory
            context: .
            smoke_test: "true"
            smoke_port: "3020"
            smoke_path: "/health"

    steps:
      - name: Checkout code
        uses: actions/checkout@v5

      - name: Log in to GHCR
        uses: docker/login-action@v4
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Log in to Docker Hardened Images (dhi.io)
        id: dhi_login
        if: ${{ env.DHI_TOKEN != '' }}
        continue-on-error: true
        uses: docker/login-action@v4
        with:
          registry: dhi.io
          username: ${{ github.actor }}
          password: ${{ env.DHI_TOKEN }}

      - name: Fallback to public images when DHI unavailable
        if: ${{ steps.dhi_login.outcome != 'success' }}
        run: |
          echo "::warning::dhi.io login unavailable. Rewriting dhi.io/ base image references to public Docker Hub equivalents."
          find . -name "Dockerfile*" -type f -exec sed -i 's|dhi.io/||g' {} +

      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v6
        with:
          images: ${{ env.NAMESPACE }}/${{ matrix.service }}
          tags: |
            # Tag as 'latest' on main branch pushes
            type=raw,value=latest,enable=${{ github.ref == 'refs/heads/main' }}
            # Always tag with the git SHA (short)
            type=sha,prefix=,format=short
            # Tag PRs with pr-<number>
            type=ref,event=pr

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v4

      - name: Build image reference
        id: image_ref
        run: |
          if [ "${{ github.event_name }}" = "pull_request" ]; then
            echo "value=${{ env.NAMESPACE }}/${{ matrix.service }}:pr-${{ github.event.pull_request.number }}" >> "$GITHUB_OUTPUT"
          else
            echo "value=${{ env.NAMESPACE }}/${{ matrix.service }}:sha-${GITHUB_SHA::7}" >> "$GITHUB_OUTPUT"
          fi

      - name: Resolve build tags
        id: build_tags
        run: |
          if [ "${{ github.event_name }}" = "pull_request" ] && [ "${{ matrix.smoke_test }}" = "true" ]; then
            echo "value=${{ steps.image_ref.outputs.value }}" >> "$GITHUB_OUTPUT"
          else
            {
              echo "value<<EOF"
              echo "${{ steps.meta.outputs.tags }}"
              echo "EOF"
            } >> "$GITHUB_OUTPUT"
          fi

      - name: Build and publish ${{ matrix.service }}
        uses: docker/build-push-action@v7
        with:
          context: ${{ matrix.context }}
          file: ${{ matrix.dockerfile }}
          push: ${{ github.ref == 'refs/heads/main' && github.event_name == 'push' }}
          load: ${{ github.event_name == 'pull_request' && matrix.smoke_test == 'true' }}
          pull: true
          tags: ${{ steps.build_tags.outputs.value }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha,scope=${{ matrix.service }}
          cache-to: type=gha,mode=max,scope=${{ matrix.service }}
          provenance: ${{ github.event_name != 'pull_request' }}
          sbom: ${{ github.event_name != 'pull_request' }}

      - name: Inspect loaded image metadata
        if: ${{ github.event_name == 'pull_request' && matrix.smoke_test == 'true' }}
        run: docker image inspect "${{ steps.image_ref.outputs.value }}" >/dev/null

      - name: Smoke test container startup
        if: ${{ github.event_name == 'pull_request' && matrix.smoke_test == 'true' }}
        env:
          IMAGE_REF: ${{ steps.image_ref.outputs.value }}
          CONTAINER_NAME: ci-${{ matrix.service }}
          SMOKE_PORT: ${{ matrix.smoke_port }}
          SMOKE_PATH: ${{ matrix.smoke_path }}
        run: |
          set -euo pipefail

          container_started=false

          cleanup() {
            if [ "$container_started" = true ]; then
              docker logs "$CONTAINER_NAME" 2>/dev/null || true
            fi
            docker rm -f "$CONTAINER_NAME" 2>/dev/null || true
          }
          trap cleanup EXIT

          extra_env_args=()
          if [ "${{ matrix.service }}" = "adhd-engine" ]; then
            # The service already supports degraded startup for local/test workflows.
            extra_env_args+=( -e ADHD_ENGINE_ALLOW_DEGRADED_STARTUP=1 )
          fi

          docker run -d \
            --name "$CONTAINER_NAME" \
            -p "${SMOKE_PORT}:${SMOKE_PORT}" \
            "${extra_env_args[@]}" \
            "$IMAGE_REF"
          container_started=true

          health_url="http://127.0.0.1:${SMOKE_PORT}${SMOKE_PATH}"
          for _ in $(seq 1 30); do
            state="$(docker inspect --format '{{.State.Status}}' "$CONTAINER_NAME" 2>&1 || true)"
            if echo "$state" | grep -q "No such object"; then
              echo "::error::Container disappeared before becoming healthy."
              exit 1
            fi
            if [ "$state" = "exited" ]; then
              echo "::error::Container exited before becoming healthy."
              docker logs "$CONTAINER_NAME" 2>/dev/null || true
              exit 1
            fi
            health_state="$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{end}}' "$CONTAINER_NAME" 2>/dev/null || true)"
            if [ "$health_state" = "healthy" ]; then
              break
            fi
            if curl -fsS "$health_url" >/dev/null; then
              break
            fi
            sleep 2
          done

          curl -fsS "$health_url"

      - name: Build Summary
        if: always()
        run: |
          echo "## ${{ matrix.service }}" >> $GITHUB_STEP_SUMMARY
          echo "" >> $GITHUB_STEP_SUMMARY
          echo "| Field | Value |" >> $GITHUB_STEP_SUMMARY
          echo "|---|---|" >> $GITHUB_STEP_SUMMARY
          echo "| Image | \`${{ env.NAMESPACE }}/${{ matrix.service }}\` |" >> $GITHUB_STEP_SUMMARY
          echo "| Tags | ${{ steps.meta.outputs.tags }} |" >> $GITHUB_STEP_SUMMARY
          echo "| Pushed | ${{ github.ref == 'refs/heads/main' && github.event_name == 'push' }} |" >> $GITHUB_STEP_SUMMARY
          echo "| Smoke tested | ${{ github.event_name == 'pull_request' && matrix.smoke_test == 'true' }} |" >> $GITHUB_STEP_SUMMARY
.github/workflows/docs.yml
name: docs
on:
  push:
    branches:
      - main
  pull_request:
  merge_group:
    types: [checks_requested]
jobs:
  checks:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
        with:
          fetch-depth: 0
      - uses: actions/setup-python@v5
        with: { python-version: "3.11" }
      - run: pip install pre-commit
      - run: |
          if [ "${{ github.event_name }}" = "pull_request" ]; then
            git fetch origin "${{ github.base_ref }}"
            pre-commit run --from-ref "origin/${{ github.base_ref }}" --to-ref HEAD
          else
            BEFORE="${{ github.event.before }}"
            if [ -z "$BEFORE" ] || [ "$BEFORE" = "0000000000000000000000000000000000000000" ] || ! git cat-file -e "$BEFORE^{commit}" 2>/dev/null; then
              pre-commit run --all-files
            else
              pre-commit run --from-ref "$BEFORE" --to-ref "${{ github.sha }}"
            fi
          fi
        env:
          SKIP: docs-graph-validator  # Temporarily skip graph validator (pre-existing validation issues)
      - name: Broken-link check (lychee)
        uses: lycheeverse/lychee-action@v2  # Security: Fixed code injection vulnerability in v1
        with:
          args: --config .lychee.toml docs/**/*.md task-packets/**/*.md
          fail: false
.github/workflows/ci-complete.yml
name: 🚀 Complete CI Pipeline (ADHD-Optimized)

on:
  push:
    branches: [main]
  pull_request:
    types: [opened, synchronize, reopened, ready_for_review]
  merge_group:
    types: [checks_requested]
  workflow_dispatch:

concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true  # ADHD-friendly: cancel outdated runs

jobs:
  # ADHD chunk #1: Code quality (fast feedback)
  code-quality:
    name: "💅 Code Quality & Linting"
    runs-on: ubuntu-latest
    timeout-minutes: 10  # Quick feedback loop

    steps:
      - name: 📥 Checkout code
        uses: actions/checkout@v5
        with:
          fetch-depth: 0

      - name: 🐍 Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: 📦 Install pre-commit & deps
        run: |
          pip install pre-commit
          pre-commit install --install-hooks

      - name: 📌 Verify dopetask pin contract
        run: |
          if [[ ! -f .dopetask-pin ]]; then
            echo "ERROR: .dopetask-pin is missing (required by arch contract)" >&2
            exit 1
          fi
          echo "Found .dopetask-pin: $(cat .dopetask-pin)"


      - name: 🧹 Enforce repo root hygiene
        run: |
          if [ "${{ github.event_name }}" = "pull_request" ]; then
            git fetch origin "${{ github.base_ref }}"
            CHANGED_FILES="$(git -c core.quotePath=false diff --name-only --diff-filter=ACMR "origin/${{ github.base_ref }}"...HEAD)"
          else
            BEFORE="${{ github.event.before }}"
            if [ -z "$BEFORE" ] || [ "$BEFORE" = "0000000000000000000000000000000000000000" ] || ! git cat-file -e "$BEFORE^{commit}" 2>/dev/null; then
              # Fallback to main if it's a new branch push
              echo "Fallback activated: github.event.before is unavailable in this checkout; diffing against origin/main."
              git fetch origin main --depth=1
              CHANGED_FILES="$(git -c core.quotePath=false diff --name-only --diff-filter=ACMR origin/main...HEAD)"
            else
              CHANGED_FILES="$(git -c core.quotePath=false diff --name-only --diff-filter=ACMR "$BEFORE" "${{ github.sha }}")"
            fi
          fi

          if [ -z "$CHANGED_FILES" ]; then
            echo "No changed files to validate for root hygiene."
            exit 0
          fi

          echo "$CHANGED_FILES" | tr '\n' '\0' | xargs -0 -r python scripts/check_root_hygiene.py --quiet

      - name: 🔍 Run pre-commit (code quality)
        run: |
          if [ "${{ github.event_name }}" = "pull_request" ]; then
            git fetch origin "${{ github.base_ref }}"
            pre-commit run --from-ref "origin/${{ github.base_ref }}" --to-ref HEAD
          else
            BEFORE="${{ github.event.before }}"
            if [ -z "$BEFORE" ] || [ "$BEFORE" = "0000000000000000000000000000000000000000" ] || ! git cat-file -e "$BEFORE^{commit}" 2>/dev/null; then
              # Fallback to main if it's a new branch push
              echo "Fallback activated: github.event.before is unavailable in this checkout; running pre-commit from origin/main."
              git fetch origin main --depth=1
              pre-commit run --from-ref origin/main --to-ref HEAD
            else
              pre-commit run --from-ref "$BEFORE" --to-ref "${{ github.sha }}"
            fi
          fi
        env:
          SKIP: docs-graph-validator  # Temporarily skip graph validator (pre-existing validation issues)

      - name: 🎯 ADHD-Friendly Summary
        if: always()
        run: |
          echo "## 💅 Code Quality Check" >> $GITHUB_STEP_SUMMARY
          if [ $? -eq 0 ]; then
            echo "✅ **Code looks great!** Ready for the next step." >> $GITHUB_STEP_SUMMARY
          else
            echo "⚠️ **Code quality items found** - Check the details above." >> $GITHUB_STEP_SUMMARY
            echo "_Focus on the most important fixes first._" >> $GITHUB_STEP_SUMMARY
          fi

  # ADHD chunk #2: Security (takes longer, separate job)
  security:
    name: "🔒 Security Review"
    runs-on: ubuntu-latest
    timeout-minutes: 25  # 25-minute focus session
    env:
      ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}

    steps:
      - name: 📥 Checkout code
        uses: actions/checkout@v5
        with:
          ref: ${{ github.event.pull_request.head.sha || github.sha }}
          fetch-depth: 2

      - name: 🛡️ AI-Powered Security Analysis
        if: ${{ env.ANTHROPIC_API_KEY != '' }}
        uses: anthropics/claude-code-security-review@main
        with:
          comment-pr: true
          claude-api-key: ${{ env.ANTHROPIC_API_KEY }}
          # Use absolute paths: the upstream composite action chdirs into
          # `github.action_path` before opening these files, so a repo-relative
          # path resolves under the action's checkout instead of the workspace
          # and the customizations silently fall back to defaults.
          custom-security-scan-instructions: ${{ github.workspace }}/.github/security-scan-instructions.txt
          false-positive-filtering-instructions: ${{ github.workspace }}/.github/security-filtering-instructions.txt
          claudecode-timeout: "20"

      - name: 🎯 Gentle Security Summary
        if: always() && github.event_name == 'pull_request'
        run: |
          echo "## 🔒 Security Check Complete" >> $GITHUB_STEP_SUMMARY
          echo "AI-powered analysis finished! Check PR comments for details." >> $GITHUB_STEP_SUMMARY
          echo "_Remember: Security is about progress, not perfection._" >> $GITHUB_STEP_SUMMARY

  docs:
    name: "📚 Documentation Check"
    runs-on: ubuntu-latest
    timeout-minutes: 15

    steps:
      - name: 📥 Checkout code
        uses: actions/checkout@v5

      - name: 🔗 Check links (lychee)
        uses: lycheeverse/lychee-action@v2  # Security: Fixed code injection vulnerability in v1
        with:
          args: --config .lychee.toml docs/**/*.md README.md
          fail: false

      - name: 📖 Documentation Summary
        if: always()
        run: |
          echo "## 📚 Documentation Check" >> $GITHUB_STEP_SUMMARY
          echo "Link checking completed! Your docs are being kept current." >> $GITHUB_STEP_SUMMARY

  tests:
    name: "🧪 Unit Tests"
    runs-on: ubuntu-latest
    timeout-minutes: 30

    steps:
      - name: 📥 Checkout code
        uses: actions/checkout@v5
        with:
          fetch-depth: 0

      - name: 🐍 Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: ⚡ Setup uv
        uses: astral-sh/setup-uv@v7
        with:
          enable-cache: true
          cache-dependency-glob: uv.lock

      - name: 📦 Sync fast unit test environment
        run: uv sync --frozen --extra test --extra services

      - name: ▶️ Run fast unit gate
        run: |
          uv run --frozen pytest \
            tests/unit \
            tests/test_voice_core.py \
            tests/test_brand_voice.py \
            -n auto --maxfail=1 --disable-warnings --no-cov

      - name: 🔴 Run DCP red-lane gate (TP-DMX-DCP-CI-GATE-001)
        run: |
          PYTHONPATH=src uv run --frozen pytest \
            tests/dcp/ \
            --deselect tests/dcp/test_dcp_0002_contract_derivation.py::test_16_no_forbidden_files_modified \
            --maxfail=1 --disable-warnings --no-cov

      - name: 🎨 Run brand lint gate
        run: uv run --frozen python scripts/brand_lint.py

      - name: 🧩 Run interactive import smoke
        run: |
          uv run --frozen python - <<'PY'
          import importlib
          modules = [
              "dopemux.ux.interactive_prompts",
              "dopemux.ux.wizard.extraction",
              "dopemux.ux.wizard.prompts",
              "dopemux.ux.wizard.cost_profiles",
              "dopemux.ux.wizard.runner",
          ]
          for name in modules:
              importlib.import_module(name)
              print(f"import-ok {name}")
          PY

  extractor-smoke:
    name: "🧪 Extractor Smoke"
    runs-on: ubuntu-latest
    timeout-minutes: 30

    steps:
      - name: 📥 Checkout code
        uses: actions/checkout@v5
        with:
          fetch-depth: 0

      - name: 🐍 Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: ⚡ Setup uv
        uses: astral-sh/setup-uv@v7
        with:
          enable-cache: true
          cache-dependency-glob: uv.lock

      - name: 📦 Sync extractor smoke environment
        run: uv sync --frozen --extra test --extra services

      - name: ▶️ Run extractor smoke gate
        run: >
          uv run --frozen pytest
          services/repo-truth-extractor/tests/test_run_extraction_v4_core.py
          services/repo-truth-extractor/tests/test_rte_live_cert_characterization.py
          services/repo-truth-extractor/tests/test_rte_v5_characterization.py
          services/repo-truth-extractor/tests/test_truth_run_cli.py
          services/repo-truth-extractor/tests/test_run_extraction_v5_promptset_truth.py
          services/repo-truth-extractor/tests/test_run_extraction_v5_validator.py
          tests/unit/test_cli_upgrades_commands.py
          -n auto --maxfail=1 --disable-warnings --no-cov

  audit-validator:
    name: "🔍 Audit Proof Validator (--all)"
    runs-on: ubuntu-latest
    timeout-minutes: 10
    # Scope: machine-verifies that proof/.validator_scope.json + the in-scope
    # PROOF.json corpus stays clean. Locks in TP-DMX-VALIDATOR-SCOPE-015 so
.github/workflows/gemini-plan-execute.yml
name: '🧙 Gemini Plan Execution'

on:
  workflow_call:
    inputs:
      additional_context:
        type: 'string'
        description: 'Any additional context from the request'
        required: false

concurrency:
  group: '${{ github.workflow }}-plan-execute-${{ github.event_name }}-${{ github.event.pull_request.number || github.event.issue.number }}'
  cancel-in-progress: true

defaults:
  run:
    shell: 'bash'

jobs:
  plan-execute:
    timeout-minutes: 30
    runs-on: 'ubuntu-latest'
    env:
      GEMINI_CLI_TRUST_WORKSPACE: 'true'
    permissions:
      contents: 'write'
      id-token: 'write'
      issues: 'write'
      pull-requests: 'write'

    steps:
      - name: 'Mint identity token'
        id: 'mint_identity_token'
        if: |-
          ${{ vars.APP_ID }}
        uses: 'actions/create-github-app-token@29824e69f54612133e76f7eaac726eef6c875baf' # ratchet:actions/create-github-app-token@v2
        with:
          app-id: '${{ vars.APP_ID }}'
          private-key: '${{ secrets.APP_PRIVATE_KEY }}'
          permission-contents: 'write'
          permission-issues: 'write'
          permission-pull-requests: 'write'

      - name: 'Checkout Code'
        uses: 'actions/checkout@v4' # ratchet:exclude

      - name: 'Run Gemini CLI'
        id: 'run_gemini'
        uses: 'google-github-actions/run-gemini-cli@v0' # ratchet:exclude
        env:
          GEMINI_CLI_TRUST_WORKSPACE: 'true'
          TITLE: '${{ github.event.pull_request.title || github.event.issue.title }}'
          DESCRIPTION: '${{ github.event.pull_request.body || github.event.issue.body }}'
          EVENT_NAME: '${{ github.event_name }}'
          GITHUB_TOKEN: '${{ steps.mint_identity_token.outputs.token || secrets.GITHUB_TOKEN || github.token }}'
          IS_PULL_REQUEST: '${{ !!github.event.pull_request }}'
          ISSUE_NUMBER: '${{ github.event.pull_request.number || github.event.issue.number }}'
          REPOSITORY: '${{ github.repository }}'
          ADDITIONAL_CONTEXT: '${{ inputs.additional_context }}'
        with:
          gcp_location: '${{ vars.GOOGLE_CLOUD_LOCATION }}'
          gcp_project_id: '${{ vars.GOOGLE_CLOUD_PROJECT }}'
          gcp_service_account: '${{ vars.SERVICE_ACCOUNT_EMAIL }}'
          gcp_workload_identity_provider: '${{ vars.GCP_WIF_PROVIDER }}'
          gemini_api_key: '${{ secrets.GEMINI_API_KEY }}'
          gemini_cli_version: '${{ vars.GEMINI_CLI_VERSION }}'
          gemini_debug: '${{ fromJSON(vars.GEMINI_DEBUG || vars.ACTIONS_STEP_DEBUG || false) }}'
          gemini_model: '${{ vars.GEMINI_MODEL }}'
          google_api_key: '${{ secrets.GOOGLE_API_KEY }}'
          use_gemini_code_assist: '${{ vars.GOOGLE_GENAI_USE_GCA }}'
          use_vertex_ai: '${{ vars.GOOGLE_GENAI_USE_VERTEXAI }}'
          upload_artifacts: '${{ vars.UPLOAD_ARTIFACTS }}'
          workflow_name: 'gemini-invoke'
          settings: |-
            {
              "model": {
                "maxSessionTurns": 25
              },
              "telemetry": {
                "enabled": true,
                "target": "local",
                "outfile": ".gemini/telemetry.log"
              },
              "mcpServers": {
                "github": {
                  "command": "docker",
                  "args": [
                    "run",
                    "-i",
                    "--rm",
                    "-e",
                    "GITHUB_PERSONAL_ACCESS_TOKEN",
                    "ghcr.io/github/github-mcp-server:v0.27.0"
                  ],
                  "includeTools": [
                    "add_issue_comment",
                    "issue_read",
                    "list_issues",
                    "search_issues",
                    "create_pull_request",
                    "pull_request_read",
                    "list_pull_requests",
                    "search_pull_requests",
                    "create_branch",
                    "create_or_update_file",
                    "delete_file",
                    "fork_repository",
                    "get_commit",
                    "get_file_contents",
                    "list_commits",
                    "push_files",
                    "search_code"
                  ],
                  "env": {
                    "GITHUB_PERSONAL_ACCESS_TOKEN": "${GITHUB_TOKEN}"
                  }
                }
              },
              "tools": {
                "core": [
                  "run_shell_command(cat)",
                  "run_shell_command(echo)",
                  "run_shell_command(grep)",
                  "run_shell_command(head)",
                  "run_shell_command(tail)"
                ]
              }
            }
          prompt: '/gemini-plan-execute'
.github/workflows/embedded-audit.yml
name: embedded-audit

on:
  pull_request:
    types: [opened, synchronize, reopened, ready_for_review]
  workflow_dispatch:
    inputs:
      pr_number:
        description: Pull request number to inspect
        required: true
        type: string
      head_sha:
        description: Expected pull request head SHA
        required: true
        type: string

permissions:
  contents: read
  pull-requests: read
  checks: read
  statuses: read
  actions: read

jobs:
  embedded-audit:
    name: independent embedded audit
    runs-on: ubuntu-latest
    steps:
      - name: Set PR metadata
        id: pr
        env:
          EVENT_NAME: ${{ github.event_name }}
          EVENT_PR_NUMBER: ${{ github.event.pull_request.number }}
          EVENT_HEAD_SHA: ${{ github.event.pull_request.head.sha }}
          EVENT_BASE_SHA: ${{ github.event.pull_request.base.sha }}
          INPUT_PR_NUMBER: ${{ inputs.pr_number }}
          INPUT_HEAD_SHA: ${{ inputs.head_sha }}
          TRUSTED_FALLBACK_REF: ${{ github.event.repository.default_branch }}
        run: |
          if [ "$EVENT_NAME" = "pull_request" ]; then
            printf 'number=%s\n' "$EVENT_PR_NUMBER" >> "$GITHUB_OUTPUT"
            printf 'head_sha=%s\n' "$EVENT_HEAD_SHA" >> "$GITHUB_OUTPUT"
            printf 'trusted_ref=%s\n' "$EVENT_BASE_SHA" >> "$GITHUB_OUTPUT"
          else
            printf 'number=%s\n' "$INPUT_PR_NUMBER" >> "$GITHUB_OUTPUT"
            printf 'head_sha=%s\n' "$INPUT_HEAD_SHA" >> "$GITHUB_OUTPUT"
            printf 'trusted_ref=%s\n' "$TRUSTED_FALLBACK_REF" >> "$GITHUB_OUTPUT"
          fi
          if [ "$EVENT_NAME" = "pull_request" ]; then
            test -n "$EVENT_HEAD_SHA"
            test -n "$EVENT_BASE_SHA"
          else
            test -n "$INPUT_HEAD_SHA"
            test -n "$TRUSTED_FALLBACK_REF"
          fi

      - name: Checkout trusted audit source
        uses: actions/checkout@v4
        with:
          ref: ${{ steps.pr.outputs.trusted_ref }}
          fetch-depth: 2
          path: trusted-source

      - name: Verify trusted audit source
        env:
          EXPECTED_TRUSTED_REF: ${{ steps.pr.outputs.trusted_ref }}
        run: |
          actual_trusted_ref="$(git -C trusted-source rev-parse HEAD)"
          if printf '%s' "$EXPECTED_TRUSTED_REF" | grep -Eq '^[0-9a-f]{40}$'; then
            test "$actual_trusted_ref" = "$EXPECTED_TRUSTED_REF"
          else
            test -n "$actual_trusted_ref"
          fi

      - name: Verify requested head SHA
        id: head_integrity
        env:
          PR_NUMBER: ${{ steps.pr.outputs.number }}
          EXPECTED_HEAD_SHA: ${{ steps.pr.outputs.head_sha }}
        run: |
          if git -C trusted-source fetch --no-tags --depth=1 origin "$EXPECTED_HEAD_SHA"; then
            actual_head_sha="$(git -C trusted-source rev-parse FETCH_HEAD)"
          else
            actual_head_sha=""
          fi
          pr_head_sha="$(git -C trusted-source ls-remote origin "refs/pull/${PR_NUMBER}/head" | awk '{print $1}')"
          if [ "$actual_head_sha" = "$EXPECTED_HEAD_SHA" ] && [ "$pr_head_sha" = "$EXPECTED_HEAD_SHA" ]; then
            printf 'verified=true\n' >> "$GITHUB_OUTPUT"
          else
            printf 'verified=false\n' >> "$GITHUB_OUTPUT"
          fi

      - name: Static auditor route preflight
        continue-on-error: true
        working-directory: trusted-source
        run: |
          mkdir -p ../embedded-audit-artifacts
          set +e
          python -m tools.auditor_router.preflight \
            --packet-id "TP-DMX-AUDIT-CI-PROVENANCE-104" \
            --out ../embedded-audit-artifacts \
            --format json
          preflight_status=$?
          set -e
          if [ ! -f ../embedded-audit-artifacts/AUDITOR_ROUTE.json ]; then
            cat > ../embedded-audit-artifacts/AUDITOR_ROUTE.json <<'JSON'
          {
            "tool": "pal-mcp-clink",
            "underlying_cli": null,
            "clink_client_name": null,
            "audit_safe_config_proven": false,
            "clink_mutation_flags_detected": [],
            "invocation_template": null,
            "status": "NEEDS_SUPERVISOR",
            "reason": "Static auditor route preflight did not emit AUDITOR_ROUTE.json."
          }
          JSON
          fi

      - name: Run PAL clink audit
        if: always() && steps.head_integrity.outputs.verified == 'true'
        continue-on-error: true
        working-directory: trusted-source
        run: |
          base_sha="$(git rev-parse HEAD)"
          head_sha='${{ steps.pr.outputs.head_sha }}'
          if ! git cat-file -e "${head_sha}^{commit}"; then
            git fetch --no-tags --depth=1 origin "$head_sha"
          fi
          {
            printf 'Review pull request %s in %s at head SHA %s.\n\n' \
              '${{ steps.pr.outputs.number }}' \
              "$GITHUB_REPOSITORY" \
              "$head_sha"
            printf 'Trusted base/source SHA: %s\n\n' "$base_sha"
            printf 'Changed files:\n'
            git diff --find-renames --name-status "$base_sha" "$head_sha"
            printf '\nUnified diff:\n```diff\n'
            git diff --find-renames --no-ext-diff "$base_sha" "$head_sha"
            printf '\n```\n\n'
            printf 'Return JSON with status, verdict, findings, and risks.\n'
          } > ../embedded-audit-artifacts/PAL_CLINK_AUDIT_INPUT.md
          set +e
          if [ -f scripts/audit/pal_clink_runner.py ]; then
            python scripts/audit/pal_clink_runner.py \
              --route-json ../embedded-audit-artifacts/AUDITOR_ROUTE.json \
              --prompt ../embedded-audit-artifacts/PAL_CLINK_AUDIT_INPUT.md \
              --pal-output-json ../embedded-audit-artifacts/PAL_CLINK_AUDIT_OUTPUT.json \
              --raw-output-json ../embedded-audit-artifacts/PAL_CLINK_AUDIT_RUNNER_OUTPUT.json
            status=$?
          else
            status=127
          fi
          if [ ! -f ../embedded-audit-artifacts/PAL_CLINK_AUDIT_OUTPUT.json ]; then
            printf '{"status":"error","risks":["PAL clink runner did not emit output; exit_code=%s"]}\n' "$status" \
              > ../embedded-audit-artifacts/PAL_CLINK_AUDIT_OUTPUT.json
          fi
          exit 0

      - name: Emit skipped embedded audit proof
        if: always()
        working-directory: trusted-source
        env:
          HEAD_VERIFIED: ${{ steps.head_integrity.outputs.verified }}
        run: |
          if [ "$HEAD_VERIFIED" != "true" ]; then
            SKIP_REASON="Independent embedded audit skipped because the requested head SHA could not be fetched or did not match the requested PR head."
          elif [ ! -f scripts/audit/run_embedded_audit.py ]; then
            SKIP_REASON="Independent embedded audit skipped because the trusted source ref does not yet contain scripts/audit/run_embedded_audit.py."
          else
            exit 0
          fi
          export SKIP_REASON
            python - <<'PY'
          import json
          import os
          from datetime import datetime, timezone
          from pathlib import Path

          packet_id = "TP-DMX-AUDIT-CI-PROVENANCE-104"
          report_path = f"proof/{packet_id}/AUDITOR_REPORT.md"
          reason = os.environ["SKIP_REASON"]
          out_dir = Path("../embedded-audit-artifacts")
          out_dir.mkdir(parents=True, exist_ok=True)
          proof = {
              "packet_id": packet_id,
              "repo": os.environ["GITHUB_REPOSITORY"],
              "pr_number": int("${{ steps.pr.outputs.number }}"),
              "head_sha": "${{ steps.pr.outputs.head_sha }}",
              "generated_at": datetime.now(timezone.utc)
              .replace(microsecond=0)
              .isoformat()
              .replace("+00:00", "Z"),
              "mutation_performed": False,
              "github_mutation_route_added": False,
              "embedded_audit": {
                  "required": True,
                  "status": "SKIPPED",
                  "auditor_tool": "none",
                  "auditor_model": "unknown",
                  "invocation": None,
                  "exit_code": None,
                  "report_path": report_path,
                  "findings": [],
                  "fixes_applied": [],
                  "remaining_risks": [reason],
                  "skip_reason": reason,
              },
              "provenance": {
                  "proof_author": "independent-embedded-audit",
                  "workflow": "embedded-audit.yml",
                  "trusted_token_status": "UNKNOWN",
                  "token_source": "EMBEDDED_AUDIT_TOKEN",
                  "token_value_recorded": False,
                  "permissions": {
                      "actions": "read",
                      "checks": "read",
                      "contents": "read",
                      "pull-requests": "read",
                      "statuses": "read",
                  },
                  "engine_authored_proof": False,
                  "engine_requested_only": True,
              },
          }
          (out_dir / "PROOF.json").write_text(
              json.dumps(proof, indent=2, sort_keys=True) + "\n",
              encoding="utf-8",
          )
          report_file = out_dir / report_path
          report_file.parent.mkdir(parents=True, exist_ok=True)
          report_text = f"# Embedded audit\n\nstatus: SKIPPED\n\nreason: {reason}\n"
          report_file.write_text(report_text, encoding="utf-8")
          (out_dir / "AUDITOR_REPORT.md").write_text(report_text, encoding="utf-8")
          PY

      - name: Emit embedded audit proof with trusted token
        if: always() && steps.head_integrity.outputs.verified == 'true'
        working-directory: trusted-source
        env:
          EMBEDDED_AUDIT_TOKEN: ${{ secrets.EMBEDDED_AUDIT_TOKEN }}
        run: |
          if [ ! -f scripts/audit/run_embedded_audit.py ]; then
            exit 0
          fi
          python scripts/audit/run_embedded_audit.py \
            --packet-id "TP-DMX-AUDIT-CI-PROVENANCE-104" \
            --repo "$GITHUB_REPOSITORY" \
            --pr "${{ steps.pr.outputs.number }}" \
            --head-sha "${{ steps.pr.outputs.head_sha }}" \
            --route-json ../embedded-audit-artifacts/AUDITOR_ROUTE.json \
            --pal-output-json ../embedded-audit-artifacts/PAL_CLINK_AUDIT_OUTPUT.json \
            --out ../embedded-audit-artifacts

      - name: Write job summary
        if: always()
        run: |
          {
            printf '## Embedded audit\n\n'
            printf -- '- mutation_performed: false\n'
.github/workflows/repo-identity.yml
name: Repo Identity Check

on:
  push:
  pull_request:
  merge_group:
    types: [checks_requested]

jobs:
  identity-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Verify Repo Identity
        run: |
          test -f .repo_id
          grep "^project=dopemux-mvp$" .repo_id
.github/workflows/docker-scout.yml
name: Docker Scout

on:
  pull_request:
    paths:
      - "Dockerfile"
      - "services/**/Dockerfile*"
      - "docker/**/Dockerfile*"
      - ".github/workflows/docker-scout.yml"
      - ".github/workflows/containers.yml"
  push:
    branches:
      - main
    paths:
      - "Dockerfile"
      - "services/**/Dockerfile*"
      - "docker/**/Dockerfile*"
      - ".github/workflows/docker-scout.yml"
      - ".github/workflows/containers.yml"

concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

env:
  REGISTRY: docker.io
  NAMESPACE: docker.io/${{ vars.DOCKER_SCOUT_HUB_NAMESPACE }}

jobs:
  scout:
    name: Scout ${{ matrix.service }}
    runs-on: ubuntu-latest
    timeout-minutes: 30

    permissions:
      contents: read
      packages: read
      pull-requests: write
      security-events: write

    env:
      DHI_TOKEN: ${{ secrets.DHI_TOKEN }}
      DOCKER_SCOUT_ORGANIZATION: ${{ vars.DOCKER_SCOUT_ORGANIZATION }}
      DOCKER_SCOUT_COMPARE_ENABLED: ${{ vars.DOCKER_SCOUT_COMPARE_ENABLED }}

    strategy:
      fail-fast: false
      matrix:
        include:
          - service: dopemux-backend
            dockerfile: Dockerfile
            context: .
          - service: conport
            dockerfile: docker/mcp-servers-source/conport/Dockerfile
            context: .
          - service: litellm
            dockerfile: docker/mcp-servers-source/litellm/Dockerfile
            context: .
          - service: task-orchestrator
            dockerfile: services/task-orchestrator/Dockerfile
            context: .
          - service: claude-brain
            dockerfile: services/claude_brain/Dockerfile
            context: .
          - service: adhd-engine
            dockerfile: services/adhd_engine/Dockerfile
            context: .
          - service: dopecon-bridge
            dockerfile: services/dopecon-bridge/Dockerfile
            context: .
          - service: webhook-receiver
            dockerfile: services/webhook_receiver/Dockerfile
            context: .
          - service: dope-memory
            dockerfile: services/working-memory-assistant/Dockerfile.dope-memory
            context: .

    steps:
      - name: Checkout code
        uses: actions/checkout@v5

      - name: Authenticate to Docker Hub
        uses: docker/login-action@v4
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ secrets.DOCKER_SCOUT_HUB_USER }}
          password: ${{ secrets.DOCKER_SCOUT_HUB_PASSWORD }}

      - name: Authenticate to Docker Hardened Images
        id: dhi_login
        if: ${{ env.DHI_TOKEN != '' }}
        continue-on-error: true
        uses: docker/login-action@v4
        with:
          registry: dhi.io
          username: ${{ github.actor }}
          password: ${{ env.DHI_TOKEN }}

      - name: Fail when DHI login unavailable on non-PR runs
        if: ${{ steps.dhi_login.outcome != 'success' && github.event_name != 'pull_request' }}
        run: |
          echo "::error::DHI login unavailable (outcome: ${{ steps.dhi_login.outcome }}). Refusing to rewrite dhi.io image references on non-pull_request runs — Scout results must reflect the same hardened images that are built and published."
          exit 1

      - name: Fallback to public images when DHI login unavailable (PR only)
        if: ${{ steps.dhi_login.outcome != 'success' && github.event_name == 'pull_request' }}
        run: |
          echo "::warning::DHI login unavailable (outcome: ${{ steps.dhi_login.outcome }}). Rewriting dhi.io/ base image references to public Docker Hub equivalents for this PR Scout build."
          find . -name "Dockerfile*" -type f -exec sed -i 's|dhi.io/||g' {} +

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v4

      - name: Compute image reference
        id: image
        run: |
          SHORT_SHA="$(echo "${GITHUB_SHA}" | cut -c1-7)"
          if [ "${{ github.event_name }}" = "pull_request" ]; then
            SHORT_SHA="$(echo "${{ github.event.pull_request.head.sha }}" | cut -c1-7)"
            echo "ref=${{ env.NAMESPACE }}/${{ matrix.service }}:pr-${{ github.event.pull_request.number }}-${SHORT_SHA}" >> "$GITHUB_OUTPUT"
          else
            echo "ref=${{ env.NAMESPACE }}/${{ matrix.service }}:sha-${SHORT_SHA}" >> "$GITHUB_OUTPUT"
          fi

      - name: Detect Docker Scout environment capability
        id: scout_compare
        run: |
          if [ -z "${DOCKER_SCOUT_ORGANIZATION}" ]; then
            echo "::warning::DOCKER_SCOUT_ORGANIZATION is unset. Falling back to Docker Scout CVE scanning."
            echo "enabled=false" >> "$GITHUB_OUTPUT"
          elif [ "${DOCKER_SCOUT_COMPARE_ENABLED}" != "true" ]; then
            echo "::warning::DOCKER_SCOUT_COMPARE_ENABLED is not true. Falling back to Docker Scout CVE scanning until the organization is enrolled and the production environment is populated."
            echo "enabled=false" >> "$GITHUB_OUTPUT"
          else
            echo "enabled=true" >> "$GITHUB_OUTPUT"
          fi

      - name: Build image for Scout analysis
        uses: docker/build-push-action@v7
        with:
          context: ${{ matrix.context }}
          file: ${{ matrix.dockerfile }}
          load: ${{ github.event_name == 'pull_request' }}
          push: ${{ github.event_name != 'pull_request' }}
          tags: ${{ steps.image.outputs.ref }}
          labels: |
            org.opencontainers.image.revision=${{ github.event.pull_request.head.sha || github.sha }}
          cache-from: type=gha,scope=scout-${{ matrix.service }}
          cache-to: type=gha,mode=max,scope=scout-${{ matrix.service }}

      - name: Record production environment
        if: ${{ github.event_name != 'pull_request' && steps.scout_compare.outputs.enabled == 'true' }}
        env:
          DOCKER_SCOUT_HUB_USER: ${{ secrets.DOCKER_SCOUT_HUB_USER }}
          DOCKER_SCOUT_HUB_PASSWORD: ${{ secrets.DOCKER_SCOUT_HUB_PASSWORD }}
          IMAGE_REF: ${{ steps.image.outputs.ref }}
        run: |
          docker run --rm \
            -e DOCKER_SCOUT_HUB_USER \
            -e DOCKER_SCOUT_HUB_PASSWORD \
            docker/scout-cli environment \
            --org "${DOCKER_SCOUT_ORGANIZATION}" \
            production \
            "${IMAGE_REF}" \
            --platform linux/amd64

      - name: Docker Scout compare against production
        if: ${{ github.event_name == 'pull_request' && steps.scout_compare.outputs.enabled == 'true' }}
        uses: docker/scout-action@v1
        with:
          command: compare
          image: ${{ steps.image.outputs.ref }}
          to-env: production
          organization: ${{ env.DOCKER_SCOUT_ORGANIZATION }}
          ignore-unchanged: true
          only-severities: critical,high
          github-token: ${{ secrets.GITHUB_TOKEN }}

      - name: Docker Scout CVEs on pull requests
        if: ${{ github.event_name == 'pull_request' && steps.scout_compare.outputs.enabled != 'true' }}
        uses: docker/scout-action@v1
        with:
          command: cves
          image: ${{ steps.image.outputs.ref }}
          only-severities: critical,high
          summary: true

      - name: Docker Scout CVEs
        if: ${{ github.event_name != 'pull_request' }}
        uses: docker/scout-action@v1
        with:
          command: cves
          image: ${{ steps.image.outputs.ref }}
          only-severities: critical,high
          exit-code: true
          summary: true
          sarif-file: scout-${{ matrix.service }}.sarif

      - name: Upload Scout SARIF
        if: ${{ always() && github.event_name != 'pull_request' }}
        uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: scout-${{ matrix.service }}.sarif
          category: docker-scout-${{ matrix.service }}
.github/workflows/gemini-triage.yml
name: '🔀 Gemini Triage'

on:
  workflow_call:
    inputs:
      additional_context:
        type: 'string'
        description: 'Any additional context from the request'
        required: false

concurrency:
  group: '${{ github.workflow }}-triage-${{ github.event_name }}-${{ github.event.pull_request.number || github.event.issue.number }}'
  cancel-in-progress: true

defaults:
  run:
    shell: 'bash'

jobs:
  triage:
    runs-on: 'ubuntu-latest'
    timeout-minutes: 7
    env:
      GEMINI_CLI_TRUST_WORKSPACE: 'true'
    outputs:
      available_labels: '${{ steps.get_labels.outputs.available_labels }}'
      selected_labels: '${{ env.SELECTED_LABELS }}'
    permissions:
      contents: 'read'
      id-token: 'write'
      issues: 'read'
      pull-requests: 'read'
    steps:
      - name: 'Get repository labels'
        id: 'get_labels'
        uses: 'actions/github-script@ed597411d8f924073f98dfc5c65a23a2325f34cd' # ratchet:actions/github-script@v8.0.0
        with:
          # NOTE: we intentionally do not use the given token. The default
          # GITHUB_TOKEN provided by the action has enough permissions to read
          # the labels.
          script: |-
            const labels = [];
            for await (const response of github.paginate.iterator(github.rest.issues.listLabelsForRepo, {
              owner: context.repo.owner,
              repo: context.repo.repo,
              per_page: 100, // Maximum per page to reduce API calls
            })) {
              labels.push(...response.data);
            }

            if (!labels || labels.length === 0) {
              core.setFailed('There are no issue labels in this repository.')
            }

            const labelNames = labels.map(label => label.name).sort();
            core.setOutput('available_labels', labelNames.join(','));
            core.info(`Found ${labelNames.length} labels: ${labelNames.join(', ')}`);
            return labelNames;

      - name: 'Run Gemini issue analysis'
        id: 'gemini_analysis'
        if: |-
          ${{ steps.get_labels.outputs.available_labels != '' }}
        uses: 'google-github-actions/run-gemini-cli@v0' # ratchet:exclude
        env:
          GITHUB_TOKEN: '' # Do NOT pass any auth tokens here since this runs on untrusted inputs
          ISSUE_TITLE: '${{ github.event.issue.title }}'
          ISSUE_BODY: '${{ github.event.issue.body }}'
          AVAILABLE_LABELS: '${{ steps.get_labels.outputs.available_labels }}'
        with:
          gcp_location: '${{ vars.GOOGLE_CLOUD_LOCATION }}'
          gcp_project_id: '${{ vars.GOOGLE_CLOUD_PROJECT }}'
          gcp_service_account: '${{ vars.SERVICE_ACCOUNT_EMAIL }}'
          gcp_workload_identity_provider: '${{ vars.GCP_WIF_PROVIDER }}'
          gemini_api_key: '${{ secrets.GEMINI_API_KEY }}'
          gemini_cli_version: '${{ vars.GEMINI_CLI_VERSION }}'
          gemini_debug: '${{ fromJSON(vars.GEMINI_DEBUG || vars.ACTIONS_STEP_DEBUG || false) }}'
          gemini_model: '${{ vars.GEMINI_MODEL }}'
          google_api_key: '${{ secrets.GOOGLE_API_KEY }}'
          use_gemini_code_assist: '${{ vars.GOOGLE_GENAI_USE_GCA }}'
          use_vertex_ai: '${{ vars.GOOGLE_GENAI_USE_VERTEXAI }}'
          upload_artifacts: '${{ vars.UPLOAD_ARTIFACTS }}'
          workflow_name: 'gemini-triage'
          settings: |-
            {
              "model": {
                "maxSessionTurns": 25
              },
              "telemetry": {
                "enabled": true,
                "target": "local",
                "outfile": ".gemini/telemetry.log"
              },
              "tools": {
                "core": [
                  "run_shell_command(echo)"
                ]
              }
            }
          prompt: '/gemini-triage'

  label:
    runs-on: 'ubuntu-latest'
    needs:
      - 'triage'
    if: |-
      ${{ needs.triage.outputs.selected_labels != '' }}
    permissions:
      contents: 'read'
      issues: 'write'
      pull-requests: 'write'
    steps:
      - name: 'Mint identity token'
        id: 'mint_identity_token'
        if: |-
          ${{ vars.APP_ID }}
        uses: 'actions/create-github-app-token@29824e69f54612133e76f7eaac726eef6c875baf' # ratchet:actions/create-github-app-token@v2
        with:
          app-id: '${{ vars.APP_ID }}'
          private-key: '${{ secrets.APP_PRIVATE_KEY }}'
          permission-contents: 'read'
          permission-issues: 'write'
          permission-pull-requests: 'write'

      - name: 'Apply labels'
        env:
          ISSUE_NUMBER: '${{ github.event.issue.number }}'
          AVAILABLE_LABELS: '${{ needs.triage.outputs.available_labels }}'
          SELECTED_LABELS: '${{ needs.triage.outputs.selected_labels }}'
        uses: 'actions/github-script@ed597411d8f924073f98dfc5c65a23a2325f34cd' # ratchet:actions/github-script@v8.0.0
        with:
          # Use the provided token so that the "gemini-cli" is the actor in the
          # log for what changed the labels.
          github-token: '${{ steps.mint_identity_token.outputs.token || secrets.GITHUB_TOKEN || github.token }}'
          script: |-
            // Parse the available labels
            const availableLabels = (process.env.AVAILABLE_LABELS || '').split(',')
              .map((label) => label.trim())
              .sort()

            // Parse the label as a CSV, reject invalid ones - we do this just
            // in case someone was able to prompt inject malicious labels.
            const selectedLabels = (process.env.SELECTED_LABELS || '').split(',')
              .map((label) => label.trim())
              .filter((label) => availableLabels.includes(label))
              .sort()

            // Set the labels
            const issueNumber = process.env.ISSUE_NUMBER;
            if (selectedLabels && selectedLabels.length > 0) {
              await github.rest.issues.setLabels({
                owner: context.repo.owner,
                repo: context.repo.repo,
                issue_number: issueNumber,
                labels: selectedLabels,
              });
              core.info(`Successfully set labels: ${selectedLabels.join(',')}`);
            } else {
              core.info(`Failed to determine labels to set. There may not be enough information in the issue or pull request.`)
            }
.github/workflows/gemini-scheduled-triage.yml
name: '📋 Gemini Scheduled Issue Triage'

on:
  schedule:
    - cron: '0 * * * *' # Runs every hour
  pull_request:
    branches:
      - 'main'
      - 'release/**/*'
    paths:
      - '.github/workflows/gemini-scheduled-triage.yml'
  push:
    branches:
      - 'main'
      - 'release/**/*'
    paths:
      - '.github/workflows/gemini-scheduled-triage.yml'
  workflow_dispatch:

concurrency:
  group: '${{ github.workflow }}'
  cancel-in-progress: true

defaults:
  run:
    shell: 'bash'

jobs:
  triage:
    runs-on: 'ubuntu-latest'
    timeout-minutes: 7
    env:
      GEMINI_CLI_TRUST_WORKSPACE: 'true'
    permissions:
      contents: 'read'
      id-token: 'write'
      issues: 'read'
      pull-requests: 'read'
    outputs:
      available_labels: '${{ steps.get_labels.outputs.available_labels }}'
      triaged_issues: '${{ env.TRIAGED_ISSUES }}'
    steps:
      - name: 'Get repository labels'
        id: 'get_labels'
        uses: 'actions/github-script@ed597411d8f924073f98dfc5c65a23a2325f34cd' # ratchet:actions/github-script@v8.0.0
        with:
          # NOTE: we intentionally do not use the minted token. The default
          # GITHUB_TOKEN provided by the action has enough permissions to read
          # the labels.
          script: |-
            const labels = [];
            for await (const response of github.paginate.iterator(github.rest.issues.listLabelsForRepo, {
              owner: context.repo.owner,
              repo: context.repo.repo,
              per_page: 100, // Maximum per page to reduce API calls
            })) {
              labels.push(...response.data);
            }

            if (!labels || labels.length === 0) {
              core.setFailed('There are no issue labels in this repository.')
            }

            const labelNames = labels.map(label => label.name).sort();
            core.setOutput('available_labels', labelNames.join(','));
            core.info(`Found ${labelNames.length} labels: ${labelNames.join(', ')}`);
            return labelNames;

      - name: 'Find untriaged issues'
        id: 'find_issues'
        env:
          GITHUB_REPOSITORY: '${{ github.repository }}'
          GITHUB_TOKEN: '${{ secrets.GITHUB_TOKEN || github.token }}'
        run: |-
          echo '🔍 Finding unlabeled issues and issues marked for triage...'
          ISSUES="$(gh issue list \
            --state 'open' \
            --search 'no:label label:"status/needs-triage"' \
            --json number,title,body \
            --limit '100' \
            --repo "${GITHUB_REPOSITORY}"
          )"

          echo '📝 Setting output for GitHub Actions...'
          echo "issues_to_triage=${ISSUES}" >> "${GITHUB_OUTPUT}"

          ISSUE_COUNT="$(echo "${ISSUES}" | jq 'length')"
          echo "✅ Found ${ISSUE_COUNT} issue(s) to triage! 🎯"

      - name: 'Detect Gemini credentials'
        id: 'detect_gemini_credentials'
        env:
          GEMINI_API_KEY: '${{ secrets.GEMINI_API_KEY }}'
          GOOGLE_API_KEY: '${{ secrets.GOOGLE_API_KEY }}'
          GCP_WIF_PROVIDER: '${{ vars.GCP_WIF_PROVIDER }}'
        run: |-
          if [[ -n "${GEMINI_API_KEY}" || -n "${GOOGLE_API_KEY}" || -n "${GCP_WIF_PROVIDER}" ]]; then
            echo 'available=true' >> "${GITHUB_OUTPUT}"
          else
            echo 'available=false' >> "${GITHUB_OUTPUT}"
          fi

      - name: 'Run Gemini Issue Analysis'
        id: 'gemini_issue_analysis'
        if: |-
          steps.find_issues.outputs.issues_to_triage != '[]' && steps.detect_gemini_credentials.outputs.available == 'true'
        uses: 'google-github-actions/run-gemini-cli@v0' # ratchet:exclude
        env:
          GITHUB_TOKEN: '' # Do not pass any auth token here since this runs on untrusted inputs
          ISSUES_TO_TRIAGE: '${{ steps.find_issues.outputs.issues_to_triage }}'
          REPOSITORY: '${{ github.repository }}'
          AVAILABLE_LABELS: '${{ steps.get_labels.outputs.available_labels }}'
        with:
          gcp_location: '${{ vars.GOOGLE_CLOUD_LOCATION }}'
          gcp_project_id: '${{ vars.GOOGLE_CLOUD_PROJECT }}'
          gcp_service_account: '${{ vars.SERVICE_ACCOUNT_EMAIL }}'
          gcp_workload_identity_provider: '${{ vars.GCP_WIF_PROVIDER }}'
          gemini_api_key: '${{ secrets.GEMINI_API_KEY }}'
          gemini_cli_version: '${{ vars.GEMINI_CLI_VERSION }}'
          gemini_debug: '${{ fromJSON(vars.GEMINI_DEBUG || vars.ACTIONS_STEP_DEBUG || false) }}'
          gemini_model: '${{ vars.GEMINI_MODEL }}'
          google_api_key: '${{ secrets.GOOGLE_API_KEY }}'
          use_gemini_code_assist: '${{ vars.GOOGLE_GENAI_USE_GCA }}'
          use_vertex_ai: '${{ vars.GOOGLE_GENAI_USE_VERTEXAI }}'
          upload_artifacts: '${{ vars.UPLOAD_ARTIFACTS }}'
          workflow_name: 'gemini-scheduled-triage'
          settings: |-
            {
              "model": {
                "maxSessionTurns": 25
              },
              "telemetry": {
                "enabled": true,
                "target": "local",
                "outfile": ".gemini/telemetry.log"
              },
              "tools": {
                "core": [
                  "run_shell_command(echo)",
                  "run_shell_command(jq)",
                  "run_shell_command(printenv)"
                ]
              }
            }
          prompt: '/gemini-scheduled-triage'

  label:
    runs-on: 'ubuntu-latest'
    needs:
      - 'triage'
    if: |-
      needs.triage.outputs.available_labels != '' &&
      needs.triage.outputs.available_labels != '[]' &&
      needs.triage.outputs.triaged_issues != '' &&
      needs.triage.outputs.triaged_issues != '[]'
    permissions:
      contents: 'read'
      issues: 'write'
      pull-requests: 'write'
    steps:
      - name: 'Mint identity token'
        id: 'mint_identity_token'
        if: |-
          ${{ vars.APP_ID }}
        uses: 'actions/create-github-app-token@29824e69f54612133e76f7eaac726eef6c875baf' # ratchet:actions/create-github-app-token@v2
        with:
          app-id: '${{ vars.APP_ID }}'
          private-key: '${{ secrets.APP_PRIVATE_KEY }}'
          permission-contents: 'read'
          permission-issues: 'write'
          permission-pull-requests: 'write'

      - name: 'Apply labels'
        env:
          AVAILABLE_LABELS: '${{ needs.triage.outputs.available_labels }}'
          TRIAGED_ISSUES: '${{ needs.triage.outputs.triaged_issues }}'
        uses: 'actions/github-script@ed597411d8f924073f98dfc5c65a23a2325f34cd' # ratchet:actions/github-script@v8.0.0
        with:
          # Use the provided token so that the "gemini-cli" is the actor in the
          # log for what changed the labels.
          github-token: '${{ steps.mint_identity_token.outputs.token || secrets.GITHUB_TOKEN || github.token }}'
          script: |-
            // Parse the available labels
            const availableLabels = (process.env.AVAILABLE_LABELS || '').split(',')
              .map((label) => label.trim())
              .sort()

            // Parse out the triaged issues
            const triagedIssues = (JSON.parse(process.env.TRIAGED_ISSUES || '{}'))
              .sort((a, b) => a.issue_number - b.issue_number)

            core.debug(`Triaged issues: ${JSON.stringify(triagedIssues)}`);

            // Iterate over each label
            for (const issue of triagedIssues) {
              if (!issue) {
                core.debug(`Skipping empty issue: ${JSON.stringify(issue)}`);
                continue;
              }

              const issueNumber = issue.issue_number;
              if (!issueNumber) {
                core.debug(`Skipping issue with no data: ${JSON.stringify(issue)}`);
                continue;
              }

              // Extract and reject invalid labels - we do this just in case
              // someone was able to prompt inject malicious labels.
              let labelsToSet = (issue.labels_to_set || [])
                .map((label) => label.trim())
                .filter((label) => availableLabels.includes(label))
                .sort()

              core.debug(`Identified labels to set: ${JSON.stringify(labelsToSet)}`);

              if (labelsToSet.length === 0) {
                core.info(`Skipping issue #${issueNumber} - no labels to set.`)
                continue;
              }

              core.debug(`Setting labels on issue #${issueNumber} to ${labelsToSet.join(', ')} (${issue.explanation || 'no explanation'})`)

              await github.rest.issues.setLabels({
                owner: context.repo.owner,
                repo: context.repo.repo,
                issue_number: issueNumber,
                labels: labelsToSet,
              });
            }

## tests inventory
tests/.claude/claude.md
tests/__init__.py
tests/arch/test_compose_guard.py
tests/arch/test_dopetask_submodule_contract.py
tests/arch/test_registry_compose_alignment.py
tests/arch/test_service_env_contract.py
tests/audit/__init__.py
tests/audit/fixtures/clean_file.txt
tests/audit/test_audit_proof.py
tests/audit/test_auditor_router.py
tests/audit/test_evidence_bundle.py
tests/audit/test_pal_clink_runner.py
tests/audit/test_pr_audit_router.py
tests/audit/test_run_embedded_audit.py
tests/audit/test_validator_scope.py
tests/auditor_router/test_pal_clink.py
tests/auditor_router/test_preflight.py
tests/ci/__init__.py
tests/ci/test_pr_gate.py
tests/claude_tools/test_agent_communication.py
tests/claude_tools/test_debugging_support.py
tests/claude_tools/test_safety_hooks.py
tests/claude_tools/test_session_manager.py
tests/claude_tools/test_tmux_cli.py
tests/conftest.py
tests/copilot_repair/__init__.py
tests/copilot_repair/test_generator.py
tests/copilot_repair/test_repair_packet.py
tests/dcp/fixtures/dcp_core_fixture.json
tests/dcp/fixtures/tp_dcp_0002_approval_artifact.fixture.json
tests/dcp/fixtures/tp_dcp_0002_mutation_class.fixture.json
tests/dcp/fixtures/tp_dcp_0002_project_resource_map.fixture.json
tests/dcp/fixtures/tp_dcp_0003_conflicting_artifacts.json
tests/dcp/fixtures/tp_dcp_0003_stale_sha.json
tests/dcp/fixtures/tp_dcp_0003_unknown_family.json
tests/dcp/fixtures/tp_dcp_0003_valid_merge_readiness.json
tests/dcp/fixtures/tp_dcp_0003_valid_proof_bundle.json
tests/dcp/fixtures/tp_dcp_0003_valid_proof_pointer.json
tests/dcp/test_dcp_0002_contract_derivation.py
tests/dcp/test_dcp_0003_proof_family_dispatch.py
tests/dcp/test_dcp_0004_control_snapshot.py
tests/dcp/test_dcp_0005_red_lane_scanner.py
tests/dcp/test_dcp_contracts.py
tests/dcp/test_dcp_model_routing_0001_domain.py
tests/docker/test_gptr_mcp_dockerfile.py
tests/dopemux/__init__.py
tests/dopemux/test_e2e_recovery.py
tests/dopemux/test_epic2_e2e.py
tests/dopemux/test_epic3_e2e.py
tests/dopemux/test_error_handling.py
tests/dopemux/test_event_bus.py
tests/dopemux/test_instance_state_filtering.py
tests/dopemux/test_logging_packet.py
tests/dopemux/test_main_worktree_detector.py
tests/dopemux/test_protection_interceptor.py
tests/dopemux/test_startup_integration.py
tests/dopemux/test_task_decomposer.py
tests/dopemux/test_uncommitted_detector.py
tests/dopemux/test_worktree_name_inferrer.py
tests/dopemux/test_worktree_recovery.py
tests/dopemux_cli/test_doctor.py
tests/dopemux_cli/test_pr_steward_cmd.py
tests/dopemux_init/test_pr_steward_scaffold.py
tests/embeddings/__init__.py
tests/embeddings/conftest.py
tests/embeddings/integration/__init__.py
tests/embeddings/integration/test_embedding_system_integration.py
tests/embeddings/unit/__init__.py
tests/embeddings/unit/test_core_config.py
tests/embeddings/unit/test_enhancers.py
tests/embeddings/unit/test_integrations.py
tests/embeddings/unit/test_pipelines.py
tests/embeddings/unit/test_providers.py
tests/embeddings/unit/test_storage_hybrid.py
tests/extractor/conftest.py
tests/extractor/test_extractor_routing_ladders.py
tests/fixtures/auditor_router/pal_clink_audit_safe_claude_available/probes.json
tests/fixtures/auditor_router/pal_clink_audit_safe_gemini_available/probes.json
tests/fixtures/auditor_router/pal_clink_chosen_when_direct_auth_required/probes.json
tests/fixtures/auditor_router/pal_clink_mutation_flag_in_role_args/probes.json
tests/fixtures/auditor_router/pal_clink_no_configs_found/probes.json
tests/fixtures/auditor_router/pal_clink_no_verdict_needs_supervisor/PAL_CLINK_AUDIT_OUTPUT.json
tests/fixtures/auditor_router/pal_clink_no_verdict_needs_supervisor/probes.json
tests/fixtures/auditor_router/pal_clink_not_chosen_when_direct_available/probes.json
tests/fixtures/auditor_router/pal_clink_only_mutating_configs/probes.json
tests/fixtures/auditor_router/pal_clink_selected_when_all_tier1_not_installed/probes.json
tests/fixtures/dcp/model_routing_0001/agent_authority_unknown.json
tests/fixtures/dcp/model_routing_0001/arbitrary_selector_rejected.json
tests/fixtures/dcp/model_routing_0001/auditor_verdict_distinct.json
tests/fixtures/dcp/model_routing_0001/design_only_task.json
tests/fixtures/dcp/model_routing_0001/dopecode_legacy_serena_alias.json
tests/fixtures/dcp/model_routing_0001/dopetask_execution_forbidden.json
tests/fixtures/dcp/model_routing_0001/litellm_unhealthy_stop.json
tests/fixtures/dcp/model_routing_0001/mcp_unknown_surface.json
tests/fixtures/dcp/model_routing_0001/opencode_backend_only.json
tests/fixtures/dcp/model_routing_0001/policy_advisory_not_runtime.json
tests/fixtures/dcp/model_routing_0001/proof_extension_additive.json
tests/fixtures/dcp/model_routing_0001/safe_read_task.json
tests/fixtures/dcp/model_routing_0001/stale_alias_stop.json
tests/fixtures/dcp/model_routing_0001/task_orchestrator_write_forbidden.json
tests/fixtures/dcp/model_routing_0001/workflow_red_lane_forbidden.json
tests/fixtures/dopetask_contract/help-0.2.0.txt
tests/fixtures/dopetask_contract/help-0.5.0.txt
tests/fixtures/dopetask_contract/help-0.5.1.txt
tests/fixtures/dopetask_contract/requirements-memory.txt
tests/fixtures/dopetask_contract/requirements.txt
tests/fixtures/dopetask_contract/sample_tp.json
tests/fixtures/dopetask_contract/tp-help-0.2.0.txt
tests/fixtures/dopetask_contract/tp-help-0.5.0.txt
tests/fixtures/dopetask_contract/tp-help-0.5.1.txt
tests/fixtures/dopetask_contract/tp-series-exec-help-0.5.1.txt
tests/fixtures/dopetask_contract/tp-series-finalize-help-0.5.1.txt
tests/fixtures/dopetask_contract/tp-series-help-0.2.0.txt
tests/fixtures/dopetask_contract/tp-series-help-0.5.0.txt
tests/fixtures/dopetask_contract/tp-series-help-0.5.1.txt
tests/fixtures/dopetask_contract/tp-series-status-help-0.5.1.txt
tests/fixtures/dopetask_contract/version-0.2.0.txt
tests/fixtures/dopetask_contract/version-0.5.0.txt
tests/fixtures/dopetask_contract/version-0.5.1.txt
tests/fixtures/pr_action_bridge/needs_implementer_failed_check.json
tests/fixtures/pr_action_bridge/needs_supervisor_proof_missing.json
tests/fixtures/pr_action_bridge/needs_supervisor_proof_stale.json
tests/fixtures/pr_action_bridge/needs_supervisor_unknown_author.json
tests/fixtures/pr_action_bridge/ready_green.json
tests/fixtures/pr_steward/draft_pr_blocks/harvest.json
tests/fixtures/pr_steward/embedded_audit_pass_with_risks_nonblocking/harvest.json
tests/fixtures/pr_steward/failed_check_blocks/harvest.json
tests/fixtures/pr_steward/missing_auth_or_harvest_blocks/harvest.json
tests/fixtures/pr_steward/mixed_sha_checks_block/harvest.json
tests/fixtures/pr_steward/outdated_resolved_thread_nonblocking/harvest.json
tests/fixtures/pr_steward/pending_check_not_ready/harvest.json
tests/fixtures/pr_steward/pr713_like_resolved_threads_with_pass_with_risks_audit/harvest.json
tests/fixtures/pr_steward/proof_current_exact_head_ready/harvest.json
tests/fixtures/pr_steward/proof_missing_blocks/harvest.json
tests/fixtures/pr_steward/proof_self_reference_exception_ready_or_needs_supervisor/harvest.json
tests/fixtures/pr_steward/proof_self_reference_exception_rejects_runtime_changes/harvest.json
tests/fixtures/pr_steward/proof_stale_blocks/harvest.json
tests/fixtures/pr_steward/raw_review_comment_without_thread_still_blocks/harvest.json
tests/fixtures/pr_steward/ready_all_green/harvest.json
tests/fixtures/pr_steward/ready_with_resolved_outdated_threads/harvest.json
tests/fixtures/pr_steward/resolved_thread_clears_review_item/harvest.json
tests/fixtures/pr_steward/skipped_required_audit_blocks/harvest.json
tests/fixtures/pr_steward/unknown_pr_author_blocks/harvest.json
tests/fixtures/pr_steward/unknown_reviewer_blocks/harvest.json
tests/fixtures/pr_steward/unresolved_thread_blocks/harvest.json
tests/fixtures/pr_steward/unresolved_thread_still_blocks/harvest.json
tests/github_specialist/test_cli_smoke.py
tests/github_specialist/test_redaction.py
tests/integration/__init__.py
tests/integration/orchestrator/test_memory_writers_integration.py
tests/integration/orchestrator/test_transitions_integration.py
tests/integration/pm/__init__.py
tests/integration/task-orchestrator/circuit_breaker.py
tests/integration/task-orchestrator/docker-compose.yml.save
tests/integration/task-orchestrator/mcp_wrapper.py
tests/integration/test_architecture_3_0_complete.py
tests/integration/test_autoreview_loop.py
tests/integration/test_batch_integration.py
tests/integration/test_canonical_ledger_convergence.py
tests/integration/test_claude_autoresponder_integration.py
tests/integration/test_claude_integration.py
tests/integration/test_dope_layout.py
tests/integration/test_dual_capture_convergence.py
tests/integration/test_project_workflow.py
tests/integration/test_start_command.py
tests/integration/test_start_crit_gaps.py
tests/integration/test_start_wave3.py
tests/integration/test_task_commands.py
tests/mcp/test_conport_mcp_real.py
tests/mcp/test_conport_surface_contract.py
tests/mcp/test_discovery_gate.py
tests/mcp/test_discovery_gate_strict.py
tests/mcp/test_mcp_internal_lockdown.py
tests/mcp/test_provision.py
tests/mcp/test_resolver.py
tests/orchestrator/__init__.py
tests/orchestrator/test_adhd_orchestrator.py
tests/orchestrator/test_dx_surface_manifest.py
tests/orchestrator/test_dynamic_layouts.py
tests/orchestrator/test_status_updates.py
tests/orchestrator/tmux/__init__.py
tests/pr_action_bridge/__init__.py
tests/pr_action_bridge/test_cli.py
tests/pr_action_bridge/test_compiler.py
tests/pr_action_bridge/test_compiler_fixtures.py
tests/pr_docgen_sync_skill/test_pr_docgen_workflow_contracts.py
tests/pr_docgen_sync_skill/test_pr_docgen_workflow_e2e.py
tests/pr_docgen_sync_skill/test_pr_docgen_workflow_integration.py
tests/pr_merge_specialist/test_agentic_fix_classification.py
tests/pr_merge_specialist/test_agentic_thread_remediation.py
tests/pr_merge_specialist/test_finalization_gate.py
tests/pr_merge_specialist/test_ordering_and_classification.py
tests/pr_merge_specialist/test_policy_and_validation.py
tests/pr_merge_specialist/test_queue_drain_integration.py
tests/pr_merge_specialist/test_remediation_gate.py
tests/pr_merge_specialist/test_steward_gate.py
tests/pr_merge_specialist/test_template_contracts.py
tests/pr_merge_specialist/test_thread_and_merge_logic.py
tests/pr_steward/test_classifier_embedded_audit_normalization.py
tests/pr_steward/test_classifier_mixed_sha.py
tests/pr_steward/test_classifier_proof_status.py
tests/pr_steward/test_classifier_readiness_harden.py
tests/pr_steward/test_intake.py
tests/regression/__init__.py
tests/regression/test_claude_code_enrichment.py
tests/regression/test_fnew3_unified_complexity.py
tests/regression/test_fnew5_code_graph_enrichment.py
tests/regression/test_fnew6_session_intelligence.py
tests/regression/test_fnew7_phase3_intelligence.py
tests/regression/test_fnew7_unified_queries.py
tests/regression/test_fnew8_eventbus_wiring.py
tests/regression/test_fnew9_api_integration.py
tests/regression/test_fnew9_matching_engine.py
tests/regression/test_production_integration.py
tests/regression/test_serena_enhancements.py
tests/regression/test_websocket_streaming.py
tests/resources/test_docs/claude.md
tests/resources/test_docs/config.yaml
tests/scripts/TEST_ROUTING.sh
tests/scripts/simple_search_test.sh
tests/scripts/test_adhd_ux.py
tests/scripts/test_claude_hooks.py
tests/scripts/test_docs_filename_hygiene.py
tests/scripts/test_docs_hygiene.py
tests/scripts/test_dope_layout.sh
tests/scripts/test_env_extract.py
tests/scripts/test_gpt_researcher_two_phase_runner.py
tests/scripts/test_hooks.py
tests/scripts/test_install_sh_secrets.py
tests/scripts/test_shell_installer.py
tests/security/README.md
tests/security/test_cors.py
tests/security/test_input_validation.py
tests/security/test_rate_limiting.py
tests/shared/test_dopecon_bridge_client.py
tests/system_data/test_classifier_planner.py
tests/system_data/test_cli.py
tests/system_data/test_executor_proof.py
tests/system_data/test_tools.py
tests/test_agent_orchestrator.py
tests/test_attention_monitor.py
tests/test_brand_voice.py
tests/test_bridge_integration.py
tests/test_claude_code_router.py
tests/test_claude_config.py
tests/test_claude_configurator.py
tests/test_claude_launcher.py
tests/test_cli.py
tests/test_cli_mcp_startup.py
tests/test_component6_phase1.py
tests/test_config_manager.py
tests/test_config_sanitization.py
tests/test_config_validation.py
tests/test_conport_wiring.py
tests/test_context_manager.py
tests/test_dope_context_workspace.py
tests/test_event_multi_instance.py.disabled
tests/test_execution_store.py
tests/test_freeflow_quota.py
tests/test_freeflow_router.py
tests/test_freeflow_trace_logger.py
tests/test_init.py
tests/test_instance_manager_env.py
tests/test_instance_manager_ports.py
tests/test_layer1.py
tests/test_leantime_api.py
tests/test_leantime_integration.py
tests/test_litellm_manager.py
tests/test_litellm_manager_integration.py
tests/test_litellm_proxy.py
tests/test_local_workflow_commands.py
tests/test_mcp_config_generation.py
tests/test_mcp_registry.py
tests/test_mobile_cli.py
tests/test_mobile_env_migration.py
tests/test_mobile_hooks.py
tests/test_mobile_runtime.py
tests/test_model_routing_consistency.py
tests/test_model_routing_policy.py
tests/test_monitoring.py
tests/test_multi_workspace.py
tests/test_native_hooks_workflow.py
tests/test_navigation_workflow.py
tests/test_orchestrator_enforcement_hooks.py
tests/test_orchestrator_hooks.py
tests/test_orchestrator_subagent_protocol.py
tests/test_pm_api.py
tests/test_port_config.py
tests/test_profile_models.py
tests/test_profile_parser.py
tests/test_project_init_templates.py
tests/test_real_navigation.py
tests/test_real_navigation_scenarios.py
tests/test_roles_catalog.py
tests/test_routing_config.py
tests/test_session_commands.py
tests/test_shield_coordinator.py
tests/test_shield_integration.py
tests/test_task_management_integration.py
tests/test_thread_bootstrap_docs_exist.py
tests/test_ui_splash.py
tests/test_voice_core.py
tests/test_workflow_assets.py
tests/test_workflow_models.py
tests/test_workflow_service.py
tests/test_workspace_detection.py
tests/testgen_skill/test_workflow_contracts.py
tests/testgen_skill/test_workflow_e2e.py
tests/testgen_skill/test_workflow_integration.py
tests/unit/__init__.py
tests/unit/dopemux/pm/test_conport_adapter.py
tests/unit/dopemux/pm/test_writes.py
tests/unit/dopemux/ui/test_pm_writes.py
tests/unit/orchestrator/test_daemon.py
tests/unit/orchestrator/test_data_sources.py
tests/unit/orchestrator/test_github_adapter.py
tests/unit/orchestrator/test_hooks.py
tests/unit/orchestrator/test_idempotency.py
tests/unit/orchestrator/test_mcp_wrappers.py
tests/unit/orchestrator/test_memory_writers.py
tests/unit/orchestrator/test_operator_workflows.py
tests/unit/orchestrator/test_perpacket.py
tests/unit/orchestrator/test_policy.py
tests/unit/orchestrator/test_transitions.py
tests/unit/orchestrator/test_ui_data_sources.py
tests/unit/orchestrator/test_validation.py
tests/unit/orchestrator/test_workflow_dsl.py
tests/unit/pm/__init__.py
tests/unit/pm/test_chronicle.py
tests/unit/pm/test_pm_adapters.py
tests/unit/pm/test_pm_events.py
tests/unit/pm/test_pm_mapping.py
tests/unit/pm/test_pm_models.py
tests/unit/pm/test_pm_publish.py
tests/unit/pm/test_pm_route_contracts.py
tests/unit/pm/test_pm_store.py
tests/unit/pm/test_reads.py
tests/unit/test_adhd_activity_loop.py
tests/unit/test_adhd_baseline_calibration.py
tests/unit/test_adhd_boundary_detection.py
tests/unit/test_adhd_engine_settings_contract.py
tests/unit/test_adhd_engine_task_orchestrator_url.py
tests/unit/test_adhd_event_backbone.py
tests/unit/test_adhd_hyperfocus_latch.py
tests/unit/test_adhd_operator_identity.py
tests/unit/test_adhd_operator_profile_seed.py
tests/unit/test_adhd_optimizations.py
tests/unit/test_adhd_privacy_guard.py
tests/unit/test_adhd_real_assessment.py
tests/unit/test_alt_routing_config.py
tests/unit/test_altp_skips_openrouter_gate.py
tests/unit/test_auto_configurator.py
tests/unit/test_auto_detection_service.py
tests/unit/test_brand_lint.py
tests/unit/test_bridge_task_integration.py
tests/unit/test_ccr_models_env_for_altp.py
tests/unit/test_circuit_breaker.py
tests/unit/test_claude_autoresponder.py
tests/unit/test_cli_audit_remediations.py
tests/unit/test_cli_capture_commands.py
tests/unit/test_cli_kernel_commands.py
tests/unit/test_cli_orchestrator_commands.py
tests/unit/test_cli_orchestrator_validation_commands.py
tests/unit/test_cli_repscan_passthrough.py
tests/unit/test_cli_upgrades_commands.py
tests/unit/test_cli_workflow_commands.py
tests/unit/test_cockpit_cli.py
tests/unit/test_confidence_band_ux.py
tests/unit/test_config_generator.py
tests/unit/test_conport_client_semantic_search.py
tests/unit/test_conport_memory_server.py
tests/unit/test_conport_semantic_search_deprecation.py
tests/unit/test_dashboard_api_client.py
tests/unit/test_dashboard_operator_ui.py
tests/unit/test_decisions_commands.py
tests/unit/test_desktop_commander_security.py
tests/unit/test_document_classifier_security.py
tests/unit/test_dopecon_bridge_semantic_proxy.py
tests/unit/test_dopetask_sequential_plan_runner.py
tests/unit/test_dopetask_series_adapter.py
tests/unit/test_dopetask_series_loader.py
tests/unit/test_dopetask_series_status_mapper.py
tests/unit/test_dopetask_wrapper_submodule.py
tests/unit/test_dotenv_loader.py
tests/unit/test_env_export_allowlist.py
tests/unit/test_error_handling.py
tests/unit/test_event_bus.py
tests/unit/test_event_bus_safety.py
tests/unit/test_execution_plane_concurrency.py
tests/unit/test_extract_local_smoke.py
tests/unit/test_extractor_command_authority.py
tests/unit/test_extractor_gemini_thinking_config.py
tests/unit/test_extractor_key_hygiene.py
tests/unit/test_extractor_runner_resolution.py
tests/unit/test_extractor_schema_repair.py
tests/unit/test_extractor_validation.py
tests/unit/test_extractor_validation_ui.py
tests/unit/test_global_rollup.py
tests/unit/test_health.py
tests/unit/test_launcher_wizard.py
tests/unit/test_leantime_bridge.py
tests/unit/test_mcp_commands_catalog.py
tests/unit/test_mcp_response_budget.py
tests/unit/test_memory_capture_client.py
tests/unit/test_pattern_correlation_engine.py
tests/unit/test_pr_merge_specialist_dashboard_and_train.py
tests/unit/test_pr_merge_specialist_merge_strategy.py
tests/unit/test_pr_merge_specialist_queue_states.py
tests/unit/test_prescan_online_gate.py
tests/unit/test_profile_analytics.py
tests/unit/test_profile_analyzer.py
tests/unit/test_profile_cli_registration.py
tests/unit/test_profile_config_integration.py
tests/unit/test_profile_detector_adhd_client.py
tests/unit/test_profile_detector_scoring.py
tests/unit/test_profile_epic_compat_shims.py
tests/unit/test_profile_management_commands.py
tests/unit/test_profile_manager_detection.py
tests/unit/test_profile_usage_analysis_command.py
tests/unit/test_profile_use_command.py
tests/unit/test_profile_wizard.py
tests/unit/test_repo_truth_extractor_prompt_governance.py
tests/unit/test_run_extraction_v3_phase_m.py
tests/unit/test_run_extraction_v3_pipeline_controls.py
tests/unit/test_run_extraction_v3_processpool_stability.py
tests/unit/test_runtime_authority_manifest.py
tests/unit/test_security.py
tests/unit/test_shell_hooks_generation.py
tests/unit/test_task_coordinator_execution_leases.py
tests/unit/test_task_decomposer.py
tests/unit/test_task_decomposer_enhanced.py
tests/unit/test_task_decomposer_pm.py
tests/unit/test_task_decomposer_pm_coverage.py
tests/unit/test_task_orchestrator_conport_semantic_resolution.py
tests/unit/test_task_orchestrator_launcher.py
tests/unit/test_task_orchestrator_mcp_wrappers.py
tests/unit/test_task_orchestrator_project_workflow_contract.py
tests/unit/test_task_orchestrator_runtime_config.py
tests/unit/test_task_orchestrator_startup.py
tests/unit/test_task_orchestrator_workflow_api.py
tests/unit/test_task_orchestrator_workflow_models.py
tests/unit/test_task_orchestrator_workflow_route_certification.py
tests/unit/test_task_orchestrator_workflow_service.py
tests/unit/test_task_orchestrator_workflow_store.py
tests/unit/test_task_orchestrator_workflow_write_serialization.py
tests/unit/test_ui_dashboard_backend_api.py
tests/unit/test_unified_complexity_coordinator.py
tests/unit/test_wire_project.py
tests/unit/test_wizard_interactivity.py
tests/unit/test_wma_conport_semantic_resolution.py
tests/unit/test_wma_secret_config.py
tests/unit/tui/test_app.py
tests/unit/tui/test_widgets.py

## compileall
compileall_exit=0

## pytest
........................................................................ [  2%]
........................................................................ [  4%]
........................................................................ [  6%]
...........................................................F............ [  8%]
........................................................................ [ 10%]
................................................................F....... [ 12%]
........................................................................ [ 15%]
........................................................................ [ 17%]
........................................................................ [ 19%]
........................................................................ [ 21%]
..........................................................F............. [ 23%]
........................................................................ [ 25%]
........................................................................ [ 28%]
...............................FF....................................... [ 30%]
............................................pytest_exit=137

## Pytest Network Stop Condition

Status: BLOCKED_RUNTIME_UNSAFE_NETWORK

During the repo-wide pytest collection/run, a pytest subprocess was observed holding an external HTTPS connection.

Action taken:
- pytest subprocess terminated
- partial pytest log preserved
- no retry attempted
- no test result marked green
- Pack 2 classified as evidence-ready-with-gaps / blocked for runtime network uncertainty

Reason:
This packet is evidence-only. Unexpected live external network activity during a repo-wide test suite crosses into unsafe runtime uncertainty.

Required follow-up:
- identify test/process responsible
- rerun only under a network-deny harness or targeted offline-safe tests
- do not claim repo-wide tests passed

## Targeted Offline-Safe Follow-Up Checks

Generated at: 2026-06-12T00:42:21Z

```bash
python -m compileall -q src services
```
compileall_followup_exit=0

```bash
python -m pytest -q tests/unit/test_cli_kernel_commands.py || true
```
..........                                                               [100%]
test_cli_kernel_commands_exit=0

```bash
python -m pytest -q tests/unit/test_dopetask_wrapper_submodule.py || true
```
.....                                                                    [100%]
test_dopetask_wrapper_submodule_exit=0

Repo-wide pytest remains NOT_RERUN after BLOCKED_RUNTIME_UNSAFE_NETWORK.
