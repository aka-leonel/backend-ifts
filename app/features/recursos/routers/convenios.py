from fastapi import APIRouter, Depends, Query
from typing import List

from app.shared.schemas.pagination import PaginatedResponse
from app.features.recursos.schema import ConvenioResponse, ConvenioCreate
from app.features.recursos.service import ConvenioService
from app.features.recursos.dependencies import get_convenio_service

router = APIRouter(
    prefix="/convenios",
    tags=["convenios"]
)


@router.get("/", response_model=PaginatedResponse[ConvenioResponse])
def get_all_paginated(
    service_convenio: ConvenioService = Depends(get_convenio_service),
    page: int = Query(1, ge=1, description="Número de página"),
    per_page: int = Query(20, ge=1, le=100, description="Convenios por página")
):
    return service_convenio.get_all_paginated(page=page, per_page=per_page)


@router.get("/{convenio_id}", response_model=ConvenioResponse)
def get_by_id(convenio_id: int, service_convenio: ConvenioService = Depends(get_convenio_service)):
    return service_convenio.get_by_id(convenio_id)
