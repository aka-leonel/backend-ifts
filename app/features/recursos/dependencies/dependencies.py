from app.database import get_db
from sqlalchemy.orm import Session
from app.features.recursos.schema import RecursoCreate, RecursoResponse
from app.features.recursos import repository
from app.features.recursos.service import RecursoService, ConvenioService, TalentoTechService
from fastapi import Depends

def get_recurso_service(db: Session = Depends(get_db)) -> RecursoService:
    return RecursoService(repository.RecursoRepository(db))

def get_convenio_service(db: Session = Depends(get_db)) -> ConvenioService:
    return ConvenioService(repository.ConvenioRepository(db))

def get_talentotech_service(db: Session = Depends(get_db)) -> TalentoTechService:
    return TalentoTechService(repository.TalentoTechRepository(db))