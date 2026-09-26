# TAREAS FRONTEND — Persona B: Recordatorios y Notificaciones Push

> Documento de requerimientos para el equipo de frontend. Basado en **SPRINT_7.md** y la implementación backend completada.

---

## Contexto General

El backend ya implementa la infraestructura completa de notificaciones push (Web Push Protocol con VAPID). El frontend debe:

1. **Registrar Service Worker** y manejar ciclo de vida
2. **Solicitar permiso** de notificaciones (desde gesto de usuario)
3. **Suscribirse** usando `pushManager.subscribe()` y enviar suscripción al backend
4. **Mostrar indicador visual** (círculo) cuando hay recordatorios pendientes
5. **Manejar notificaciones** recibidas (foreground/background)

---

## Endpoints Backend Disponibles

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| `POST` | `/notificaciones/suscripcion` | Registra/actualiza suscripción push del usuario autenticado |
| `DELETE` | `/notificaciones/suscripcion` | Elimina suscripción push del usuario autenticado |

### Payload POST `/notificaciones/suscripcion`
```json
{
  "endpoint": "https://fcm.googleapis.com/fcm/send/...",
  "p256dh": "BEl62iUYgU...",  // Clave pública ECDH (base64 URL-safe, 87+ chars)
  "auth": "dGhpcyBpcyBhIHNlY3JldA=="  // Secreto auth (base64 URL-safe, 24+ chars)
}
```

### Respuesta Exitosa (201)
```json
{
  "id": 1,
  "usuario_id": 1,
  "endpoint": "https://fcm.googleapis.com/fcm/send/...",
  "p256dh": "BEl62iUYgU...",
  "auth": "dGhpcyBpcyBhIHNlY3JldA==",
  "fecha_creacion": "2026-09-26T10:30:00Z"
}
```

### Payload DELETE `/notificaciones/suscripcion`
```json
{
  "endpoint": "https://fcm.googleapis.com/fcm/send/..."
}
```

---

## Variables de Entorno Requeridas (Frontend)

| Variable | Descripción | Ejemplo |
|----------|-------------|---------|
| `VITE_VAPID_PUBLIC_KEY` | Clave pública VAPID del backend (base64 URL-safe) | `BEl62iUYgU...` |

> **Nota:** La clave pública VAPID debe coincidir con `VAPID_PUBLIC_KEY` configurada en el backend. Se genera con: `python -c "from pywebpush import generate_vapid_keys; print(generate_vapid_keys())"`

---

## Tarea 1: Service Worker y Suscripción Push (4 pts)

### 1.1 Registrar Service Worker
- Crear/registrar `sw.js` en el scope raíz (`/`)
- Manejar eventos: `install`, `activate`, `push`, `notificationclick`, `notificationclose`
- Registrar solo en entorno seguro (HTTPS o localhost)

```javascript
// Ejemplo registro
if ('serviceWorker' in navigator) {
  navigator.serviceWorker.register('/sw.js')
    .then(reg => console.log('SW registrado:', reg.scope))
    .catch(err => console.error('SW error:', err));
}
```

### 1.2 Solicitar Permiso (Gesto de Usuario)
- **NUNCA** pedir permiso al cargar la página
- Disparar desde acción explícita: botón "Activar notificaciones", click en campana, etc.
- Mostrar UI explicativa antes de pedir permiso (rationale)

```javascript
// Solo tras gesto de usuario
async function solicitarPermiso() {
  const permission = await Notification.requestPermission();
  if (permission === 'granted') {
    await suscribirPush();
  }
}
```

### 1.3 Suscripción con `pushManager.subscribe()`
```javascript
async function suscribirPush() {
  const reg = await navigator.serviceWorker.ready;
  
  const subscription = await reg.pushManager.subscribe({
    userVisibleOnly: true,
    applicationServerKey: urlBase64ToUint8Array(VITE_VAPID_PUBLIC_KEY)
  });
  
  // Enviar al backend
  await fetch('/api/notificaciones/suscripcion', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
    body: JSON.stringify({
      endpoint: subscription.endpoint,
      p256dh: arrayBufferToBase64(subscription.getKey('p256dh')),
      auth: arrayBufferToBase64(subscription.getKey('auth'))
    })
  });
}
```

**Funciones auxiliares necesarias:**
- `urlBase64ToUint8Array(base64String)` — convierte clave VAPID a Uint8Array
- `arrayBufferToBase64(buffer)` — convierte ArrayBuffer a base64 URL-safe

### 1.4 Manejo de Eventos Push en SW
```javascript
// sw.js
self.addEventListener('push', event => {
  const data = event.data?.json() || {};
  const title = data.title || 'Recordatorio';
  const options = {
    body: data.body || 'Tienes un recordatorio pendiente',
    icon: '/icons/icon-192.png',
    badge: '/icons/badge-72.png',
    data: data.data || {}, // { recordatorio_id, tipo, materia_id }
    actions: [
      { action: 'open', title: 'Ver' },
      { action: 'dismiss', title: 'Descartar' }
    ],
    requireInteraction: true
  };
  
  event.waitUntil(self.registration.showNotification(title, options));
});

self.addEventListener('notificationclick', event => {
  event.notification.close();
  if (event.action === 'open' && event.notification.data?.recordatorio_id) {
    event.waitUntil(clients.openWindow(`/recordatorios/${event.notification.data.recordatorio_id}`));
  }
});
```

### 1.5 Desuscripción (Logout / Configuración)
- Botón "Desactivar notificaciones" en settings
- Llama `pushManager.unsubscribe()` + `DELETE /notificaciones/suscripcion`

---

## Tarea 2: Círculo Indicador en Ícono de Recordatorios (2 pts)

### Requisito
Mostrar un **badge/círculo rojo** con contador en el ícono de recordatorios (campana) cuando existan recordatorios **pendientes/no leídos** para el usuario actual.

### Comportamiento
| Estado | Visual |
|--------|--------|
| 0 recordatorios pendientes | Sin círculo (ícono limpio) |
| 1-9 recordatorios | Círculo rojo con número (ej: "3") |
| 10+ recordatorios | Círculo rojo con "9+" |

### Fuente de Datos
- **Opción A (Recomendada):** Endpoint existente `GET /recordatorios` con filtro `?estado=pendiente` o similar
- **Opción B:** Nuevo endpoint dedicado `GET /recordatorios/pendientes/count`
- **Opción C:** WebSocket / Server-Sent Events para tiempo real (si ya existe infraestructura)

### Integración con Push
- Al recibir push en foreground: actualizar contador inmediatamente
- Al click en notificación (abre app): recargar contador
- Al marcar recordatorio como leído/completado: decrementar contador

### Implementación Sugerida (React/Vue/Svelte)
```jsx
// Componente BadgeNotificaciones
function BadgeNotificaciones({ count }) {
  if (count === 0) return null;
  return (
    <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full h-5 w-5 flex items-center justify-center">
      {count > 9 ? '9+' : count}
    </span>
  );
}

// En componente padre
const [pendientes, setPendientes] = useState(0);

useEffect(() => {
  // Carga inicial
  fetch('/api/recordatorios?estado=pendiente&limit=1')
    .then(r => r.json())
    .then(data => setPendientes(data.total || data.length));
  
  // Escuchar eventos push en foreground
  navigator.serviceWorker.addEventListener('message', handlePushMessage);
}, []);
```

---

## Tarea 3: Consideraciones de Plataforma (Documentación)

### Android (Chrome, Edge, Firefox, Samsung Internet)
- ✅ Push funciona con PWA **cerrada**
- ✅ Service Worker persiste en background
- ✅ Notificaciones aparecen en bandeja del sistema

### iOS / iPadOS (16.4+)
- ⚠️ **Solo funciona si PWA instalada** ("Añadir a pantalla de inicio")
- ⚠️ Push **NO funciona** si abren la web en Safari sin instalar
- ✅ Una vez instalada, comportamiento similar a Android
- 📱 Requiere manifest.json con `display: "standalone"` y icons

### Desktop (Chrome, Edge, Firefox, Safari)
- ✅ Funciona con pestaña cerrada (si browser permite background SW)
- ⚠️ Safari macOS: requiere permiso explícito + PWA instalada en algunos casos

### Desarrollo Local
- ✅ `localhost` y `127.0.0.1` son considerados "secure contexts"
- ✅ No requiere HTTPS en desarrollo
- ⚠️ Para probar en red local (móvil), usar `ngrok` / `cloudflared` / `localhost.run` para HTTPS

---

## Tarea 4: Fallback Sin Push (Opcional / Mejora)

> "Alternativa sin push: mostrar los recordatorios dentro de la app al abrirla. No requiere nada de lo anterior, pero no avisa con la app cerrada."

### Implementación Mínima
- Si `Notification.permission === 'denied'` o push no disponible:
  - Mostrar banner: "Activa notificaciones para recibir avisos"
  - Al abrir app, consultar `GET /recordatorios?proximos=true` y mostrar lista
  - No bloquear funcionalidad principal

---

## Checklist de Validación (Definition of Done)

| ✅ | Criterio |
|----|----------|
| 1 | Service Worker registrado y funcional en HTTPS/localhost |
| 2 | Permiso solicitado **solo tras gesto de usuario** |
| 3 | Suscripción exitosa → `POST /notificaciones/suscripcion` 201 |
| 4 | Clave VAPID pública usada correctamente (`applicationServerKey`) |
| 5 | Push recibido en **foreground** → muestra notificación nativa |
| 6 | Push recibido en **background/cerrada** → muestra notificación nativa |
| 7 | Click en notificación → navega a recordatorio correspondiente |
| 8 | Círculo indicador muestra contador correcto de pendientes |
| 9 | Contador se actualiza al recibir push / marcar leído |
| 10 | Desuscripción funciona (logout / settings) |
| 11 | iOS: probado con PWA instalada ("Añadir a pantalla de inicio") |
| 12 | Android: probado con app cerrada |
| 13 | Manejo graceful si permiso denegado / push no soportado |
| 14 | Sin errores en consola (SW registration, push, fetch) |

---

## Archivos Referencia Backend (para desarrollo frontend)

```
backend-ifts/
├── app/features/notificaciones/
│   ├── router.py          # Endpoints POST/DELETE
│   ├── schema.py          # Schemas Pydantic (validación)
│   └── service.py         # Lógica envío push (pywebpush)
├── .env.example           # VAPID_PUBLIC_KEY example
└── requirements.txt       # pywebpush, apscheduler
```

---

## Próximos Pasos / Coordinación

1. **Frontend team**: Implementar Tareas 1 y 2 en paralelo
2. **Backend team**: Proveer `VITE_VAPID_PUBLIC_KEY` para entorno de staging/prod
3. **QA**: Probar matriz completa (Android/iOS/Desktop × PWA instalada/no × foreground/background)
4. **Documentación usuario**: Guía "Cómo activar notificaciones" con capturas por plataforma

---

## Contacto

- **Backend API**: Revisar `app/features/notificaciones/router.py` para detalles de validación/errores
- **VAPID Keys**: Generar nuevas para producción (no usar las de ejemplo)
- **Dudas**: Consultar implementación service (`send_push_to_user`) para formato de payload `data`