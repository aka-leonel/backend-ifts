# backend-ifts

Backend para el proyecto integrador miIFTS.

## Autenticación y roles

La API usa JWT (Bearer token). Se obtiene con `POST /auth/login` y se envía en
el header `Authorization: Bearer <token>` en los endpoints protegidos.

### Roles de usuario

El modelo `Usuario` tiene un campo `rol` con dos valores posibles:

| Rol          | Valor         | Descripción                                              |
|--------------|---------------|---------------------------------------------------------|
| Estudiante   | `estudiante`  | Rol por defecto al registrarse. Gestiona sus propios datos (cursadas, recursos). |
| Administrador| `admin`       | Además de lo anterior, gestiona el catálogo académico (carreras y materias). |

**Alta de usuarios:** `POST /auth/registro` **siempre** crea usuarios con rol
`estudiante`. El campo `rol` del body se ignora (evita escalada de privilegios).
Los administradores se crean con `python seed.py` (`admin@miifts.ar` / `admin1234`)
o promoviendo un usuario en la base de datos.

### Dependencias de seguridad (`app/features/auth/dependencies.py`)

- `get_current_user` — valida el token y devuelve el usuario autenticado.
  Responde `401` si no hay token o es inválido.
- `require_admin` — además de autenticar, exige `rol == admin`.
  Responde `403` si el usuario es estudiante.

### Matriz de permisos

| Endpoint                                | Público | Estudiante | Admin |
|-----------------------------------------|:-------:|:----------:|:-----:|
| `GET /materias/**` (lecturas)           |   ✅    |     ✅     |  ✅   |
| `POST/PUT/DELETE /materias/carreras/**` |   ❌    |  ❌ (403)  |  ✅   |
| `POST/PUT/DELETE /materias/**` (materias)|  ❌    |  ❌ (403)  |  ✅   |
| `POST /recursos/`                       |   ❌    |     ✅     |  ✅   |
| `PUT /recursos/{id}`                    |   ❌    | ✅ solo dueño |  ✅ solo dueño |
| `DELETE /recursos/{id}`                 |   ❌    | ✅ solo dueño |  ✅ solo dueño |

**Recursos:** `PUT` y `DELETE` verifican que `usuario_actual.id == recurso.usuario_id`.
Si el recurso pertenece a otro usuario se responde `403`; si no existe, `404`.

## Tests

```bash
pip install -r requirements.txt
pytest -q
```

Los tests de autorización están en `tests/test_authorization.py` (roles admin vs
estudiante y ownership de recursos). Los fixtures `auth_headers` (estudiante) y
`admin_headers` (admin) están en `tests/conftest.py`.
