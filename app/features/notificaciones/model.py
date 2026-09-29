from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class PushSubscription(Base):
    __tablename__ = "push_subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False, index=True)
    endpoint = Column(String, nullable=False, unique=True, index=True)
    p256dh = Column(String, nullable=False)
    auth = Column(String, nullable=False)
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relación bidireccional con Usuario
    usuario = relationship("Usuario", back_populates="push_subscriptions")

    # Constraint único compuesto para evitar duplicados (usuario_id, endpoint)
    __table_args__ = (
        UniqueConstraint("usuario_id", "endpoint", name="uq_push_subscription_usuario_endpoint"),
    )