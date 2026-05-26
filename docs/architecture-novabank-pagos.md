# Documento de Arquitectura Técnica
## NovaBank — Pagos Internacionales Instantáneos
### RFC-2024-47 · Revisión 1.3

**Autor:** Daniel Reyes, Arquitecto de Software Senior
**Revisores:** Sofia Chen (Product), Priya Kapoor (QA Lead), Marcus Torres (Delivery Lead)
**Estado:** Aprobado para implementación
**Fecha:** 2024-11-08
**Objetivo de entrega:** 6 semanas (sprint 1 inicia 2024-11-11)

---

## 1. Contexto y objetivo

NovaBank requiere habilitar pagos internacionales instantáneos para su segmento corporativo en LATAM. El sistema deberá procesar transferencias SWIFT/IBAN con confirmación al usuario en menos de 10 segundos, cumpliendo regulación local y PCI-DSS nivel 1.

Este documento describe la arquitectura propuesta para el MVP, las decisiones de diseño tomadas, y los componentes involucrados.

**Restricciones no negociables:**
- Usar el gateway CoreBanking v2.1 existente (sistema legado, on-premise)
- No migrar la base de datos de cuentas (Oracle 11g)
- Infraestructura on-premise sin Kubernetes
- Timeline de 6 semanas para el primer release

---

## 2. Vista general del sistema

```
[Cliente Web]
     |
     | HTTPS
     v
[API Gateway]  ←── JWT Auth ──→  [Auth Service (existente)]
     |
     | HTTP interno
     v
[Payment Service]
     |         |              |
     v         v              v
[CoreBanking] [FraudShield]  [PostgreSQL]
  (SWIFT v2.1) (externo)     (transacciones)
     |
     v
[Oracle 11g]  ← solo lectura
(cuentas)

[Payment Service] ──→ [SendGrid] (notificaciones email)
```

**Flujo principal de un pago:**

1. Cliente envía `POST /api/payments` con monto, moneda, IBAN destino
2. API Gateway valida JWT y enruta al Payment Service
3. Payment Service consulta Oracle 11g para validar cuenta origen (saldo)
4. Payment Service llama a FraudShield para validación antifraude
5. Si FraudShield aprueba, se llama al CoreBanking gateway para ejecutar la transferencia SWIFT
6. CoreBanking retorna confirmación (o error)
7. Payment Service persiste el resultado en PostgreSQL
8. Payment Service llama a SendGrid para enviar email de confirmación
9. Se retorna respuesta al cliente

---

## 3. Componentes y decisiones de diseño

### 3.1 Frontend — React SPA

**Tecnología:** React 18, TypeScript, Axios
**Hosting:** Nginx en VM on-premise

**Decisiones:**
- SPA clásica, sin SSR (next.js descartado por simplicidad de despliegue)
- Actualización de estado de pagos mediante **polling HTTP cada 3 segundos** al endpoint `GET /api/payments/{id}/status`
- WebSockets descartados para el MVP: la infraestructura de red interna no tiene soporte habilitado para conexiones persistentes sin cambios de configuración adicionales que están fuera del scope del equipo de plataforma
- Diseño responsivo orientado a escritorio; la version mobile se define como mejora post-MVP en el roadmap

**Accesibilidad:**
- Se usará HTML semántico
- Los colores de estado (verde/rojo/amarillo) tienen etiquetas de texto acompañando cada indicador
- No se ha realizado auditoría WCAG formal; se planea para Q1 2025

### 3.2 API Gateway — Node.js + Express

**Tecnología:** Node.js 20 LTS, Express 4, jsonwebtoken
**Despliegue:** VM dedicada, instancia única

**Decisiones:**
- Express elegido por familiaridad del equipo; alternativas como Fastify o Kong descartadas por curva de aprendizaje
- Validación de JWT con clave secreta compartida (HS256); rotación de clave planificada post-MVP
- El API Gateway actúa como punto único de entrada: maneja CORS, logging de requests, y enrutamiento interno
- **Rate limiting:** no está implementado en este MVP. Se asume que el volumen inicial (piloto con 20 clientes corporativos) no lo requiere. Se revisará antes de la apertura masiva
- Sin health check endpoint implementado aún (pendiente antes del go-live)
- Escalamiento: instancia única. En caso de necesidad, se agrega manualmente una segunda instancia y se configura el balanceador de carga existente

### 3.3 Payment Service — Python + FastAPI

**Tecnología:** Python 3.11, FastAPI, SQLAlchemy, httpx
**Despliegue:** VM dedicada, 2 instancias (activo-activo manual)

**Flujo interno detallado:**

```python
# Pseudocódigo del endpoint principal
async def create_payment(request):
    # 1. Validar fondos en Oracle (lectura directa)
    balance = await oracle_client.get_balance(account_id)
    if balance < request.amount:
        raise InsufficientFundsError()

    # 2. Llamar FraudShield (síncrono, promedio 3s)
    fraud_result = await fraudshield_client.check(request)
    if fraud_result.is_fraud:
        raise FraudDetectedError()

    # 3. Ejecutar en CoreBanking (síncrono, 2-15s)
    banking_result = await corebanking_client.execute(request)

    # 4. Persistir en PostgreSQL
    await db.save_transaction(banking_result)

    # 5. Notificar por email
    await sendgrid_client.send_confirmation(request.user_email, banking_result)

    return banking_result
```

**Decisiones y consideraciones:**
- Las llamadas a FraudShield y CoreBanking son **secuenciales y síncronas**. Se evaluó paralelizarlas pero FraudShield debe correr antes de CoreBanking por política de compliance
- **Timeouts:** se usa el cliente HTTP por defecto (httpx). No se han configurado timeouts explícitos; se asume que los SLAs de los proveedores externos son suficiente garantía
- **Retry:** no implementado en este MVP. Si CoreBanking falla, el error se propaga directamente al cliente. Se documentará el procedimiento manual de reconciliación
- **Idempotencia:** no hay clave de idempotencia en las transacciones. Si el cliente re-envía una solicitud por un timeout en la red, podría generarse un pago duplicado. Se acepta este riesgo para el MVP dado el volumen bajo del piloto
- **Circuit breaker:** no implementado. Si CoreBanking se degrada, el Payment Service seguirá intentando llamadas hasta que los workers de FastAPI se agoten

### 3.4 CoreBanking Gateway (legacy)

**Sistema:** Propiedad de NovaBank, on-premise, equipo de Infraestructura
**API:** REST síncrona sobre HTTPS interno
**Latencia:** Variable, documentada entre 2 y 15 segundos por transacción
**SLA interno:** No documentado formalmente. El equipo de Infraestructura indica "disponibilidad alta" sin métricas específicas

**Riesgos conocidos:**
- Es el único camino para ejecutar transferencias SWIFT; no hay ruta alternativa
- No hay entorno de staging equivalente al de producción; las pruebas de integración se harán contra el entorno de UAT que tiene datos sintéticos y latencias distintas

### 3.5 Base de datos — PostgreSQL + Oracle 11g

**PostgreSQL 15:** almacena transacciones del Payment Service
**Oracle 11g:** base de datos de cuentas existente, solo lectura desde el nuevo sistema

**Decisiones:**
- No se migra Oracle al MVP; la lectura es directa vía JDBC (usando el driver `cx_Oracle`)
- PostgreSQL en VM dedicada, sin réplica de lectura para el MVP
- Los backups de PostgreSQL son responsabilidad del equipo de Infraestructura (proceso manual existente, diario)
- **Transacciones distribuidas:** no se implementan. Si el pago es exitoso en CoreBanking pero falla la escritura en PostgreSQL, el estado quedará inconsistente. El proceso de reconciliación manual cubrirá este caso

### 3.6 Notificaciones — SendGrid

**Tecnología:** API REST de SendGrid (plan Essentials)
**Integración:** Llamada directa desde Payment Service al finalizar cada transacción

**Decisiones:**
- Sin cola de mensajes intermediaria; la llamada es síncrona dentro del flujo de pago
- Si SendGrid falla (outage, rate limit), la transacción ya fue ejecutada en CoreBanking pero el cliente no recibirá el email de confirmación. No hay retry ni registro de emails pendientes
- Las notificaciones in-app (mencionadas en el PRD) se implementarán en la siguiente iteración; para el MVP solo hay email

---

## 4. Infraestructura y despliegue

**Entorno:** On-premise, data center NovaBank LATAM
**Orquestación:** Ninguna (VMs individuales, systemd para gestión de procesos)

| Componente      | VM          | CPU  | RAM  | Instancias |
|----------------|-------------|------|------|------------|
| API Gateway    | api-gw-01   | 4c   | 8GB  | 1          |
| Payment Service| pay-svc-01  | 8c   | 16GB | 2 (manual) |
| PostgreSQL     | db-pay-01   | 8c   | 32GB | 1          |
| Frontend       | web-01      | 2c   | 4GB  | 1          |

**Estrategia de despliegue:**
- Despliegue manual vía scripts bash coordinado por Marcus
- No hay pipeline CI/CD automatizado para este proyecto (se usará el de infraestructura existente adaptado)
- El rollback implica restaurar la versión anterior del artefacto y reiniciar el servicio via systemd
- Las VMs están en la misma VLAN interna; no hay segmentación de red entre componentes

**Estimación de capacidad para el piloto:**
- 20 clientes corporativos
- Pico estimado: 50 transacciones por hora en días de cierre de mes
- El SLA regulatorio de 10 segundos se asume alcanzable con la arquitectura propuesta

*Nota: El PRD menciona soporte para 500 transacciones por minuto. Esto corresponde a la fase de escala masiva post-piloto y está fuera del scope de esta arquitectura.*

---

## 5. Seguridad y compliance

**Autenticación:** JWT HS256 con clave compartida entre API Gateway y servicios internos
**Transporte:** TLS 1.2 en todas las comunicaciones externas
**Almacenamiento de datos sensibles:** Los números IBAN/SWIFT se almacenan en PostgreSQL; el cifrado en reposo está pendiente de implementación por el equipo de Infraestructura
**Auditoría:** Todas las transacciones se loguean en PostgreSQL con timestamp y usuario
**PCI-DSS:** El equipo legal está evaluando qué controles aplican al MVP. Se implementarán las recomendaciones antes del go-live con el primer cliente

---

## 6. Observabilidad

**Logging:** Logs estructurados (JSON) en cada servicio, centralizados en el servidor de logs existente vía rsyslog
**Métricas:** Prometheus + Grafana instalados en la VM de monitoreo. Los dashboards están en construcción; se priorizará el dashboard de disponibilidad del Payment Service antes del go-live
**Alertas:** No configuradas aún. Marcus coordinará con el equipo de operaciones para definir los umbrales
**Tracing distribuido:** No implementado en el MVP; se evaluará en la siguiente iteración

---

## 7. Supuestos y riesgos aceptados

| # | Supuesto / Riesgo | Responsable | Plan de mitigación |
|---|-------------------|-------------|-------------------|
| R1 | CoreBanking disponible >99% durante el piloto | Infraestructura | Monitoreo manual; escalación inmediata si hay incidencia |
| R2 | FraudShield responde en ≤3s consistentemente | Proveedor externo | SLA contractual existente; sin fallback definido |
| R3 | Volumen del piloto no excede capacidad actual | Marcus | Review semanal de métricas |
| R4 | PCI-DSS: controles básicos suficientes para piloto | Legal / Daniel | Evaluación en curso |
| R5 | Pagos duplicados por re-envío del cliente (<0.1% esperado) | Daniel | Reconciliación manual |

---

## 8. Decisiones descartadas y justificación

| Decisión | Descartada | Razón |
|----------|-----------|-------|
| WebSockets para estado en tiempo real | Sí | Soporte de red no disponible sin cambios de plataforma |
| Cola de mensajes (RabbitMQ/SQS) | Sí | Complejidad operacional fuera del timeline de 6 semanas |
| Circuit breaker (Resilience4j/Tenacity) | Sí | Se prioriza velocidad de entrega; se agrega post-piloto |
| Kubernetes | Sí | Infraestructura on-premise sin capacidad operacional actual |
| Llamadas paralelas a FraudShield + CoreBanking | No aplica | FraudShield debe preceder a CoreBanking por compliance |

---

## 9. Pendientes antes del go-live

- [ ] Configurar health check endpoint en API Gateway
- [ ] Definir y documentar timeouts para llamadas a CoreBanking y FraudShield
- [ ] Confirmar scope de PCI-DSS con equipo legal y aplicar controles mínimos
- [ ] Configurar alertas en Grafana (umbrales con Marcus y operaciones)
- [ ] Prueba de carga contra UAT (aunque no sea equivalente a producción)
- [ ] Documentar procedimiento de reconciliación manual para transacciones inconsistentes
- [ ] Definir proceso de rollback validado y ejecutarlo en un drill

---

## 10. Próximos pasos (post-MVP)

- Implementar cola de mensajes para notificaciones y reintentos
- Agregar circuit breaker en llamadas a CoreBanking
- Migrar a WebSockets o SSE para estado en tiempo real
- Evaluar migración de Oracle 11g o capa de abstracción
- Revisión formal de accesibilidad WCAG 2.1 AA
- Pipeline CI/CD automatizado
- Soporte para escala de 500 tx/min (requiere rediseño de infraestructura)
