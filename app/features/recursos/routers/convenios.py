from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.features.recursos.service import ConvenioService
from app.features.recursos import ConvenioCreate, ConvenioResponse
from app.features.recursos.dependencies import get_convenio_service

router = APIRouter(
    prefix="/convenios",
    tags=["convenios"]
)


@router.get("/", response_model=List[ConvenioResponse])
def get_all(service_convenio: ConvenioService = Depends(get_convenio_service)):
    return service_convenio.get_all()

@router.get("/{convenio_id}", response_model=ConvenioResponse)
def get_by_id(convenio_id: int, service_convenio: ConvenioService = Depends(get_convenio_service)):
    try:
        return service_convenio.get_by_id(convenio_id)
    except ConvenioNotFound as err:
        raise HTTPException(status_code=404, detail=str(err))

@router.get("/carrera/{carrera_id}", response_model=List[ConvenioResponse])
def get_by_carrera(carrera_id: int, service_convenio: ConvenioService = Depends(get_convenio_service)):
    return service_convenio.get_by_carrera(carrera_id)

@router.post("/", response_model=ConvenioResponse, status_code=status.HTTP_201_CREATED)
def create(convenio: ConvenioCreate, service_convenio: ConvenioService = Depends(get_convenio_service)):
    return service_convenio.create(convenio)

@router.update("/{convenio_id}", response_model=ConvenioResponse, status_code=status.HTTP_204_NO_CONTENT)
def update(convenio_id: int, convenio: ConvenioCreate, service_convenio: ConvenioService = Depends(get_convenio_service)):
    try:
        return service_convenio.update(convenio_id, convenio)
    except ConvenioNotFound as err:
        raise HTTPException(status_code=404, detail=str(err))

@router.delete("/{convenio_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete(convenio_id: int, service_convenio: ConvenioService = Depends(get_convenio_service)):
    try:
        return service_convenio.delete(convenio_id)
    except ConvenioNotFound as err:
        raise: HTTPException(status_code= 404, detail=str(err))