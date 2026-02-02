# Makefile for Component 7: Interruption Shield
# Quick commands for development workflow

.PHONY: help install test lint format clean run

help:  ## Show this help message
	@echo "Component 7: Environmental Interruption Shield"
	@echo ""
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install:  ## Install dependencies
	pip install -r requirements.txt
	pip install pre-commit
	pre-commit install

test:  ## Run tests with coverage
	pytest --cov=interruption_shield --cov-report=html --cov-report=term

test-fast:  ## Run tests without coverage (faster)
	pytest -v

test-unit:  ## Run only unit tests
	pytest tests/unit/ -v

test-integration:  ## Run only integration tests
	pytest tests/integration/ -v

lint:  ## Run all linters
	black --check .
	isort --check .
	flake8 . --max-line-length=100 --extend-ignore=E203
	mypy . --ignore-missing-imports

format:  ## Format code with black and isort
	black .
	isort .

security:  ## Run security scan
	bandit -r . -ll -i

clean:  ## Clean up generated files
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name .pytest_cache -exec rm -rf {} +
	find . -type d -name .mypy_cache -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf coverage.xml
	rm -rf dist/
	rm -rf build/
	rm -rf *.egg-info

run:  ## Run the interruption shield service
	python -m interruption_shield.main

run-dev:  ## Run in development mode with auto-reload
	python -m interruption_shield.main --dev

setup:  ## First-time setup (install + pre-commit)
	make install
	make format
	make test
	@echo ""
	@echo "✅ Setup complete! You're ready to start development."

ci:  ## Run all CI checks locally
	make format
	make lint
	make security
	make test
	@echo ""
	@echo "✅ All CI checks passed!"

week1:  ## Week 1 checklist
	@echo "Week 1: Core Infrastructure"
	@echo "  [ ] Day 1-2: Development environment setup"
	@echo "  [ ] Day 3-4: ShieldCoordinator implementation"
	@echo "  [ ] Day 5: Productivity monitoring"
	@echo ""
	@echo "Run 'make install' to get started"
