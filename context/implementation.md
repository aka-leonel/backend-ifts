# Plan de Implementación: Notificaciones Push (Persona B)

## Objetivo
Implementar el sistema de notificaciones push para recordatorios (RF-22 a RF-27, RNF-09 a RNF-11) siguiendo la arquitectura por features del proyecto.

---

## Desglose de Tasks

### Task 1: Modelo y Migración de Suscripciones Push
**ID:** NOTIF-001
**Objetivo:** Crear modelo SQLAlchemy `PushSubscription` y migración Alembic correspondiente.
**Requisitos:** RF-22
**Componentes afectados:**
- `app/features/notificaciones/model.py` (nuevo)
- `alembic/versions/xxxx_push_subscriptions.py` (nuevo)
- `alembic/env.py` (importar modelo)

**Detalles de implementación:**
- Tabla: `push_subscriptions`
- Campos: `id` (PK), `usuario_id` (FK → usuarios.id, unique), `endpoint` (String, unique), `p256dh` (String), `auth` (String), `fecha_creacion` (DateTime, server_default=now)
- Índices en `usuario_id` y `endpoint`
- Relación `usuario = relationship("Usuario", back_populates="push_subscriptions")` en modelo Usuario

**Criterios de aceptación:**
- Migración se ejecuta sin errores (`alembic upgrade head`)
- Modelo se integra con Base.metadata existente
- Relación bidireccional con Usuario funciona

---

### Task 2: Schemas Pydantic para Suscripciones
**ID:** NOTIF-002
**Objetivo:** Definir schemas de entrada/salida para suscripciones push.
**Requisitos:** RF-23, RF-24
**Componentes afectados:**
- `app/features/notificaciones/schema.py` (nuevo)

**Schemas requeridos:**
- `PushSubscriptionCreate`: `endpoint` (str, URL válida), `p256dh` (str, base64), `auth` (str, base64)
- `PushSubscriptionResponse`: `id`, `usuario_id`, `endpoint`, `fecha_creacion`
- Validaciones: endpoint no vacío, p256dh/auth no vacíos (base64 válido)

**Criterios de aceptación:**
- `from_attributes = True` en ConfigDict
- Validación de campos requeridos
- No expone claves privadas en respuesta

---

### Task 3: Repository de Suscripciones Push
**ID:** NOTIF-003
**Objetivo:** Capa de acceso a datos para suscripciones push.
**Requisitos:** RF-22, RF-23, RF-24, RF-26
**Componentes afectados:**
- `app/features/notificaciones/repository.py` (nuevo)

**Métodos requeridos:**
- `get_by_usuario(usuario_id: int)` → suscripción del usuario (una por usuario)
- `get_by_endpoint(endpoint: str)` → suscripción por endpoint (para cleanup)
- `create(subscription: PushSubscription)` → guardar nueva
- `delete_by_usuario(usuario_id: int)` → eliminar suscripción del usuario
- `delete_by_endpoint(endpoint: str)` → eliminar por endpoint (cleanup 404/410)
- `get_all()` → todas las suscripciones activas (para job de envío)

**Criterios de aceptación:**
- Una sola suscripción por usuario (enforce en DB con unique constraint o lógica)
- CRUD completo funcional

---

### Task 4: Service de Notificaciones Push
**ID:** NOTIF-004
**Objetivo:** Lógica de negocio para gestión de suscripciones y envío push.
**Requisitos:** RF-23, RF-24, RF-25, RF-26
**Componentes afectados:**
- `app/features/notificaciones/service.py` (nuevo)

**Funciones requeridas:**
- `suscribir_usuario(db, usuario_id, subscription_data)` → registra/actualiza suscripción
- `desuscribir_usuario(db, usuario_id)` → elimina suscripción del usuario
- `enviar_push_a_usuario(db, usuario_id, titulo, cuerpo, data_opcional)` → envía push a un usuario
- `enviar_push_a_suscripcion(endpoint, p256dh, auth, payload)` → bajo nivel, usa pywebpush
- `limpiar_suscripciones_invalidas(db, endpoints_invalidos)` → elimina suscripciones 404/410
- Manejo de errores pywebpush (WebPushException) → detectar 404/410 y limpiar

**Configuración VAPID:**
- Leer `VAPID_PUBLIC_KEY` y `VAPID_PRIVATE_KEY` de variables de entorno
- Leer `VAPID_CLAIMS_SUB` (mailto: o https://) de variable de entorno
- Validar presencia al iniciar servicio

**Criterios de aceptación:**
- Envío push funciona con claves VAPID de entorno
- Limpieza automática al recibir 404/410
- Excepciones de dominio apropiadas (NotFoundError, BadRequestError)

---

### Task 5: Router de Notificaciones Push
**ID:** NOTIF-005
**Objetivo:** Endpoints REST para suscripciones push.
**Requisitos:** RF-23, RF-24
**Componentes afectados:**
- `app/features/notificaciones/router.py` (nuevo)

**Endpoints:**
- `POST /notificaciones/suscripcion` (201) — registra suscripción del usuario autenticado
  - Body: `PushSubscriptionCreate`
  - Response: `PushSubscriptionResponse`
  - Auth: `get_current_user`
- `DELETE /notificaciones/suscripcion` (204) — elimina suscripción del usuario autenticado
  - Auth: `get_current_user`

**Convenciones:**
- Prefix `/notificaciones`, tags=["notificaciones"]
- response_model explícito
- Status codes HTTP correctos

**Criterios de aceptación:**
- Endpoints registrados en `main.py`
- Autenticación JWT requerida
- Validación de entrada con Pydantic

---

### Task 6: Dependencias y Registro en main.py
**ID:** NOTIF-006
**Objetivo:** Integrar feature notificaciones en la app principal.
**Requisitos:** RF-23, RF-24
**Componentes afectados:**
- `app/features/notificaciones/dependencies.py` (nuevo) — `get_notificacion_service`
- `app/main.py` — importar e incluir router

**Criterios de aceptación:**
- Router incluido en FastAPI app
- Dependencia de service disponible

---

### Task 7: Job Periódico con APScheduler
**ID:** NOTIF-007
**Objetivo:** Scheduler que busque recordatorios próximos a vencer y envíe notificaciones.
**Requisitos:** RF-27, RNF-11
**Componentes afectados:**
- `app/features/notificaciones/scheduler.py` (nuevo)
- `app/main.py` — inicializar scheduler en lifespan

**Detalles de implementación:**
- Usar `AsyncIOScheduler` de APScheduler
- Job que se ejecute cada N minutos (configurable, ej: 5 min)
- Buscar recordatorios con `fecha` entre `ahora` y `ahora + ventana` (ej: 1 hora)
- Para cada recordatorio, enviar push al `usuario_id` del recordatorio
- Payload push: `{ "titulo": recordatorio.titulo, "recordatorio_id": recordatorio.id, "tipo": recordatorio.tipo }`
- Evitar duplicados: marcar recordatorios notificados o usar ventana deslizante

**Criterios de aceptación:**
- Scheduler inicia al arrancar la app
- Job se ejecuta periódicamente
- Envía push solo para recordatorios en ventana temporal
- No envía duplicados para el mismo recordatorio

---

### Task 8: Variables de Entorno y Configuración
**ID:** NOTIF-008
**Objetivo:** Documentar y validar variables de entorno requeridas.
**Requisitos:** RNF-09, RNF-10
**Componentes afectados:**
- `.env.example` — agregar VAPID_PUBLIC_KEY, VAPID_PRIVATE_KEY, VAPID_CLAIMS_SUB
- Validación en service al iniciar

**Variables requeridas:**
- `VAPID_PUBLIC_KEY` — clave pública VAPID (base64 URL-safe)
- `VAPID_PRIVATE_KEY` — clave privada VAPID (base64 URL-safe)
- `VAPID_CLAIMS_SUB` — contacto para VAPID (ej: `mailto:admin@miifts.com` o `https://miifts.com`)

**Criterios de aceptación:**
- Variables documentadas en .env.example
- Service falla claro si faltan en producción
- Localhost permitido para desarrollo (RNF-10)

---

### Task 9: Tests de Integración
**ID:** NOTIF-009
**Objetivo:** Tests pytest para endpoints y lógica de notificaciones.
**Requisitos:** RNF-05
**Componentes afectados:**
- `tests/test_notificaciones.py` (nuevo)

**Tests requeridos:**
- POST /notificaciones/suscripcion — crea suscripción válida (201)
- POST /notificaciones/suscripcion — rechaza endpoint duplicado (409)
- POST /notificaciones/suscripcion — valida campos requeridos (422)
- DELETE /notificaciones/suscripcion — elimina propia suscripción (204)
- DELETE /notificaciones/suscripcion — 404 si no tiene suscripción
- Auth requerido en ambos endpoints (401 sin token)
- Service: enviar_push_a_suscripcion — mock pywebpush
- Service: limpieza 404/410 — mock WebPushException

**Criterios de aceptación:**
- Tests pasan con `pytest tests/test_notificaciones.py`
- Usan fixtures existentes (client, auth_headers, db_session)
- Cobertura de casos principales y edge cases

---

### Task 10: Actualizar Documentación y Contexto
**ID:** NOTIF-010
**Objetivo:** Actualizar context/architecture.md y decisions.md si aplica.
**Componentes afectados:**
- `context/architecture.md` — agregar feature notificaciones a estructura
- `context/decisions.md` — decisión de pywebpush + APScheduler

---

## Dependencias Entre Tasks

```
NOTIF-001 (modelo + migración)
    ↓
NOTIF-002 (schemas)
    ↓
NOTIF-003 (repository)
    ↓
NOTIF-004 (service) ← NOTIF-008 (config VAPID)
    ↓
NOTIF-005 (router) ← NOTIF-006 (deps + main.py)
    ↓
NOTIF-007 (scheduler) ← NOTIF-004, NOTIF-003
    ↓
NOTIF-009 (tests)
    ↓
NOTIF-010 (docs)
```

---

## Orden de Ejecución Recomendado

1. **NOTIF-001** — Modelo y migración (base de todo)
2. **NOTIF-002** — Schemas
3. **NOTIF-003** — Repository
4. **NOTIF-008** — Variables de entorno (necesario para service)
5. **NOTIF-004** — Service (core logic)
6. **NOTIF-006** — Dependencias y main.py
7. **NOTIF-005** — Router (endpoints)
8. **NOTIF-007** — Scheduler (integra recordatorios + push)
9. **NOTIF-009** — Tests
10. **NOTIF-010** — Documentación

---

## Notas de Implementación

### Convenciones a seguir:
- Estructura por feature: `model.py`, `schema.py`, `repository.py`, `service.py`, `router.py`, `dependencies.py`, `__init__.py`
- `from_attributes = True` en todos los response schemas
- Excepciones de dominio (`NotFoundError`, `DuplicateError`, `BadRequestError`)
- `response_model` explícito en routers
- Status codes HTTP semánticos
- Logging en service para trazabilidad

### Integración con Recordatorios:
- El scheduler (NOTIF-007) consultará recordatorios usando `RecordatorioRepository` existente
- No modificar feature `recordatorios` — solo usar su repository desde `notificaciones.service`
- Importar: `from app.features.recordatorios.repository import RecordatorioRepository`

### Dependencias nuevas en requirements.txt:
- `pywebpush` — para envío de notificaciones push
- `apscheduler` — para job periódico

### VAPID Keys Generation (para desarrollo):
```bash
# Generar claves VAPID (una sola vez)
python -c "from pywebpush import generate_vapid_keys; print(generate_vapid_keys())"
```

---

## Estimación de Esfuerzo

| Task | Complejidad | Estimación |
|------|-------------|------------|
| NOTIF-001 | Baja | 30 min |
| NOTIF-002 | Baja | 20 min |
| NOTIF-003 | Baja | 30 min |
| NOTIF-004 | Media | 60 min |
| NOTIF-005 | Baja | 30 min |
| NOTIF-006 | Baja | 15 min |
| NOTIF-007 | Media | 60 min |
| NOTIF-008 | Baja | 15 min |
| NOTIF-009 | Media | 60 min |
| NOTIF-010 | Baja | 15 min |
| **Total** | | **~5.5 horas** |

---

## Riesgos y Mitigaciones

| Riesgo | Impacto | Mitigación |
|--------|---------|------------|
| pywebpush no compatible con Python version | Alto | Verificar versión en requirements, testear temprano |
| VAPID keys no configuradas en deploy | Alto | Validar al inicio, documentar claramente |
| Scheduler no inicia en producción (gunicorn/uvicorn workers) | Medio | Usar lifespan de FastAPI, considerar worker dedicado |
| Duplicados de notificación para mismo recordatorio | Medio | Ventana deslizante + tracking de notificados |
| iOS PWA requiere instalación | Bajo | Documentar en README, no bloquea backend |

---

## Próximos Pasos

1. Ejecutar NOTIF-001: Crear modelo y migración
2. Ejecutar migración y verificar
3. Continuar con tasks secuenciales