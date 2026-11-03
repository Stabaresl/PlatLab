from datetime import datetime, timezone


def ahora_utc() -> datetime:
    """
    Instante actual con zona horaria (UTC). Reemplaza a `datetime.utcnow()`,
    que devuelve un datetime "naive": Django (USE_TZ=True) lo guarda con un
    RuntimeWarning y compararlo con uno leído de la BD (aware) lanza TypeError.
    """
    return datetime.now(timezone.utc)
