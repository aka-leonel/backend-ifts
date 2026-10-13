from datetime import datetime
from zoneinfo import ZoneInfo

# Los recordatorios se guardan como hora de pared naive (la que ve el usuario).
# El servidor corre en UTC, así que "ahora" se calcula explícitamente en esta zona.
TZ_APP = ZoneInfo("America/Argentina/Buenos_Aires")


def ahora_local() -> datetime:
    """Hora actual en la zona de la app, naive (comparable con Recordatorio.fecha)."""
    return datetime.now(TZ_APP).replace(tzinfo=None)
