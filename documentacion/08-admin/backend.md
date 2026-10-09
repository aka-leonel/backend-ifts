# Admin - Backend

## Auth Dependency

```python
def require_admin(current_user: UsuarioResponse = Depends(get_current_user)) -> UsuarioResponse:
    if current_user.rol != RolUsuario.ADMIN:
        raise ForbiddenError("Se requiere rol admin")
    return current_user
```

## Endpoints Protegidos (require_admin)

| Feature | Endpoints | Métodos |
|---------|-----------|---------|
| **Carreras** | `/materias/carreras`, `/materias/carreras/{id}` | POST, PUT, DELETE |
| **Materias** | `/materias/`, `/materias/{id}` | POST, PUT, DELETE |
| **Correlativas** | `/materias/correlativas`, `/materias/correlativas/{id}` | POST, DELETE |
| **Convenios** | `/convenios/`, `/convenios/{id}` | POST, PUT, DELETE |
| **TalentoTech** | `/talentotech/`, `/talentotech/{id}` | POST, PUT, DELETE |

> **Lectura pública (SIN auth):** GET `/materias/carreras`, `/materias/carrera/{id}`, `/materias/buscar`, `/materias/{id}`, `/materias/correlativas/{id}`, `/convenios/`, `/convenios/carrera/{id}`, `/talentotech/`, `/talentotech/carrera/{id}`, `/talentotech/categoria/{cat}`

## Uso en Routers

```python
# Crear carrera
@router.post("/carreras", response_model=CarreraResponse, status_code=201)
def crear_carrera(datos: CarreraCreate, db: Session = Depends(get_db), 
                  usuario_actual: UsuarioResponse = Depends(require_admin)):
    return service.create_carrera(db, datos)

# Crear convenio
@router.post("/", response_model=ConvenioResponse, status_code=201)
def create(convenio: ConvenioCreate, service: ConvenioService = Depends(get_convenio_service),
           usuario_actual: UsuarioResponse = Depends(require_admin)):
    return service.create(convenio)
```

## Modelo Usuario (Rol)

```python
class RolUsuario(str, enum.Enum):
    ESTUDIANTE = "estudiante"
    ADMIN = "admin"

class Usuario(Base):
    # ...
    rol = Column(Enum(RolUsuario), nullable=False, default=RolUsuario.ESTUDIANTE)
```

## Creación Admin Inicial

```python
# seed.py o script manual
admin = Usuario(nombre="Admin", apellido="Sistema", email="admin@miifts.edu.ar",
                password_hash=hash_password("admin123"), carrera_id=1, rol=RolUsuario.ADMIN)
db.add(admin); db.commit()
```
> En producción: crear via registro normal + actualizar rol en BD, o script de setup.