# Spec-to-Data Pipelines
## Diagrama de arquitectura — Confidence Map

---

## Por que se implemento

Las especificaciones de software (PRDs, historias de usuario, documentos de arquitectura) son texto
no estructurado. Los equipos las leen, las interpretan, y toman decisiones — pero ese proceso es
invisible, no trazable, y no comparable entre proyectos.

El desafio de **Spec-to-Data Pipelines** consiste en transformar ese texto en bruto en datos
estructurados, accionables y consultables: hallazgos con tipo, nivel de confianza, evidencia,
supuestos, y acciones recomendadas.

Sin esta transformacion, la IA solo puede "hablar sobre" la especificacion. Con ella, puede
razonar sobre ella, cuantificarla y hacerla visible para todo el equipo.

---

## Como es aplicado en el proyecto

### 1. Input: texto no estructurado

El usuario ingresa hasta tres tipos de texto:
- **PRD / Spec**: requisitos funcionales, historias de usuario, criterios de aceptacion
- **Architecture notes**: decisiones tecnicas, patrones elegidos, dependencias
- **Context**: restricciones regulatorias, SLAs, integraciones externas

### 2. Transformacion: Claude tool use con schema Pydantic

Cada agente recibe el texto y usa la herramienta `report_findings` con un JSON Schema estricto:

```json
{
  "title":             "string (max 100 chars)",
  "description":       "string",
  "confidence":        "green | yellow | red",
  "confidence_score":  "float 0.0-1.0",
  "evidence":          "cita exacta de la spec",
  "assumptions":       ["lista de supuestos"],
  "needs_validation":  ["lista de preguntas abiertas"],
  "recommended_action":"siguiente paso concreto",
  "category":          "ambiguity | contradiction | risk | gap | accessibility | cost | pattern"
}
```

### 3. Output: datos estructurados con trazabilidad completa

Cada hallazgo es un objeto Pydantic validado con:
- Nivel de confianza semantico (verde/amarillo/rojo) + score numerico (0.0-1.0)
- Evidencia: cita textual de la especificacion original
- Supuestos explicitos que el agente esta haciendo
- Preguntas abiertas que el equipo debe validar
- Accion recomendada concreta

### 4. Distribucion y score global

El orquestador agrega todos los hallazgos y calcula:
- Distribucion: cuantos verdes, amarillos, rojos
- Score global de confianza: promedio ponderado de todos los confidence_scores
- Ese numero aparece en el hub central del mapa visual

---

## Diagrama

```mermaid
%%{init: {'theme': 'dark', 'themeVariables': {
  'primaryColor': '#1e293b', 'primaryTextColor': '#f1f5f9',
  'primaryBorderColor': '#3b82f6', 'lineColor': '#475569',
  'clusterBkg': '#0f172a', 'clusterBorder': '#334155',
  'fontFamily': 'Segoe UI, system-ui, sans-serif'
}}}%%
flowchart LR
  classDef input   fill:#1d3461,stroke:#3b82f6,color:#bfdbfe
  classDef agent   fill:#14532d,stroke:#22c55e,color:#86efac
  classDef tool    fill:#312e81,stroke:#818cf8,color:#c7d2fe
  classDef valid   fill:#78350f,stroke:#f59e0b,color:#fde68a
  classDef output  fill:#3b0764,stroke:#a855f7,color:#e9d5ff
  classDef consume fill:#1e293b,stroke:#475569,color:#94a3b8

  subgraph IN["  INPUT — Texto no estructurado  "]
    A1["📄 PRD / User Stories"]:::input
    A2["🏗️ Architecture Notes"]:::input
    A3["🌐 Context / Constraints"]:::input
  end

  subgraph PHASE1["  FASE 1  "]
    B1["🔍 Spec Analyst\n(sequential)"]:::agent
  end

  subgraph PHASE2["  FASE 2 — Paralelo  "]
    B2["🏛️ Arch Validator"]:::agent
    B3["🛡️ Risk Intelligence"]:::agent
    B4["💼 Business Impact"]:::agent
    B5["♿ Accessibility"]:::agent
    B6["📚 Delivery Historian"]:::agent
  end

  subgraph TOOL["  Claude Tool Use  "]
    C1["🔧 report_findings\nJSON Schema estricto"]:::tool
    C2["✅ Pydantic v2\n+ guardrails"]:::valid
  end

  subgraph OUT["  OUTPUT  "]
    D1["🟢🟡🔴 Finding\nconfianza · score · evidencia"]:::output
    D2["📦 AgentResult\nfindings + summary"]:::output
    D3["📊 Score global\n+ distribución"]:::output
  end

  subgraph CONSUME["  Consumo Frontend  "]
    E1["🗺️ Mapa visual"]:::consume
    E2["📋 Decision Table"]:::consume
    E3["📄 Export PDF"]:::consume
    E4["🎫 Backlog Jira"]:::consume
    E5["💬 AI Chat"]:::consume
  end

  A1 & A2 & A3 --> B1
  B1 -->|blackboard| B2 & B3 & B4 & B5 & B6
  B1 & B2 & B3 & B4 & B5 & B6 --> C1
  C1 --> C2 --> D1 --> D2 --> D3
  D2 --> E1 & E2 & E3 & E4 & E5
```

---

## Archivos clave en el proyecto

| Archivo | Rol en el pipeline |
|---------|-------------------|
| `backend/confidence_map/models/findings.py` | Schema Pydantic de Finding y AgentResult |
| `backend/confidence_map/agents/base.py` | `REPORT_FINDINGS_TOOL` — JSON Schema para Claude tool use |
| `backend/confidence_map/agents/base.py` | `_apply_guardrails()` — validacion post-extraccion |
| `backend/confidence_map/core/orchestrator.py` | Agregacion de findings y calculo del score global |
| `frontend/types/index.ts` | Tipos TypeScript que consumen el output del pipeline |
