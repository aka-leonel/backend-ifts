from fastapi import APIRouter, Depends, status

from app.features.recursos.service import ConvenioService
from app.features.recursos import ConvenioCreate, ConvenioResponse
from app.features.recursos.dependencies import get_convenio_service
from app.features.auth.dependencies import require_admin
from app.features.auth.schema import UsuarioResponse
from app.shared.schemas.pagination import PaginatedResponse
from app.shared.utils.pagination import PaginationParams

router = APIRouter(
    prefix="/convenios",
    tags=["convenios"]
)

@router.get("/carrera/{carrera_id}", response_model=PaginatedResponse[ConvenioResponse])
def get_by_carrera(
    carrera_id: int,
    service_convenio: ConvenioService = Depends(get_convenio_service),
    pagination: PaginationParams = Depends(),
):
    return service_convenio.get_by_carrera_paginado(carrera_id, pagination)


@router.put("/{convenio_id}", response_model=ConvenioResponse, status_code=status.HTTP_200_OK)
def update(
    convenio_id: int,
    convenio: ConvenioCreate,
    service_convenio: ConvenioService = Depends(get_convenio_service),
    usuario_actual: UsuarioResponse = Depends(require_admin),
):
    return service_convenio.update(convenio_id, convenio)

@router.delete("/{convenio_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete(
    convenio_id: int,
    service_convenio: ConvenioService = Depends(get_convenio_service),
    usuario_actual: UsuarioResponse = Depends(require_admin),
):
    service_convenio.delete(convenio_id)
    return None

@router.get("/{convenio_id}", response_model=ConvenioResponse)
def get_by_id(convenio_id: int, service_convenio: ConvenioService = Depends(get_convenio_service)):
    return service_convenio.get_by_id(convenio_id)

@router.get("/", response_model=PaginatedResponse[ConvenioResponse])
def get_all(
    service_convenio: ConvenioService = Depends(get_convenio_service),
    pagination: PaginationParams = Depends(),
):
    return service_convenio.get_all_paginado(pagination)


@router.post("/", response_model=ConvenioResponse, status_code=status.HTTP_201_CREATED)
def create(
    convenio: ConvenioCreate,
    service_convenio: ConvenioService = Depends(get_convenio_service),
    usuario_actual: UsuarioResponse = Depends(require_admin),
):
    return service_convenio.create(convenio)
