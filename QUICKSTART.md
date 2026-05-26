# Guía de inicio rápido — Confidence Map

Esta guía lleva el proyecto desde cero hasta funcionando en menos de 10 minutos.

---

## Requisitos previos

Instala estas herramientas antes de comenzar:

| Herramienta | Versión mínima | Verificar |
|-------------|---------------|-----------|
| Python | 3.12+ | `python3 --version` |
| uv | 0.11+ | `uv --version` |
| Node.js | 20+ | `node --version` |
| pnpm | 8+ | `pnpm --version` |

### Instalar uv (si no lo tienes)
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Instalar pnpm (si no lo tienes)
```bash
npm install -g pnpm
```

---

## Paso 1 — Obtener una API key de Anthropic

1. Ir a [console.anthropic.com](https://console.anthropic.com)
2. Crear una cuenta o iniciar sesión
3. Ir a **API Keys** → **Create Key**
4. Copiar la key (comienza con `sk-ant-...`)

> **Limitaciones con la API key:**
> - El plan gratuito tiene límites de uso. Para el hackathon recomendamos el plan de pago mínimo (~$5 USD).
> - En desarrollo, usar el modelo `claude-haiku-4-5-20251001` que es ~20x más barato que Sonnet.
> - El **modo demo** (`DEMO_MODE=true`) no consume créditos — usa resultados pre-generados.

---

## Paso 2 — Configurar el backend

```bash
cd backend
```

### 2.1 Crear archivo de configuración

```bash
cp .env.example .env
```

### 2.2 Editar `.env`

```env
# Modo demo: true = sin API key ($0), false = Claude API real
DEMO_MODE=true

# Solo requerida cuando DEMO_MODE=false
ANTHROPIC_API_KEY=sk-ant-api03-xxxxxxxxxxxxxxxxxx

# Modelo a usar (cambiar a haiku para reducir costos)
MODEL=claude-sonnet-4-6

# URL del frontend (para CORS)
FRONTEND_URL=http://localhost:3000
```

### 2.3 Instalar dependencias

```bash
uv sync
```

### 2.4 Verificar instalación

```bash
ANTHROPIC_API_KEY=test uv run pytest --no-header -q
# Esperado: 42 passed, cobertura ≥80%
```

### 2.5 Arrancar el servidor

```bash
uv run uvicorn confidence_map.main:app --reload
```

Verificar: `http://localhost:8000/health` debe responder `{"status":"ok","version":"0.1.0"}`

---

## Paso 3 — Configurar el frontend

Abrir una nueva terminal:

```bash
cd frontend
```

### 3.1 Instalar dependencias

```bash
pnpm install --registry https://registry.npmjs.org
```

> Si tienes un registry privado configurado en tu sistema (Artifactory, Nexus, etc.), el flag `--registry` es necesario para instalar desde el registry público.

### 3.2 Arrancar el servidor

```bash
pnpm dev
```

Verificar: abrir `http://localhost:3000` en el navegador.

---

## Paso 4 — Ejecutar el demo

1. Abrir `http://localhost:3000`
2. Hacer clic en **"NovaBank · Pagos"** o **"NovaBank · Auth MFA"** para cargar un spec de ejemplo
3. Hacer clic en **"Run Analysis"**
4. Observar cómo los 6 agentes se activan en tiempo real en el mapa

Con `DEMO_MODE=true`, el análisis completo toma aproximadamente **5 segundos**.
Con la API real, toma entre **60–120 segundos** (6 agentes × ~20s con paralelismo).

---

## Variables de entorno — referencia completa

### Backend (`backend/.env`)

| Variable | Requerida | Valor por defecto | Descripción |
|----------|-----------|-------------------|-------------|
| `DEMO_MODE` | No | `false` | `true` = resultados pre-generados sin API |
| `ANTHROPIC_API_KEY` | Solo si `DEMO_MODE=false` | — | API key de Anthropic |
| `MODEL` | No | `claude-sonnet-4-6` | Modelo Claude a usar |
| `FRONTEND_URL` | No | `http://localhost:3000` | Origen permitido en CORS |

### Modelos disponibles y costos relativos

| Modelo | Velocidad | Costo relativo | Recomendado para |
|--------|-----------|---------------|------------------|
| `claude-haiku-4-5-20251001` | Rápido | Bajo (~1x) | Desarrollo y pruebas |
| `claude-sonnet-4-6` | Medio | Medio (~5x) | Demo y producción |

### Frontend

El frontend no requiere variables de entorno en desarrollo local. El proxy `next.config.ts` redirige `/api/*` → `localhost:8000` automáticamente.

---

## Secrets a configurar

| Secret | Dónde configurar | Ejemplo |
|--------|-----------------|---------|
| `ANTHROPIC_API_KEY` | `backend/.env` (local) | `sk-ant-api03-...` |
| `ANTHROPIC_API_KEY` | Variable de entorno del servidor (producción) | — |

**Nunca commitear `.env` al repositorio.** El archivo está en `.gitignore`.

Para CI/CD o despliegue en la nube, configurar `ANTHROPIC_API_KEY` como secret en:
- GitHub Actions: Settings → Secrets and variables → Actions
- Vercel/Railway/Render: Variables de entorno en el dashboard

---

## Reducir consumo de API key

### Opción 1: Modo demo con datos pre-generados (recomendado)
```env
DEMO_MODE=true
```
El análisis usa resultados pre-generados realistas — $0 de costo.

### Opción 2: Usar Haiku en `.env`
```env
DEMO_MODE=false
MODEL=claude-haiku-4-5-20251001
```

### Opción 3: Mockear la API en tests
Los tests usan mocks y nunca llaman a la API real:
```bash
ANTHROPIC_API_KEY=test uv run pytest
```

---

## Verificar que todo funciona

```bash
# Terminal 1: backend
cd backend && uv run uvicorn confidence_map.main:app --reload

# Terminal 2: frontend
cd frontend && pnpm dev

# Terminal 3: verificar health
curl http://localhost:8000/health
# → {"status":"ok","version":"0.1.0"}
```

Abrir `http://localhost:3000`, cargar un preset, ejecutar análisis.

---

## Troubleshooting

### Error: `ANTHROPIC_API_KEY` no configurada
```
pydantic_settings.main.SettingsError: field required
```
Solución: crear `backend/.env` con `DEMO_MODE=true` (o agregar la key).

### Error: `Connection refused` al hacer análisis
El backend no está corriendo. Ejecutar:
```bash
cd backend && uv run uvicorn confidence_map.main:app --reload
```

### Error: `pnpm install` falla con 401
Registry privado detectado. Usar:
```bash
pnpm install --registry https://registry.npmjs.org
```

### El análisis tarda demasiado
Cambiar a modo demo en `backend/.env`:
```env
DEMO_MODE=true
```
O usar Haiku:
```env
MODEL=claude-haiku-4-5-20251001
```

### Tests fallan con error de importación
```bash
cd backend && uv sync
```

---

## Comandos de referencia rápida

```bash
# Instalar todo
cd backend && uv sync
cd frontend && pnpm install --registry https://registry.npmjs.org

# Arrancar (2 terminales)
cd backend && uv run uvicorn confidence_map.main:app --reload
cd frontend && pnpm dev

# Tests
cd backend && ANTHROPIC_API_KEY=test uv run pytest -q

# Quality gates
cd backend && uv run mypy --strict confidence_map/ && uv run ruff check confidence_map/
cd frontend && pnpm exec tsc --noEmit
```
