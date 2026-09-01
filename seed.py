"""
Script de seed para miIFTS.

Uso:
    python seed.py              # borra y recrea todo
    python seed.py --no-drop   # solo inserta si las tablas están vacías

IMPORTANTE: Actualizá los datos de IFTS, carreras, materias y correlativas
según el plan de estudios real de tu institución (usá el PDF como fuente).
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from passlib.context import CryptContext
from app.database import Base, engine, SessionLocal

# Importar TODOS los modelos para que SQLAlchemy los registre antes del create_all
from app.features.auth.model import Usuario, RolUsuario
from app.features.materias.model import IFTS, Carrera, Materia, Correlativa, MateriaUsuario
from app.features.recordatorios.model import Recordatorio
from app.features.recursos.model import Recurso, Convenio, TalentoTech

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def reset_db():
    print("Eliminando tablas existentes...")
    Base.metadata.drop_all(bind=engine)
    print("Creando tablas...")
    Base.metadata.create_all(bind=engine)
    print("Tablas creadas.")


def seed():
    db = SessionLocal()
    try:
        # ── 1. IFTS ──────────────────────────────────────────────────────────
        # REEMPLAZÁ con el nombre real de tu IFTS
        print("\nCargando IFTS...")
        ifts = IFTS(
            nombre="IFTS N° 18 - Colpayo",
            ubicacion="CABA",
        )
        db.add(ifts)
        db.flush()

        # ── 2. Carreras ───────────────────────────────────────────────────────
        # REEMPLAZÁ con las carreras reales de tu IFTS
        print("Cargando carreras...")
        dev_software = Carrera(
            nombre="Tecnicatura Superior en Desarrollo de Software",
            duracion_cuatrimestres=6,
            ifts_id=ifts.id,
        )
        analisis_sistemas = Carrera(
            nombre="Tecnicatura Superior en Análisis de Sistemas",
            duracion_cuatrimestres=6,
            ifts_id=ifts.id,
        )
        db.add_all([dev_software, analisis_sistemas])
        db.flush()

        # ── 3. Materias ───────────────────────────────────────────────────────
        # REEMPLAZÁ con las materias reales del plan de estudios (PDF).
        # El campo 'codigo' debe coincidir con el código del plan (ej: "1.1.3").
        # Cada combinación (carrera_id, codigo) debe ser única.
        print("Cargando materias de Desarrollo de Software...")
        materias_dev = [
            # Año 1 — Cuatrimestre 1
            Materia(carrera_id=dev_software.id, nombre="Matemática",                      codigo="1.1.1", anio=1, cuatrimestre=1),
            Materia(carrera_id=dev_software.id, nombre="Introducción a la Programación",  codigo="1.1.2", anio=1, cuatrimestre=1),
            Materia(carrera_id=dev_software.id, nombre="Arquitectura de Computadoras",    codigo="1.1.3", anio=1, cuatrimestre=1),
            Materia(carrera_id=dev_software.id, nombre="Inglés Técnico I",                codigo="1.1.4", anio=1, cuatrimestre=1),
            # Año 1 — Cuatrimestre 2
            Materia(carrera_id=dev_software.id, nombre="Matemática II",                   codigo="1.2.1", anio=1, cuatrimestre=2),
            Materia(carrera_id=dev_software.id, nombre="Programación I",                  codigo="1.2.2", anio=1, cuatrimestre=2),
            Materia(carrera_id=dev_software.id, nombre="Sistemas Operativos",             codigo="1.2.3", anio=1, cuatrimestre=2),
            Materia(carrera_id=dev_software.id, nombre="Inglés Técnico II",               codigo="1.2.4", anio=1, cuatrimestre=2),
            # Año 2 — Cuatrimestre 1
            Materia(carrera_id=dev_software.id, nombre="Base de Datos I",                 codigo="2.1.1", anio=2, cuatrimestre=1),
            Materia(carrera_id=dev_software.id, nombre="Programación II",                 codigo="2.1.2", anio=2, cuatrimestre=1),
            Materia(carrera_id=dev_software.id, nombre="Redes y Comunicaciones",          codigo="2.1.3", anio=2, cuatrimestre=1),
            # Año 2 — Cuatrimestre 2
            Materia(carrera_id=dev_software.id, nombre="Base de Datos II",                codigo="2.2.1", anio=2, cuatrimestre=2),
            Materia(carrera_id=dev_software.id, nombre="Programación III",                codigo="2.2.2", anio=2, cuatrimestre=2),
            Materia(carrera_id=dev_software.id, nombre="Ingeniería de Software I",        codigo="2.2.3", anio=2, cuatrimestre=2),
            # Año 3 — Cuatrimestre 1
            Materia(carrera_id=dev_software.id, nombre="Programación IV",                 codigo="3.1.1", anio=3, cuatrimestre=1),
            Materia(carrera_id=dev_software.id, nombre="Ingeniería de Software II",       codigo="3.1.2", anio=3, cuatrimestre=1),
            Materia(carrera_id=dev_software.id, nombre="Gestión de Proyectos",            codigo="3.1.3", anio=3, cuatrimestre=1),
            # Año 3 — Cuatrimestre 2
            Materia(carrera_id=dev_software.id, nombre="Práctica Profesionalizante",      codigo="3.2.1", anio=3, cuatrimestre=2),
            Materia(carrera_id=dev_software.id, nombre="Proyecto Final",                  codigo="3.2.2", anio=3, cuatrimestre=2),
        ]
        db.add_all(materias_dev)
        db.flush()

        # Dict por codigo para armar correlativas sin hardcodear IDs
        dev = {m.codigo: m for m in materias_dev}

        # ── 4. Correlativas ───────────────────────────────────────────────────
        # Formato: materia X requiere haber aprobado materia Y.
        # Usá los codigos del plan (el dict 'dev' los mapea a IDs reales).
        print("Cargando correlativas...")
        correlativas = [
            Correlativa(materia_id=dev["1.2.1"].id, requiere_id=dev["1.1.1"].id),  # Matemática II ← Matemática
            Correlativa(materia_id=dev["1.2.2"].id, requiere_id=dev["1.1.2"].id),  # Programación I ← Intro Prog
            Correlativa(materia_id=dev["1.2.4"].id, requiere_id=dev["1.1.4"].id),  # Inglés II ← Inglés I
            Correlativa(materia_id=dev["2.1.1"].id, requiere_id=dev["1.2.2"].id),  # BD I ← Programación I
            Correlativa(materia_id=dev["2.1.2"].id, requiere_id=dev["1.2.2"].id),  # Programación II ← Prog I
            Correlativa(materia_id=dev["2.2.1"].id, requiere_id=dev["2.1.1"].id),  # BD II ← BD I
            Correlativa(materia_id=dev["2.2.2"].id, requiere_id=dev["2.1.2"].id),  # Programación III ← Prog II
            Correlativa(materia_id=dev["2.2.3"].id, requiere_id=dev["2.1.2"].id),  # Ing Software I ← Prog II
            Correlativa(materia_id=dev["3.1.1"].id, requiere_id=dev["2.2.2"].id),  # Programación IV ← Prog III
            Correlativa(materia_id=dev["3.1.2"].id, requiere_id=dev["2.2.3"].id),  # Ing Software II ← IS I
            Correlativa(materia_id=dev["3.1.3"].id, requiere_id=dev["2.2.3"].id),  # Gestión ← IS I
        ]
        db.add_all(correlativas)
        db.flush()

        # ── 5. Usuario de prueba ──────────────────────────────────────────────
        # Credenciales compartidas para que todos puedan probar sin JWT.
        # Eliminalo cuando implementen auth real en producción.
        print("Cargando usuario de prueba...")
        test_user = Usuario(
            nombre="Estudiante Test",
            email="test@miifts.ar",
            password_hash=pwd_context.hash("test1234"),
            carrera_id=dev_software.id,
            rol=RolUsuario.ESTUDIANTE,
        )
        db.add(test_user)
        db.flush()

        # ── 6. Usuario administrador ─────────────────────────────────────────
        # El registro público (/auth/registro) SOLO crea estudiantes.
        # El admin se crea acá (o promoviendo un usuario en la DB).
        print("Cargando usuario administrador...")
        admin_user = Usuario(
            nombre="Administrador",
            email="admin@miifts.ar",
            password_hash=pwd_context.hash("admin1234"),
            carrera_id=dev_software.id,
            rol=RolUsuario.ADMIN,
        )
        db.add(admin_user)
        db.flush()

        db.commit()

        print("\n[OK] Seed completado.")
        print(f"  IFTS:         {ifts.nombre}")
        print(f"  Carreras:     2")
        print(f"  Materias:     {len(materias_dev)} (Desarrollo de Software)")
        print(f"  Correlativas: {len(correlativas)}")
        print(f"  Usuario test:  test@miifts.ar / test1234   (id={test_user.id}, rol=estudiante)")
        print(f"  Usuario admin: admin@miifts.ar / admin1234  (id={admin_user.id}, rol=admin)")
        print("\n  IMPORTANTE: el usuario de prueba tiene id=1.")
        print("  get_usuario_actual() devuelve 1 mientras no este el JWT completo.")

    except Exception as exc:
        db.rollback()
        print(f"\nError durante el seed: {exc}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    no_drop = "--no-drop" in sys.argv
    if not no_drop:
        reset_db()
    seed()
