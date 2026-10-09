# Push - Decisiones Clave

| ID | Decisión | Rationale |
|----|----------|-----------|
| **D021** | Scheduler APScheduler **condicional** (`try/except ImportError`) | Sin `apscheduler` → warning, app funciona sin push; fácil habilitar en prod instalando dependencia; config via env var |
| **D022** | Limpieza auto suscripciones 404/410 en cada envío batch | Limpieza inmediata evita reintentos futuros; delete físico simple; batch delete eficiente (`IN` query) |
| **D023** | Upsert suscripción via `UniqueConstraint(usuario_id, endpoint)` + catch `IntegrityError` | Funciona SQLite + PostgreSQL; actualiza claves si cambian (rotación keys navegador); idempotente |
| **D024** | Hook `usePush` centralizado | Single responsibility, reusable, fácil testear/mockear, separa lógica push de UI |
| **D025** | Auto-suscripción en mount (`App.tsx` + `RecordatoriosScreen`) | UX zero-config para usuarios con permiso concedido; idempotente (backend upsert); no molesta si permiso denegado |
| **D026** | `VITE_VAPID_PUBLIC_KEY` en build (clave pública no secreta) | Cero request extra en mount; clave pública diseñada para ser pública; build-time injection via Vite |
| **D027** | `vite-plugin-pwa` genera SW automático (Workbox) | Integrado en build Vite; auto-update habilitado; config declarativa en `vite.config.ts` |
| **Requisitos plataforma documentados** | iOS 16.4+ requiere PWA instalada; Android funciona app cerrada; HTTPS obligatorio | Decisiones de UX informadas; evita sorpresas en prod |

## Referencias

| Decisión | Backend | Frontend |
|----------|---------|----------|
| D021 | `app/main.py` lifespan, `app/features/notificaciones/scheduler.py` | — |
| D022 | `app/features/notificaciones/service.py` (`send_push`, `send_push_to_user`) | — |
| D023 | `app/features/notificaciones/service.py` (`subscribe`), `model.py` (UniqueConstraint) | — |
| D024 | — | `hooks/usePush.ts` |
| D025 | — | `src/App.tsx`, `features/recordatorios/RecordatoriosScreen.tsx` |
| D026 | — | `.env` frontend `VITE_VAPID_PUBLIC_KEY`, `hooks/usePush.ts` |
| D027 | — | `vite.config.ts` (vite-plugin-pwa), `public/sw.js` (generado) |