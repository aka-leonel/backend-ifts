from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.features.recursos.service import TalentoTechService
from app.features.recursos import TalentoTechCreate, TalentoTechResponse
from app.features.recursos.dependencies import get_talentotech_service

router = APIRouter(
    prefix="/talentotech",
    tags=["talentotech"]
)

@router.get("/talentotech/", response_model=List[TalentoTechResponse])
def get_all(service_talentotech: TalentoTechService = Depends(get_talentotech_service)):
    return service_talentotech.get_all()

@router.get("/talentotech/{talentotech_id}", response_model=TalentoTechResponse)
def get_by_id(talentotech_id: int, service_talentotech: TalentoTechService = Depends(get_talentotech_service)):
    try:
        return service_talentotech.get_by_id(talentotech_id)
    except TalentoTechNotFound as err:
        raise HTTPException(status_code=404, detail=str(err))

@router.get("/talentotech/carrera/{carrera_id}", response_model=List[TalentoTechResponse])
def get_by_carrera(carrera_id: int, service_talentotech: TalentoTechService = Depends(get_talentotech_service)):
    return service_talentotech.get_by_carrera(carrera_id)

@router.get("/talentotech/categoria/{categoria}", response_model=List[TalentoTechResponse])
def get_by_categoria(categoria: str, service_talentotech: TalentoTechService = Depends(get_talentotech_service)):
    return service_talentotech.get_by_categoria(categoria)

@router.post("/talentotech", response_model=TalentoTechResponse, status_code=status.HTTP_201_CREATED)
def create(talentotech: TalentoTechCreate, service_talentotech: TalentoTechService = Depends(get_talentotech_service)):
    try:
        return service_talentotech.create(talentotech)
    except TalentoTechAlreadyExists as err:
        raise HTTPException(status_code=409, detail=str(err))

def update(talentotech_id: int, talentotech: TalentoTechCreate, service_talentotech: TalentoTechService = Depends(get_talentotech_service)):
    try:
        return service_talentotech.update(talentotech_id, talentotech)
    except TalentoTechNotFound as err:
        raise HTTPException(status_code=404, detail=str(err))
        
def delete(talentotech_id: int, service_talentotech: TalentoTechService = Depends(get_talentotech_service)):
    try:
        return service_talentotech.delete(talentotech_id)
    except TalentoTechNotFound as err:
        raise HTTPException(status_code=404, detail=str(err))
