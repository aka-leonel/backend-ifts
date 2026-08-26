from sqlalchemy.orm import Session

from app.features.recursos.model import Recurso, Convenio, TalentoTech
from app.features.recursos.schema import RecursoBase, RecursoCreate, ConvenioResponse, TalentoTechResponse, TalentoTechCreate, ConvenioCreate
from typing import Optional


class RecursoRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def get_all(self) -> list[Recurso]:
        return self.db.query(Recurso).all()

    def get_recursos_by_usuario(self, usuario_id: int) -> list[Recurso]:
        return (self.db.query(Recurso).filter(Recurso.usuario_id == usuario_id).all())

    def create_recurso(self, recurso: RecursoCreate) -> Recurso:
        recurso_db = Recurso(
            usuario_id = recurso.usuario_id,
            materia_id = recurso.materia_id,
            titulo = recurso.titulo,
            url = str(recurso.url),
            descripcion = recurso.descripcion if recurso.descripcion else None,
            fecha_creacion = recurso.fecha_creacion
        )
        self.db.add(recurso_db)
        self.db.commit()
        self.db.refresh(recurso_db)
        return recurso_db

    def update_recurso(self, recurso_id: int, recurso: RecursoCreate) -> Optional[Recurso]: 
        db_recurso = self.db.query(Recurso).filter(Recurso.id == recurso_id).first()
        if db_recurso is None:
            return None
        db_recurso.titulo = recurso.titulo
        db_recurso.url = str(recurso.url)
        db_recurso.descripcion = recurso.descripcion if recurso.descripcion else None
        db_recurso.materia_id = recurso.materia_id
        self.db.commit()
        self.db.refresh(db_recurso)
        return db_recurso

    def delete_recurso(self, recurso_id: int) -> None:
        db_recurso = self.db.query(Recurso).filter(Recurso.id == recurso_id).first()
        if db_recurso is None:
            return None
        self.db.delete(db_recurso)
        self.db.commit()

    def get_recurso_by_id(self, recurso_id: int) -> Optional[Recurso]:
        return self.db.query(Recurso).filter(Recurso.id == recurso_id).first()

    def get_recurso_by_materia(self, materia_id: int) -> list[Recurso]:
        return (self.db.query(Recurso).filter(Recurso.materia_id == materia_id).all())


class ConvenioRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_convenio_by_id(self, convenio_id: int) -> Optional[Convenio]:
        return self.db.query(Convenio).filter(Convenio.id == convenio_id).first()  

    def get_all(self) -> list[Convenio]:
        return self.db.query(Convenio).all()
    
    def get_convenios_by_carrera(self, carrera_id: int) -> list[Convenio]:
        return self.db.query(Convenio).filter(Convenio.carrera_id == carrera_id).all()

    def create_convenio(self, convenio: ConvenioCreate) -> Convenio:
        db_convenio = Convenio(
            institucion = convenio.institucion,
            carrera_destino = convenio.carrera_destino,
            descripcion = convenio.descripcion,
            link_info = str(convenio.link_info),
            carrera_id = convenio.carrera_id
        )
        self.db.add(db_convenio)
        self.db.commit()
        self.db.refresh(db_convenio)
        return db_convenio

    def update_convenio(self, convenio_id: int, convenio: ConvenioCreate) -> Optional[Convenio]:
        db_convenio = self.db.query(Convenio).filter(Convenio.id == convenio_id).first()
        if db_convenio is None:
            return None
        db_convenio.institucion = convenio.institucion
        db_convenio.carrera_destino = convenio.carrera_destino
        db_convenio.descripcion = convenio.descripcion
        db_convenio.link_info = str(convenio.link_info)
        db_convenio.carrera_id = convenio.carrera_id
        self.db.commit()
        self.db.refresh(db_convenio)
        return db_convenio

    def delete_convenio(self, convenio_id: int) -> None:
        db_convenio = self.db.query(Convenio).filter(Convenio.id == convenio_id).first()
        if db_convenio is None:
            return None
        self.db.delete(db_convenio)
        self.db.commit()
    
class TalentoTechRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self) -> list[TalentoTech]:
        return self.db.query(TalentoTech).all()
    
    def get_talentotech_by_id(self, talentotech_id: int) -> Optional[TalentoTech]:
        return self.db.query(TalentoTech).filter(TalentoTech.id == talentotech_id).first()
    
    def get_talentotech_by_carrera(self, carrera_id: int) -> list[TalentoTech]:
        return self.db.query(TalentoTech).filter(TalentoTech.carrera_id == carrera_id).all()

    def get_talentotech_by_categoria(self, categoria: str) -> list[TalentoTech]:
        return self.db.query(TalentoTech).filter(TalentoTech.categoria == categoria).all()

    def create_talentotech(self, talentotech: TalentoTechCreate) -> TalentoTech:
        db_talentotech = TalentoTech(
            carrera_id = talentotech.carrera_id,
            nombre_curso = talentotech.nombre_curso,
            categoria = talentotech.categoria,
            descripcion = talentotech.descripcion,
            duracion = talentotech.duracion,
            link_inscripcion = str(talentotech.link_inscripcion)
        )
        self.db.add(db_talentotech)
        self.db.commit()
        self.db.refresh(db_talentotech)
        return db_talentotech

    def update_talentotech(self, talentotech_id: int, talentotech: TalentoTechCreate) -> Optional[TalentoTech]:
        db_talentotech = self.db.query(TalentoTech).filter(TalentoTech.id == talentotech_id).first()
        if (db_talentotech) is None:
            return None
        db_talentotech.carrera_id = talentotech.carrera_id
        db_talentotech.nombre_curso = talentotech.nombre_curso
        db_talentotech.categoria = talentotech.categoria
        db_talentotech.descripcion = talentotech.descripcion
        db_talentotech.duracion = talentotech.duracion
        db_talentotech.link_inscripcion = str(talentotech.link_inscripcion)
        self.db.commit()
        self.db.refresh(db_talentotech)
        return db_talentotech   

    def delete_talentotech(self, talentotech_id: int) -> None:
        db_talentotech = self.db.query(TalentoTech).filter(TalentoTech.id == talentotech_id).first()
        if db_talentotech is None:
            return None
        self.db.delete(db_talentotech)
        self.db.commit()
        




    






