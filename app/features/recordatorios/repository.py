from sqlalchemy.orm import Session
from app.features.recordatorios.model import Recordatorio

class RecordatorioRepository:
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_usuario(self, usuario_id: int):
        return self.db.query(Recordatorio).filter(
            Recordatorio.usuario_id == usuario_id
        ).all()
    
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