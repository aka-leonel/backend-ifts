from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class Recordatorio(Base):
    __tablename__ = "recordatorios"

    id = Column(Integer, primary_key=True, index=True)
    titulo = Column(String, nullable=False)
    fecha = Column(DateTime, nullable=False)
    tipo = Column(String, nullable=False)  # "parcial" / "tp" / "final" / "otro"
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    materia_id = Column(Integer, ForeignKey("materias.id"), nullable=True)

    usuario = relationship("Usuario", back_populates="recordatorios")
