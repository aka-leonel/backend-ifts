# Sprint de 4 días - Backend miIFTS
**Objetivo:** Avance significativo en funcionalidad, seguridad y calidad

---

## 📊 Distribución de Tareas por Integrante

### 🔐 **Integrante 1 - SEGURIDAD Y AUTENTICACIÓN**
**Prioridad:** ALTA | **Complejidad:** Media | **Días:** 3-4

#### Tareas:
1. **Proteger endpoints CRUD de Materias con JWT**
   - Importar `get_current_user` de `auth.dependencies`
   - Agregar `usuario_actual = Depends(get_current_user)` a todos los endpoints CRUD:
     - POST /materias/carreras
     - PUT /materias/carreras/{id}
     - DELETE /materias/carreras/{id}
     - POST /materias/
     - PUT /materias/{id}
     - DELETE /materias/{id}
   - Guardar `usuario_id` en logs/auditoría (opcional)

2. **Proteger endpoints de Recursos con JWT**
   - Ya está en `/recursos/` (POST)
   - Agregar a PUT y DELETE si existen
   - Verificar que `usuario_actual.id` coincida con `recurso.usuario_id`

3. **Implementar roles de usuario**
   - Agregar campo `rol` al modelo Usuario (admin/estudiante)
   - Crear decorador `@require_admin` para operaciones sensibles
   - Solo admins pueden: crear/editar/eliminar carreras y materias

**Entregables:**
- [ ] Todos los endpoints CRUD protegidos
- [ ] Tests de autorización (mínimo 3)
- [ ] Documentación de roles en README

---

### 🧪 **Integrante 2 - TESTING Y CALIDAD**
**Prioridad:** ALTA | **Complejidad:** Media-Alta | **Días:** 4

#### Tareas:
1. **Tests unitarios para Auth**
   ```python
   # tests/test_auth.py
   - test_registro_exitoso()
   - test_registro_email_duplicado()
   - test_login_exitoso()
   - test_login_credenciales_invalidas()
   - test_get_current_user_token_valido()
   - test_get_current_user_token_invalido()
   ```

2. **Tests de integración para Materias CRUD**
   ```python
   # tests/test_materias.py
   - test_crear_carrera_con_auth()
   - test_crear_carrera_sin_auth() → 401
   - test_actualizar_carrera()
   - test_eliminar_carrera()
   - test_crear_materia_codigo_duplicado() → 409
   ```

3. **Setup de CI/CD básico**
   - Crear `.github/workflows/tests.yml`
   - Correr tests en cada push a dev/main
   - Verificar que pasa pylint/black

**Entregables:**
- [ ] Mínimo 15 tests funcionando
- [ ] Coverage > 60%
- [ ] CI configurado en GitHub Actions

---

### 🔍 **Integrante 3 - FILTROS Y BÚSQUEDA**
**Prioridad:** MEDIA | **Complejidad:** Media | **Días:** 3

#### Tareas:
1. **Búsqueda de materias**
   - Endpoint: `GET /materias/buscar?q=programacion&anio=1&cuatrimestre=1`
   - Buscar por: nombre, código, año, cuatrimestre
   - Implementar en service y repository

2. **Filtros avanzados para recursos**
   - `GET /recursos/?materia_id=1&tipo=pdf&desde=2024-01-01`
   - Filtrar por: materia, tipo de archivo, rango de fechas
   - Ordenar por: fecha_creacion, titulo

3. **Búsqueda de recordatorios**
   - `GET /recordatorios/?tipo=examen&desde=2024-12-01&hasta=2024-12-31`
   - Filtrar por: tipo, rango de fechas, materia
   - Ordenar por: fecha (próximos primero)

**Entregables:**
- [ ] 3 endpoints de búsqueda/filtrado funcionando
- [ ] Documentación en Swagger con ejemplos
- [ ] Tests de casos edge (búsqueda vacía, sin resultados)

---

### 📄 **Integrante 4 - PAGINACIÓN Y PERFORMANCE**
**Prioridad:** MEDIA | **Complejidad:** Baja-Media | **Días:** 2-3

#### Tareas:
1. **Implementar paginación en listados**
   - Crear esquema común de paginación:
     ```python
     # schemas/pagination.py
     class PaginationParams(BaseModel):
         page: int = 1
         per_page: int = 20
     
     class PaginatedResponse(BaseModel):
         items: List[Any]
         total: int
         page: int
         per_page: int
         total_pages: int
     ```

2. **Aplicar paginación a endpoints clave:**
   - `GET /materias/carrera/{id}?page=1&per_page=10`
   - `GET /recursos/?page=1&per_page=20`
   - `GET /recordatorios/?page=1&per_page=15`

3. **Optimizar queries con relaciones**
   - Usar `joinedload()` en queries que traen relaciones
   - Agregar índices en columnas más consultadas:
     ```python
     # En models:
     __table_args__ = (Index('idx_materia_carrera', 'carrera_id'),)
     ```

**Entregables:**
- [ ] Paginación funcionando en 3+ endpoints
- [ ] Queries optimizadas (verificar con EXPLAIN)
- [ ] Documentación de uso de paginación

---

### 📝 **Integrante 5 - VALIDACIONES Y MANEJO DE ERRORES**
**Prioridad:** ALTA | **Complejidad:** Media | **Días:** 3

#### Tareas:
1. **Mejorar validaciones en schemas**
   - Agregar validadores personalizados:
     ```python
     # materias/schema.py
     @validator('cuatrimestre')
     def validar_cuatrimestre(cls, v):
         if v not in [1, 2]:
             raise ValueError('Cuatrimestre debe ser 1 o 2')
         return v
     
     @validator('nota_final')
     def validar_nota(cls, v):
         if v and (v < 1 or v > 10):
             raise ValueError('Nota debe estar entre 1 y 10')
         return v
     ```

2. **Manejo consistente de errores**
   - Crear clase base de excepciones:
     ```python
     # exceptions.py
     class APIException(HTTPException):
         def __init__(self, detail: str):
             super().__init__(status_code=self.status_code, detail=detail)
     
     class NotFoundError(APIException):
         status_code = 404
     
     class DuplicateError(APIException):
         status_code = 409
     ```
   - Usar en todos los services

3. **Validar lógica de negocio**
   - No permitir eliminar carrera con materias asociadas
   - No permitir eliminar materia con cursadas activas
   - Validar que fecha de recordatorio sea futura
   - Validar que materia pertenezca a la carrera del usuario

**Entregables:**
- [ ] Validadores en todos los schemas principales
- [ ] Manejo de errores consistente en toda la API
- [ ] Tests de validaciones (mínimo 10)

---

## 📅 Cronograma sugerido

### **Día 1** (Lunes)
- Todos: Setup del entorno, pull de dev, crear rama feature/{nombre}
- Integrante 1: Proteger endpoints de Materias
- Integrante 2: Setup de tests + primeros 5 tests de Auth
- Integrante 3: Endpoint de búsqueda de materias
- Integrante 4: Implementar esquema de paginación
- Integrante 5: Validadores de Materias

### **Día 2** (Martes)
- Integrante 1: Implementar sistema de roles
- Integrante 2: Tests de Materias CRUD
- Integrante 3: Filtros de recursos
- Integrante 4: Aplicar paginación a endpoints
- Integrante 5: Clase base de excepciones

### **Día 3** (Miércoles)
- Integrante 1: Proteger endpoints de Recursos
- Integrante 2: Tests de integración + CI/CD
- Integrante 3: Filtros de recordatorios
- Integrante 4: Optimización de queries
- Integrante 5: Validaciones de lógica de negocio

### **Día 4** (Jueves)
- Todos: Testing cruzado
- Todos: Documentar cambios en README
- Todos: PR a dev
- Code review en pares

---

## ✅ Criterios de aceptación

Para considerar el sprint exitoso:

1. **Funcionalidad:**
   - [ ] Todos los endpoints CRUD están protegidos con JWT
   - [ ] Al menos 2 de 3 funciones de búsqueda/filtrado funcionando
   - [ ] Paginación implementada en al menos 2 endpoints

2. **Calidad:**
   - [ ] Mínimo 15 tests pasando
   - [ ] No hay endpoints que devuelvan stack traces al usuario
   - [ ] Validaciones en todos los campos críticos

3. **Documentación:**
   - [ ] README actualizado con nuevas features
   - [ ] Swagger docs completo con ejemplos
   - [ ] api-requests.http actualizado

4. **Proceso:**
   - [ ] Cada feature en su propia rama
   - [ ] PRs revisados por al menos 1 compañero
   - [ ] Sin conflictos en merge a dev

---

## 🚀 Bonus (si sobra tiempo)

1. **Migraciones con Alembic**
   - Crear primera migración para rol de usuario
   - Documentar proceso de migraciones

2. **Logging estructurado**
   - Implementar logging con loguru
   - Logs de todas las operaciones críticas

3. **.env.example mejorado**
   - Todas las variables documentadas
   - Valores seguros por defecto

4. **Docker Compose**
   - Containerizar la aplicación
   - Setup fácil para nuevos dev

---

## 📞 Coordinación

### Daily Standup (10 min diarios)
- ¿Qué hice ayer?
- ¿Qué haré hoy?
- ¿Tengo algún blocker?

### Slack/Discord
- Canal #backend para dudas técnicas
- Avisar cuando se sube PR para review
- Compartir snippets de código útiles

### Git Flow
```bash
# Crear rama
git checkout dev
git pull origin dev
git checkout -b feature/tu-nombre-tarea

# Durante desarrollo
git add .
git commit -m "feat: descripción clara"
git push origin feature/tu-nombre-tarea

# Cuando termines
# Crear PR en GitHub: feature/tu-nombre → dev
```

---

## 🎯 Métricas de éxito

Al final del sprint, medir:
- Endpoints con autenticación: objetivo 100%
- Cobertura de tests: objetivo >60%
- Endpoints con paginación: objetivo >50%
- Validaciones implementadas: objetivo >80% de campos críticos
- PRs mergeados sin conflictos: objetivo 100%

---

**¿Preguntas? Consultar en el canal #backend o revisar TESTING.md**
