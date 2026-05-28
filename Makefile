# ==============================================================================
# Confidence Map — Makefile
# Centralized project management: setup, development, tests, and quality.
#
# Quick start:
#   make setup   → first time (creates .env + installs everything)
#   make dev     → start backend + frontend
#   make test    → run all tests
#   make check   → full quality gates (lint + types + tests)
#   make help    → list all available commands
# ==============================================================================

# ── Tools ──────────────────────────────────────────────────────────────────────
UV           := uv
PNPM         := pnpm
PYTHON       := python3
CURL         := curl

# ── Directories ────────────────────────────────────────────────────────────────
BACKEND_DIR  := backend
FRONTEND_DIR := frontend
PKG          := confidence_map

# ── Server ─────────────────────────────────────────────────────────────────────
BACKEND_HOST := 0.0.0.0
BACKEND_PORT := 8000
FRONTEND_PORT := 3000

# ── npm/pnpm registry (avoids private registries on the network) ───────────────
NPM_REGISTRY := https://registry.npmjs.org

# ── API key for tests (does not call the real API) ────────────────────────────
TEST_API_KEY := test

# ── Output colors ──────────────────────────────────────────────────────────────
CYAN  := \033[36m
RESET := \033[0m
BOLD  := \033[1m
GREEN := \033[32m
YELLOW := \033[33m
RED   := \033[31m

.DEFAULT_GOAL := help
.PHONY: all setup env install install-backend install-frontend \
        dev dev-backend dev-frontend demo \
        test test-unit test-integration test-coverage \
        lint format typecheck typecheck-backend typecheck-frontend \
        check health build eval \
        clean clean-backend clean-frontend clean-all \
        venv-info prereqs help

# ==============================================================================
# SETUP — First time
# ==============================================================================

setup: prereqs env install ## [START] Full setup: verify tools + create .env + install deps
	@printf "$(GREEN)$(BOLD)\n✓ Project ready.$(RESET)\n"
	@printf "  Next step: $(CYAN)make dev$(RESET)\n\n"

prereqs: ## Verify that uv, pnpm, and python3 are installed
	@printf "$(CYAN)→ Checking tools...$(RESET)\n"
	@command -v $(UV)     >/dev/null 2>&1 || { printf "$(RED)✗ uv not found.$(RESET) Install: curl -LsSf https://astral.sh/uv/install.sh | sh\n"; exit 1; }
	@command -v $(PNPM)   >/dev/null 2>&1 || { printf "$(RED)✗ pnpm not found.$(RESET) Install: npm install -g pnpm\n"; exit 1; }
	@command -v $(PYTHON) >/dev/null 2>&1 || { printf "$(RED)✗ python3 not found.$(RESET) Requires Python 3.12+\n"; exit 1; }
	@$(PYTHON) -c "import sys; assert sys.version_info >= (3,12), 'Python 3.12+ required'" 2>/dev/null || \
		{ printf "$(RED)✗ Python 3.12+ required$(RESET) (current: $$($(PYTHON) --version))\n"; exit 1; }
	@printf "  $(GREEN)✓$(RESET) uv     $$($(UV) --version)\n"
	@printf "  $(GREEN)✓$(RESET) pnpm   $$($(PNPM) --version)\n"
	@printf "  $(GREEN)✓$(RESET) python $$($(PYTHON) --version)\n"

env: ## Create backend/.env from .env.example if it does not exist
	@if [ ! -f $(BACKEND_DIR)/.env ]; then \
		cp $(BACKEND_DIR)/.env.example $(BACKEND_DIR)/.env; \
		printf "$(GREEN)✓$(RESET) Created $(BACKEND_DIR)/.env\n"; \
		printf "  $(YELLOW)→ Edit ANTHROPIC_API_KEY if using DEMO_MODE=false$(RESET)\n"; \
	else \
		printf "  → $(BACKEND_DIR)/.env already exists (no changes)\n"; \
	fi

# ==============================================================================
# DEPENDENCY INSTALLATION
# ==============================================================================

install: install-backend install-frontend ## Install all dependencies (backend + frontend)
	@printf "$(GREEN)✓ Dependencies installed$(RESET)\n"

install-backend: ## Install Python dependencies with uv sync
	@printf "$(CYAN)→ Backend: uv sync$(RESET)\n"
	@cd $(BACKEND_DIR) && $(UV) sync

install-frontend: ## Install Node.js dependencies with pnpm
	@printf "$(CYAN)→ Frontend: pnpm install$(RESET)\n"
	@cd $(FRONTEND_DIR) && $(PNPM) install --registry $(NPM_REGISTRY)

# ==============================================================================
# DEVELOPMENT — Start services
# ==============================================================================

dev: env ## Start backend + frontend in parallel (Ctrl+C to stop both)
	@printf "$(CYAN)$(BOLD)→ Starting Confidence Map$(RESET)\n"
	@printf "  Backend:  $(CYAN)http://localhost:$(BACKEND_PORT)$(RESET)\n"
	@printf "  Frontend: $(CYAN)http://localhost:$(FRONTEND_PORT)$(RESET)\n"
	@printf "  Health:   $(CYAN)http://localhost:$(BACKEND_PORT)/health$(RESET)\n"
	@printf "  $(YELLOW)Ctrl+C stops both services$(RESET)\n\n"
	@trap 'kill 0' INT; \
		(cd $(BACKEND_DIR) && $(UV) run uvicorn $(PKG).main:app \
			--reload \
			--host $(BACKEND_HOST) \
			--port $(BACKEND_PORT)) & \
		(cd $(FRONTEND_DIR) && $(PNPM) dev --port $(FRONTEND_PORT)) & \
		wait

dev-backend: env ## Start backend only (hot reload on :8000)
	@printf "$(CYAN)→ Backend at http://localhost:$(BACKEND_PORT)$(RESET)\n"
	@printf "  Docs: http://localhost:$(BACKEND_PORT)/docs\n\n"
	@cd $(BACKEND_DIR) && $(UV) run uvicorn $(PKG).main:app \
		--reload \
		--host $(BACKEND_HOST) \
		--port $(BACKEND_PORT)

dev-frontend: ## Start frontend only (hot reload on :3000)
	@printf "$(CYAN)→ Frontend at http://localhost:$(FRONTEND_PORT)$(RESET)\n\n"
	@cd $(FRONTEND_DIR) && $(PNPM) dev --port $(FRONTEND_PORT)

stop: ## Kill processes on backend (:8000) and frontend (:3000) ports
	@printf "$(CYAN)→ Killing processes on :$(BACKEND_PORT) and :$(FRONTEND_PORT)$(RESET)\n"
	@kill $$(lsof -ti :$(BACKEND_PORT)) 2>/dev/null && printf "  $(GREEN)✓$(RESET) Backend stopped (:$(BACKEND_PORT))\n" || printf "  → Nothing running on :$(BACKEND_PORT)\n"
	@kill $$(lsof -ti :$(FRONTEND_PORT)) 2>/dev/null && printf "  $(GREEN)✓$(RESET) Frontend stopped (:$(FRONTEND_PORT))\n" || printf "  → Nothing running on :$(FRONTEND_PORT)\n"

demo: ## Start in DEMO_MODE=true (no API key, pre-generated data)
	@printf "$(CYAN)$(BOLD)→ Confidence Map — DEMO MODE$(RESET) (no API key)\n"
	@printf "  Backend:  $(CYAN)http://localhost:$(BACKEND_PORT)$(RESET)\n"
	@printf "  Frontend: $(CYAN)http://localhost:$(FRONTEND_PORT)$(RESET)\n\n"
	@trap 'kill 0' INT; \
		(cd $(BACKEND_DIR) && DEMO_MODE=true $(UV) run uvicorn $(PKG).main:app \
			--reload \
			--host $(BACKEND_HOST) \
			--port $(BACKEND_PORT)) & \
		(cd $(FRONTEND_DIR) && $(PNPM) dev --port $(FRONTEND_PORT)) & \
		wait

# ==============================================================================
# TESTS
# ==============================================================================

test: ## Run all tests with coverage (≥80% required)
	@printf "$(CYAN)→ Running tests...$(RESET)\n\n"
	@cd $(BACKEND_DIR) && ANTHROPIC_API_KEY=$(TEST_API_KEY) $(UV) run pytest

test-unit: ## Run unit tests only
	@printf "$(CYAN)→ Unit tests$(RESET)\n\n"
	@cd $(BACKEND_DIR) && ANTHROPIC_API_KEY=$(TEST_API_KEY) $(UV) run pytest tests/unit/ -v

test-integration: ## Run integration tests only
	@printf "$(CYAN)→ Integration tests$(RESET)\n\n"
	@cd $(BACKEND_DIR) && ANTHROPIC_API_KEY=$(TEST_API_KEY) $(UV) run pytest tests/integration/ -v

test-fast: ## Run tests without coverage (faster)
	@cd $(BACKEND_DIR) && ANTHROPIC_API_KEY=$(TEST_API_KEY) $(UV) run pytest \
		--no-cov --no-header -q

eval: ## Run golden spec evaluations — requires ANTHROPIC_API_KEY (calls real API)
	@if [ -z "$(ANTHROPIC_API_KEY)" ]; then \
		printf "$(RED)✗ ANTHROPIC_API_KEY is required for evals$(RESET)\n"; \
		printf "  Usage: $(CYAN)ANTHROPIC_API_KEY=sk-ant-... make eval$(RESET)\n"; \
		exit 1; \
	fi
	@printf "$(CYAN)→ Running golden spec eval suite...$(RESET)\n"
	@cd $(BACKEND_DIR) && ANTHROPIC_API_KEY=$(ANTHROPIC_API_KEY) $(UV) run python -m evals

test-coverage: ## Show HTML coverage report
	@cd $(BACKEND_DIR) && ANTHROPIC_API_KEY=$(TEST_API_KEY) $(UV) run pytest \
		--cov-report=html
	@printf "$(GREEN)✓ Report at $(BACKEND_DIR)/htmlcov/index.html$(RESET)\n"

# ==============================================================================
# CODE QUALITY
# ==============================================================================

lint: ## Lint backend with ruff
	@printf "$(CYAN)→ ruff check$(RESET)\n"
	@cd $(BACKEND_DIR) && $(UV) run ruff check $(PKG)/

format: ## Format backend with ruff (includes import auto-fix)
	@printf "$(CYAN)→ ruff format + fix$(RESET)\n"
	@cd $(BACKEND_DIR) && $(UV) run ruff format $(PKG)/ && \
		$(UV) run ruff check --fix $(PKG)/
	@printf "$(GREEN)✓ Code formatted$(RESET)\n"

typecheck-backend: ## Type-check backend with mypy --strict
	@printf "$(CYAN)→ mypy --strict$(RESET)\n"
	@cd $(BACKEND_DIR) && $(UV) run mypy --strict $(PKG)/

typecheck-frontend: ## Type-check frontend with tsc --noEmit
	@printf "$(CYAN)→ tsc --noEmit$(RESET)\n"
	@cd $(FRONTEND_DIR) && $(PNPM) exec tsc --noEmit

typecheck: typecheck-backend typecheck-frontend ## Type-check backend and frontend

check: ## Full quality gates: lint → types → tests (fails on first error)
	@printf "$(CYAN)$(BOLD)→ Quality gates$(RESET)\n\n"
	@$(MAKE) lint
	@$(MAKE) typecheck
	@$(MAKE) test
	@printf "\n$(GREEN)$(BOLD)✓ All quality gates passed$(RESET)\n"

# ==============================================================================
# BUILD AND UTILITIES
# ==============================================================================

build: ## Production build of the frontend
	@printf "$(CYAN)→ next build$(RESET)\n"
	@cd $(FRONTEND_DIR) && $(PNPM) build

health: ## Check that the backend responds on :8000
	@printf "$(CYAN)→ GET http://localhost:$(BACKEND_PORT)/health$(RESET)\n"
	@$(CURL) -sf http://localhost:$(BACKEND_PORT)/health | $(PYTHON) -m json.tool && \
		printf "$(GREEN)✓ Backend healthy$(RESET)\n" || \
		printf "$(RED)✗ Backend not responding on :$(BACKEND_PORT) — is it running? (make dev-backend)$(RESET)\n"

venv-info: ## Show Python virtual environment info
	@printf "$(CYAN)→ Python virtual environment (managed by uv)$(RESET)\n"
	@cd $(BACKEND_DIR) && $(UV) run python --version
	@cd $(BACKEND_DIR) && $(UV) run python -c "import sys; print('  Path:', sys.executable)"
	@cd $(BACKEND_DIR) && $(UV) pip list 2>/dev/null | head -20

# ==============================================================================
# CLEANUP
# ==============================================================================

clean-backend: ## Clean Python caches (__pycache__, .pytest_cache, etc.)
	@printf "$(CYAN)→ Cleaning backend$(RESET)\n"
	@find $(BACKEND_DIR) -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@find $(BACKEND_DIR) -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	@find $(BACKEND_DIR) -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
	@find $(BACKEND_DIR) -type d -name .ruff_cache -exec rm -rf {} + 2>/dev/null || true
	@find $(BACKEND_DIR) -type d -name htmlcov -exec rm -rf {} + 2>/dev/null || true
	@rm -f $(BACKEND_DIR)/.coverage $(BACKEND_DIR)/coverage.xml

clean-frontend: ## Clean .next and node_modules
	@printf "$(CYAN)→ Cleaning frontend$(RESET)\n"
	@rm -rf $(FRONTEND_DIR)/.next
	@rm -rf $(FRONTEND_DIR)/node_modules

clean: clean-backend ## Clean caches (without removing node_modules)
	@rm -rf $(FRONTEND_DIR)/.next
	@printf "$(GREEN)✓ Cleanup complete$(RESET)\n"

clean-all: clean-backend clean-frontend ## Full cleanup (includes node_modules — requires reinstall)
	@printf "$(GREEN)✓ Full cleanup complete. Run $(CYAN)make install$(RESET)$(GREEN) to reinstall$(RESET)\n"

# ==============================================================================
# HELP
# ==============================================================================

help: ## Show this help
	@printf "\n$(BOLD)Confidence Map$(RESET) — Available commands\n"
	@printf "=========================================\n\n"
	@printf "$(BOLD)Quick start:$(RESET)\n"
	@printf "  $(CYAN)make setup$(RESET)   → First time: verify tools, create .env, install everything\n"
	@printf "  $(CYAN)make dev$(RESET)     → Start backend (:8000) + frontend (:3000)\n"
	@printf "  $(CYAN)make demo$(RESET)    → Same as dev but forces DEMO_MODE=true\n"
	@printf "  $(CYAN)make check$(RESET)   → Quality gates: lint + types + tests\n"
	@printf "\n$(BOLD)All commands:$(RESET)\n"
	@awk 'BEGIN {FS = ":.*##"} /^[a-zA-Z_-]+:.*##/ { printf "  $(CYAN)%-22s$(RESET) %s\n", $$1, $$2 }' $(MAKEFILE_LIST)
	@printf "\n$(BOLD)Configurable variables:$(RESET)\n"
	@printf "  $(CYAN)BACKEND_PORT$(RESET)=$(BACKEND_PORT)    Backend port (default: 8000)\n"
	@printf "  $(CYAN)FRONTEND_PORT$(RESET)=$(FRONTEND_PORT)   Frontend port (default: 3000)\n"
	@printf "  $(CYAN)NPM_REGISTRY$(RESET)=$(NPM_REGISTRY)\n"
	@printf "\n  Example: $(CYAN)make dev BACKEND_PORT=9000$(RESET)\n\n"
