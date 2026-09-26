# Sprint 7 — Reparto de tareas

Reparto equitativo por complejidad entre 3 personas. Las tareas relacionadas o dependientes quedan con la misma persona, con front y back incluidos.

**Escala de complejidad (puntos):** 1 = trivial · 2 = simple · 3 = media · 5 = compleja · 8 = grande.

| Persona | Foco | Puntos |
|---|---|---|
| A | Flujo de materias y cursada | 15 |
| B | Recordatorios y notificaciones push | 14 |
| C | Administración y visibilidad | 14 |

---

## Persona A — Flujo de materias y cursada (15 pts)

Todo gira alrededor del modal de agregar materia y del detalle de la materia.

| Tarea | Lado | Pts |
|---|---|---|
| Devolver el `nombre` de la materia en el objeto al agregarla | Back | 1 |
| Modal de agregar materia: por primera vez solo debe mostrar MATERIA y "ESTÁS CURSANDO" | Front | 2 |
| Mostrar NOTA 1, NOTA 2 y FINAL recién al entrar a la materia | Front | 3 |
| Signo de pregunta clickeable que abre una card: si la materia tiene un solo parcial, se carga una sola nota y se computa al pasar a "no está cursando" | Front | 1 |
| El porcentaje de progreso se calcula sobre el TOTAL de materias de la carrera, no sobre las materias en curso | Front | 2 |
| Por defecto mostrar "cursando" primero y "total" al final | Front | 1 |
| Botón **Recursar** en materias desaprobadas: aparece al editar la materia, abre el modal "estás cursando" y desaparece. Toast de confirmación ("¿Seguro que vas a recursar? Se borran las notas viejas y pasa a cursando") | Front | 5 |

**Orden sugerido**
1. Back de una línea (`nombre` en el objeto).
2. Modal de agregar materia.
3. Notas en el detalle, junto con su "?".
4. Progreso y orden por defecto.
5. Recursar al final, porque reutiliza el modal.

---

## Persona B — Recordatorios y notificaciones push (14 pts)

| Tarea | Lado | Pts |
|---|---|---|
| Modelo de suscripciones (`usuario_id`, `endpoint`, `p256dh`, `auth`), migración de Alembic y endpoints `POST` y `DELETE /notificaciones/suscripcion` | Back | 3 |
| Envío con `pywebpush` y claves VAPID en variables de entorno. Borrar suscripciones que devuelvan 404 o 410 | Back | 3 |
| Job periódico (APScheduler) que busque recordatorios próximos a vencer y mande el push | Back | 2 |
| Service Worker, pedido de permiso (desde un gesto del usuario) y suscripción con `pushManager.subscribe()` | Front | 4 |
| Círculo indicador en el ícono de recordatorios cuando hay alguno pendiente | Front | 2 |

**Orden sugerido**
1. Back (modelo, endpoints, envío y job).
2. Service Worker y suscripción, que dependen de los endpoints.
3. El círculo indicador es independiente y puede hacerse en paralelo.

**Notas técnicas**
- **Android (Chrome, Edge, Firefox):** funciona incluso con la PWA cerrada.
- **iOS 16.4 o más nuevo:** solo funciona si la PWA está instalada con "Añadir a pantalla de inicio".
- **HTTPS:** obligatorio (`localhost` sirve en desarrollo).
- **Alternativa sin push:** mostrar los recordatorios dentro de la app al abrirla. No requiere nada de lo anterior, pero no avisa con la app cerrada.

---

## Persona C — Administración y visibilidad (14 pts)

| Tarea | Lado | Pts |
|---|---|---|
| Endpoints de alta y baja de correlatividades, solo admin | Back | 3 |
| Panel admin con ruta protegida por rol: carreras, materias por carrera, correlatividades y convenios | Front | 8 |
| El ícono de calendario de Recordatorio no se ve | Front | 1 |
| Visibilidad baja | Front | 2 (estimado) |

**Orden sugerido**
1. Endpoint de correlatividades.
2. En paralelo, las pantallas de carreras, materias y convenios, que ya tienen CRUD solo para admin en el back.
3. Correlatividades en el front cuando el endpoint esté listo.

---

## Puntos a definir

- **"Visibilidad baja":** no está claro a qué se refiere (contraste o accesibilidad, o prioridad baja). Se asignó a C junto con el ícono del calendario, por si es el mismo problema. Si es otra cosa, hay que reasignarlo.
- **Recursar:** se puede resolver con el `PATCH /materias/cursada/{id}` existente, mandando estado "cursando" y notas en `null`. Si se prefiere que el back garantice el borrado de notas, hay que sumar un endpoint `recursar` (unos 2 pts, para A).
- **Correlatividades:** en el router de `dev` solo existe `GET /materias/correlativas/{materia_id}`. Falta confirmar si la creación de materia ya las acepta; si es así, baja la complejidad del endpoint de C.
- **Progreso sobre el total:** alcanza con la lista paginada de materias de la carrera si trae el total. Si no, hay que sumarlo al back.
- **Migraciones de Alembic:** B agrega una migración. Si C necesita otra, coordinar para no generar dos heads.
- **Service Worker:** no figuraba en la lista original del front, pero es requisito de la parte de push, por eso se sumó como tarea de B.
