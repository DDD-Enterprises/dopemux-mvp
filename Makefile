# Dopemux Development Makefile

.PHONY: help install install-dev test test-unit test-integration test-coverage test-extractor test-extractor-smoke clean lint format type-check build docs serve-docs probe probe-c

# Default target
help:
	@echo "Dopemux Development Commands:"
	@echo ""
	@echo "Installation:"
	@echo "  install        Install package in production mode"
	@echo "  install-dev    Install package in development mode with dev dependencies"
	@echo ""
	@echo "Testing:"
	@echo "  test           Run all tests"
	@echo "  test-unit      Run unit tests only"
	@echo "  test-integration  Run integration tests only"
	@echo "  test-coverage  Run tests with coverage report"
	@echo "  test-fast      Run tests without slow tests"
	@echo "  test-extractor Run Repo Truth Extractor tests without global coverage gate"
	@echo "  test-extractor-smoke  Run extractor rename-migration unit smoke tests without coverage gate"
	@echo ""
	@echo "Quality:"
	@echo "  lint           Run linting checks (flake8)"
	@echo "  format         Format code with black and isort"
	@echo "  type-check     Run type checking with mypy"
	@echo "  quality        Run all quality checks"
	@echo ""
	@echo "Development:"
	@echo "  clean          Clean build artifacts and cache"
	@echo "  build          Build distribution packages"
	@echo "  docs           Build documentation"
	@echo "  serve-docs     Serve documentation locally"
	@echo ""
	@echo "Docs Audit:"
	@echo "  docs-audit     Scan docs, create report + triage + rename plan (dry)"
	@echo "  docs-audit-frontmatter-apply  Insert minimal frontmatter where missing"
	@echo "  docs-audit-apply-rename PLAN=reports/docs-audit/rename_plan.csv  Apply renames"
	@echo ""
	@echo "Project Management (Leantime + Task-Master):"
	@echo "  pm-install     Interactive installer (Leantime + Task-Master)"
	@echo "  pm-install-unattended  Unattended install with default config"
	@echo "  pm-up          Start PM stack (docker-compose up -d)"
	@echo "  pm-down        Stop PM stack (docker-compose down)"
	@echo "  pm-logs        Tail PM stack logs"
	@echo ""
	@echo "Extraction Pipeline (Upgrade Pipeline):"
	@echo "  x-run-init RUN_ID=YYYYMMDD_HHMM_<slug>  Initialize new extraction run scaffolding"
	@echo "  x-phase-dirs PHASE=<A|H|D|C|E|W|B|G|Q|R|X|T|Z>  Print target directories for a phase"
	@echo "  x-status                                     Print file counts per phase"
	@echo "  x-manifest                                   Update/generate MANIFEST.json for run"
	@echo "  x-doctor                                     Run pipeline doctor on latest run"
	@echo "  probe                                        Deterministic run/phase/step debug bundle"
	@echo "  probe-c                                      Convenience probe for Phase C (default STEP=C0)"

# Installation targets
install:
	pip install -e .

install-dev:
	pip install -e .[dev]

# Testing targets
test:
	pytest

test-unit:
	pytest -m "not integration"

test-integration:
	pytest -m integration

test-coverage:
	pytest --cov-report=term-missing --cov-report=html

test-fast:
	pytest -m "not slow"

test-verbose:
	pytest -v

test-extractor:
	pytest --no-cov services/repo-truth-extractor/tests

test-extractor-smoke:
	pytest --no-cov tests/unit/test_run_extraction_v3_phase_m.py tests/unit/test_run_extraction_v3_pipeline_controls.py

# Quality targets
lint:
	flake8 src/ tests/

format:
	black src/ tests/
	isort src/ tests/

type-check:
	mypy src/

quality: lint type-check
	@echo "✓ All quality checks passed"

# Development targets
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf coverage.xml
	rm -rf .mypy_cache/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

build: clean
	python -m build

# Development server
dev-server:
	@echo "Starting development environment..."
	@echo "Run 'make test-coverage' to see test coverage"
	@echo "Run 'make quality' to check code quality"

# Pre-commit hook simulation
pre-commit: format lint type-check test-fast
	@echo "✓ Pre-commit checks passed"

# CI simulation
ci: quality test-coverage
	@echo "✓ CI checks passed"

# Documentation (placeholder for future)
docs:
	@echo "Documentation build not yet implemented"

serve-docs:
	@echo "Documentation server not yet implemented"

# ---- Docs Audit helpers ----
docs-audit:
	python3 scripts/docs_audit/audit_docs.py scan --roots docs CCDOCS CHECKPOINT archive --out reports/docs-audit
	python3 scripts/docs_audit/audit_docs.py report --out reports/docs-audit
	python3 scripts/docs_audit/audit_docs.py triage-template --out reports/docs-audit
	python3 scripts/docs_audit/audit_docs.py plan-rename --out reports/docs-audit --template "{date} - {title}.md"
	@echo "\n✓ Docs audit complete. See reports/docs-audit/"

docs-audit-frontmatter-apply:
	python3 scripts/docs_audit/audit_docs.py enforce-frontmatter --out reports/docs-audit --apply

docs-audit-apply-rename:
	@if [ -z "$(PLAN)" ]; then echo "Usage: make docs-audit-apply-rename PLAN=reports/docs-audit/rename_plan.csv"; exit 1; fi
	python3 scripts/docs_audit/audit_docs.py apply-rename --plan $(PLAN)

# ---- Project Management (Leantime + Task-Master) ----
pm-install:
	python3 installers/leantime/install.py

pm-install-unattended:
	python3 installers/leantime/install.py -u -c installers/leantime/configs/default.yaml

pm-up:
	docker compose -f compose.yml up -d leantime mysql_leantime redis_leantime

pm-down:
	docker compose -f compose.yml stop leantime mysql_leantime redis_leantime

pm-logs:
	docker compose -f compose.yml logs -f leantime

# ---- Webhook Receiver ----
webhook-up:  ## Start webhook receiver
	@docker compose up -d webhook-receiver

webhook-down:  ## Stop webhook receiver
	@docker compose stop webhook-receiver && docker compose rm -f webhook-receiver

webhook-logs:  ## Tail webhook receiver logs
	@docker compose logs -f webhook-receiver

webhook-smoke:  ## Run full smoke tests for webhooks
	@./scripts/webhooks/smoke.sh

webhook-health:  ## Check webhook receiver health (local and public)
	@echo "Checking local health..."
	@curl -fsS http://localhost:8790/healthz && echo "" || echo "Local health check failed"
	@echo "Checking public health..."
	@curl -fsS https://webhooks.krohman.org/healthz && echo "" || echo "Public health check failed"

webhook-db-stats:  ## Print webhook receiver DB stats
	@docker compose exec webhook-receiver python services/webhook_receiver/admin.py db stats

webhook-db-tail:  ## Tail last 20 webhook events
	@docker compose exec webhook-receiver python services/webhook_receiver/admin.py db tail --table provider_events --limit 20

webhook-db-tail-run:  ## Tail last 20 run events
	@docker compose exec webhook-receiver python services/webhook_receiver/admin.py db tail --table run_events --limit 20

webhook-proof:  ## Generate proof bundle
	@echo "--- webhook-db-stats ---"
	@$(MAKE) webhook-db-stats
	@echo "\n--- webhook-db-tail ---"
	@$(MAKE) webhook-db-tail
	@echo "\n--- webhook-db-tail-run ---"
	@$(MAKE) webhook-db-tail-run

# ============================================
# ADHD Dashboard & Orchestrator
# ============================================

orchestrator:  ## Launch full Dopemux orchestrator environment (4 panes)
	@./scripts/launch-dopemux-orchestrator.sh

minimal:  ## Launch minimal environment (2 panes: dashboard + CLI)
	@./scripts/launch-dopemux-minimal.sh

dashboard:  ## Launch standalone 3-pane ADHD dashboard (bash version)
	@test -f scripts/launch-adhd-dashboard.sh && ./scripts/launch-adhd-dashboard.sh || echo "❌ Dashboard script not found"

attach:  ## Attach to existing orchestrator session
	@tmux attach -t dopemux-orchestrator || echo "❌ No session found. Run 'make orchestrator' first"

attach-minimal:  ## Attach to minimal session
	@tmux attach -t dmx || echo "❌ No session found. Run 'make minimal' first"

kill-orchestrator:  ## Kill orchestrator tmux session
	@tmux kill-session -t dopemux-orchestrator 2>/dev/null && echo "✅ Orchestrator session killed" || echo "ℹ️  No session to kill"

kill-minimal:  ## Kill minimal session
	@tmux kill-session -t dmx 2>/dev/null && echo "✅ Minimal session killed" || echo "ℹ️  No session to kill"

list-sessions:  ## List all tmux sessions
	@tmux list-sessions 2>/dev/null || echo "No tmux sessions running"

# ---- Extraction Pipeline (Upgrade Pipeline) ----
LATEST_RUN := $(shell cat extraction/latest_run_id.txt 2>/dev/null)

x-run-init:
	@if [ -n "$(RUN_ID)" ]; then \
		ID="$(RUN_ID)"; \
	else \
		SHA=$$(git rev-parse --short HEAD 2>/dev/null || echo nogit); \
		ID=$$(date '+%Y%m%d_%H%M%S_PST')_$$SHA; \
	fi; \
	echo "Initializing run $$ID..."; \
	mkdir -p "extraction/runs/$$ID/00_inputs"; \
	for PHASE_DIR in \
		A_repo_control_plane \
		H_home_control_plane \
		D_docs_pipeline \
		C_code_surfaces \
		E_execution_plane \
		W_workflow_plane \
		B_boundary_plane \
		G_governance_plane \
		Q_quality_assurance \
		R_arbitration \
		X_feature_index \
		T_task_packets \
		Z_handoff_freeze; do \
		mkdir -p "extraction/runs/$$ID/$$PHASE_DIR/inputs"; \
		mkdir -p "extraction/runs/$$ID/$$PHASE_DIR/raw"; \
		mkdir -p "extraction/runs/$$ID/$$PHASE_DIR/norm"; \
		mkdir -p "extraction/runs/$$ID/$$PHASE_DIR/qa"; \
	done; \
	echo "$$ID" > extraction/latest_run_id.txt; \
	rm -f extraction/latest; \
	ln -s "runs/$$ID" extraction/latest; \
	echo "✓ Initialized run $$ID in extraction/latest"

x-phase-dirs:
	@if [ -z "$(PHASE)" ]; then echo "Usage: make x-phase-dirs PHASE=<A|H|D|C|E|W|B|G|Q|R|X|T|Z>"; exit 1; fi
	@case $(PHASE) in \
		A) echo "extraction/latest/A_repo_control_plane" ;; \
		H) echo "extraction/latest/H_home_control_plane" ;; \
		D) echo "extraction/latest/D_docs_pipeline" ;; \
		C) echo "extraction/latest/C_code_surfaces" ;; \
		E) echo "extraction/latest/E_execution_plane" ;; \
		W) echo "extraction/latest/W_workflow_plane" ;; \
		B) echo "extraction/latest/B_boundary_plane" ;; \
		G) echo "extraction/latest/G_governance_plane" ;; \
		Q) echo "extraction/latest/Q_quality_assurance" ;; \
		R) echo "extraction/latest/R_arbitration" ;; \
		X) echo "extraction/latest/X_feature_index" ;; \
		T) echo "extraction/latest/T_task_packets" ;; \
		Z) echo "extraction/latest/Z_handoff_freeze" ;; \
		*) echo "Invalid phase $(PHASE)"; exit 1 ;; \
	esac

x-status:
	@echo "Current Run: $(LATEST_RUN)"
	@find extraction/latest -maxdepth 2 -not -path '*/.*' | sort

x-manifest:
	@python3 scripts/pipeline_manifest.py

x-doctor:
	@python3 scripts/pipeline_doctor.py

probe:
	@if [ -z "$(PHASE)" ]; then echo "Usage: make probe PHASE=<A|H|D|C|E|W|B|G|Q|R|X|T|Z> (RID=<rid> | RID_FROM_LATEST=1) [STEP=<step>]"; exit 1; fi
	@if [ -n "$(RID)" ] && [ "$(RID_FROM_LATEST)" = "1" ]; then echo "Set either RID=<rid> or RID_FROM_LATEST=1, not both."; exit 1; fi
	@if [ -z "$(RID)" ] && [ "$(RID_FROM_LATEST)" != "1" ]; then echo "Set RID=<rid> or RID_FROM_LATEST=1."; exit 1; fi
	@python3 services/repo-truth-extractor/run_probe.py --phase "$(PHASE)" \
		$(if $(RID),--rid "$(RID)",--rid-from-latest) \
		$(if $(STEP),--step "$(STEP)",) \
		$(if $(MAX_PARTITIONS),--max-partitions "$(MAX_PARTITIONS)",) \
		$(if $(MAX_FAILURES),--max-failures "$(MAX_FAILURES)",) \
		$(if $(SEARCH_ROOT),--search-root "$(SEARCH_ROOT)",)

probe-c:
	@$(MAKE) probe PHASE=C STEP=$(if $(STEP),$(STEP),C0) RID="$(RID)" RID_FROM_LATEST="$(RID_FROM_LATEST)" MAX_PARTITIONS="$(MAX_PARTITIONS)" MAX_FAILURES="$(MAX_FAILURES)" SEARCH_ROOT="$(SEARCH_ROOT)"
