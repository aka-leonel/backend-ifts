# Guía de Testing - miIFTS API

## 🚀 Paso 1: Ejecutar el seed

```bash
# Activar entorno virtual
.\venv\Scripts\activate

 source venv/Scripts/activate
 pip install

# Ejecutar seed (borra y recrea la DB)
python seed.py
```

**Datos creados:**
- Usuario: `test@miifts.ar` / `test1234` (ID: 1)
- Carreras: ID 1 y 2
- Materias: ID 1-19

---

## 🌐 Paso 2: Levantar el servidor

```bash
uvicorn app.main:app --reload
```

El servidor estará en: **http://localhost:8000**

---

## 📝 Paso 3: Probar endpoints

### **Opción A: Usando FastAPI Docs (MÁS FÁCIL)**

1. Abre en tu navegador: **http://localhost:8000/docs**
2. Verás una interfaz interactiva con todos los endpoints

#### Ejemplo: Login y probar endpoints protegidos

**1. Hacer login:**
- Busca `POST /auth/login`
- Click en "Try it out"
- Pega este JSON:
```json
{
  "email": "test@miifts.ar",
  "password": "test1234"
}
```
- Click "Execute"
- **COPIA EL TOKEN** de la respuesta (el campo `access_token`)

**2. Autorizar en Swagger:**
- Click en el botón verde "Authorize" (arriba a la derecha)
- Pega el token en el campo
- Click "Authorize"
- Ahora todos los endpoints protegidos usarán ese token automáticamente

**3. Probar endpoints:**

Ejemplos que puedes probar:

```
GET /auth/me                          ← Ver tu usuario
GET /materias/carreras               ← Listar carreras
GET /materias/carrera/1              ← Materias de la carrera 1
POST /materias/carreras              ← Crear nueva carrera (CRUD nuevo)
PUT /materias/carreras/1             ← Actualizar carrera (CRUD nuevo)
GET /materias/usuario/1              ← Materias del usuario 1
```

---

### **Opción B: Usando curl (Terminal)**

#### 1. Login y obtener token:
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"test@miifts.ar\",\"password\":\"test1234\"}"
```

Respuesta:
```json
{
  "access_token": "eyJ0eXAiOi...",
  "token_type": "bearer"
}
```

#### 2. Usar el token en otros endpoints:
```bash
# Reemplaza TU_TOKEN con el access_token de arriba
TOKEN="eyJ0eXAiOi..."

# Ver tu perfil
curl http://localhost:8000/auth/me \
  -H "Authorization: Bearer $TOKEN"

# Listar carreras
curl http://localhost:8000/materias/carreras

# Crear una carrera (CRUD nuevo)
curl -X POST http://localhost:8000/materias/carreras \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d "{\"nombre\":\"Nueva Carrera\",\"duracion_cuatrimestres\":6,\"ifts_id\":1}"

# Actualizar una carrera (CRUD nuevo)
curl -X PUT http://localhost:8000/materias/carreras/1 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d "{\"nombre\":\"Carrera Actualizada\"}"
```

---

### **Opción C: Usando Postman**

#### 1. Importar la colección:

Crea un archivo `miifts.postman_collection.json` con:

```json
{
  "info": {
    "name": "miIFTS API",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "item": [
    {
      "name": "Auth",
      "item": [
        {
          "name": "Login",
          "request": {
            "method": "POST",
            "header": [],
            "body": {
              "mode": "raw",
              "raw": "{\n  \"email\": \"test@miifts.ar\",\n  \"password\": \"test1234\"\n}",
              "options": {
                "raw": {
                  "language": "json"
                }
              }
            },
            "url": {
              "raw": "http://localhost:8000/auth/login",
              "protocol": "http",
              "host": ["localhost"],
              "port": "8000",
              "path": ["auth", "login"]
            }
          }
        }
      ]
    }
  ]
}
```

#### 2. En Postman:
- Import → selecciona el archivo JSON
- Envía el request de Login
- Copia el `access_token`
- En otros requests, ve a "Authorization" → Type: "Bearer Token" → pega el token

---

## 🧪 Ejemplos de testing completo

### **Probar el CRUD de Carreras:**

1. **Listar todas** (no requiere auth):
```bash
GET http://localhost:8000/materias/carreras
```

2. **Crear una nueva** (requiere auth):
```bash
POST http://localhost:8000/materias/carreras
{
  "nombre": "Tecnicatura en Desarrollo Web",
  "duracion_cuatrimestres": 5,
  "ifts_id": 1
}
```

3. **Actualizar** (requiere auth):
```bash
PUT http://localhost:8000/materias/carreras/3
{
  "nombre": "Tecnicatura en Desarrollo Web Full Stack",
  "duracion_cuatrimestres": 6
}
```

4. **Eliminar** (requiere auth):
```bash
DELETE http://localhost:8000/materias/carreras/3
```

### **Probar el CRUD de Materias:**

1. **Crear una materia**:
```bash
POST http://localhost:8000/materias/
{
  "carrera_id": 1,
  "nombre": "Inglés Técnico",
  "codigo": "ING",
  "anio": 1,
  "cuatrimestre": 1
}
```

2. **Actualizar materia**:
```bash
PUT http://localhost:8000/materias/20
{
  "nombre": "Inglés Técnico I"
}
```

3. **Eliminar materia**:
```bash
DELETE http://localhost:8000/materias/20
```

---

## 🔍 Verificar respuestas

### Respuesta exitosa (200/201):
```json
{
  "id": 3,
  "nombre": "Nueva Carrera",
  "duracion_cuatrimestres": 6,
  "ifts_id": 1
}
```

### Error 404 (no encontrado):
```json
{
  "detail": "Carrera no encontrada"
}
```

### Error 401 (no autorizado):
```json
{
  "detail": "Not authenticated"
}
```

---

## 📊 Endpoints disponibles

### Auth:
- `POST /auth/registro` - Registrar usuario
- `POST /auth/login` - Login (devuelve token)
- `GET /auth/me` - Perfil del usuario autenticado
- `GET /auth/verify` - Verificar token

### Materias:
- `GET /materias/carreras` - Listar carreras
- `POST /materias/carreras` - Crear carrera ⭐ NUEVO
- `PUT /materias/carreras/{id}` - Actualizar carrera ⭐ NUEVO
- `DELETE /materias/carreras/{id}` - Eliminar carrera ⭐ NUEVO
- `GET /materias/carrera/{id}` - Materias de una carrera
- `POST /materias/` - Crear materia ⭐ NUEVO
- `PUT /materias/{id}` - Actualizar materia ⭐ NUEVO
- `DELETE /materias/{id}` - Eliminar materia ⭐ NUEVO
- `GET /materias/correlativas/{id}` - Correlativas de una materia
- `GET /materias/usuario/{id}` - Materias del usuario
- `GET /materias/promedio/{id}` - Promedio del usuario

### Recursos:
- `GET /recursos/` - Listar recursos
- `POST /recursos/` - Crear recurso
- `GET /recursos/materia/{id}` - Recursos de una materia

### Recordatorios:
- `GET /recordatorios/` - Listar recordatorios
- `POST /recordatorios/` - Crear recordatorio
- `DELETE /recordatorios/{id}` - Eliminar recordatorio

---

## 💡 Tips

1. **Siempre ejecuta el seed antes de probar** si quieres datos limpios
2. **Usa /docs** para explorar la API interactivamente
3. **Guarda el token** después del login para usarlo en otros endpoints
4. **Los endpoints con 🔒 requieren autenticación** (token en el header)
5. **Verifica los códigos de estado:**
   - 200: OK
   - 201: Created
   - 204: No Content (delete exitoso)
   - 401: No autorizado
   - 404: No encontrado
   - 409: Conflicto (ej: email ya existe)

---

## 🐛 Solución de problemas

### "Module not found"
```bash
# Asegúrate de activar el venv
.\venv\Scripts\activate
```

### "Port already in use"
```bash
# Mata el proceso en el puerto 8000
# Windows:
netstat -ano | findstr :8000
taskkill /PID <número> /F
```

### "Database is locked"
```bash
# Detén el servidor (Ctrl+C)
# Borra la DB y vuelve a ejecutar seed
rm miifts.db
python seed.py
```
