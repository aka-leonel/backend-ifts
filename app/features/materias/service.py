from __future__ import annotations

from typing import Optional

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.features.auth.repository import AuthRepository
from app.features.materias.model import Carrera, Correlativa, Materia, MateriaUsuario
from app.features.materias.repository import (
    CarreraRepository,
    CorrelativaRepository,
    MateriaRepository,
    MateriaUsuarioRepository,
)
from app.features.materias.schema import (
    CarreraCreate,
    CarreraUpdate,
    MateriaCreate,
    MateriaUpdate,
    MateriaUsuarioCreate,
    MateriaUsuarioResponse,
    MateriaUsuarioUpdate,
)
from app.shared.exceptions import BusinessRuleError, DuplicateError, NotFoundError
from app.shared.schemas.pagination import PaginatedResponse
from app.shared.utils.pagination import PaginationParams, paginate


def get_carreras(db: Session, params: PaginationParams) -> PaginatedResponse[Carrera]:
    return paginate(CarreraRepository(db).query_all(), params)


def get_carrera(db: Session, carrera_id: int) -> Carrera:
    carrera = CarreraRepository(db).get_by_id(carrera_id)
    if carrera is None:
        raise NotFoundError("Carrera no encontrada")
    return carrera


def create_carrera(db: Session, datos: CarreraCreate) -> Carrera:
    return CarreraRepository(db).create(datos)


def update_carrera(db: Session, carrera_id: int, datos: CarreraUpdate) -> Carrera:
    carrera = CarreraRepository(db).update(carrera_id, datos)
    if carrera is None:
        raise NotFoundError("Carrera no encontrada")
    return carrera


def delete_carrera(db: Session, carrera_id: int) -> Carrera:
    repo = CarreraRepository(db)
    carrera = repo.get_by_id(carrera_id)
    if carrera is None:
        raise NotFoundError("Carrera no encontrada")

    if MateriaRepository(db).query_by_carrera(carrera_id).count() > 0:
        raise BusinessRuleError(
            "No se puede eliminar una carrera con materias asociadas"
        )

    return repo.delete(carrera_id)


def get_materias_by_carrera(db: Session, carrera_id: int) -> list[Materia]:
    return MateriaRepository(db).get_by_carrera(carrera_id)


def get_materia(db: Session, materia_id: int) -> Materia:
    materia = MateriaRepository(db).get_by_id(materia_id)
    if materia is None:
        raise NotFoundError("Materia no encontrada")
    return materia


def buscar_materias(
    db: Session, q: str, anio: Optional[int], cuatrimestre: Optional[int], params: PaginationParams
) -> PaginatedResponse[Materia]:
    return paginate(MateriaRepository(db).query_search(q, anio, cuatrimestre), params)


def get_materias_by_carrera_paginado(
    db: Session, carrera_id: int, params: PaginationParams
) -> PaginatedResponse[Materia]:
    query = MateriaRepository(db).query_by_carrera(carrera_id)
    return paginate(query, params)


def create_materia(db: Session, datos: MateriaCreate) -> Materia:
    try:
        return MateriaRepository(db).create(datos)
    except IntegrityError:
        db.rollback()
        raise DuplicateError(
            f"Ya existe una materia con código '{datos.codigo}' en esa carrera"
        )


def update_materia(db: Session, materia_id: int, datos: MateriaUpdate) -> Materia:
    materia = MateriaRepository(db).update(materia_id, datos)
    if materia is None:
        raise NotFoundError("Materia no encontrada")
    return materia


def delete_materia(db: Session, materia_id: int) -> Materia:
    repo = MateriaRepository(db)
    materia = repo.get_by_id(materia_id)
    if materia is None:
        raise NotFoundError("Materia no encontrada")

    if MateriaUsuarioRepository(db).count_by_materia(materia_id) > 0:
        raise BusinessRuleError(
            "No se puede eliminar una materia con cursadas asociadas"
        )

    return repo.delete(materia_id)


def get_correlativas(
    db: Session, materia_id: int, params: PaginationParams
) -> PaginatedResponse[Correlativa]:
    return paginate(CorrelativaRepository(db).query_by_materia(materia_id), params)


def promociona_por_parciales(
    nota_parcial_1: Optional[float], nota_parcial_2: Optional[float]
) -> bool:
    """La promoción exime de rendir el final: se decide por los parciales."""
    return (
        nota_parcial_1 is not None
        and nota_parcial_2 is not None
        and nota_parcial_1 >= 7
        and nota_parcial_2 >= 7
    )


def derivar_estado_cursada(
    cursando: bool,
    nota_parcial_1: Optional[float],
    nota_parcial_2: Optional[float],
    examen_final: Optional[float],
) -> str:
    """Regla de negocio: estado de una cursada.

    Ambos parciales `>= 7` -> promocionada (exime del final). Si no
    promocionó y se rindió el `examen_final`: `>= 4` aprueba, `< 4`
    desaprueba. `cursando=True` manda por sobre cualquier nota cargada.
    """
    if cursando:
        return "cursando"
    if promociona_por_parciales(nota_parcial_1, nota_parcial_2):
        return "promocionada"
    if examen_final is not None:
        if examen_final >= 4:
            return "aprobada"
        return "desaprobada"
    return "pendiente"


def derivar_nota_final(
    nota_parcial_1: Optional[float],
    nota_parcial_2: Optional[float],
    examen_final: Optional[float],
) -> Optional[float]:
    """La nota que cierra la cursada: si promocionó, el promedio de los
    parciales (nunca rindió examen final); si no, la nota del examen_final
    rendido. No es una nota que se cargue: se calcula siempre a partir de
    los parciales y el examen_final."""
    if promociona_por_parciales(nota_parcial_1, nota_parcial_2):
        return round((nota_parcial_1 + nota_parcial_2) / 2, 2)
    return examen_final


def _a_materia_usuario_response(cursada: MateriaUsuario) -> MateriaUsuarioResponse:
    """Arma la respuesta de una cursada calculando `estado` y `nota_final` acá
    (capa de negocio) — ninguno de los dos es una columna que se manda."""
    return MateriaUsuarioResponse(
        id=cursada.id,
        usuario_id=cursada.usuario_id,
        materia_id=cursada.materia_id,
        cursando=cursada.cursando,
        nota_parcial_1=cursada.nota_parcial_1,
        nota_parcial_2=cursada.nota_parcial_2,
        examen_final=cursada.examen_final,
        nota_final=derivar_nota_final(
            cursada.nota_parcial_1, cursada.nota_parcial_2, cursada.examen_final
        ),
        estado=derivar_estado_cursada(
            cursada.cursando,
            cursada.nota_parcial_1,
            cursada.nota_parcial_2,
            cursada.examen_final,
        ),
    )


def get_materias_usuario(
    db: Session, usuario_id: int, params: PaginationParams
) -> PaginatedResponse[MateriaUsuarioResponse]:
    pagina = paginate(MateriaUsuarioRepository(db).query_by_usuario(usuario_id), params)
    items = [_a_materia_usuario_response(c) for c in pagina.items]
    return PaginatedResponse.build(
        items=items, total=pagina.total, page=pagina.page, per_page=pagina.per_page
    )


def add_materia_usuario(
    db: Session, datos: MateriaUsuarioCreate, usuario_id: int
) -> MateriaUsuarioResponse:
    usuario = AuthRepository(db).get_by_id(usuario_id)
    if usuario is None:
        raise NotFoundError("Usuario no encontrado")

    materia = MateriaRepository(db).get_by_id(datos.materia_id)
    if materia is None:
        raise NotFoundError(f"No existe la materia {datos.materia_id}")

    if materia.carrera_id != usuario.carrera_id:
        raise BusinessRuleError("La materia no pertenece a la carrera del alumno")

    repo = MateriaUsuarioRepository(db)
    if repo.get_by_usuario_y_materia(usuario_id, datos.materia_id) is not None:
        raise DuplicateError("Esa materia ya está cargada")

    nueva = MateriaUsuario(usuario_id=usuario_id, **datos.model_dump())

    try:
        creada = repo.create(nueva)
    except IntegrityError:
        db.rollback()
        raise DuplicateError("Esa materia ya está cargada")
    return _a_materia_usuario_response(creada)


def update_materia_usuario(
    db: Session,
    materia_usuario_id: int,
    usuario_id: int,
    datos: MateriaUsuarioUpdate,
) -> MateriaUsuarioResponse:
    cambios = datos.model_dump(exclude_unset=True)
    cursada = MateriaUsuarioRepository(db).update(materia_usuario_id, usuario_id, cambios)
    if cursada is None:
        raise NotFoundError("No se encontró esa cursada")
    return _a_materia_usuario_response(cursada)


def delete_materia_usuario(
    db: Session, materia_usuario_id: int, usuario_id: int
) -> MateriaUsuario:
    cursada = MateriaUsuarioRepository(db).delete(materia_usuario_id, usuario_id)
    if cursada is None:
        raise NotFoundError("No se encontró esa cursada")
    return cursada


def calcular_promedio(db: Session, usuario_id: int) -> dict:
    """Promedia la `nota_final` (calculada) de todas las cursadas que ya
    cerraron: promocionada (promedio de parciales) o aprobada/desaprobada
    (nota del examen_final). Las que siguen `cursando` o están `pendiente`
    no tienen nota_final y no entran en la cuenta."""
    cursadas = MateriaUsuarioRepository(db).get_by_usuario(usuario_id)

    notas = [
        derivar_nota_final(c.nota_parcial_1, c.nota_parcial_2, c.examen_final)
        for c in cursadas
        if not c.cursando
    ]
    notas = [n for n in notas if n is not None]

    if not notas:
        return {"promedio": None, "materias_computadas": 0}

    promedio = sum(notas) / len(notas)
    return {"promedio": round(promedio, 2), "materias_computadas": len(notas)}
