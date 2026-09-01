from fastapi import APIRouter, Depends, status
from typing import List

from app.features.recursos.service import TalentoTechService
from app.features.recursos import TalentoTechCreate, TalentoTechResponse
from app.features.recursos.dependencies import get_talentotech_service
from app.shared.schemas.pagination import PaginatedResponse
from app.shared.utils.pagination import PaginationParams

router = APIRouter(
    prefix="/talentotech",
    tags=["talentotech"]
)

@router.get("/carrera/{carrera_id}", response_model=List[TalentoTechResponse])
def get_by_carrera(carrera_id: int, service_talentotech: TalentoTechService = Depends(get_talentotech_service)):
    return service_talentotech.get_by_carrera(carrera_id)

@router.get("/categoria/{categoria}", response_model=List[TalentoTechResponse])
def get_by_categoria(categoria: str, service_talentotech: TalentoTechService = Depends(get_talentotech_service)):
    return service_talentotech.get_by_categoria(categoria)

@router.put("/{talentotech_id}", response_model=TalentoTechResponse, status_code=status.HTTP_201_CREATED)
def update(talentotech_id: int, talentotech: TalentoTechCreate, service_talentotech: TalentoTechService = Depends(get_talentotech_service)):
    return service_talentotech.update(talentotech_id, talentotech)

@router.delete("/{talentotech_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete(talentotech_id: int, service_talentotech: TalentoTechService = Depends(get_talentotech_service)):
    service_talentotech.delete(talentotech_id)
    return None

@router.get("/", response_model=PaginatedResponse[TalentoTechResponse])
def get_all(
    service_talentotech: TalentoTechService = Depends(get_talentotech_service),
    pagination: PaginationParams = Depends(),
):
    return service_talentotech.get_all_paginado(pagination)

@router.get("/{talentotech_id}", response_model=TalentoTechResponse)
def get_by_id(talentotech_id: int, service_talentotech: TalentoTechService = Depends(get_talentotech_service)):
    return service_talentotech.get_by_id(talentotech_id)

@router.post("/", response_model=TalentoTechResponse, status_code=status.HTTP_201_CREATED)
def create(talentotech: TalentoTechCreate, service_talentotech: TalentoTechService = Depends(get_talentotech_service)):
    return service_talentotech.create(talentotech)
