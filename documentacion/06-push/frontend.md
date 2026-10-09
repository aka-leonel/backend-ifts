# Notificaciones Push - Frontend

## Integración (no hay pantalla dedicada)

- **`App.tsx` mount:** Registro SW, solicitud permisos, suscripción automática si `permission === "granted"`
- **`RecordatoriosScreen` mount:** Trigger adicional `subscribe()`
- **NavBar:** Badge "●" verde si suscripción activa
- **`usePush` hook:** Lógica centralizada

---

## Service Worker (`public/sw.js` - workbox via `vite-plugin-pwa`)

```javascript
self.addEventListener("push", (event) => {
  const data = event.data.json();
  event.waitUntil(self.registration.showNotification(data.title, {
    body: data.body,
    icon: "/icons/icon-192.png",
    badge: "/icons/badge-72.png",
    vibrate: [200, 100, 200],
    data: data.data || {},           // { recordatorio_id, tipo, materia_id, url }
    actions: [{action:"open",title:"Ver"}, {action:"dismiss",title:"Descartar"}],
    requireInteraction: true,
  }));
});

self.addEventListener("notificationclick", (event) => {
  event.notification.close();
  const url = event.notification.data?.url || "/recordatorios";
  event.waitUntil(clients.openWindow(url));
});
```

---

## Hook `usePush` (`hooks/usePush.ts`)

```typescript
export function usePush() {
  const { token, usuario } = useAuth();
  const [subscription, setSubscription] = useState(null);
  const [permission, setPermission] = useState("default");
  const [isSupported, setIsSupported] = useState(false);

  useEffect(() => {
    const supported = "serviceWorker" in navigator && "PushManager" in window;
    setIsSupported(supported);
    setPermission(Notification.permission);
    if (!supported) return;
    navigator.serviceWorker.register("/sw.js");
  }, []);

  const requestPermission = async () => {
    const perm = await Notification.requestPermission();
    setPermission(perm);
    return perm === "granted";
  };

  const subscribe = async () => {
    if (permission !== "granted") { const ok = await requestPermission(); if (!ok) return; }
    const reg = await navigator.serviceWorker.ready;
    const sub = await reg.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey: urlBase64ToUint8Array(import.meta.env.VITE_VAPID_PUBLIC_KEY),
    });
    await fetch("/notificaciones/suscripcion", {
      method: "POST",
      headers: { "Content-Type": "application/json", "Authorization": `Bearer ${token}` },
      body: JSON.stringify({
        endpoint: sub.endpoint,
        p256dh: arrayBufferToBase64(sub.getKey("p256dh")),
        auth: arrayBufferToBase64(sub.getKey("auth")),
      }),
    });
    setSubscription(sub);
  };

  const unsubscribe = async () => {
    // DELETE /notificaciones/suscripcion + sub.unsubscribe()
  };

  return { isSupported, permission, subscription, requestPermission, subscribe, unsubscribe };
}
```

**Helpers:** `urlBase64ToUint8Array()`, `arrayBufferToBase64()` para claves VAPID.

---

## Integración en `App.tsx`

```typescript
useEffect(() => {
  if (!isSupported || !isAuthenticated) return;
  if (permission === "granted") subscribe().catch(console.error);
}, [isAuthenticated, isSupported, permission, subscribe]);
```

## Integración en `RecordatoriosScreen`

```typescript
useEffect(() => {
  if (permission === "granted") subscribe().catch(console.error);
}, [permission, subscribe]);
```

## Badge Nav (opcional)

```tsx
<NavItem>
  <Icon name="bell" />
  <span>Recordatorios</span>
  {subscription && <Badge className="ml-1">●</Badge>}
</NavItem>
```

## Variables de Entorno Frontend

```env
VITE_API_URL=http://localhost:8000
VITE_VAPID_PUBLIC_KEY=...   # MISMA que backend VAPID_PUBLIC_KEY
```

## Estados UI

| Estado | UI | Acción |
|--------|-----|--------|
| `isSupported=false` | Sin indicador | Push no disponible |
| `permission="default"` | Botón "Activar notificaciones" | `requestPermission()` |
| `permission="denied"` | "Habilita en configuración del navegador" | Link a settings |
| `permission="granted"`, no suscrito | Botón "Conectar notificaciones" | `subscribe()` |
| Suscrito | Badge verde "Push activo" | `unsubscribe()` disponible |

## Testing Push (Dev)

```bash
# 1. Generar claves
npx web-push generate-vapid-keys
# 2. Agregar a .env backend + frontend
# 3. Backend: pip install pywebpush apscheduler
# 4. Build frontend + preview (SW solo en build)
npm run build && npm run preview
```

## Limitaciones

| Plataforma | Limitación |
|------------|------------|
| iOS < 16.4 | No soportado |
| iOS 16.4+ | Requiere PWA instalada |
| Android | Funciona app cerrada |
| Incógnito/Privado | SW no persiste |
| Todos | HTTPS obligatorio (localhost OK dev) |