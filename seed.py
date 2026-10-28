"""
Script de seed para miIFTS.

Uso:
    python seed.py              # borra y recrea todo
    python seed.py --no-drop    # solo inserta si las tablas están vacías
    python seed.py --convenios  # solo inserta convenios faltantes (no borra nada)

IMPORTANTE: Actualizá los datos de IFTS, carreras, materias y correlativas
según el plan de estudios real de tu institución (usá el PDF como fuente).
"""
import sys
import os
from app.features.notificaciones.model import PushSubscription
from app.features.quiz.model import QuizUso

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from passlib.context import CryptContext
from app.database import Base, engine, SessionLocal

# Importar TODOS los modelos para que SQLAlchemy los registre antes del create_all
from app.features.auth.model import Usuario, RolUsuario
from app.features.materias.model import IFTS, Carrera, Materia, Correlativa, MateriaUsuario
from app.features.recordatorios.model import Recordatorio
from app.features.recursos.model import Recurso, Convenio, ConvenioCarrera, TalentoTech
from app.features.notificaciones.model import PushSubscription
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ── Convenios a cargar ───────────────────────────────────────────────────────
# Cada ítem usa el formato canónico:
#
#   "carrera_ids": [1, 2]              # ids reales de la tabla `carreras`
#   "todas_las_carreras": true         # alternativa: aplica a todas
#
# Es excluyente: o `carrera_ids` no vacío, o `todas_las_carreras: true`.
# La idempotencia es por (institucion, carrera_destino).
CONVENIOS_SEED: list[dict] = [
    {
        "carrera_ids": [1, 2],
        "institucion": "Universidad Nacional de la Matanza",
        "carrera_destino": "Licenciatura en Gestión de Tecnología",
        "descripcion": (
            "Este Ciclo de Complementación Curricular tiene como propósito central "
            "fusionar las competencias técnicas de la informática con las herramientas "
            "de management y liderazgo empresarial, preparando a los graduados para "
            "conducir la transformación digital y administrar la infraestructura "
            "tecnológica de cualquier organización. A diferencia de una ingeniería "
            "tradicional centrada en el desarrollo puro de código o hardware, este ciclo "
            "se enfoca en cómo utilizar la tecnología para resolver problemas de "
            "negocios y optimizar procesos productivos"
        ),
        "link_info": "https://formacioncontinua.unlam.edu.ar/licenciatura-en-gestion-de-tecnologia/",
    },
    {
        "todas_las_carreras": True,
        "institucion": "Universidad de Palermo",
        "carrera_destino": "Licenciatura en Tecnología de la Información",
        "descripcion": (
            "El Ciclo de Complementación de la Licenciatura en Tecnología de la "
            "Información forma profesionales enfocados en la conducción, desarrollo e "
            "implementación de tecnologías de software, hardware, comunicaciones, y los "
            "servicios relacionados, en todo tipo de negocios y organizaciones."
        ),
        "link_info": "https://www.palermo.edu/ingenieria/complementacion-lic-en-tecnologia-de-la-informacion",
    },
    {
        "todas_las_carreras": True,
        "institucion": "Universidad de Palermo",
        "carrera_destino": "Licenciatura en Redes y Comunicación de Datos",
        "descripcion": (
            "La Licenciatura en Redes y Comunicación de Datos en la UP es la carrera en "
            "Argentina más reconocida en las redes de comunicaciones de datos, sus "
            "protocolos, arquitectura, administración, integración y análisis. Sus "
            "egresados son los profesionales más destacados en la Industria de Servicios "
            "de Telecomunicaciones."
        ),
        "link_info": "https://www.palermo.edu/ingenieria/complementacion_redes_comunicacion/index.html",
    },
    {
        "carrera_ids": [2],
        "institucion": "Universidad de Palermo",
        "carrera_destino": "Licenciatura en Administración de Sistemas y Empresas",
        "descripcion": (
            "Forma profesionales para liderar y desarrollar sistemas en empresas e "
            "introducir innovaciones que generen nuevos negocios."
        ),
        "link_info": "https://www.palermo.edu/negocios/ciclo-administracion-sistemas-y-empresas",
    },
    {
        "todas_las_carreras": True,
        "institucion": "Universidad de la Ciudad de Buenos Aires",
        "carrera_destino": "Licenciatura en Tecnologías Digitales",
        "descripcion": (
            "La Licenciatura en Tecnologías Digitales forma profesionales expertos en "
            "tecnologías digitales de innovación, capaces de ser referentes en los "
            "procesos de transformación digital que generen valor agregado en "
            "organizaciones privadas, públicas y ONG, destacándose por la innovación, "
            "adaptabilidad al cambio y la gestión del mundo de los negocios, su "
            "contribución al desarrollo local y regional con altos estándares éticos y de "
            "compromiso social."
        ),
        "link_info": "https://www.udelaciudad.edu.ar/licenciatura-en-tecnologias-digitales/",
    },
    {
        "carrera_ids": [3],
        "institucion": "Universidad de la Ciudad de Buenos Aires",
        "carrera_destino": "Licenciatura en Ciencia de Datos",
        "descripcion": (
            "Por medio de la Licenciatura en Ciencia de Datos (CCC) forma profesionales "
            "capacitados para analizar, interpretar y transformar datos en información "
            "estratégica para la toma de decisiones en distintos tipos de organizaciones. "
            "El graduado desarrolla competencias en análisis de datos, herramientas "
            "tecnológicas y resolución de problemas complejos, destacándose por la "
            "innovación, la adaptabilidad al cambio y el uso ético de la información, "
            "contribuyendo al desarrollo local y regional con compromiso social."
        ),
        "link_info": "https://www.udelaciudad.edu.ar/licenciatura-en-ciencia-de-datos/",
    },
    {
        "todas_las_carreras": True,
        "institucion": "Universidad de la Ciudad de Buenos Aires",
        "carrera_destino": "Licenciatura en Desarrollo y Producción de Videojuegos",
        "descripcion": (
            "Estudiar la Licenciatura en Desarrollo y Producción de Videojuegos (Ciclo de "
            "Complementación Curricular) en la UdelaCiudad permite formarse en una "
            "industria en crecimiento, adquiriendo una sólida formación en diseño, "
            "programación y producción de videojuegos, junto con competencias en gestión "
            "de proyectos, liderazgo y desarrollo de emprendimientos digitales, en un "
            "sector estratégico de la economía del conocimiento."
        ),
        "link_info": "https://www.udelaciudad.edu.ar/licenciatura-en-desarrollo-y-produccion-de-videojuegos",
    },
    {
        "todas_las_carreras": True,
        "institucion": "Universidad Nacional de Lanús",
        "carrera_destino": "Licenciatura en Tecnologías Digitales para la Educación",
        "descripcion": (
            "Durante el Ciclo aprenderás sobre los nuevos escenarios educativos a partir "
            "de la utilización de tecnologías digitales; conocerás aplicaciones libres "
            "destinadas a la enseñanza y el aprendizaje; y trabajarás en distintas "
            "propuestas pedagógicas que involucren activamente a sus estudiantes"
        ),
        "link_info": "https://www.unla.edu.ar/carreras/grado/ciclos-de-licenciatura/tecnologias-digitales-para-la-educacion",
    },
    {
        "carrera_ids": [2, 3],
        "institucion": "Universidad Nacional de Lomas de Zamora",
        "carrera_destino": "Licenciatura en Gestión de la Información",
        "descripcion": (
            "La Licenciatura en Gestión de la Información tiene por objetivo formar "
            "profesionales con sólida formación teórica, metodológica y técnica en la "
            "gestión de la información, integrando los aspectos teóricos y prácticos de "
            "las disciplinas de la gestión de la información a las nuevas nuevas "
            "tecnologías y adecuando la formación profesional a las exigencias del mercado "
            "laboral."
        ),
        "link_info": "https://ingenieria.unlz.edu.ar/oferta-academica/grado#licenciaturas",
    },
    {
        "carrera_ids": [1, 3],
        "institucion": "Universidad Nacional de Lomas de Zamora",
        "carrera_destino": "Gestión de Sistemas de Automatización y Robótica",
        "descripcion": (
            "Los/as graduados/as de la Licenciatura en Gestión de Sistemas de Automación "
            "y Robótica serán capaces de integrar equipos de planificación, desarrollo y "
            "gestión de sistemas integrados de procesos productivos y de colaborar en el "
            "análisis y simulación de sistemas automáticos de producción y fabricación. A "
            "su vez, estarán habilitados para participar tanto en la conducción de equipos "
            "de trabajo destinados a tareas de producción como también en investigaciones "
            "de técnicas y procedimientos relacionados con su campo de estudio."
        ),
        "link_info": "https://ingenieria.unlz.edu.ar/oferta-academica/grado#licenciaturas",
    },
]

# Nombre real de cada carrera del seed. La clave es la que se usa en
# CONVENIOS_SEED; el valor es el `nombre` que tiene que existir en la tabla
# `carreras`. Se usa tanto al crear las carreras como al cargar convenios sobre
# una base ya poblada (`python seed.py --convenios`).
CARRERAS_SEED: dict[str, str] = {
    "dev_software": "Tecnicatura Superior en Desarrollo de Software",
    "analisis_sistemas": "Tecnicatura Superior en Análisis de Sistemas",
    "ciencia_datos_ia": "Tecnicatura Superior en Ciencia de Datos e Inteligencia Artificial",
}


def reset_db():
    print("Eliminando tablas existentes...")
    Base.metadata.drop_all(bind=engine)
    print("Creando tablas...")
    Base.metadata.create_all(bind=engine)
    print("Tablas creadas.")


def hay_datos():
    db = SessionLocal()
    try:
        return db.query(IFTS).first() is not None
    finally:
        db.close()


def _insertar_convenios(db) -> int:
    """Inserta los convenios de `CONVENIOS_SEED` que todavía no existan.

    Formato canónico por ítem: `carrera_ids` (ids reales de `carreras`) **o**
    `todas_las_carreras: true` (excluyente). El atajo `carrera` (clave de
    `CARRERAS_SEED`) sigue aceptado para una sola carrera. La idempotencia es
    por `(institucion, carrera_destino)`. Devuelve cuántos insertó.
    """
    if not CONVENIOS_SEED:
        return 0

    carreras = db.query(Carrera).all()
    por_id = {c.id: c for c in carreras}
    por_nombre = {c.nombre: c for c in carreras}

    resueltos = []
    for datos in CONVENIOS_SEED:
        todas = bool(datos.get("todas_las_carreras"))
        ids = datos.get("carrera_ids")

        if ids is None and "carrera" in datos:
            clave = datos["carrera"]
            if clave not in CARRERAS_SEED:
                raise ValueError(
                    f"CONVENIOS_SEED: carrera desconocida {clave!r}. "
                    f"Usá una de: {', '.join(sorted(CARRERAS_SEED))} "
                    f"o pasá 'carrera_ids' directamente."
                )
            carrera = por_nombre.get(CARRERAS_SEED[clave])
            if carrera is None:
                raise ValueError(
                    "Faltan carreras en la base: "
                    + CARRERAS_SEED[clave]
                    + ". Corré `python seed.py` o creá las carreras antes de cargar convenios."
                )
            ids = [carrera.id]

        if todas:
            if ids:
                raise ValueError(
                    "CONVENIOS_SEED: 'todas_las_carreras': true no admite "
                    "'carrera_ids'. Usá uno u otro."
                )
            carreras_item = []
        else:
            if not ids:
                raise ValueError(
                    "CONVENIOS_SEED: cada ítem necesita 'carrera_ids' no vacío "
                    "o 'todas_las_carreras': true."
                )
            ids = list(dict.fromkeys(ids))
            faltantes = [cid for cid in ids if cid not in por_id]
            if faltantes:
                raise ValueError(
                    f"CONVENIOS_SEED: no existen las carreras {faltantes}. "
                    f"IDs disponibles: {sorted(por_id)}"
                )
            carreras_item = [por_id[cid] for cid in ids]

        resueltos.append((carreras_item, todas, datos))

    insertados = 0
    print("Cargando convenios...")
    for carreras_item, todas, datos in resueltos:
        ya_existe = (
            db.query(Convenio)
            .filter(
                Convenio.institucion == datos["institucion"],
                Convenio.carrera_destino == datos["carrera_destino"],
            )
            .first()
        )
        if ya_existe is not None:
            continue
        convenio = Convenio(
            institucion=datos["institucion"],
            carrera_destino=datos["carrera_destino"],
            descripcion=datos["descripcion"],
            link_info=datos["link_info"],
            todas_las_carreras=todas,
        )
        convenio.carreras = carreras_item
        db.add(convenio)
        insertados += 1
    return insertados


def seed_convenios_only() -> None:
    """Carga sólo convenios sobre una base ya existente, sin borrar nada."""
    if not CONVENIOS_SEED:
        print("CONVENIOS_SEED está vacío: no hay convenios para cargar.")
        return

    db = SessionLocal()
    try:
        insertados = _insertar_convenios(db)
        db.commit()
        print(
            f"\n[OK] Convenios insertados: {insertados}. "
            f"Ya existían: {len(CONVENIOS_SEED) - insertados}."
        )
    except Exception as exc:
        db.rollback()
        print(f"\nError al cargar convenios: {exc}")
        raise
    finally:
        db.close()


def seed_admin_only() -> None:
    """Crea el usuario administrador si no existe, sin tocar el resto de la base.

    Útil para bases ya pobladas donde no se quiere correr el seed completo
    (que dropea las tablas). Idempotente por email.
    """
    db = SessionLocal()
    try:
        existente = db.query(Usuario).filter(Usuario.email == "admin@miifts.ar").first()
        if existente is not None:
            print("\n[OK] El usuario admin@miifts.ar ya existe (no se modifica).")
            return

        carrera = db.query(Carrera).order_by(Carrera.id.asc()).first()
        if carrera is None:
            raise ValueError(
                "No hay carreras cargadas: corré `python seed.py` o creá una carrera antes."
            )

        admin = Usuario(
            nombre="Administrador",
            apellido="Sistema",
            email="admin@miifts.ar",
            password_hash=pwd_context.hash("admin1234"),
            carrera_id=carrera.id,
            rol=RolUsuario.ADMIN,
        )
        db.add(admin)
        db.commit()
        print(f"\n[OK] Admin creado: admin@miifts.ar / admin1234 (id={admin.id}).")
    except Exception as exc:
        db.rollback()
        print(f"\nError al crear el admin: {exc}")
        raise
    finally:
        db.close()


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
            nombre=CARRERAS_SEED["dev_software"],
            duracion_cuatrimestres=6,
            ifts_id=ifts.id,
        )
        analisis_sistemas = Carrera(
            nombre=CARRERAS_SEED["analisis_sistemas"],
            duracion_cuatrimestres=6,
            ifts_id=ifts.id,
        )
        ciencia_datos_ia = Carrera(
            nombre=CARRERAS_SEED["ciencia_datos_ia"],
            duracion_cuatrimestres=6,
            ifts_id=ifts.id,
        )
        db.add_all([dev_software, analisis_sistemas, ciencia_datos_ia])
        db.flush()

        # ── 3. Materias ───────────────────────────────────────────────────────
        # REEMPLAZÁ con las materias reales del plan de estudios (PDF).
        # El campo 'codigo' debe coincidir con el código del plan (ej: "1.1.3").
        # Cada combinación (carrera_id, codigo) debe ser única.
        print("Cargando materias de Desarrollo de Software...")
        materias_dev = [
            # Año 1 — Cuatrimestre 1
            Materia(carrera_id=dev_software.id, nombre="Técnicas de Programación",                                codigo="1.1.1", anio=1, cuatrimestre=1),
            Materia(carrera_id=dev_software.id, nombre="Administración de Bases de Datos",                        codigo="1.1.2", anio=1, cuatrimestre=1),
            Materia(carrera_id=dev_software.id, nombre="Elementos de Análisis Matemáticos",                      codigo="1.1.3", anio=1, cuatrimestre=1),
            Materia(carrera_id=dev_software.id, nombre="Lógica Computacional",                                   codigo="1.1.4", anio=1, cuatrimestre=1),
            # Año 1 — Cuatrimestre 2
            Materia(carrera_id=dev_software.id, nombre="Desarrollo de Sistemas Orientados a Objetos",           codigo="1.2.1", anio=1, cuatrimestre=2),
            Materia(carrera_id=dev_software.id, nombre="Modelado y Diseño de Software",                         codigo="1.2.2", anio=1, cuatrimestre=2),
            Materia(carrera_id=dev_software.id, nombre="Estadística y probabilidades para el Desarrollo de Software", codigo="1.2.3", anio=1, cuatrimestre=2),
            Materia(carrera_id=dev_software.id, nombre="Inglés",                                                codigo="1.2.4", anio=1, cuatrimestre=2),
            Materia(carrera_id=dev_software.id, nombre="PPI I - Aproximación al campo profesional del Desarrollo de Software", codigo="1.2.5", anio=1, cuatrimestre=2),
            # Año 2 — Cuatrimestre 1
            Materia(carrera_id=dev_software.id, nombre="Desarrollo de Aplicaciones para Dispositivos",          codigo="2.1.1", anio=2, cuatrimestre=1),
            Materia(carrera_id=dev_software.id, nombre="Metodología de Pruebas de Sistemas",                     codigo="2.1.2", anio=2, cuatrimestre=1),
            Materia(carrera_id=dev_software.id, nombre="Tecnologías de la Información y Comunicación",           codigo="2.1.3", anio=2, cuatrimestre=1),
            Materia(carrera_id=dev_software.id, nombre="Taller de Comunicación",                                 codigo="2.1.4", anio=2, cuatrimestre=1),
            Materia(carrera_id=dev_software.id, nombre="Desarrollo de Sistemas de información Orientados a la Gestión y apoyo de decisiones", codigo="2.1.5", anio=2, cuatrimestre=1),
            # Año 2 — Cuatrimestre 2
            Materia(carrera_id=dev_software.id, nombre="Desarrollo de Sistemas Web (Back End)",                 codigo="2.2.1", anio=2, cuatrimestre=2),
            Materia(carrera_id=dev_software.id, nombre="Desarrollo de Sistemas Web (Front End)",                codigo="2.2.2", anio=2, cuatrimestre=2),
            Materia(carrera_id=dev_software.id, nombre="Ingeniería de Software",                                 codigo="2.2.3", anio=2, cuatrimestre=2),
            Materia(carrera_id=dev_software.id, nombre="Desarrollo e implementación de sistemas en la Nube",     codigo="2.2.4", anio=2, cuatrimestre=2),
            # Año 3 — Cuatrimestre 1
            Materia(carrera_id=dev_software.id, nombre="Programación sobre Redes",                               codigo="3.1.1", anio=3, cuatrimestre=1),
            Materia(carrera_id=dev_software.id, nombre="Seminario de Profundización y/o Actualización",          codigo="3.1.2", anio=3, cuatrimestre=1),
            Materia(carrera_id=dev_software.id, nombre="Gestión de Proyectos",                                   codigo="3.1.3", anio=3, cuatrimestre=1),
            Materia(carrera_id=dev_software.id, nombre="Trabajo, Tecnología y Sociedad",                          codigo="3.1.4", anio=3, cuatrimestre=1),
            Materia(carrera_id=dev_software.id, nombre="Proyecto Integrador",                                    codigo="3.1.5", anio=3, cuatrimestre=1),
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
            # 1er año - cuatrimestre 2
            Correlativa(materia_id=dev["1.2.1"].id, requiere_id=dev["1.1.1"].id),  # Desarrollo de Sistemas OO ← Técnicas de Programación
            Correlativa(materia_id=dev["1.2.1"].id, requiere_id=dev["1.1.2"].id),  # ← Administración de BD
            Correlativa(materia_id=dev["1.2.1"].id, requiere_id=dev["1.1.4"].id),  # ← Lógica Computacional
            Correlativa(materia_id=dev["1.2.2"].id, requiere_id=dev["1.1.1"].id),  # Modelado y Diseño ← Técnicas de Programación
            # 2do año - cuatrimestre 1
            Correlativa(materia_id=dev["2.1.1"].id, requiere_id=dev["1.2.1"].id),  # Desarrollo Apps Dispositivos ← Desarrollo OO
            Correlativa(materia_id=dev["2.1.1"].id, requiere_id=dev["1.2.2"].id),  # ← Modelado y Diseño
            Correlativa(materia_id=dev["2.1.2"].id, requiere_id=dev["1.1.1"].id),  # Metodología Pruebas ← Técnicas de Programación
            Correlativa(materia_id=dev["2.1.5"].id, requiere_id=dev["1.2.1"].id),  # Desarrollo Sistemas Info ← Desarrollo OO
            Correlativa(materia_id=dev["2.1.5"].id, requiere_id=dev["1.2.2"].id),  # ← Modelado y Diseño
            Correlativa(materia_id=dev["2.1.5"].id, requiere_id=dev["1.2.5"].id),  # ← PPI I
            # 2do año - cuatrimestre 2
            Correlativa(materia_id=dev["2.2.1"].id, requiere_id=dev["2.1.1"].id),  # Web Back ← Apps Dispositivos
            Correlativa(materia_id=dev["2.2.1"].id, requiere_id=dev["2.1.2"].id),  # ← Metodología Pruebas
            Correlativa(materia_id=dev["2.2.1"].id, requiere_id=dev["2.1.5"].id),  # ← Desarrollo Sistemas Info
            Correlativa(materia_id=dev["2.2.2"].id, requiere_id=dev["1.2.2"].id),  # Web Front ← Modelado y Diseño
            Correlativa(materia_id=dev["2.2.3"].id, requiere_id=dev["1.2.2"].id),  # Ingeniería de Software ← Modelado y Diseño
            Correlativa(materia_id=dev["2.2.4"].id, requiere_id=dev["2.1.1"].id),  # Nube ← Apps Dispositivos
            Correlativa(materia_id=dev["2.2.4"].id, requiere_id=dev["2.1.3"].id),  # ← Tecnologías de la Información y Comunicación
            Correlativa(materia_id=dev["2.2.4"].id, requiere_id=dev["2.1.5"].id),  # ← Desarrollo Sistemas Info
            # 3er año
            Correlativa(materia_id=dev["3.1.1"].id, requiere_id=dev["2.2.1"].id),  # Programación sobre Redes ← Web Back
            Correlativa(materia_id=dev["3.1.1"].id, requiere_id=dev["2.2.2"].id),  # ← Web Front
            Correlativa(materia_id=dev["3.1.1"].id, requiere_id=dev["2.2.3"].id),  # ← Ingeniería de Software
            Correlativa(materia_id=dev["3.1.2"].id, requiere_id=dev["2.2.3"].id),  # Seminario ← Ingeniería de Software
            Correlativa(materia_id=dev["3.1.3"].id, requiere_id=dev["2.2.3"].id),  # Gestión de Proyectos ← Ingeniería de Software
            Correlativa(materia_id=dev["3.1.5"].id, requiere_id=dev["2.2.4"].id),  # Proyecto Integrador ← Desarrollo en la Nube
        ]
        db.add_all(correlativas)
        db.flush()

        # ── Materias y correlativas para Análisis de Sistemas ────────────────
        print("Cargando materias de Analisis de Sistemas...")
        materias_analisis_sistemas = [
            # Año 1 — Cuatrimestre 1
            Materia(carrera_id=analisis_sistemas.id, nombre="Técnicas de Programación",                      codigo="1.1.1", anio=1, cuatrimestre=1),
            Materia(carrera_id=analisis_sistemas.id, nombre="Elementos de Análisis Matemáticos",             codigo="1.1.2", anio=1, cuatrimestre=1),
            Materia(carrera_id=analisis_sistemas.id, nombre="Administración y Gestión de Bases de Datos",    codigo="1.1.3", anio=1, cuatrimestre=1),
            Materia(carrera_id=analisis_sistemas.id, nombre="Lógica Computacional",                           codigo="1.1.4", anio=1, cuatrimestre=1),
            # Año 1 — Cuatrimestre 2
            Materia(carrera_id=analisis_sistemas.id, nombre="Desarrollo de Sistemas Orientados a Objetos",   codigo="1.2.1", anio=1, cuatrimestre=2),
            Materia(carrera_id=analisis_sistemas.id, nombre="Estadística y probabilidades para el Análisis de Sistemas", codigo="1.2.2", anio=1, cuatrimestre=2),
            Materia(carrera_id=analisis_sistemas.id, nombre="Modelado y Diseño de Software",                 codigo="1.2.3", anio=1, cuatrimestre=2),
            Materia(carrera_id=analisis_sistemas.id, nombre="Inglés",                                      codigo="1.2.4", anio=1, cuatrimestre=2),
            Materia(carrera_id=analisis_sistemas.id, nombre="PPI I - Aproximación al campo laboral",       codigo="1.2.5", anio=1, cuatrimestre=2),
            # Año 2 — Cuatrimestre 1
            Materia(carrera_id=analisis_sistemas.id, nombre="Análisis de Sistemas",                         codigo="2.1.1", anio=2, cuatrimestre=1),
            Materia(carrera_id=analisis_sistemas.id, nombre="Ingeniería de Software",                        codigo="2.1.2", anio=2, cuatrimestre=1),
            Materia(carrera_id=analisis_sistemas.id, nombre="Taller de Comunicación",                        codigo="2.1.3", anio=2, cuatrimestre=1),
            Materia(carrera_id=analisis_sistemas.id, nombre="Diseño e implementación de pruebas de software", codigo="2.1.4", anio=2, cuatrimestre=1),
            Materia(carrera_id=analisis_sistemas.id, nombre="PPI II - Relevamiento de requerimientos de usuarios", codigo="2.1.5", anio=2, cuatrimestre=1),
            # Año 2 — Cuatrimestre 2
            Materia(carrera_id=analisis_sistemas.id, nombre="Trabajo, Tecnología y Sociedad",                codigo="2.2.1", anio=2, cuatrimestre=2),
            Materia(carrera_id=analisis_sistemas.id, nombre="Redes y Ciberseguridad",                         codigo="2.2.2", anio=2, cuatrimestre=2),
            Materia(carrera_id=analisis_sistemas.id, nombre="Gestión de Proyectos",                           codigo="2.2.3", anio=2, cuatrimestre=2),
            Materia(carrera_id=analisis_sistemas.id, nombre="Seminario de Actualización en Tecnología Web",    codigo="2.2.4", anio=2, cuatrimestre=2),
            Materia(carrera_id=analisis_sistemas.id, nombre="PP III - Diseño y Arquitectura de Sistemas",     codigo="2.2.5", anio=2, cuatrimestre=2),
            # Año 3 — Cuatrimestre 1
            Materia(carrera_id=analisis_sistemas.id, nombre="Sistemas de Gestión",                             codigo="3.1.1", anio=3, cuatrimestre=1),
            Materia(carrera_id=analisis_sistemas.id, nombre="Liderazgo y Gestión de Equipos",                 codigo="3.1.2", anio=3, cuatrimestre=1),
            Materia(carrera_id=analisis_sistemas.id, nombre="Aseguramiento de Calidad de los Sistemas",       codigo="3.1.3", anio=3, cuatrimestre=1),
            Materia(carrera_id=analisis_sistemas.id, nombre="Arquitectura de Sistemas en la Nube",            codigo="3.1.4", anio=3, cuatrimestre=1),
            Materia(carrera_id=analisis_sistemas.id, nombre="PP IV - Proyecto Integrador",                    codigo="3.1.5", anio=3, cuatrimestre=1),
        ]
        db.add_all(materias_analisis_sistemas)
        db.flush()

        # Dict por codigo para Analisis de Sistemas
        dict_analisis_sistemas = {m.codigo: m for m in materias_analisis_sistemas}

        print("Cargando correlativas de Analisis de Sistemas...")
        correlativas_analisis = [
            # 1er año - cuatrimestre 2
            Correlativa(materia_id=dict_analisis_sistemas["1.2.1"].id, requiere_id=dict_analisis_sistemas["1.1.1"].id),
            Correlativa(materia_id=dict_analisis_sistemas["1.2.1"].id, requiere_id=dict_analisis_sistemas["1.1.3"].id),
            Correlativa(materia_id=dict_analisis_sistemas["1.2.1"].id, requiere_id=dict_analisis_sistemas["1.1.4"].id),
            Correlativa(materia_id=dict_analisis_sistemas["1.2.3"].id, requiere_id=dict_analisis_sistemas["1.1.1"].id),
            # 2do año - cuatrimestre 1
            Correlativa(materia_id=dict_analisis_sistemas["2.1.4"].id, requiere_id=dict_analisis_sistemas["1.2.1"].id),
            Correlativa(materia_id=dict_analisis_sistemas["2.2.4"].id, requiere_id=dict_analisis_sistemas["1.2.1"].id),
            # 3er año
            Correlativa(materia_id=dict_analisis_sistemas["3.1.1"].id, requiere_id=dict_analisis_sistemas["1.1.3"].id),
            Correlativa(materia_id=dict_analisis_sistemas["3.1.2"].id, requiere_id=dict_analisis_sistemas["2.1.1"].id),
            Correlativa(materia_id=dict_analisis_sistemas["3.1.2"].id, requiere_id=dict_analisis_sistemas["2.1.2"].id),
            Correlativa(materia_id=dict_analisis_sistemas["3.1.3"].id, requiere_id=dict_analisis_sistemas["2.1.4"].id),
            Correlativa(materia_id=dict_analisis_sistemas["3.1.4"].id, requiere_id=dict_analisis_sistemas["2.2.2"].id),
            Correlativa(materia_id=dict_analisis_sistemas["3.1.5"].id, requiere_id=dict_analisis_sistemas["2.1.5"].id),
            Correlativa(materia_id=dict_analisis_sistemas["3.1.5"].id, requiere_id=dict_analisis_sistemas["2.2.5"].id),
        ]
        db.add_all(correlativas_analisis)
        db.flush()

        # ── Materias y correlativas para Ciencia de Datos e Inteligencia Artificial ─────
        print("Cargando materias de Ciencia de Datos e Inteligencia Artificial...")
        materias_ciencia_datos = [
            # Año 1 — Cuatrimestre 1
            Materia(carrera_id=ciencia_datos_ia.id, nombre="Técnicas de Programación", codigo="1.1.1", anio=1, cuatrimestre=1),
            Materia(carrera_id=ciencia_datos_ia.id, nombre="Elementos de Análisis Matemáticos", codigo="1.1.2", anio=1, cuatrimestre=1),
            Materia(carrera_id=ciencia_datos_ia.id, nombre="Administración y Gestión de Bases de Datos", codigo="1.1.3", anio=1, cuatrimestre=1),
            Materia(carrera_id=ciencia_datos_ia.id, nombre="Lógica Computacional", codigo="1.1.4", anio=1, cuatrimestre=1),
            # Año 1 — Cuatrimestre 2
            Materia(carrera_id=ciencia_datos_ia.id, nombre="Comunicación", codigo="1.2.1", anio=1, cuatrimestre=2),
            Materia(carrera_id=ciencia_datos_ia.id, nombre="Estadística y Probabilidades para Gestión de Datos", codigo="1.2.2", anio=1, cuatrimestre=2),
            # Año 2 — Cuatrimestre 1
            Materia(carrera_id=ciencia_datos_ia.id, nombre="Desarrollo de Sistemas de Inteligencia Artificial", codigo="2.1.1", anio=2, cuatrimestre=1),
            Materia(carrera_id=ciencia_datos_ia.id, nombre="PPI I - Aproximación al campo laboral", codigo="2.1.2", anio=2, cuatrimestre=1),
            Materia(carrera_id=ciencia_datos_ia.id, nombre="Ciencia de Datos", codigo="2.1.3", anio=2, cuatrimestre=1),
            Materia(carrera_id=ciencia_datos_ia.id, nombre="Gestión de Proyectos", codigo="2.1.4", anio=2, cuatrimestre=1),
            Materia(carrera_id=ciencia_datos_ia.id, nombre="Procesamiento de Aprendizaje Automático", codigo="2.1.5", anio=2, cuatrimestre=1),
            # Año 2 — Cuatrimestre 2
            Materia(carrera_id=ciencia_datos_ia.id, nombre="Modelizado de Sistemas de Inteligencia Artificial", codigo="2.2.1", anio=2, cuatrimestre=2),
            Materia(carrera_id=ciencia_datos_ia.id, nombre="Trabajo, Tecnología y Sociedad", codigo="2.2.2", anio=2, cuatrimestre=2),
            Materia(carrera_id=ciencia_datos_ia.id, nombre="Modelizado de Minería de Datos", codigo="2.2.3", anio=2, cuatrimestre=2),
            Materia(carrera_id=ciencia_datos_ia.id, nombre="Técnicas de Procesamiento del Habla", codigo="2.2.4", anio=2, cuatrimestre=2),
            Materia(carrera_id=ciencia_datos_ia.id, nombre="Análisis y Exploración de Datos", codigo="2.2.5", anio=2, cuatrimestre=2),
            # Año 3 — Cuatrimestre 1
            Materia(carrera_id=ciencia_datos_ia.id, nombre="Seminario de Actualización", codigo="3.1.1", anio=3, cuatrimestre=1),
            Materia(carrera_id=ciencia_datos_ia.id, nombre="Técnicas de Procesamiento Digital de Imágenes", codigo="3.1.2", anio=3, cuatrimestre=1),
            Materia(carrera_id=ciencia_datos_ia.id, nombre="Proyecto Integrador", codigo="3.1.3", anio=3, cuatrimestre=1),
        ]
        db.add_all(materias_ciencia_datos)
        db.flush()

        dict_ciencia_datos = {m.codigo: m for m in materias_ciencia_datos}

        print("Cargando correlativas de Ciencia de Datos e Inteligencia Artificial...")
        correlativas_ciencia_datos = [
            # 1er año - cuatrimestre 2
            Correlativa(materia_id=dict_ciencia_datos["2.1.1"].id, requiere_id=dict_ciencia_datos["1.1.1"].id),
            Correlativa(materia_id=dict_ciencia_datos["2.1.1"].id, requiere_id=dict_ciencia_datos["1.1.3"].id),
            Correlativa(materia_id=dict_ciencia_datos["2.1.1"].id, requiere_id=dict_ciencia_datos["1.1.4"].id),
            # 2do año - cuatrimestre 1
            Correlativa(materia_id=dict_ciencia_datos["2.1.3"].id, requiere_id=dict_ciencia_datos["1.1.3"].id),
            Correlativa(materia_id=dict_ciencia_datos["2.1.3"].id, requiere_id=dict_ciencia_datos["1.2.2"].id),
            Correlativa(materia_id=dict_ciencia_datos["2.1.4"].id, requiere_id=dict_ciencia_datos["2.1.3"].id),
            Correlativa(materia_id=dict_ciencia_datos["2.1.5"].id, requiere_id=dict_ciencia_datos["2.1.3"].id),
            # 2do año - cuatrimestre 2
            Correlativa(materia_id=dict_ciencia_datos["2.2.1"].id, requiere_id=dict_ciencia_datos["2.1.1"].id),
            Correlativa(materia_id=dict_ciencia_datos["2.2.1"].id, requiere_id=dict_ciencia_datos["2.1.3"].id),
            Correlativa(materia_id=dict_ciencia_datos["2.2.3"].id, requiere_id=dict_ciencia_datos["2.1.3"].id),
            Correlativa(materia_id=dict_ciencia_datos["2.2.5"].id, requiere_id=dict_ciencia_datos["2.1.3"].id),
            # 3er año - cuatrimestre 1
            Correlativa(materia_id=dict_ciencia_datos["3.1.2"].id, requiere_id=dict_ciencia_datos["2.2.3"].id),
            Correlativa(materia_id=dict_ciencia_datos["3.1.3"].id, requiere_id=dict_ciencia_datos["2.1.4"].id),
            Correlativa(materia_id=dict_ciencia_datos["3.1.3"].id, requiere_id=dict_ciencia_datos["2.2.1"].id),
        ]
        db.add_all(correlativas_ciencia_datos)
        db.flush()

        # ── 5. Usuario de prueba ──────────────────────────────────────────────
        # Credenciales compartidas para que todos puedan probar sin JWT.
        # Eliminalo cuando implementen auth real en producción.
        print("Cargando usuario de prueba...")
        test_user = Usuario(
            nombre="Estudiante",
            apellido="Test",
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
            apellido="Sistema",
            email="admin@miifts.ar",
            password_hash=pwd_context.hash("admin1234"),
            carrera_id=dev_software.id,
            rol=RolUsuario.ADMIN,
        )
        db.add(admin_user)
        db.flush()

        # ── 7. Convenios ─────────────────────────────────────────────────────
        # Datos provistos por el usuario (ver CONVENIOS_SEED al inicio del archivo).
        convenios_cargados = _insertar_convenios(db)
        db.flush()

        db.commit()

        print("\n[OK] Seed completado.")
        print(f"  IFTS:         {ifts.nombre}")
        print(f"  Carreras:     3")
        print(f"  Materias:     {len(materias_dev)} (Desarrollo de Software)")
        print(f"  Materias AS:  {len(materias_analisis_sistemas)} (Análisis de Sistemas)")
        print(f"  Materias CDAI:{len(materias_ciencia_datos)} (Ciencia de Datos e IA)")
        print(f"  Correlativas: {len(correlativas) + len(correlativas_analisis) + len(correlativas_ciencia_datos)}")
        detalle_convenios = (
            "" if convenios_cargados else " (lista vacía hasta que se carguen los datos reales)"
        )
        print(f"  Convenios:    {convenios_cargados}{detalle_convenios}")
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
    if "--admin" in sys.argv:
        seed_admin_only()
        sys.exit(0)
    if "--convenios" in sys.argv:
        seed_convenios_only()
        sys.exit(0)
    no_drop = "--no-drop" in sys.argv
    if not no_drop:
        reset_db()
    elif hay_datos():
        print("Ya hay datos cargados, no se hace nada (corré sin --no-drop para resetear).")
        sys.exit(0)
    seed()
