"""Exporta el esquema OpenAPI de la API a `docs/openapi.json`.

No levanta el servidor: importa la app y serializa `app.openapi()`. Sirve para
que el front genere su cliente tipado sin tener el backend corriendo, por ej.:

    npx openapi-typescript docs/openapi.json -o src/api/schema.d.ts

Uso:

    python scripts/export_openapi.py

Regenerar y commitear el resultado cada vez que cambie el contrato (endpoints,
schemas, status codes).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from app.main import app  # noqa: E402

DESTINO = RAIZ / "docs" / "openapi.json"


def main() -> None:
    schema = app.openapi()
    DESTINO.parent.mkdir(parents=True, exist_ok=True)
    DESTINO.write_text(
        json.dumps(schema, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(
        f"OpenAPI {schema['info']['version']} -> {DESTINO.relative_to(RAIZ)} "
        f"({len(schema['paths'])} paths)"
    )


if __name__ == "__main__":
    main()
