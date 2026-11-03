from modules.audit.application.dtos import ConsultarAuditoriaDTO, RegistroAuditoriaItemDTO
from modules.audit.domain.repositories import IAuditoriaRepository
from modules.shared.domain.exceptions import ForbiddenError

_SIN_PERMISO_MSG = "Solo un administrador tiene acceso a la auditoría."


class ConsultarAuditoriaQuery:
    """UC-12, api.md §10 `GET /audit/` — solo Admin (E2)."""

    def __init__(self, auditoria_repository: IAuditoriaRepository):
        self._repo = auditoria_repository

    def execute(self, input_dto: ConsultarAuditoriaDTO) -> list[RegistroAuditoriaItemDTO]:
        return self.execute_paginado(input_dto, limit=None, offset=0)[0]

    def execute_paginado(
        self, input_dto: ConsultarAuditoriaDTO, limit: int | None, offset: int
    ) -> tuple[list[RegistroAuditoriaItemDTO], int]:
        """
        La tabla de auditoría es append-only y crece sin límite: con 50k
        filas, traerla entera para paginar en Python tardaba ~1 s por
        request incluso sin carga (loadtests/). Acá el repositorio aplica
        LIMIT/OFFSET y COUNT en la base de datos.
        """
        if input_dto.actor_rol != "administrador":
            raise ForbiddenError(_SIN_PERMISO_MSG)

        filtros = {
            "actor_id": input_dto.actor_id,
            "accion": input_dto.accion,
            "desde": input_dto.desde,
            "hasta": input_dto.hasta,
        }
        registros = self._repo.find_todos(**filtros, limit=limit, offset=offset)
        total = self._repo.contar(**filtros) if limit is not None else len(registros)
        return self._a_items(registros), total

    def _a_items(self, registros) -> list[RegistroAuditoriaItemDTO]:
        return [
            RegistroAuditoriaItemDTO(
                id=r.id,
                actor_id=r.actor_id,
                accion=r.accion,
                entidad_tipo=r.entidad_tipo,
                entidad_id=r.entidad_id,
                timestamp=r.timestamp,
                metadata=r.metadata,
            )
            for r in registros
        ]
