from sqlalchemy.orm import Session
from app.features.recordatorios.model import Recordatorio

class RecordatorioRepository:
    
    def __init__(self, db: Session):
        self.db = db

    
    def count_by_usuario(self, usuario_id: int) -> int:
        """Cuenta el número total de recordatorios para un usuario."""
        return self.db.query(Recordatorio).filter(
            Recordatorio.usuario_id == usuario_id
        ).count()

    def get_paginated_by_usuario(self, usuario_id: int, page: int, per_page: int) -> list[Recordatorio]:
        """Obtiene los recordatorios de un usuario de forma paginada."""
        offset = (page - 1) * per_page
        return self.db.query(Recordatorio).filter(
            Recordatorio.usuario_id == usuario_id
        ).offset(offset).limit(per_page).all()
    
    
    # def get_by_usuario(self, usuario_id: int):
    #     return self.db.query(Recordatorio).filter(
    #         Recordatorio.usuario_id == usuario_id
    #     ).all()
    
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