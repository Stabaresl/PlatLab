from modules.audit.application.dtos import ConsultarAuditoriaDTO, RegistroAuditoriaItemDTO
from modules.audit.domain.repositories import IAuditoriaRepository
from modules.shared.domain.exceptions import ForbiddenError

_SIN_PERMISO_MSG = "Solo un administrador tiene acceso a la auditoría."


class ConsultarAuditoriaQuery:
    """UC-12, api.md §10 `GET /audit/` — solo Admin (E2)."""

    def __init__(self, auditoria_repository: IAuditoriaRepository):
        self._repo = auditoria_repository

    def execute(self, input_dto: ConsultarAuditoriaDTO) -> list[RegistroAuditoriaItemDTO]:
        if input_dto.actor_rol != "administrador":
            raise ForbiddenError(_SIN_PERMISO_MSG)

        registros = self._repo.find_todos(
            actor_id=input_dto.actor_id,
            accion=input_dto.accion,
            desde=input_dto.desde,
            hasta=input_dto.hasta,
        )
        return [
            RegistroAuditoriaItemDTO(
                id=r.id,
                actor_id=r.actor_id,
                accion=r.accion,
                entidad_tipo=r.entidad_tipo,
                entidad_id=r.entidad_id,
                timestamp=r.timestamp,
            )
            for r in registros
        ]
