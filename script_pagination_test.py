
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.features.auth.model import Usuario, RolUsuario
from app.features.materias.model import IFTS, Carrera, Materia
from app.features.recursos.model import Recurso, Convenio, TalentoTech
from app.features.recordatorios.model import Recordatorio

# --- Configuración de la Base de Datos ---
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./miifts.db")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def seed_database():
    db = SessionLocal()

    try:
        print("Limpiando tablas existentes...")
        # Limpiamos en orden inverso para evitar problemas de claves foráneas
        db.query(Recurso).delete()
        db.query(Convenio).delete()
        db.query(TalentoTech).delete()
        db.query(Recordatorio).delete() # <- Corregido: Añadido para limpieza
        db.query(Materia).delete()
        db.query(Usuario).delete()
        db.query(Carrera).delete()
        db.query(IFTS).delete()
        db.commit()

        print("Creando datos de prueba...")

        # --- Datos Base ---
        ifts_16 = IFTS(id=1, nombre="IFTS N° 16", ubicacion="Lafinur 644, CABA")
        db.add(ifts_16)
        db.commit()

        carrera_analisis = Carrera(id=1, nombre="Técnico Superior en Análisis de Sistemas", duracion_cuatrimestres=4, ifts_id=ifts_16.id)
        db.add(carrera_analisis)
        db.commit()

        usuario_prueba = Usuario(id=1, nombre="Estudiante de Prueba", email="test@ifts.com", password_hash="fake_password_hash", carrera_id=carrera_analisis.id, rol=RolUsuario.ESTUDIANTE)
        db.add(usuario_prueba)
        db.commit()

        materias_data = [
            {"id": 1, "carrera_id": 1, "nombre": "Programación I", "codigo": "P1", "anio": 1, "cuatrimestre": 1},
            {"id": 2, "carrera_id": 1, "nombre": "Arquitectura de Computadoras", "codigo": "AC", "anio": 1, "cuatrimestre": 1},
            {"id": 3, "carrera_id": 1, "nombre": "Bases de Datos I", "codigo": "BD1", "anio": 1, "cuatrimestre": 2},
            {"id": 4, "carrera_id": 1, "nombre": "Programación II", "codigo": "P2", "anio": 2, "cuatrimestre": 1},
        ]
        for data in materias_data:
            db.add(Materia(**data))
        db.commit()

        # --- Datos de Prueba para los Endpoints ---

        recursos_data = [
            Recurso(usuario_id=1, materia_id=1, titulo="Tutorial de Python para Principiantes", url="https://ejemplo.com/python", descripcion="Un buen recurso para empezar con Python."),
            Recurso(usuario_id=1, materia_id=1, titulo="Apuntes de Sintaxis Básica", url="https://ejemplo.com/sintaxis", descripcion="Resumen de la sintaxis del primer cuatrimestre."),
            Recurso(usuario_id=3, materia_id=3, titulo="Modelo Entidad-Relación (MER)", url="https://ejemplo.com/mer", descripcion="Explicación del modelo MER para bases de datos."),
            Recurso(usuario_id=1, materia_id=4, titulo="Programación Orientada a Objetos", url="https://ejemplo.com/poo", descripcion="Conceptos clave de POO para Programación II."),
            Recurso(usuario_id=1, materia_id=3, titulo="Guía de SQL Básico", url="https://ejemplo.com/sql", descripcion="Comandos básicos de SQL: SELECT, INSERT, UPDATE, DELETE."),
            Recurso(usuario_id=1, materia_id=1, titulo="Ejercicios de Lógica de Programación", url="https://ejemplo.com/logica", descripcion="Problemas para practicar la lógica y algoritmos."),
        ]
        db.add_all(recursos_data)

        convenios_data = [
            Convenio(carrera_id=1, institucion="Universidad Tecnológica Nacional (UTN)", carrera_destino="Ingeniería en Sistemas de Información", descripcion="Convenio de articulación para continuar estudios.", link_info="https://ejemplo.com/utn"),
            Convenio(carrera_id=1, institucion="Universidad de Palermo (UP)", carrera_destino="Licenciatura en Informática", descripcion="Ofrece un plan de estudios reducido para egresados del IFTS.", link_info="https://ejemplo.com/up"),
            Convenio(carrera_id=1, institucion="Universidad Argentina de la Empresa (UADE)", carrera_destino="Licenciatura en Sistemas", descripcion="Reconocimiento de materias y beneficios arancelarios.", link_info="https://ejemplo.com/uade"),
        ]
        db.add_all(convenios_data)

        talentotech_data = [
            TalentoTech(carrera_id=1, nombre_curso="Desarrollo Web Full Stack", categoria="Desarrollo", descripcion="Curso intensivo de 9 meses sobre frontend y backend.", duracion="36 semanas", link_inscripcion="https://ejemplo.com/fullstack"),
            TalentoTech(carrera_id=1, nombre_curso="Introducción a la Ciencia de Datos", categoria="Datos", descripcion="Aprende Python, Pandas y Scikit-learn para análisis de datos.", duracion="12 semanas", link_inscripcion="https://ejemplo.com/datascience"),
            TalentoTech(carrera_id=1, nombre_curso="Fundamentos de Ciberseguridad", categoria="Seguridad", descripcion="Conceptos básicos de seguridad informática, redes y criptografía.", duracion="8 semanas", link_inscripcion="https://ejemplo.com/cybersec"),
            TalentoTech(carrera_id=1, nombre_curso="Gestión de Proyectos con Metodologías Ágiles", categoria="Gestión", descripcion="Curso sobre Scrum, Kanban y gestión de equipos.", duracion="6 semanas", link_inscripcion="https://ejemplo.com/agile"),
        ]
        db.add_all(talentotech_data)
        
        db.commit()
        print("¡Base de datos poblada con éxito!")

    except Exception as e:
        print(f"Ocurrió un error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()