# Notificaciones Push - Contrato API

## Tipos

```typescript
interface PushSubscriptionCreate {
  endpoint: string;      // URL endpoint push navegador
  p256dh: string;        // Clave pública P-256 base64 URL-safe
  auth: string;          // Secreto auth base64 URL-safe
}

interface PushSubscriptionDelete {
  endpoint: string;
}

interface PushSubscriptionResponse {
  id: number;
  usuario_id: number;
  endpoint: string;
  p256dh: string;
  auth: string;
  fecha_creacion: string;  // ISO 8601
}
```

## Endpoints

### POST `/notificaciones/suscripcion` (Auth: JWT)
Registra o actualiza suscripción (upsert via unique constraint usuario_id+endpoint).

**Body:** `PushSubscriptionCreate`  
**Response 201:** `PushSubscriptionResponse`  
**Errores:** 400 (VAPID config/pywebpush), 401, 422

### DELETE `/notificaciones/suscripcion` (Auth: JWT)
Elimina suscripción del usuario.

**Body:** `PushSubscriptionDelete`  
**Response 204** (404 si no existe para este usuario)  
**Errores:** 401, 404

## Payload Push (enviado por backend via webpush)

```json
{
  "title": "Recordatorio: Parcial Algoritmos",
  "body": "Tu parcial es en 30 minutos",
  "data": {
    "recordatorio_id": 12,
    "tipo": "parcial",
    "materia_id": 5,
    "url": "/recordatorios"
  }
}
```
> Frontend SW: `event.notification.data` disponible en `notificationclick`.

## Configuración VAPID

### Backend (`.env`)
```env
VAPID_PUBLIC_KEY=...      # Clave pública (compartir)
VAPID_PRIVATE_KEY=...     # Clave privada (solo backend)
VAPID_CLAIMS_SUB=mailto:admin@miifts.com
```

### Generación
```bash
npx web-push generate-vapid-keys
# Public Key:  BEl62iUYgUwxIvG7...
# Private Key: UUxaiw...
```

### Frontend Usage
```typescript
const vapidPublicKey = import.meta.env.VITE_VAPID_PUBLIC_KEY;
const applicationServerKey = urlBase64ToUint8Array(vapidPublicKey);
const subscription = await reg.pushManager.subscribe({ userVisibleOnly: true, applicationServerKey });
```

## Frontend Service

```typescript
notificacionesService.subscribe(data)      // POST /notificaciones/suscripcion
notificacionesService.unsubscribe(endpoint) // DELETE /notificaciones/suscripcion
```

## Códigos Error

| Endpoint | 400 | 401 | 404 | 422 |
|----------|-----|-----|-----|-----|
| POST /suscripcion | ✓ | ✓ | | ✓ |
| DELETE /suscripcion | | ✓ | ✓ | |

## Requisitos Técnicos

| Requisito | Backend | Frontend |
|-----------|---------|----------|
| HTTPS | Requerido prod | Requerido prod (localhost OK dev) |
| VAPID Keys | Generar par, guardar ambas | `VITE_VAPID_PUBLIC_KEY` |
| Service Worker | — | `public/sw.js` registrado en mount |
| PWA | — | `vite-plugin-pwa` + manifest |
| Permisos Usuario | — | `Notification.requestPermission()` |