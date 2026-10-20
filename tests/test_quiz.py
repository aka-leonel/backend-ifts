import json
from datetime import timedelta

import httpx
import pytest

from app.features.quiz import service
from app.features.quiz.model import QuizUso
from app.shared.exceptions import BadRequestError
from app.shared.utils.tiempo import ahora_local

PREGUNTA = {
    "enunciado": "¿Capital de Argentina?",
    "opciones": ["Córdoba", "Buenos Aires", "Rosario", "Mendoza"],
    "correcta": 1,
    "explicacion": "Es la capital federal.",
}


def _respuesta_ia(contenido: str) -> httpx.Response:
    req = httpx.Request("POST", "http://ia/chat/completions")
    return httpx.Response(
        200, json={"choices": [{"message": {"content": contenido}}]}, request=req
    )


@pytest.fixture
def usuario_id(usuario_registrado):
    return usuario_registrado["response"]["id"]


@pytest.fixture
def con_ia(monkeypatch):
    monkeypatch.setenv("LLM_API_KEY", "x")
    monkeypatch.setenv("LLM_BASE_URL", "http://ia")
    monkeypatch.setattr(service, "extraer_texto", lambda _: "texto " * 100)


def test_genera_quiz(con_ia, monkeypatch, db_session, usuario_id):
    monkeypatch.setattr(service.httpx, "post", lambda *a, **k: _respuesta_ia(json.dumps({"preguntas": [PREGUNTA]})))
    quiz = service.generar_quiz(db_session, usuario_id, b"pdf", 1)
    assert quiz.preguntas[0].correcta == 1


def test_acepta_json_envuelto_en_markdown(con_ia, monkeypatch, db_session, usuario_id):
    envuelto = "```json\n" + json.dumps({"preguntas": [PREGUNTA]}) + "\n```"
    monkeypatch.setattr(service.httpx, "post", lambda *a, **k: _respuesta_ia(envuelto))
    assert len(service.generar_quiz(db_session, usuario_id, b"pdf", 1).preguntas) == 1


def test_respuesta_invalida_da_502_y_no_gasta_uso(con_ia, monkeypatch, db_session, usuario_id):
    monkeypatch.setattr(service.httpx, "post", lambda *a, **k: _respuesta_ia("no es json"))
    with pytest.raises(service.ServicioIAError):
        service.generar_quiz(db_session, usuario_id, b"pdf", 1)
    assert service._usos_de_hoy(db_session, usuario_id) == 0


def test_sin_api_key_da_503(monkeypatch, db_session, usuario_id):
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    with pytest.raises(service.ServicioIANoConfigurado):
        service.generar_quiz(db_session, usuario_id, b"pdf", 1)


def test_pdf_invalido():
    with pytest.raises(BadRequestError):
        service.extraer_texto(b"esto no es un pdf")


def test_pdf_demasiado_grande():
    with pytest.raises(BadRequestError):
        service.extraer_texto(b"0" * (service.MAX_PDF_BYTES + 1))


def test_limite_diario_da_429(con_ia, monkeypatch, db_session, usuario_id):
    monkeypatch.setattr(service.httpx, "post", lambda *a, **k: _respuesta_ia(json.dumps({"preguntas": [PREGUNTA]})))
    for _ in range(service.MAX_USOS_POR_DIA):
        service.generar_quiz(db_session, usuario_id, b"pdf", 1)
    with pytest.raises(service.LimiteDiarioError):
        service.generar_quiz(db_session, usuario_id, b"pdf", 1)


def test_usos_de_ayer_no_cuentan(con_ia, monkeypatch, db_session, usuario_id):
    monkeypatch.setattr(service.httpx, "post", lambda *a, **k: _respuesta_ia(json.dumps({"preguntas": [PREGUNTA]})))
    ayer = ahora_local() - timedelta(days=1)
    db_session.add_all([QuizUso(usuario_id=usuario_id, fecha=ayer) for _ in range(service.MAX_USOS_POR_DIA)])
    db_session.commit()
    assert len(service.generar_quiz(db_session, usuario_id, b"pdf", 1).preguntas) == 1
