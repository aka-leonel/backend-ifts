from database import get_db
from sqlalchemy.orm import Session
from features.recursos.schema import RecursoCreate, RecursoResponse
from features.recursos import repository
from features.recursos.service import RecursoService, ConvenioService, TalentoTechService

def get_recurso_service(db: Session = Depends(get_db)) -> RecursoService:
    return RecursoService(repository.RecursoRepository(db))

def get_convenio_service(db: Session = Depends(get_db)) -> ConvenioService:
    return ConvenioService(repository.ConvenioRepository(db))

def get_talentotech_service(db: Session = Depends(get_db)) -> TalentoTechService:
    return TalentoTechService(repository.TalentoTechRepository(db))