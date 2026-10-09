# Notificaciones Push - Backend

## Endpoints (auth: usuario)

| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | `/notificaciones/suscripcion` | Registra/actualiza suscripción (endpoint, p256dh, auth) |
| DELETE | `/notificaciones/suscripcion` | Elimina por endpoint |

## Modelo

```python
PushSubscription: id, usuario_id(FK), endpoint(único), p256dh, auth, fecha_creacion
UniqueConstraint(usuario_id, endpoint) → upsert en subscribe()
```

## Service (`PushNotificationService`)

### Configuración VAPID
- `_load_vapid_config()`: Lee `VAPID_PUBLIC_KEY`, `VAPID_PRIVATE_KEY`, `VAPID_CLAIMS_SUB` de `.env`; valida existencia + `pywebpush` instalado
- `_get_vapid_claims()` → `{"sub": VAPID_CLAIMS_SUB}`

### Gestión Suscripciones
- `subscribe(usuario_id, endpoint, p256dh, auth)`:
  - Intenta `CREATE` → si `IntegrityError` (unique constraint) → `UPDATE` p256dh, auth (race condition: rollback + re-check)
  - Retorna `PushSubscriptionResponse`
- `unsubscribe(usuario_id, endpoint)` → elimina si existe → bool

### Envío Push
- `send_push(subscription, title, body, data?)`:
  - `webpush()` con `vapid_private_key`, `vapid_claims`, payload JSON `{title, body, data}`
  - Retorna `True` si éxito; `False` si `WebPushException` status 404/410 (endpoint gone); otros errores propagan
- `send_push_to_user(usuario_id, title, body, data?)`:
  - Obtiene todas suscripciones del usuario
  - Envía a cada una → cuenta `sent`, `failed`, recolecta `invalid_endpoints`
  - **Limpieza auto**: `repository.delete_expired_or_invalid(invalid_endpoints)` batch
  - Retorna `{sent, failed, invalid_endpoints}`

### Limpieza Manual
- `cleanup_invalid_subscriptions(endpoints[])` → batch delete

## Scheduler APScheduler (`app/main.py` + `scheduler.py`)

```python
# lifespan startup
if APSCHEDULER_AVAILABLE:
    interval = int(os.getenv("PUSH_SCHEDULER_INTERVAL_MINUTES", "5"))
    scheduler = AsyncIOScheduler()
    scheduler.add_job(check_and_send_reminder_notifications_default, "interval", minutes=interval, id="push_reminder_job")
    scheduler.start()
else:
    logger.warning("apscheduler no instalado; job no se ejecutará")

# lifespan shutdown
scheduler.shutdown(wait=True)
```

- Job: `check_and_send_reminder_notifications_default()` → busca recordatorios próximos → `send_push_to_user()` con `data = {recordatorio_id, tipo, materia_id, url_detalle}`

## Router

```python
POST /suscripcion → service.subscribe(current_user.id, endpoint, p256dh, auth) → 201 PushSubscriptionResponse
DELETE /suscripcion → service.unsubscribe(current_user.id, endpoint) → 204 (404 si no existe)
```

## Dependencias

```python
get_notificacion_service(db) → PushNotificationService(db)
```

## Variables de Entorno

```env
VAPID_PUBLIC_KEY=...           # Compartir con frontend
VAPID_PRIVATE_KEY=...          # Solo backend
VAPID_CLAIMS_SUB=mailto:admin@miifts.com
PUSH_SCHEDULER_INTERVAL_MINUTES=5
```

## Requisitos Plataforma

| Plataforma | Requisito |
|------------|-----------|
| Android Chrome/Edge/Firefox | Funciona con app cerrada |
| iOS Safari 16.4+ | **Requiere PWA instalada** ("Añadir a pantalla de inicio") |
| iOS < 16.4 | No soportado |
| Desktop | Funciona background |
| Todos | **HTTPS obligatorio** (localhost OK en dev) |

## Errores

| Código | Endpoint | Causa |
|--------|----------|-------|
| 400 | POST/DELETE | VAPID config faltante, pywebpush no instalado |
| 401 | POST/DELETE | No autenticado |
| 404 | DELETE | Suscripción no existe para usuario |
| 422 | POST | Validación (endpoint/p256dh/auth requeridos) |
| 500 | Interno | Error webpush (red, claves VAPID inválidas) |