# Estrategia y Estado de Testing - miIFTS

## Framework
- **pytest** 8.3.3 con **pytest-cov** 5.0.0.
- Configuración en `pytest.ini`: `testpaths = tests`, `python_files = test_*.py`.

## Configuración de Test
- Base de datos SQLite en memoria (`sqlite:///:memory:`) con `StaticPool` para compartir conexión entre sesiones.
- `FastAPI TestClient` con `app.dependency_overrides[get_db]` para inyectar sesión de test sin tocar la DB de desarrollo.
- `tests/conftest.py` contiene todos los fixtures compartidos.

## Fixtures Disponibles (tests/conftest.py)
| Fixture | Scope | Descripción |
|---------|-------|-------------|
| `db_session` | function | Crea tablas, entrega sesión, hace drop al final |
| `client` | function | TestClient con override de `get_db` |
| `carrera_test` | function | IFTS + Carrera creados en BD de test |
| `usuario_payload` | function | Payload válido para POST /auth/registro |
| `usuario_registrado` | function | Usuario registrado vía API, devuelve payload + response |
| `auth_headers` | function | Header `Authorization: Bearer <token>` del usuario registrado |

## Archivos de Test
| Archivo | Alcance | Estado |
|---------|---------|--------|
| `tests/test_auth.py` | Registro, login, get_current_user, verify | 6 tests, todos pasan |
| `tests/test_materias.py` | CRUD carreras y materias | Tests activos + 2 xfail pendientes |
| `test_api.py` | Script manual (no pytest) | Testing manual con requests |
| `api-requests.http` | Colección de requests | Insomnia/Hoppscotch |

## Tests Existentes
- **test_registro_exitoso**: 201, email/nombre/rol correctos, sin password_hash.
- **test_registro_email_duplicado**: 409.
- **test_login_exitoso**: 200, access_token + token_type + usuario.
- **test_login_credenciales_invalidas**: 401 (email/password incorrectos).
- **test_get_current_user_token_valido**: 200, datos del usuario.
- **test_get_current_user_token_invalido**: 401.
- **test_get_current_user_sin_token**: 401.
- **test_crear_carrera_con_auth**: 201 con auth_headers.
- **test_actualizar_carrera**: 200, campos conservados si no enviados.
- **test_actualizar_carrera_inexistente**: 404.
- **test_eliminar_carrera**: 204, luego 404 al reutilizar.
- **test_eliminar_carrera_inexistente**: 404.
- **test_crear_materia**: 201, código correcto.
- **test_crear_materia_codigo_duplicado**: 409.

## Tests xfail (pendientes)
- **test_crear_carrera_sin_auth**: Espera 401, hoy devuelve 201 (POST /materias/carreras sin `Depends(get_current_user)`). Pendiente Integrante 1.
- **test_crear_materia_codigo_duplicado**: Espera 409, hoy explota con 500 (MateriaRepository no atrapa IntegrityError). Pendiente de corrección en service.py/router.py.

## Categorías de Test
- **Funcionales**: CRUD completo por feature.
- **Integración**: Router → Service → Repository → DB completo.
- **Negativas**: Email duplicado, credenciales inválidas, recursos no encontrados.
- **Seguridad**: Sin token, token inválido, acceso sin auth (pendiente).

## Limitaciones Conocidas
- `tests/test_materias.py` no tiene tests para recordatorios ni recursos (sin fixtures de auth para esos features).
- `test_api.py` es un script manual, no integrado en pytest.
- No hay tests para los routers de recursos (`convenios.py`, `recursos.py`, `talentotech.py`).
- Los tests de materias necesitan que `get_usuario_actual()` en el router sea reemplazado por JWT real.

## Criterios de Aceptación de Testing
- Todos los endpoints principales cubiertos por al menos un test.
- Tests pasan en pipeline (pytest sin fallas).
- Cobertura de código medible con pytest-cov.
- xfail documentados con razón y linked a tarea de sprint.