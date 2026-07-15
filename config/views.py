from django.db import connections
from django.db.utils import OperationalError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from modules.shared.infrastructure.redis_client import RedisClient


class HealthCheckView(APIView):
    """
    GET /api/v1/health/ — endpoint público (HA-04, RF-28).

    Verifica que el backend puede conectarse a sus dos dependencias
    críticas (PostgreSQL y Redis) y responde 200 si ambas están arriba,
    503 si alguna falla. Lo usa tanto el frontend (HV-01, para validar
    disponibilidad antes de mostrar la landing) como el orquestador de
    contenedores/monitoreo en producción.
    """

    permission_classes = [AllowAny]

    def get(self, request):
        checks = {
            "database": self._check_database(),
            "redis": self._check_redis(),
        }
        healthy = all(checks.values())
        status_code = 200 if healthy else 503

        return Response(
            {"status": "ok" if healthy else "degraded", "checks": checks},
            status=status_code,
        )

    def _check_database(self) -> bool:
        try:
            with connections["default"].cursor() as cursor:
                cursor.execute("SELECT 1")
            return True
        except OperationalError:
            return False

    def _check_redis(self) -> bool:
        try:
            RedisClient().raw.ping()
            return True
        except Exception:  # noqa: BLE001 — cualquier falla de conexión cuenta como "no saludable"
            return False
