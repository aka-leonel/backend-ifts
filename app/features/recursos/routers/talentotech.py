from fastapi import APIRouter, Depends, Query, HTTPException, status
from typing import List

from app.shared.schemas.pagination import PaginatedResponse
from app.features.recursos.schema import TalentoTechResponse, TalentoTechCreate
from app.features.recursos.service import TalentoTechService, TalentoTechNotFound
from app.features.recursos.dependencies import get_talentotech_service

router = APIRouter(
    prefix="/talentotech",
    tags=["talentotech"]
)

@router.get("/", response_model=PaginatedResponse[TalentoTechResponse])
def get_all_paginated(
    service_talentotech: TalentoTechService = Depends(get_talentotech_service),
    page: int = Query(1, ge=1, description="Número de página"),
    per_page: int = Query(20, ge=1, le=100, description="Cursos por página")
):
    return service_talentotech.get_all_paginated(page=page, per_page=per_page)

@router.get("/{talentotech_id}", response_model=TalentoTechResponse)
def get_by_id(talentotech_id: int, service_talentotech: TalentoTechService = Depends(get_talentotech_service)):
    try:
        return service_talentotech.get_by_id(talentotech_id)
    except TalentoTechNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.post("/", response_model=TalentoTechResponse, status_code=status.HTTP_201_CREATED)
def create_talentotech(
    talentotech: TalentoTechCreate,
    service_talentotech: TalentoTechService = Depends(get_talentotech_service)
):
    return service_talentotech.create(talentotech)
