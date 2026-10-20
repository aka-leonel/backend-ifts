from sqlalchemy import Column, DateTime, ForeignKey, Integer

from app.database import Base


class QuizUso(Base):
    """Un quiz generado con éxito; sirve para limitar usos diarios por usuario."""

    __tablename__ = "quiz_usos"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False, index=True)
    # Hora local (Buenos Aires) naive, mismo criterio que Recordatorio.fecha
    fecha = Column(DateTime, nullable=False, index=True)
