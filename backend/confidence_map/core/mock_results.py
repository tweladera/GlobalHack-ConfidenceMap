"""Pre-generated mock results for the NovaBank demo case.

Used when DEMO_MODE=true. Simulates realistic agent outputs without API calls.
Findings are based on the NovaBank international payments spec.
"""

from __future__ import annotations

from confidence_map.models.findings import AgentResult, AgentStatus, ConfidenceLevel, Finding

# Simulated agent completion times (seconds) — realistic but fast for demo
AGENT_DELAYS: dict[str, float] = {
    "spec_analyst": 2.5,
    "arch_validator": 3.2,
    "risk_intelligence": 2.8,
    "business_impact": 2.2,
    "accessibility_advocate": 2.6,
    "delivery_historian": 2.1,
}


def get_mock_results() -> dict[str, AgentResult]:
    """Return pre-generated AgentResult for each agent keyed by agent_id."""
    return {
        "spec_analyst": _spec_analyst(),
        "arch_validator": _arch_validator(),
        "risk_intelligence": _risk_intelligence(),
        "business_impact": _business_impact(),
        "accessibility_advocate": _accessibility_advocate(),
        "delivery_historian": _delivery_historian(),
    }


# ── Helpers ───────────────────────────────────────────────────────────────────


def _f(
    *,
    title: str,
    description: str,
    confidence: str,
    score: float,
    evidence: str,
    assumptions: list[str],
    needs_validation: list[str],
    recommended_action: str = "",
    category: str,
    agent_id: str,
    agent_name: str,
) -> Finding:
    return Finding(
        title=title,
        description=description,
        confidence=ConfidenceLevel(confidence),
        confidence_score=score,
        evidence=evidence,
        assumptions=assumptions,
        needs_validation=needs_validation,
        recommended_action=recommended_action,
        category=category,
        agent_id=agent_id,
        agent_name=agent_name,
    )


def _result(agent_id: str, agent_name: str, agent_icon: str, findings: list[Finding], summary: str) -> AgentResult:
    return AgentResult(
        agent_id=agent_id,
        agent_name=agent_name,
        agent_icon=agent_icon,
        status=AgentStatus.COMPLETED,
        findings=findings,
        summary=summary,
    )


# ── Agent 1: Spec Analyst ─────────────────────────────────────────────────────


def _spec_analyst() -> AgentResult:
    aid, aname = "spec_analyst", "Spec Analyst"
    findings = [
        _f(
            title="Comportamiento ante timeout del CoreBanking no definido",
            description=(
                "El spec no define qué ocurre cuando el gateway CoreBanking tarda más de 10 segundos. "
                "Sin este comportamiento definido, un retry automático generaría pagos duplicados — "
                "el riesgo más crítico en un sistema de pagos."
            ),
            confidence="red",
            score=0.08,
            evidence="'El pago debe completarse dentro del SLA regulatorio' — no se define qué pasa si no lo hace.",
            assumptions=[],
            needs_validation=[
                "¿Cuál es el comportamiento cuando CoreBanking supera el SLA?",
                "¿El sistema reintenta o cancela la transacción?",
                "¿Cómo se informa al usuario de una transacción en estado indefinido?",
            ],
            recommended_action=(
                "Organizar una sesión de refinamiento con Sofia y Daniel para definir "
                "el comportamiento de timeout: ¿cancelar, reintentar con idempotencia, "
                "o marcar como 'pending' para reconciliación manual?"
            ),
            category="ambiguity",
            agent_id=aid,
            agent_name=aname,
        ),
        _f(
            title="US-003: 'Qué hacer a continuación' no especificado",
            description=(
                "La historia de fallo dice 'el sistema debe indicar qué hacer a continuación' "
                "pero no define cuáles son esas acciones. ¿Reintentar? ¿Contactar soporte? "
                "¿El reintento es automático o manual? Sin esto, el equipo implementará "
                "comportamientos inconsistentes."
            ),
            confidence="red",
            score=0.15,
            evidence="'En caso de fallo, el sistema debe indicar qué hacer a continuación.'",
            assumptions=["'Fallo' incluye rechazo por antifraude y timeout de CoreBanking."],
            needs_validation=[
                "¿Cuáles son las acciones disponibles tras un fallo?",
                "¿El usuario puede reintentar inmediatamente o hay un período de espera?",
            ],
            recommended_action=(
                "Sofia debe redactar los criterios de aceptación de error específicos para US-003: "
                "listado de acciones disponibles (reintentar, contactar soporte, ver estado) "
                "con UX copy definido para cada caso."
            ),
            category="gap",
            agent_id=aid,
            agent_name=aname,
        ),
        _f(
            title="SLA regulatorio de 10 segundos ausente en criterios de aceptación",
            description=(
                "El valor de 10 segundos está mencionado en el contexto de negocio pero ninguna "
                "historia de usuario lo referencia explícitamente como criterio verificable. "
                "Sin este dato en los AC, QA no puede construir un test de aceptación para el SLA."
            ),
            confidence="yellow",
            score=0.42,
            evidence=(
                "'La regulación local exige confirmación de transacción en menos de 10 segundos.' "
                "— aparece en contexto, no en AC."
            ),
            assumptions=["El SLA aplica a todo el flujo de US-001, no solo a la respuesta de pantalla."],
            needs_validation=["¿El SLA de 10s aplica al tiempo total o al tiempo de respuesta del API?"],
            recommended_action=(
                "Agregar como criterio de aceptación explícito en US-001: "
                "'El sistema retorna confirmación o error al usuario en menos de 10 segundos desde el envío.' "
                "Esto convierte el SLA en un test automatizable por QA."
            ),
            category="gap",
            agent_id=aid,
            agent_name=aname,
        ),
        _f(
            title="US-002: Mecanismo de actualización automática contradice notas técnicas",
            description=(
                "Los criterios de US-002 dicen 'el estado se actualiza automáticamente sin refrescar la página', "
                "pero las notas técnicas especifican 'polling cada 3 segundos'. "
                "Polling no es actualización automática; es una simulación con latencia de hasta 3s. "
                "El criterio y la implementación propuesta son inconsistentes."
            ),
            confidence="yellow",
            score=0.38,
            evidence=(
                "AC: 'El estado se actualiza automáticamente sin refrescar la página.' "
                "Notas técnicas: 'React SPA con polling cada 3 segundos'."
            ),
            assumptions=[],
            needs_validation=["¿3 segundos de latencia máxima es aceptable para el usuario?"],
            recommended_action=(
                "Alinear con producto si el polling de 3s es aceptable para US-002. "
                "Si no lo es, habilitar WebSockets o SSE antes del inicio del sprint — "
                "retroalimentar el frontend después es 5x más costoso."
            ),
            category="contradiction",
            agent_id=aid,
            agent_name=aname,
        ),
        _f(
            title="Historial de transacciones: criterios de exportación incompletos",
            description=(
                "US-004 especifica exportación a CSV pero no define: qué campos se incluyen, "
                "si los datos sensibles (IBAN completo) se exportan o se enmascaran, "
                "y si hay límite de registros. En un contexto PCI-DSS, exportar datos de cuenta "
                "sin restricciones es un riesgo de compliance."
            ),
            confidence="yellow",
            score=0.35,
            evidence="'Exportación a CSV' — sin especificación de campos ni restricciones de seguridad.",
            assumptions=["El CSV es para uso interno de tesorería del cliente corporativo."],
            needs_validation=[
                "¿Se exportan datos sensibles (IBAN, SWIFT) completos o enmascarados?",
                "¿Existe un límite de registros por exportación?",
            ],
            recommended_action=(
                "Definir en US-004: exportar últimos 4 dígitos de IBAN/SWIFT enmascarados, "
                "límite de 10.000 registros por exportación, y revisar con Legal "
                "si el CSV requiere controles adicionales bajo PCI-DSS."
            ),
            category="gap",
            agent_id=aid,
            agent_name=aname,
        ),
    ]
    return _result(
        aid, aname, "FileSearch", findings,
        "El análisis del spec de NovaBank revela cinco problemas críticos. El más urgente: "
        "el comportamiento ante timeout del CoreBanking no está definido, creando riesgo directo de pagos duplicados. "
        "Adicionalmente, el SLA regulatorio de 10 segundos no aparece en los criterios de aceptación, "
        "la historia de fallo de pago es demasiado vaga para ser implementable, y existe una contradicción "
        "entre el criterio de 'actualización automática' y el polling propuesto. "
        "Se recomienda una sesión de refinamiento con Sofia y Daniel antes de comenzar el desarrollo.",
    )


# ── Agent 2: Architecture Validator ──────────────────────────────────────────


def _arch_validator() -> AgentResult:
    aid, aname = "arch_validator", "Architecture Validator"
    findings = [
        _f(
            title="CoreBanking síncrono (2-15s) hace el SLA de 10s matemáticamente imposible",
            description=(
                "Con latencia del CoreBanking de 2-15s y antifraude de 3s adicionales, "
                "el tiempo total en P95 supera los 18 segundos. "
                "La arquitectura propuesta no puede cumplir el SLA regulatorio de 10s "
                "bajo carga normal, garantizando incumplimiento regulatorio desde el día 1."
            ),
            confidence="red",
            score=0.05,
            evidence=(
                "'El gateway SWIFT CoreBanking v2.1 es un sistema síncrono que puede tener latencias de 2-15 segundos.' "
                "'El sistema antifraude externo (FraudShield) responde en promedio en 3 segundos.'"
            ),
            assumptions=["Las latencias son aditivas en el flujo síncrono actual."],
            needs_validation=[
                "¿Es posible precalificar la transacción con antifraude de forma asíncrona?",
                "¿Tiene el CoreBanking un modo asíncrono no documentado?",
            ],
            recommended_action=(
                "Implementar patrón async: el endpoint retorna 202 Accepted con un ID de transacción; "
                "el estado se consulta por polling o WebSocket. "
                "Esto desacopla el SLA del usuario de la latencia del CoreBanking."
            ),
            category="contradiction",
            agent_id=aid,
            agent_name=aname,
        ),
        _f(
            title="API Gateway instancia única: punto único de falla en sistema financiero",
            description=(
                "El API Gateway es una instancia única sin load balancer ni redundancia. "
                "Cualquier restart, despliegue o fallo del nodo deja el sistema completamente inaccesible. "
                "Esto contradice directamente el objetivo de 99.9% de disponibilidad."
            ),
            confidence="red",
            score=0.08,
            evidence="'API Gateway: Node.js + Express, instancia única'",
            assumptions=[],
            needs_validation=["¿Existe un plan de redundancia para el API Gateway?"],
            recommended_action=(
                "Agregar una segunda instancia del API Gateway detrás del balanceador de carga "
                "existente antes del go-live. Costo mínimo de configuración; "
                "impacto en disponibilidad máximo."
            ),
            category="risk",
            agent_id=aid,
            agent_name=aname,
        ),
        _f(
            title="Sin timeout en llamadas al CoreBanking: riesgo de thread starvation",
            description=(
                "El Payment Service llama al CoreBanking sin timeout configurado, "
                "usando el default del cliente HTTP (típicamente infinito). "
                "Si el CoreBanking se degrada, los threads del Payment Service quedan bloqueados "
                "indefinidamente, saturando el pool de conexiones y derrumbando el servicio completo."
            ),
            confidence="red",
            score=0.1,
            evidence="'Sin timeout configurado para llamadas al CoreBanking (usa el default del cliente HTTP)'",
            assumptions=[],
            needs_validation=["¿Cuál es el timeout máximo aceptable para el CoreBanking?"],
            recommended_action=(
                "Configurar timeout explícito de 8 segundos en el cliente httpx para CoreBanking. "
                "Devolver 503 al cliente si no responde. Es un cambio de 2 líneas de código "
                "que debe hacerse en el primer sprint."
            ),
            category="risk",
            agent_id=aid,
            agent_name=aname,
        ),
        _f(
            title="Sin idempotencia: reintentos generarán pagos duplicados",
            description=(
                "No hay clave de idempotencia ni deduplicación de transacciones. "
                "Si el cliente reintenta por timeout o el sistema hace retry automático, "
                "el mismo pago se ejecutará múltiples veces en el CoreBanking. "
                "En pagos internacionales, esto implica pérdidas financieras reales."
            ),
            confidence="red",
            score=0.12,
            evidence="'Sin mecanismo de idempotencia implementado en las transacciones'",
            assumptions=["El CoreBanking no tiene deduplicación propia."],
            needs_validation=["¿Puede el CoreBanking detectar transacciones duplicadas por su cuenta?"],
            recommended_action=(
                "Implementar UUID de idempotencia: el cliente envía un header `X-Idempotency-Key`, "
                "el Payment Service lo almacena en PostgreSQL con TTL de 24h "
                "y rechaza duplicados con 409 Conflict. Estándar de la industria, implementable en un sprint."
            ),
            category="gap",
            agent_id=aid,
            agent_name=aname,
        ),
        _f(
            title="Notificaciones síncronas sin cola: pérdida silenciosa en fallo de SendGrid",
            description=(
                "SendGrid se llama síncronamente al completar cada transacción, sin cola de mensajes ni retry. "
                "Si SendGrid falla (downtime, rate limit, error de red), la transacción ya fue procesada "
                "pero el cliente no recibe confirmación. El fallo es silencioso — no hay alerta ni reintento."
            ),
            confidence="yellow",
            score=0.28,
            evidence="'Llamada directa a SendGrid desde el Payment Service al completar cada transacción. Sin cola de mensajes. Sin retry en caso de fallo de SendGrid.'",
            assumptions=["SendGrid tiene SLA del 99.9%, pero el 0.1% restante afecta transacciones reales."],
            needs_validation=["¿Es aceptable que una transacción exitosa no genere email de confirmación?"],
            recommended_action=(
                "Agregar tabla `pending_notifications` en PostgreSQL. "
                "El Payment Service inserta el registro y un worker asíncrono envía el email "
                "con retry exponencial. Desacopla el éxito del pago del éxito de la notificación."
            ),
            category="risk",
            agent_id=aid,
            agent_name=aname,
        ),
    ]
    return _result(
        aid, aname, "GitBranch", findings,
        "La arquitectura propuesta tiene tres problemas bloqueantes para producción. "
        "Primero, la combinación de latencias del CoreBanking (2-15s) y el antifraude (3s) hace matemáticamente "
        "imposible cumplir el SLA regulatorio de 10 segundos. Segundo, la ausencia de timeout en las llamadas "
        "al CoreBanking y la falta de circuit breaker crean riesgo de cascading failure total. "
        "Tercero, sin idempotencia, los reintentos generarán pagos duplicados con certeza. "
        "Se recomienda priorizar: desacoplamiento asíncrono del CoreBanking, timeout explícito y clave de idempotencia.",
    )


# ── Agent 3: Risk Intelligence ────────────────────────────────────────────────


def _risk_intelligence() -> AgentResult:
    aid, aname = "risk_intelligence", "Risk Intelligence"
    findings = [
        _f(
            title="Sin circuit breaker al CoreBanking: fallo en cascada garantizado",
            description=(
                "No hay circuit breaker entre el Payment Service y el CoreBanking. "
                "Si el CoreBanking se degrada o cae, todas las solicitudes de pago quedarán bloqueadas "
                "esperando, agotando el pool de conexiones del Payment Service y derrumbando "
                "la plataforma completa — no solo los pagos internacionales."
            ),
            confidence="red",
            score=0.07,
            evidence="'Sin lógica de retry implementada' y 'sin timeout configurado' implican ausencia de circuit breaker.",
            assumptions=["El CoreBanking tiene historial de degradaciones por ser sistema legacy."],
            needs_validation=["¿Hay SLA interno del CoreBanking documentado?"],
            recommended_action=(
                "Implementar circuit breaker con Tenacity (Python): 5 fallos consecutivos abren el circuito "
                "por 30 segundos y retornan 503 inmediato al cliente. "
                "Implementable en un día; evita que un fallo del CoreBanking derrumbe toda la plataforma."
            ),
            category="risk",
            agent_id=aid,
            agent_name=aname,
        ),
        _f(
            title="PCI-DSS nivel 1 declarado pero cifrado de datos de cuenta no definido",
            description=(
                "El spec prohíbe almacenar IBAN/SWIFT en texto plano pero no define: "
                "algoritmo de cifrado, gestión de claves, cifrado en tránsito entre servicios internos, "
                "ni tokenización. Sin esta definición, el cumplimiento PCI-DSS no puede verificarse "
                "y el sistema fallará una auditoría de seguridad."
            ),
            confidence="red",
            score=0.1,
            evidence="'Los datos de cuenta SWIFT/IBAN no pueden almacenarse en texto plano.' — sin especificación de cómo protegerlos.",
            assumptions=[],
            needs_validation=[
                "¿Se usa tokenización o cifrado simétrico para IBAN/SWIFT?",
                "¿Quién gestiona las claves de cifrado?",
                "¿Los datos viajan cifrados entre Payment Service y CoreBanking?",
            ],
            recommended_action=(
                "Reunión urgente con el equipo de seguridad esta semana. "
                "Definir: AES-256-GCM para cifrado en reposo de IBAN/SWIFT, claves en HashiCorp Vault. "
                "Bloquear el go-live hasta aprobación formal del equipo legal y de seguridad."
            ),
            category="risk",
            agent_id=aid,
            agent_name=aname,
        ),
        _f(
            title="Sin rate limiting en el API Gateway",
            description=(
                "El API Gateway no implementa rate limiting. Con picos proyectados de 500 TPS "
                "y crecimiento del 300%, un actor malicioso o un error de cliente podría generar "
                "carga arbitraria sobre el CoreBanking legacy, que no fue diseñado para absorber "
                "tráfico no controlado."
            ),
            confidence="yellow",
            score=0.32,
            evidence="'Sin rate limiting implementado aún'",
            assumptions=["El CoreBanking no tiene rate limiting propio."],
            needs_validation=["¿Cuál es el límite de TPS que el CoreBanking puede absorber?"],
            recommended_action=(
                "Agregar rate limiting en Express con `express-rate-limit`: "
                "100 req/min por JWT token. Implementable en 4 horas. "
                "Protege el CoreBanking de ráfagas accidentales o maliciosas."
            ),
            category="risk",
            agent_id=aid,
            agent_name=aname,
        ),
        _f(
            title="Sin estrategia de rollback transaccional",
            description=(
                "Si el pago se ejecuta exitosamente en el CoreBanking pero falla la escritura "
                "en la base de datos local de NovaBank (o la notificación), el sistema queda "
                "en estado inconsistente: el dinero salió pero el sistema no lo registró. "
                "No hay mecanismo de compensación ni reconciliación automática definido."
            ),
            confidence="red",
            score=0.14,
            evidence="Ausencia de mención de transacciones distribuidas, sagas o mecanismos de compensación en toda la arquitectura.",
            assumptions=[
                "La base de datos Oracle 11g no soporta transacciones distribuidas con el Payment Service.",
            ],
            needs_validation=[
                "¿Hay un proceso de reconciliación manual con el CoreBanking?",
                "¿Cómo se detecta y resuelve una transacción fantasma?",
            ],
            recommended_action=(
                "Documentar el procedimiento de reconciliación manual antes del go-live — "
                "quién lo ejecuta, cuándo, y cómo se detecta una transacción inconsistente. "
                "Para el siguiente sprint: evaluar patrón Saga con compensaciones automáticas."
            ),
            category="risk",
            agent_id=aid,
            agent_name=aname,
        ),
        _f(
            title="Trazabilidad de auditoría requerida pero sin especificación de implementación",
            description=(
                "El spec exige 'trazabilidad completa' por compliance, pero no define: "
                "qué eventos se registran (inicio, validación antifraude, ejecución, notificación), "
                "formato del log de auditoría, período de retención, ni integridad de los logs "
                "(un log que puede modificarse no cumple con regulación financiera)."
            ),
            confidence="yellow",
            score=0.38,
            evidence="'Todas las transacciones deben quedar auditadas con trazabilidad completa.'",
            assumptions=["La regulación LATAM requiere logs inmutables con timestamp certificado."],
            needs_validation=[
                "¿Cuál es el período mínimo de retención de auditoría según regulación?",
                "¿Los logs deben ser inmutables (append-only)?",
            ],
            recommended_action=(
                "Crear tabla `audit_log` append-only en PostgreSQL: "
                "timestamp, transaction_id, event_type, actor, payload. "
                "Revisar con Legal el período de retención requerido (mínimo 5 años en varios mercados LATAM) "
                "antes del go-live."
            ),
            category="gap",
            agent_id=aid,
            agent_name=aname,
        ),
    ]
    return _result(
        aid, aname, "Shield", findings,
        "El análisis de riesgos identifica vulnerabilidades críticas en seguridad y resiliencia. "
        "El riesgo más severo es la ausencia de circuit breaker ante el CoreBanking legacy, "
        "que garantiza un fallo en cascada ante la primera degradación del sistema legado. "
        "En segundo lugar, el cumplimiento PCI-DSS está declarado pero no implementado: "
        "no hay definición de cifrado para datos IBAN/SWIFT ni gestión de claves. "
        "Adicionalmente, la ausencia de rollback transaccional creará inconsistencias de datos "
        "desde el primer incidente de producción.",
    )


# ── Agent 4: Business Impact ──────────────────────────────────────────────────


def _business_impact() -> AgentResult:
    aid, aname = "business_impact", "Business Impact"
    findings = [
        _f(
            title="Incumplimiento del SLA regulatorio: multas cuantificables desde el día 1",
            description=(
                "Dado que la arquitectura no puede cumplir el SLA de 10 segundos (análisis del Architecture Validator), "
                "NovaBank estará en incumplimiento regulatorio desde el lanzamiento. "
                "En mercados LATAM, las multas por incumplimiento de pagos instantáneos van de $50K a $500K USD "
                "por trimestre. El costo de rediseñar la arquitectura ahora es menor que la primera multa."
            ),
            confidence="red",
            score=0.09,
            evidence="SLA regulatorio de 10s + latencias arquitectónicas de 5-18s = incumplimiento estructural.",
            assumptions=["Los reguladores LATAM aplican multas por incumplimiento de SLA en pagos instantáneos."],
            needs_validation=[
                "¿Cuál es el régimen de multas aplicable en cada mercado objetivo?",
                "¿Hay un período de gracia regulatorio para nuevos entrantes?",
            ],
            recommended_action=(
                "Presentar este análisis a los stakeholders antes de aprobar el MVP. "
                "El costo del rediseño arquitectónico (2-3 sprints) es menor que la primera multa. "
                "Priorizar la arquitectura asíncrona con respuesta 202 Accepted."
            ),
            category="cost",
            agent_id=aid,
            agent_name=aname,
        ),
        _f(
            title="Crecimiento 300% con infraestructura on-premise: costo operacional sin techo",
            description=(
                "El crecimiento proyectado del 300% en 6 meses con despliegue manual on-premise "
                "implica contratar y aprovisionar hardware físico en múltiples ocasiones. "
                "El costo marginal por unidad de capacidad en on-premise es 3-5x mayor que cloud "
                "a este ritmo de crecimiento. Además, el tiempo de aprovisionamiento (semanas) "
                "no podrá seguir picos de demanda."
            ),
            confidence="red",
            score=0.13,
            evidence="'Infraestructura actual: on-premise, sin orquestación de contenedores, escalamiento manual.'",
            assumptions=["El crecimiento del 300% es el escenario base, no el optimista."],
            needs_validation=["¿Existe presupuesto aprobado para infraestructura de escalamiento?"],
            recommended_action=(
                "Definir en el roadmap post-MVP un punto de migración cloud explícito (ej: al superar 100 TPS). "
                "Incluir análisis TCO comparativo cloud vs. on-premise "
                "antes de que el crecimiento haga la migración urgente y costosa."
            ),
            category="cost",
            agent_id=aid,
            agent_name=aname,
        ),
        _f(
            title="Latencia visible al usuario impacta conversión frente a competidores",
            description=(
                "Wise y Remitly ofrecen confirmación en menos de 3 segundos. "
                "Con la arquitectura actual, NovaBank mostrará tiempos de espera de 5-18 segundos. "
                "Estudios de UX en pagos muestran abandono del 40% por cada 3 segundos adicionales de espera. "
                "Esto impacta directamente la tasa de adopción del producto."
            ),
            confidence="yellow",
            score=0.35,
            evidence="Latencias documentadas: CoreBanking 2-15s + FraudShield 3s vs. Wise/Remitly <3s.",
            assumptions=["El usuario corporativo tiene alternativas disponibles (Wise Business, Remitly for Business)."],
            needs_validation=["¿Cuál es la tasa de abandono aceptable para el equipo de producto?"],
            recommended_action=(
                "Implementar respuesta inmediata de 202 Accepted con UI de estado 'procesando' "
                "y barra de progreso. El usuario percibe rapidez aunque el backend tarde 10s. "
                "Este cambio requiere el rediseño asíncrono pero tiene el mayor impacto en UX."
            ),
            category="cost",
            agent_id=aid,
            agent_name=aname,
        ),
        _f(
            title="Deuda técnica de Oracle 11g bloqueará evolución del producto en 6 meses",
            description=(
                "Oracle 11g (sin soporte oficial desde 2013) no soporta transacciones distribuidas modernas "
                "ni JSON nativo. Cada feature posterior que requiera nuevas consultas o esquemas "
                "implicará workarounds costosos o una migración no planificada. "
                "El costo de migración aumenta exponencialmente con el volumen de datos."
            ),
            confidence="yellow",
            score=0.4,
            evidence="'Base de datos de cuentas está en Oracle 11g (no soporta transacciones distribuidas modernas)'",
            assumptions=["El volumen de datos crecerá con el 300% de crecimiento proyectado."],
            needs_validation=["¿Existe un roadmap de migración de Oracle 11g?"],
            recommended_action=(
                "Crear una capa de abstracción (patrón Repositorio) sobre Oracle 11g desde el día 1. "
                "Esto aísla la deuda técnica, facilita la futura migración "
                "y no requiere tiempo de desarrollo adicional — solo disciplina arquitectónica."
            ),
            category="cost",
            agent_id=aid,
            agent_name=aname,
        ),
    ]
    return _result(
        aid, aname, "TrendingUp", findings,
        "El análisis de impacto de negocio identifica riesgos financieros directos y cuantificables. "
        "El más urgente: la arquitectura garantiza incumplimiento del SLA regulatorio, "
        "con multas potenciales que superan el costo del proyecto desde el primer trimestre. "
        "El crecimiento proyectado del 300% es incompatible con la infraestructura on-premise actual, "
        "creando un techo de escalamiento que llegará antes de que el producto alcance rentabilidad. "
        "Se recomienda presentar este análisis a los stakeholders de negocio antes de aprobar el MVP.",
    )


# ── Agent 5: Accessibility Advocate ──────────────────────────────────────────


def _accessibility_advocate() -> AgentResult:
    aid, aname = "accessibility_advocate", "Accessibility Advocate"
    findings = [
        _f(
            title="Polling sin aria-live: usuarios con lector de pantalla no reciben actualizaciones",
            description=(
                "El estado del pago se actualiza mediante polling cada 3 segundos, "
                "pero sin regiones aria-live los cambios de estado son invisibles para lectores de pantalla. "
                "Un usuario con discapacidad visual no sabrá que su pago fue procesado hasta que "
                "explore manualmente la página, violando WCAG 2.1 criterio 4.1.3 (Status Messages)."
            ),
            confidence="red",
            score=0.12,
            evidence="'React SPA con polling cada 3 segundos para actualizar estado de pagos' — sin mención de aria-live.",
            assumptions=[],
            needs_validation=["¿El componente de estado de pago tiene aria-live='polite' o aria-atomic?"],
            recommended_action=(
                "Agregar `aria-live='polite'` al contenedor del estado del pago. "
                "Al cambiar el estado, actualizar el texto del elemento para que el lector de pantalla lo anuncie. "
                "Es un cambio de 10 minutos que resuelve una brecha crítica de WCAG 4.1.3."
            ),
            category="accessibility",
            agent_id=aid,
            agent_name=aname,
        ),
        _f(
            title="Diseño mobile-last excluye tecnologías de asistencia más usadas",
            description=(
                "El spec define el diseño 'principalmente para escritorio' con móvil como mejora futura. "
                "En LATAM, el 68% de las tecnologías de asistencia se usan en dispositivos móviles. "
                "Un sistema de pagos corporativos inaccessible en móvil excluye a usuarios con "
                "discapacidad motora que usan conmutadores, usuarios con baja visión que amplifican "
                "pantalla en su teléfono, y usuarios de TalkBack/VoiceOver en Android/iOS."
            ),
            confidence="red",
            score=0.15,
            evidence="'Diseñado principalmente para escritorio; móvil como mejora futura'",
            assumptions=["Los clientes corporativos en LATAM autorizan pagos frecuentemente desde móvil."],
            needs_validation=[
                "¿Cuál es el porcentaje de usuarios que acceden desde móvil en el segmento B2B objetivo?",
            ],
            recommended_action=(
                "Incluir diseño responsive desde el primer componente del MVP. "
                "El costo de retroalimentar responsive es 5-10x mayor que hacerlo desde el inicio. "
                "Elena debe revisar los mockups antes de que el equipo comience el desarrollo del frontend."
            ),
            category="accessibility",
            agent_id=aid,
            agent_name=aname,
        ),
        _f(
            title="Comprobante PDF sin especificación de accesibilidad de documento",
            description=(
                "El spec menciona 'email de confirmación con comprobante en PDF' sin especificar "
                "si el PDF cumple con PDF/UA (ISO 14289). Un PDF no etiquetado es ilegible para "
                "lectores de pantalla. En contexto financiero, un comprobante inaccesible "
                "puede tener implicaciones legales en mercados con regulación de accesibilidad."
            ),
            confidence="yellow",
            score=0.38,
            evidence="'Email de confirmación con comprobante en PDF'",
            assumptions=["El PDF se genera programáticamente, no es un documento escaneado."],
            needs_validation=[
                "¿El generador de PDF soporta etiquetado semántico (PDF/UA)?",
                "¿Los mercados objetivo tienen regulación de accesibilidad en documentos financieros?",
            ],
            recommended_action=(
                "Usar una librería de generación PDF con soporte PDF/UA: ReportLab con etiquetado o WeasyPrint. "
                "Agregar como criterio de aceptación en US-003: "
                "'El PDF de confirmación debe ser legible por lectores de pantalla (PDF/UA).'"
            ),
            category="accessibility",
            agent_id=aid,
            agent_name=aname,
        ),
        _f(
            title="Mensajes de error de pago: dependencia visual no definida",
            description=(
                "El spec menciona notificaciones de error pero no define si los mensajes "
                "usan solo color rojo para indicar fallo. Si es así, viola WCAG 1.4.1 (Use of Color). "
                "Los mensajes de error deben incluir un ícono o texto que no dependa solo del color, "
                "y deben estar marcados con role='alert' para lectores de pantalla."
            ),
            confidence="yellow",
            score=0.42,
            evidence="'En caso de fallo, el sistema debe indicar qué hacer a continuación' — sin especificación de diseño accesible.",
            assumptions=["El equipo de diseño no tiene guidelines de accesibilidad definidas aún."],
            needs_validation=["¿Existen mockups del estado de error que podamos revisar?"],
            recommended_action=(
                "Definir en el design system: mensajes de error incluyen ícono + texto descriptivo, no solo color rojo. "
                "Agregar `role='alert'` y `aria-live='assertive'` al componente de error. "
                "Esta combinación cumple WCAG 1.4.1 y 4.1.3 simultáneamente."
            ),
            category="accessibility",
            agent_id=aid,
            agent_name=aname,
        ),
    ]
    return _result(
        aid, aname, "Eye", findings,
        "El análisis de accesibilidad identifica cuatro brechas contra WCAG 2.1 AA. "
        "La más crítica: las actualizaciones de estado por polling no serán anunciadas a lectores de pantalla, "
        "dejando a usuarios con discapacidad visual sin información sobre el resultado de sus pagos. "
        "Adicionalmente, el enfoque mobile-last excluye a la mayoría de usuarios de tecnologías de asistencia en LATAM. "
        "Estos problemas son significativamente más baratos de corregir en diseño que en código, "
        "y Elena debería revisar los mockups antes de que el equipo comience el desarrollo del frontend.",
    )


# ── Agent 6: Delivery Historian ───────────────────────────────────────────────


def _delivery_historian() -> AgentResult:
    aid, aname = "delivery_historian", "Delivery Historian"
    findings = [
        _f(
            title="Sin idempotencia en pagos: este patrón causó 900K duplicados en producción",
            description=(
                "En 2019, un banco europeo procesó 900,000 pagos duplicados en un incidente de 4 horas "
                "causado exactamente por este patrón: reintentos sin clave de idempotencia sobre un gateway "
                "de pagos síncrono. La recuperación tomó 3 semanas y costó €12M en reversiones. "
                "La arquitectura actual de NovaBank reproduce este antipatrón exactamente."
            ),
            confidence="red",
            score=0.08,
            evidence="'Sin mecanismo de idempotencia implementado en las transacciones.' 'Sin lógica de retry implementada.'",
            assumptions=[],
            needs_validation=[
                "¿El CoreBanking puede detectar duplicados por su cuenta usando algún campo de referencia?",
            ],
            recommended_action=(
                "Implementar idempotency keys ANTES del primer deploy a producción. "
                "Patrón: UUID en header `X-Idempotency-Key`, almacenado en DB con TTL 24h, "
                "rechazar duplicados con 409 Conflict. No es una mejora futura — es un requisito de seguridad."
            ),
            category="pattern",
            agent_id=aid,
            agent_name=aname,
        ),
        _f(
            title="Thread starvation por llamadas síncronas a legacy: patrón de cascading failure",
            description=(
                "El 'thread starvation' por llamadas síncronas a sistemas lentos es uno de los patrones "
                "de fallo más documentados en arquitecturas de microservicios. Amazon describió este antipatrón "
                "en su post-mortem de 2004 como el origen del diseño de circuit breakers en AWS. "
                "Sin timeout ni circuit breaker, el primer incidente del CoreBanking derribará toda la plataforma."
            ),
            confidence="red",
            score=0.1,
            evidence="'Sin timeout configurado para llamadas al CoreBanking (usa el default del cliente HTTP)'",
            assumptions=["El CoreBanking tiene historial de degradaciones por ser sistema legacy on-premise."],
            needs_validation=["¿Cuál es la disponibilidad histórica del CoreBanking en los últimos 12 meses?"],
            recommended_action=(
                "Implementar timeout explícito y circuit breaker esta semana — son cambios independientes que "
                "pueden hacerse en paralelo en el primer sprint. "
                "No hay justificación para no tenerlos desde el día 1."
            ),
            category="pattern",
            agent_id=aid,
            agent_name=aname,
        ),
        _f(
            title="Integración SWIFT legacy en 6 semanas: históricamente el doble del tiempo estimado",
            description=(
                "La integración con gateways SWIFT legacy tiene un historial consistente de tomar "
                "el doble del tiempo estimado. El 'último 10%' — manejo de formatos edge case, "
                "gestión de errores no documentados, certificaciones de seguridad — consume "
                "típicamente el 50% del esfuerzo total. Priya y Daniel deben planificar con este factor."
            ),
            confidence="yellow",
            score=0.35,
            evidence="'El gateway SWIFT CoreBanking v2.1 es un sistema síncrono' — integración en 6 semanas totales.",
            assumptions=["El equipo no tiene experiencia previa con el CoreBanking v2.1."],
            needs_validation=[
                "¿Hay documentación técnica completa del CoreBanking disponible desde el día 1?",
                "¿Existe un ambiente de sandbox/staging del CoreBanking para pruebas?",
            ],
            recommended_action=(
                "Obtener acceso al ambiente de UAT del CoreBanking el día 1 del sprint. "
                "Si no está disponible en la primera semana, escalar inmediatamente: "
                "este es el mayor riesgo de timeline del proyecto."
            ),
            category="pattern",
            agent_id=aid,
            agent_name=aname,
        ),
        _f(
            title="Despliegue manual en sistema financiero crítico: segunda causa de incidentes en prod",
            description=(
                "Los errores humanos en despliegues manuales son la segunda causa más común de incidentes "
                "en producción en sistemas financieros (después de los cambios de configuración). "
                "Un deploy mal ejecutado en un sistema de pagos activo puede dejar transacciones "
                "en vuelo en estado indefinido. Marcus debe incluir automatización de despliegue "
                "como requisito, no como mejora futura."
            ),
            confidence="yellow",
            score=0.38,
            evidence="'Despliegue en VMs on-premise. Sin orquestación de contenedores. Escalamiento manual.'",
            assumptions=["El equipo realizará múltiples deploys durante las 6 semanas de desarrollo."],
            needs_validation=[
                "¿Hay un proceso de rollback definido para el sistema de pagos en producción?",
            ],
            recommended_action=(
                "Implementar CI/CD básico con GitHub Actions en el primer sprint: "
                "tests automáticos en PR + deploy automático a staging. "
                "El deploy a producción puede seguir siendo manual, pero con un script validado y rollback documentado."
            ),
            category="pattern",
            agent_id=aid,
            agent_name=aname,
        ),
    ]
    return _result(
        aid, aname, "History", findings,
        "El análisis histórico identifica que NovaBank está reproduciendo tres patrones de fallo "
        "bien documentados en la industria fintech. El más urgente: la ausencia de idempotencia "
        "en un sistema con reintentos es el mismo patrón que causó 900,000 pagos duplicados "
        "en un banco europeo en 2019. La recomendación es clara: implementar idempotencia y "
        "circuit breaker son requisitos no negociables antes del lanzamiento. "
        "Adicionalmente, la estimación de 6 semanas para la integración SWIFT legacy es optimista — "
        "Marcus debería planificar con un buffer del 100% para la integración del CoreBanking.",
    )
