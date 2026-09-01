from datetime import date
from typing import Optional
from sqlalchemy.orm import Session
from app.features.recordatorios.model import Recordatorio

class RecordatorioRepository:
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_usuario(self, usuario_id: int):
        return self.query_by_usuario(usuario_id).all()

    def query_by_usuario(self, usuario_id: int):
        return (
            self.db.query(Recordatorio)
            .filter(Recordatorio.usuario_id == usuario_id)
            .order_by(Recordatorio.fecha)
        )
    
    def create(self, recordatorio: Recordatorio):
        self.db.add(recordatorio)
        self.db.commit()
        self.db.refresh(recordatorio)
        return recordatorio
    
    def delete(self, recordatorio_id: int, usuario_id: int):
        recordatorio = self.db.query(Recordatorio).filter(
            Recordatorio.id == recordatorio_id,
            Recordatorio.usuario_id == usuario_id
        ).first()
        if recordatorio:
            self.db.delete(recordatorio)
            self.db.commit()
        return recordatorio

    def query_search(self, usuario_id: int, tipo: Optional[str], desde: Optional[date], hasta: Optional[date], materia_id: Optional[int]):
        query = self.db.query(Recordatorio).filter(Recordatorio.usuario_id == usuario_id)
        if tipo is not None:
            query = query.filter(Recordatorio.tipo == tipo)
        if materia_id is not None:
            query = query.filter(Recordatorio.materia_id == materia_id)
        if desde is not None:
            query = query.filter(Recordatorio.fecha >= desde)
        if hasta is not None:
            query = query.filter(Recordatorio.fecha <= hasta)
        return query.order_by(Recordatorio.fecha.desc())

    def search(self, usuario_id: int, tipo: Optional[str], desde: Optional[date], hasta: Optional[date], materia_id: Optional[int]) -> list[Recordatorio]:
        return self.query_search(usuario_id, tipo, desde, hasta, materia_id).all()