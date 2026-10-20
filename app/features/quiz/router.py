from fastapi import APIRouter, Depends, File, Query, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.features.auth.dependencies import get_current_user
from app.features.auth.schema import UsuarioResponse
from app.features.quiz import service
from app.features.quiz.schema import QuizResponse

router = APIRouter(prefix="/quiz", tags=["quiz"])


@router.post("/", response_model=QuizResponse)
def generar_quiz(
    archivo: UploadFile = File(..., description="PDF con el material de estudio (máx. 10 MB)"),
    cantidad: int = Query(5, ge=1, le=10, description="Cantidad de preguntas"),
    db: Session = Depends(get_db),
    current_user: UsuarioResponse = Depends(get_current_user),
):
    contenido = archivo.file.read(service.MAX_PDF_BYTES + 1)
    return service.generar_quiz(db, current_user.id, contenido, cantidad)
