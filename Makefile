# ==============================================================================
# Confidence Map — Makefile
# Gestión centralizada del proyecto: setup, desarrollo, tests y calidad.
#
# Uso rápido:
#   make setup   → primera vez (crea .env + instala todo)
#   make dev     → levanta backend + frontend
#   make test    → ejecuta los 42 tests
#   make check   → quality gates completos (lint + tipos + tests)
#   make help    → lista todos los comandos disponibles
# ==============================================================================

# ── Herramientas ───────────────────────────────────────────────────────────────
UV           := uv
PNPM         := pnpm
PYTHON       := python3
CURL         := curl

# ── Directorios ───────────────────────────────────────────────────────────────
BACKEND_DIR  := backend
FRONTEND_DIR := frontend
PKG          := confidence_map

# ── Servidor ──────────────────────────────────────────────────────────────────
BACKEND_HOST := 0.0.0.0
BACKEND_PORT := 8000
FRONTEND_PORT := 3000

# ── Registry npm/pnpm (evita registries privados en la red) ───────────────────
NPM_REGISTRY := https://registry.npmjs.org

# ── API key para tests (no llama a la API real) ───────────────────────────────
TEST_API_KEY := test

# ── Colores para output ────────────────────────────────────────────────────────
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
        check health build \
        clean clean-backend clean-frontend clean-all \
        venv-info prereqs help

# ==============================================================================
# SETUP — Primera vez
# ==============================================================================

setup: prereqs env install ## [INICIO] Setup completo: verifica tools + crea .env + instala deps
	@printf "$(GREEN)$(BOLD)\n✓ Proyecto listo.$(RESET)\n"
	@printf "  Próximo paso: $(CYAN)make dev$(RESET)\n\n"

prereqs: ## Verificar que uv, pnpm y python3 están instalados
	@printf "$(CYAN)→ Verificando herramientas...$(RESET)\n"
	@command -v $(UV)     >/dev/null 2>&1 || { printf "$(RED)✗ uv no encontrado.$(RESET) Instalar: curl -LsSf https://astral.sh/uv/install.sh | sh\n"; exit 1; }
	@command -v $(PNPM)   >/dev/null 2>&1 || { printf "$(RED)✗ pnpm no encontrado.$(RESET) Instalar: npm install -g pnpm\n"; exit 1; }
	@command -v $(PYTHON) >/dev/null 2>&1 || { printf "$(RED)✗ python3 no encontrado.$(RESET) Requiere Python 3.12+\n"; exit 1; }
	@$(PYTHON) -c "import sys; assert sys.version_info >= (3,12), 'Python 3.12+ requerido'" 2>/dev/null || \
		{ printf "$(RED)✗ Python 3.12+ requerido$(RESET) (actual: $$($(PYTHON) --version))\n"; exit 1; }
	@printf "  $(GREEN)✓$(RESET) uv     $$($(UV) --version)\n"
	@printf "  $(GREEN)✓$(RESET) pnpm   $$($(PNPM) --version)\n"
	@printf "  $(GREEN)✓$(RESET) python $$($(PYTHON) --version)\n"

env: ## Crear backend/.env desde .env.example si no existe
	@if [ ! -f $(BACKEND_DIR)/.env ]; then \
		cp $(BACKEND_DIR)/.env.example $(BACKEND_DIR)/.env; \
		printf "$(GREEN)✓$(RESET) Creado $(BACKEND_DIR)/.env\n"; \
		printf "  $(YELLOW)→ Edita ANTHROPIC_API_KEY si usas DEMO_MODE=false$(RESET)\n"; \
	else \
		printf "  → $(BACKEND_DIR)/.env ya existe (sin cambios)\n"; \
	fi

# ==============================================================================
# INSTALACIÓN DE DEPENDENCIAS
# ==============================================================================

install: install-backend install-frontend ## Instalar todas las dependencias (backend + frontend)
	@printf "$(GREEN)✓ Dependencias instaladas$(RESET)\n"

install-backend: ## Instalar dependencias Python con uv sync
	@printf "$(CYAN)→ Backend: uv sync$(RESET)\n"
	@cd $(BACKEND_DIR) && $(UV) sync

install-frontend: ## Instalar dependencias Node.js con pnpm
	@printf "$(CYAN)→ Frontend: pnpm install$(RESET)\n"
	@cd $(FRONTEND_DIR) && $(PNPM) install --registry $(NPM_REGISTRY)

# ==============================================================================
# DESARROLLO — Levantar servicios
# ==============================================================================

dev: env ## Levantar backend + frontend en paralelo (Ctrl+C para detener ambos)
	@printf "$(CYAN)$(BOLD)→ Iniciando Confidence Map$(RESET)\n"
	@printf "  Backend:  $(CYAN)http://localhost:$(BACKEND_PORT)$(RESET)\n"
	@printf "  Frontend: $(CYAN)http://localhost:$(FRONTEND_PORT)$(RESET)\n"
	@printf "  Health:   $(CYAN)http://localhost:$(BACKEND_PORT)/health$(RESET)\n"
	@printf "  $(YELLOW)Ctrl+C detiene ambos servicios$(RESET)\n\n"
	@trap 'kill 0' INT; \
		(cd $(BACKEND_DIR) && $(UV) run uvicorn $(PKG).main:app \
			--reload \
			--host $(BACKEND_HOST) \
			--port $(BACKEND_PORT)) & \
		(cd $(FRONTEND_DIR) && $(PNPM) dev --port $(FRONTEND_PORT)) & \
		wait

dev-backend: env ## Levantar solo el backend (hot reload en :8000)
	@printf "$(CYAN)→ Backend en http://localhost:$(BACKEND_PORT)$(RESET)\n"
	@printf "  Docs: http://localhost:$(BACKEND_PORT)/docs\n\n"
	@cd $(BACKEND_DIR) && $(UV) run uvicorn $(PKG).main:app \
		--reload \
		--host $(BACKEND_HOST) \
		--port $(BACKEND_PORT)

dev-frontend: ## Levantar solo el frontend (hot reload en :3000)
	@printf "$(CYAN)→ Frontend en http://localhost:$(FRONTEND_PORT)$(RESET)\n\n"
	@cd $(FRONTEND_DIR) && $(PNPM) dev --port $(FRONTEND_PORT)

demo: ## Levantar en DEMO_MODE=true (sin API key, datos pre-generados)
	@printf "$(CYAN)$(BOLD)→ Confidence Map — MODO DEMO$(RESET) (sin API key)\n"
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

test: ## Ejecutar todos los tests con cobertura (≥80% requerido)
	@printf "$(CYAN)→ Ejecutando 42 tests...$(RESET)\n\n"
	@cd $(BACKEND_DIR) && ANTHROPIC_API_KEY=$(TEST_API_KEY) $(UV) run pytest

test-unit: ## Ejecutar solo tests unitarios
	@printf "$(CYAN)→ Tests unitarios$(RESET)\n\n"
	@cd $(BACKEND_DIR) && ANTHROPIC_API_KEY=$(TEST_API_KEY) $(UV) run pytest tests/unit/ -v

test-integration: ## Ejecutar solo tests de integración
	@printf "$(CYAN)→ Tests de integración$(RESET)\n\n"
	@cd $(BACKEND_DIR) && ANTHROPIC_API_KEY=$(TEST_API_KEY) $(UV) run pytest tests/integration/ -v

test-fast: ## Ejecutar tests sin cobertura (más rápido)
	@cd $(BACKEND_DIR) && ANTHROPIC_API_KEY=$(TEST_API_KEY) $(UV) run pytest \
		--no-cov --no-header -q

test-coverage: ## Mostrar reporte de cobertura HTML
	@cd $(BACKEND_DIR) && ANTHROPIC_API_KEY=$(TEST_API_KEY) $(UV) run pytest \
		--cov-report=html
	@printf "$(GREEN)✓ Reporte en $(BACKEND_DIR)/htmlcov/index.html$(RESET)\n"

# ==============================================================================
# CALIDAD DE CÓDIGO
# ==============================================================================

lint: ## Linting del backend con ruff
	@printf "$(CYAN)→ ruff check$(RESET)\n"
	@cd $(BACKEND_DIR) && $(UV) run ruff check $(PKG)/

format: ## Formatear backend con ruff (incluye auto-fix de imports)
	@printf "$(CYAN)→ ruff format + fix$(RESET)\n"
	@cd $(BACKEND_DIR) && $(UV) run ruff format $(PKG)/ && \
		$(UV) run ruff check --fix $(PKG)/
	@printf "$(GREEN)✓ Código formateado$(RESET)\n"

typecheck-backend: ## Verificar tipos en backend con mypy --strict
	@printf "$(CYAN)→ mypy --strict$(RESET)\n"
	@cd $(BACKEND_DIR) && $(UV) run mypy --strict $(PKG)/

typecheck-frontend: ## Verificar tipos en frontend con tsc --noEmit
	@printf "$(CYAN)→ tsc --noEmit$(RESET)\n"
	@cd $(FRONTEND_DIR) && $(PNPM) exec tsc --noEmit

typecheck: typecheck-backend typecheck-frontend ## Verificar tipos en backend y frontend

check: ## Quality gates completos: lint → tipos → tests (falla en el primero que rompa)
	@printf "$(CYAN)$(BOLD)→ Quality gates$(RESET)\n\n"
	@$(MAKE) lint
	@$(MAKE) typecheck
	@$(MAKE) test
	@printf "\n$(GREEN)$(BOLD)✓ Todos los quality gates pasaron$(RESET)\n"

# ==============================================================================
# BUILD Y UTILIDADES
# ==============================================================================

build: ## Build de producción del frontend
	@printf "$(CYAN)→ next build$(RESET)\n"
	@cd $(FRONTEND_DIR) && $(PNPM) build

health: ## Verificar que el backend responde en :8000
	@printf "$(CYAN)→ GET http://localhost:$(BACKEND_PORT)/health$(RESET)\n"
	@$(CURL) -sf http://localhost:$(BACKEND_PORT)/health | $(PYTHON) -m json.tool && \
		printf "$(GREEN)✓ Backend saludable$(RESET)\n" || \
		printf "$(RED)✗ Backend no responde en :$(BACKEND_PORT) — ¿está corriendo? (make dev-backend)$(RESET)\n"

venv-info: ## Mostrar información del entorno virtual Python
	@printf "$(CYAN)→ Entorno virtual Python (gestionado por uv)$(RESET)\n"
	@cd $(BACKEND_DIR) && $(UV) run python --version
	@cd $(BACKEND_DIR) && $(UV) run python -c "import sys; print('  Ruta:', sys.executable)"
	@cd $(BACKEND_DIR) && $(UV) pip list 2>/dev/null | head -20

# ==============================================================================
# LIMPIEZA
# ==============================================================================

clean-backend: ## Limpiar caches de Python (__pycache__, .pytest_cache, etc.)
	@printf "$(CYAN)→ Limpiando backend$(RESET)\n"
	@find $(BACKEND_DIR) -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@find $(BACKEND_DIR) -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	@find $(BACKEND_DIR) -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
	@find $(BACKEND_DIR) -type d -name .ruff_cache -exec rm -rf {} + 2>/dev/null || true
	@find $(BACKEND_DIR) -type d -name htmlcov -exec rm -rf {} + 2>/dev/null || true
	@rm -f $(BACKEND_DIR)/.coverage $(BACKEND_DIR)/coverage.xml

clean-frontend: ## Limpiar .next y node_modules
	@printf "$(CYAN)→ Limpiando frontend$(RESET)\n"
	@rm -rf $(FRONTEND_DIR)/.next
	@rm -rf $(FRONTEND_DIR)/node_modules

clean: clean-backend ## Limpiar caches (sin borrar node_modules)
	@rm -rf $(FRONTEND_DIR)/.next
	@printf "$(GREEN)✓ Limpieza completada$(RESET)\n"

clean-all: clean-backend clean-frontend ## Limpieza total (incluye node_modules — requiere reinstalar)
	@printf "$(GREEN)✓ Limpieza total completada. Ejecuta $(CYAN)make install$(RESET)$(GREEN) para reinstalar$(RESET)\n"

# ==============================================================================
# AYUDA
# ==============================================================================

help: ## Mostrar esta ayuda
	@printf "\n$(BOLD)Confidence Map$(RESET) — Comandos disponibles\n"
	@printf "=========================================\n\n"
	@printf "$(BOLD)Flujo de inicio rápido:$(RESET)\n"
	@printf "  $(CYAN)make setup$(RESET)   → Primera vez: verifica tools, crea .env, instala todo\n"
	@printf "  $(CYAN)make dev$(RESET)     → Levanta backend (:8000) + frontend (:3000)\n"
	@printf "  $(CYAN)make demo$(RESET)    → Igual que dev pero fuerza DEMO_MODE=true\n"
	@printf "  $(CYAN)make check$(RESET)   → Quality gates: lint + tipos + tests\n"
	@printf "\n$(BOLD)Todos los comandos:$(RESET)\n"
	@awk 'BEGIN {FS = ":.*##"} /^[a-zA-Z_-]+:.*##/ { printf "  $(CYAN)%-22s$(RESET) %s\n", $$1, $$2 }' $(MAKEFILE_LIST)
	@printf "\n$(BOLD)Variables configurables:$(RESET)\n"
	@printf "  $(CYAN)BACKEND_PORT$(RESET)=$(BACKEND_PORT)    Puerto del backend (default: 8000)\n"
	@printf "  $(CYAN)FRONTEND_PORT$(RESET)=$(FRONTEND_PORT)   Puerto del frontend (default: 3000)\n"
	@printf "  $(CYAN)NPM_REGISTRY$(RESET)=$(NPM_REGISTRY)\n"
	@printf "\n  Ejemplo: $(CYAN)make dev BACKEND_PORT=9000$(RESET)\n\n"
