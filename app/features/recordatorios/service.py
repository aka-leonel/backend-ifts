from sqlalchemy.orm import Session
from app.features.recordatorios.repository import RecordatorioRepository
from app.features.recordatorios.model import Recordatorio
from app.features.recordatorios.schema import RecordatorioCreate

def get_recordatorios(db: Session, usuario_id: int):
    repo = RecordatorioRepository(db)
    return repo.get_by_usuario(usuario_id)

def create_recordatorio(db: Session, recordatorio: RecordatorioCreate, usuario_id: int):
    repo = RecordatorioRepository(db)
    nuevo = Recordatorio(
        titulo=recordatorio.titulo,
        fecha=recordatorio.fecha,
        tipo=recordatorio.tipo,
        materia_id=recordatorio.materia_id,
        usuario_id=usuario_id
    )
    return repo.create(nuevo)

def delete_recordatorio(db: Session, recordatorio_id: int, usuario_id: int):
    repo = RecordatorioRepository(db)
    return repo.delete(recordatorio_id, usuario_id)