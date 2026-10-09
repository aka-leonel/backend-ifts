# Stack Tecnológico

## Backend
| Capa | Tecnología | Versión |
|------|------------|---------|
| Framework | FastAPI | 0.115.5 |
| ORM | SQLAlchemy | 2.0.36 |
| Migraciones | Alembic | 1.14.0 |
| BD | SQLite (dev) / PostgreSQL (prod) | — |
| Validación | Pydantic v2 | 2.13.4 |
| Auth | python-jose (JWT HS256), bcrypt | 3.3.0 / 4.0.1 |
| Push | pywebpush, APScheduler | ≥1.13 / ≥3.10 |
| Testing | pytest, pytest-cov | 8.3.3 / 5.0.0 |
| Calidad | black, pylint | 24.8.0 / 3.2.7 |

## Frontend
| Capa | Tecnología | Versión |
|------|------------|---------|
| Runtime | React | 19.2.8 |
| Lenguaje | TypeScript | 6.0.2 |
| Build | Vite | 8.2 |
| Estilos | Tailwind CSS v4 | 4.3.3 |
| HTTP | Fetch nativo + `apiClient` wrapper | — |
| Auth | JWT 24h (localStorage + memoria) | — |
| PWA | vite-plugin-pwa (Workbox) | 1.3 |
| Testing | Vitest + RTL + MSW | 5.0.2 |

---

## Arquitectura General

**Backend:** Feature-based 4 capas por dominio (`model → schema → repository → service → router`). Excepciones de dominio unificadas (`app/shared/exceptions.py`). Paginación genérica (`PaginationParams` + `PaginatedResponse`).

**Frontend:** Feature-based + hooks transversales (`useApiForm`, `useAsyncQuery`, `usePush`). `apiClient` único con interceptors (Bearer, 401→logout, 422 parse). Navegación `switch(screen)` en memoria (sin React Router). Componentes UI reutilizables (`FormModal`, `EntityForm`, `ListState`, `Paginador`, `ByteWidget`).

---

## Variables de Entorno

### Backend (`.env`)
```env
DATABASE_URL=sqlite:///./miifts.db
SECRET_KEY=cambiar-en-produccion
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
FRONTEND_RESET_PASSWORD_URL=http://localhost:5173/reset-password
VAPID_PUBLIC_KEY=...
VAPID_PRIVATE_KEY=...
VAPID_CLAIMS_SUB=mailto:admin@miifts.com
PUSH_SCHEDULER_INTERVAL_MINUTES=5
```

### Frontend (`.env`)
```env
VITE_API_URL=http://localhost:8000
VITE_VAPID_PUBLIC_KEY=...   # Igual que backend
```

---

## Comandos Clave

```bash
# Backend
uvicorn app.main:app --reload          # Dev
alembic upgrade head                   # Migraciones
python seed.py                         # Datos iniciales
pytest --cov=app                       # Tests

# Frontend
npm run dev                            # Dev (5173)
npm run build                          # Build prod
npm run gen:api                        # Tipos desde openapi.json (backend corriendo)
```