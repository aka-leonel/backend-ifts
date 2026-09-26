# Documentación: Notificaciones Push

## Resumen

Se implementó el sistema completo de **notificaciones push** (Web Push Protocol) para avisar a los usuarios sobre recordatorios próximos a vencer, incluso con la aplicación cerrada.

---

## Arquitectura

```
┌─────────────┐     HTTP/JSON      ┌─────────────┐     Web Push      ┌─────────────┐
│  Frontend   │ ◄─────────────────► │   Backend   │ ◄────────────────► │  Navegador  │
│  (PWA/SW)   │  Suscripción/      │  (FastAPI)  │   Protocolo Push   │  (Usuario)  │
└─────────────┘     Push           └─────────────┘     (VAPID)        └─────────────┘
                           │                    │
                           │                    ▼
                           │           ┌─────────────┐
                           └──────────►│  APScheduler│
                                       │  (Job cada 5m)│
                                       └─────────────┘
```

---

## Componentes Backend

### 1. Modelo de Datos (`app/features/notificaciones/model.py`)

```python
PushSubscription:
  - id: PK
  - usuario_id: FK → usuarios.id
  - endpoint: URL única del push service (FCM, Mozilla, etc.)
  - p256dh: Clave pública ECDH (base64 URL-safe)
  - auth: Secreto de autenticación (base64 URL-safe)
  - fecha_creacion: Timestamp
  
  Constraint único: (usuario_id, endpoint) — evita duplicados
```

### 2. Endpoints API (`app/features/notificaciones/router.py`)

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| `POST` | `/notificaciones/suscripcion` | Registra/actualiza suscripción del usuario autenticado |
| `DELETE` | `/notificaciones/suscripcion` | Elimina suscripción por endpoint |

**Autenticación:** JWT requerido (header `Authorization: Bearer <token>`)

### 3. Servicio de Envío (`app/features/notificaciones/service.py`)

- **`subscribe()`**: Registra o actualiza suscripción (maneja duplicados actualizando claves)
- **`unsubscribe()`**: Elimina suscripción del usuario
- **`send_push()`**: Envía notificación individual via `pywebpush` con claves VAPID
- **`send_push_to_user()`**: Envía a todas las suscripciones del usuario + limpieza automática de endpoints inválidos (404/410)

### 4. Job Programado (`app/features/notificaciones/scheduler.py`)

- Se ejecuta **cada 5 minutos** (configurable: `PUSH_SCHEDULER_INTERVAL_MINUTES`)
- Busca recordatorios con `fecha` en los **próximos 15 minutos** (configurable: `PUSH_REMINDER_WINDOW_MINUTES`)
- Para cada recordatorio, envía push al usuario dueño
- **Payload enviado:**
  ```json
  {
    "title": "Recordatorio",
    "body": "Título del recordatorio",
    "data": {
      "recordatorio_id": 123,
      "tipo": "examen",
      "materia_id": 456
    }
  }
  ```

### 5. Integración FastAPI (`app/main.py`)

- `AsyncIOScheduler` inicia en `lifespan` (startup)
- Job registrado con intervalo configurable
- Shutdown graceful al apagar la app

---

## Variables de Entorno

```env
# Claves VAPID (generar con: python -c "from pywebpush import generate_vapid_keys; print(generate_vapid_keys())")
VAPID_PUBLIC_KEY=BEl62iUYgU...
VAPID_PRIVATE_KEY=uV2G...
VAPID_CLAIMS_SUB=mailto:admin@miifts.com

# Scheduler
PUSH_REMINDER_WINDOW_MINUTES=15    # Ventana anticipación recordatorios
PUSH_SCHEDULER_INTERVAL_MINUTES=5  # Frecuencia job
```

---

## Flujo de Funcionamiento

### 1. Suscripción (Frontend → Backend)
```
Usuario click "Activar notificaciones"
       │
       ▼
navigator.serviceWorker.register('/sw.js')
       │
       ▼
reg.pushManager.subscribe({ userVisibleOnly: true, applicationServerKey: VAPID_PUBLIC_KEY })
       │
       ▼
POST /notificaciones/suscripcion { endpoint, p256dh, auth }
       │
       ▼
Backend guarda en BD (PushSubscription)
```

### 2. Envío Automático (Backend → Navegador)
```
Cada 5 minutos (APScheduler)
       │
       ▼
SELECT * FROM recordatorios WHERE fecha BETWEEN now() AND now() + 15min
       │
       ▼
Para cada recordatorio:
  - Obtener suscripciones del usuario
  - pywebpush.send(..., vapid_keys)
  - Si 404/410 → DELETE suscripción inválida
```

### 3. Recepción (Service Worker → Usuario)
```
Evento 'push' en sw.js
       │
       ▼
self.registration.showNotification(title, options)
       │
       ▼
Usuario ve notificación nativa del SO
       │
       ▼
Click → notificationclick → clients.openWindow('/recordatorios/{id}')
```

---

## Frontend Requerido

Ver documento completo: **`TAREAS_FRONT_PERSONA_B.md`**

**Resumen tareas frontend:**
1. **Service Worker** + `pushManager.subscribe()` + envío al backend (4 pts)
2. **Círculo indicador** en ícono campana con contador de pendientes (2 pts)

---

## Compatibilidad

| Plataforma | Funciona | Notas |
|------------|----------|-------|
| Android (Chrome/Edge/Firefox) | ✅ | Incluso con app cerrada |
| iOS 16.4+ (Safari) | ⚠️ | **Solo si PWA instalada** ("Añadir a pantalla de inicio") |
| Desktop (Chrome/Edge/Firefox) | ✅ | Con pestaña cerrada si browser lo permite |
| Desarrollo (localhost) | ✅ | HTTPS no requerido en local |

---

## Tests

| Tipo | Archivos | Tests |
|------|----------|-------|
| Unitarios | `tests/features/notificaciones/test_*.py` | 99 passed |
| Integración | `tests/features/notificaciones/test_integration.py` | 19 passed |
| **Total** | | **118 passed** |

---

## Dependencias Agregadas

```txt
pywebpush>=1.13    # Envío Web Push con VAPID
apscheduler>=3.10  # Job scheduler async
```

---

## Próximos Pasos

1. Frontend implemente Service Worker y suscripción
2. Configurar `VITE_VAPID_PUBLIC_KEY` en frontend (misma que backend)
3. Probar en staging: Android + iOS (PWA instalada) + Desktop
4. Documentar para usuarios: "Cómo activar notificaciones"