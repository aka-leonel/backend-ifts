# Estado Operativo Actual

## Fase: PLANNING

## Próxima Acción
Iniciar implementación de **NOTIF-001**: Modelo y migración de suscripciones push.

## Tasks Planificados (Notificaciones Push - Persona B)

| Task ID | Descripción | Estado | Dependencias |
|---------|-------------|--------|--------------|
| NOTIF-001 | Modelo PushSubscription + migración Alembic | Pendiente | — |
| NOTIF-002 | Schemas Pydantic (Create/Response) | Pendiente | NOTIF-001 |
| NOTIF-003 | Repository (CRUD suscripciones) | Pendiente | NOTIF-002 |
| NOTIF-004 | Service (lógica push + VAPID + cleanup) | Pendiente | NOTIF-003, NOTIF-008 |
| NOTIF-005 | Router (POST/DELETE /notificaciones/suscripcion) | Pendiente | NOTIF-004, NOTIF-006 |
| NOTIF-006 | Dependencias + registro en main.py | Pendiente | NOTIF-004 |
| NOTIF-007 | Scheduler APScheduler (recordatorios → push) | Pendiente | NOTIF-003, NOTIF-004 |
| NOTIF-008 | Variables de entorno VAPID (.env.example) | Pendiente | — |
| NOTIF-009 | Tests de integración (pytest) | Pendiente | NOTIF-005 |
| NOTIF-010 | Actualizar architecture.md / decisions.md | Pendiente | Todas |

## Blockers
- Ninguno identificado.

## Notas
- Requiere agregar `pywebpush` y `apscheduler` a `requirements.txt`
- Claves VAPID deben generarse y configurarse en `.env` antes de probar envío push
- El scheduler se integra con `RecordatorioRepository` existente (no modificar feature recordatorios)