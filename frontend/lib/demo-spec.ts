// Caso de uso: NovaBank — Pagos Internacionales Instantáneos
// Personajes: Sofia (PM), Daniel (Arquitecto), Priya (QA Lead), Marcus (Delivery Lead), Elena (Accesibilidad)
// Contexto: 6 semanas, arquitectura legacy, presión regulatoria

export const DEMO_SPEC = `# NovaBank — Pagos Internacionales Instantáneos
## Product Requirements Document v1.2

**Autor:** Sofia Chen, Product Manager
**Revisado por:** Daniel Reyes, Arquitecto de Software
**Estado:** En revisión
**Objetivo de entrega:** 6 semanas

---

## Contexto de negocio

NovaBank necesita lanzar pagos internacionales instantáneos para clientes corporativos en LATAM.
La regulación local exige confirmación de transacción en menos de 10 segundos.
El producto competirá directamente con Wise y Remitly en el segmento B2B.
Se proyecta un crecimiento de 300% en volumen transaccional en los primeros 6 meses.

---

## Alcance del MVP

### US-001: Iniciar pago internacional
Como cliente corporativo, 
quiero iniciar un pago internacional desde mi dashboard
para transferir fondos a proveedores en el extranjero.

**Criterios de aceptación:**
- El usuario ingresa: monto, moneda destino, cuenta IBAN/SWIFT del beneficiario
- El sistema valida los fondos disponibles antes de procesar
- Se muestra confirmación de la transacción al usuario
- El pago debe completarse dentro del SLA regulatorio

**Notas técnicas:**
- El procesamiento pasa por el gateway SWIFT legado de NovaBank (CoreBanking v2.1)
- La validación antifraude es obligatoria antes de ejecutar

### US-002: Consultar estado del pago
Como cliente, quiero consultar el estado de un pago en tiempo real
para saber si fue procesado correctamente.

**Criterios de aceptación:**
- El usuario puede ver: pendiente, procesando, completado, fallido
- El estado se actualiza automáticamente sin refrescar la página
- Se muestra el tiempo estimado de acreditación en cuenta destino

### US-003: Notificación de resultado
Como cliente, quiero recibir una notificación cuando mi pago sea procesado
para confirmar que la operación fue exitosa.

**Criterios de aceptación:**
- Notificación in-app inmediata al cambiar el estado
- Email de confirmación con comprobante en PDF
- En caso de fallo, el sistema debe indicar qué hacer a continuación

### US-004: Historial de transacciones
Como cliente, quiero ver el historial completo de mis pagos internacionales
para conciliar con mi contabilidad.

**Criterios de aceptación:**
- Listado paginado de transacciones
- Filtros por fecha, estado y monto
- Exportación a CSV

---

## Restricciones técnicas conocidas

- El gateway SWIFT CoreBanking v2.1 es un sistema síncrono que puede tener latencias de 2-15 segundos
- El sistema antifraude externo (FraudShield) responde en promedio en 3 segundos
- La base de datos de cuentas está en Oracle 11g (no soporta transacciones distribuidas modernas)
- Infraestructura actual: on-premise, sin Kubernetes, despliegue manual

## Requisitos no funcionales

- Alta disponibilidad: el sistema debe estar disponible 99.9% del tiempo
- El SLA regulatorio exige confirmación en menos de 10 segundos
- Soporte para picos de hasta 500 transacciones por minuto en días de cierre contable

## Seguridad y compliance

- Todas las transacciones deben quedar auditadas con trazabilidad completa
- Cumplimiento con PCI-DSS nivel 1
- Los datos de cuenta SWIFT/IBAN no pueden almacenarse en texto plano

## Fuera de alcance

- Pagos en criptomonedas
- Integración con contabilidades externas (ERP)
- Soporte multiidioma (solo español para el MVP)`;

export const DEMO_SPEC_AUTH = `# NovaBank — Sistema de Autenticación Multi-Factor (MFA)
## Product Requirements Document v0.9

**Autor:** Rodrigo Salazar, Product Manager
**Revisado por:** Daniel Reyes, Arquitecto de Software
**Estado:** Borrador para revisión técnica
**Objetivo de entrega:** 8 semanas (deadline regulatorio: 1 de julio)

---

## Contexto de negocio

NovaBank debe implementar autenticación multi-factor obligatoria para todos los clientes corporativos antes del plazo regulatorio de Q2. La regulación local exige MFA para acceso a funcionalidades de transferencias a partir del 1 de julio. El equipo de seguridad detectó 3 intentos de acceso no autorizado en los últimos 90 días.

---

## Alcance del MVP

### US-101: Registro de segundo factor
Como cliente corporativo, quiero registrar un segundo factor de autenticación para proteger mi cuenta.

**Criterios de aceptación:**
- El usuario puede registrar una app de autenticación (TOTP)
- El usuario puede registrar su número de teléfono para SMS OTP como alternativa
- Se generan 8 códigos de recuperación al activar el segundo factor
- El sistema valida el segundo factor antes de activarlo

**Notas técnicas:**
- Los códigos TOTP siguen el estándar RFC 6238 (ventana de 30 segundos)
- El número de teléfono actúa como fallback ante pérdida de la app autenticadora
- Los códigos de recuperación son de uso único

### US-102: Autenticación con segundo factor
Como cliente, quiero autenticarme con mi segundo factor para acceder a mi cuenta de forma segura.

**Criterios de aceptación:**
- Después del login con usuario/contraseña, se solicita el segundo factor
- El usuario puede ingresar código TOTP de 6 dígitos o OTP de SMS
- Se permite un máximo de 3 intentos incorrectos antes de bloquear la sesión temporalmente
- La sesión MFA tiene privilegios superiores a la sesión sin MFA

**Notas técnicas:**
- El JWT resultante incluye el claim \`mfa_verified: true\`
- La ventana de validez del OTP de SMS es de 10 minutos

### US-103: Gestión de dispositivos confiables
Como cliente, quiero marcar un dispositivo como confiable para no repetir el MFA en cada sesión.

**Criterios de aceptación:**
- El usuario puede marcar el dispositivo actual como confiable por 30 días
- Los dispositivos confiables se listan en la configuración de cuenta
- El usuario puede revocar dispositivos confiables individualmente

### US-104: Recuperación de cuenta
Como cliente, quiero recuperar el acceso si pierdo mi segundo factor.

**Criterios de aceptación:**
- El usuario puede autenticarse con los códigos de recuperación generados en el registro
- Tras usar un código de recuperación, se requiere registrar un nuevo segundo factor
- El administrador corporativo puede resetear el MFA de un usuario con aprobación del equipo de seguridad

---

## Restricciones técnicas conocidas

- El sistema de autenticación actual usa JWTs almacenados en localStorage del browser
- El servicio de SMS es Twilio; se ha observado latencia variable de 5-30 segundos en algunos mercados LATAM
- La autenticación biométrica fue evaluada y descartada para el MVP por complejidad de integración
- El backend de auth es parte de un monolito Node.js sin separación de servicios

## Requisitos no funcionales

- El flujo MFA no debe agregar más de 10 segundos al tiempo total de login
- Alta disponibilidad: el sistema de autenticación requiere 99.95% de uptime
- Todos los intentos de login deben loguearse con IP, user-agent y timestamp

## Seguridad y compliance

- Cumplimiento con OWASP Authentication Cheat Sheet
- Los seeds TOTP y códigos de recuperación no pueden almacenarse en texto plano
- Se requiere rate limiting en los endpoints de login y verificación MFA
- Toda actividad de autenticación debe quedar auditada

## Fuera de alcance

- Autenticación biométrica (planificada para Q3)
- SSO/SAML para clientes enterprise
- Hardware security keys (FIDO2/WebAuthn)`;

export const DEMO_ARCH_AUTH = `# Arquitectura Propuesta — NovaBank MFA
## Autor: Daniel Reyes, Arquitecto de Software

### Componentes principales

**Frontend:**
- Formulario MFA integrado en el flujo de login existente
- JWTs almacenados en localStorage (sin cambio respecto al sistema actual)
- Sin expiración de sesión por inactividad implementada
- Los códigos de recuperación se muestran una sola vez; responsabilidad del usuario guardarlos

**Auth Service (Node.js, monolito existente):**
- Se agrega endpoint POST /auth/mfa/verify para verificar TOTP/OTP
- Generación de seeds TOTP con librería \`speakeasy\` (sin auditoría de seguridad externa)
- Seeds TOTP almacenados cifrados con AES-128; clave de cifrado hardcodeada en .env
- Sin invalidación de sesiones activas existentes al activar o cambiar configuración MFA
- Sin detección de replay attacks en OTP de SMS

**Servicio de SMS (Twilio):**
- OTP enviado en texto plano en el cuerpo del SMS: "Tu código NovaBank es: 123456"
- Sin límite de reenvíos del SMS OTP por intento de login
- Latencia variable 5-30s en LATAM; sin timeout configurable desde el Auth Service
- Sin fallback si Twilio no está disponible (el usuario queda bloqueado)

**Base de datos:**
- PostgreSQL para tokens MFA, dispositivos confiables y códigos de recuperación
- Códigos de recuperación almacenados hasheados con MD5
- Sin rotación de la clave AES planificada

**Dispositivos confiables:**
- Token de dispositivo es un UUID almacenado en cookie sin flag httpOnly
- Sin binding del token al dispositivo (user-agent, IP) — el mismo token funciona desde cualquier equipo
- Expiración fija a 30 días, sin opción de configuración por el administrador`;

export const DEMO_ARCHITECTURE = `# Arquitectura Propuesta — NovaBank Pagos Internacionales
## Autor: Daniel Reyes, Arquitecto de Software

### Componentes principales

**Frontend:**
- React SPA con polling cada 3 segundos para actualizar estado de pagos
- Sin WebSockets (decisión de simplificación para MVP)
- Diseñado principalmente para escritorio; móvil como mejora futura

**API Gateway:**
- Node.js + Express, instancia única
- Maneja autenticación JWT y enrutamiento
- Sin rate limiting implementado aún

**Payment Service:**
- Python + FastAPI
- Llama síncronamente al CoreBanking gateway en cada transacción
- Llama síncronamente a FraudShield antes de autorizar
- Sin timeout configurado para llamadas al CoreBanking (usa el default del cliente HTTP)
- Sin lógica de retry implementada

**CoreBanking Gateway (legacy):**
- Sistema SWIFT propio, on-premise
- API REST síncrona con latencia variable (2-15 segundos)
- Sin SLA interno documentado
- Punto único de integración para todos los pagos

**Base de datos:**
- PostgreSQL para datos del Payment Service
- Oracle 11g para datos de cuentas (solo lectura desde el nuevo sistema)
- Sin mecanismo de idempotencia implementado en las transacciones

**Notificaciones:**
- Llamada directa a SendGrid desde el Payment Service al completar cada transacción
- Sin cola de mensajes
- Sin retry en caso de fallo de SendGrid

**Infraestructura:**
- Despliegue en VMs on-premise
- Sin orquestación de contenedores
- Escalamiento manual`;
