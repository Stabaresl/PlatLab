from modules.laboratories.application.dtos import LaboratorioEnRevisionItemDTO
from modules.laboratories.domain.repositories import ILaboratorioRepository
from modules.shared.domain.exceptions import ForbiddenError

_SIN_PERMISO_MSG = "Solo un administrador puede ver la cola de revisión."


class ListarLaboratoriosEnRevisionQuery:
    """`GET /laboratories/review-queue/` — cola de laboratorios personalizados pendientes."""

    def __init__(self, laboratorio_repository: ILaboratorioRepository):
        self._repo = laboratorio_repository

    def execute(self, actor_rol: str) -> list[LaboratorioEnRevisionItemDTO]:
        if actor_rol != "administrador":
            raise ForbiddenError(_SIN_PERMISO_MSG)

        laboratorios = self._repo.find_en_revision()
        return [
            LaboratorioEnRevisionItemDTO(
                id=lab.id,
                nombre=lab.nombre,
                instructor_id=lab.instructor_id,
                updated_at=lab.updated_at,
            )
            for lab in laboratorios
        ]
