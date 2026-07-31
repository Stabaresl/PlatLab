from django.contrib.auth.hashers import check_password

from modules.laboratories.application.dtos import VerificarFlagPreviewDTO
from modules.laboratories.domain.repositories import ILaboratorioRepository
from modules.shared.domain.exceptions import ForbiddenError, NotFoundError

_LAB_NO_ENCONTRADO_MSG = "Laboratorio no encontrado."
_SECCION_NO_ENCONTRADA_MSG = "Sección no encontrada."
_SIN_FLAG_MSG = "Esta sección todavía no tiene una flag definida."
_SIN_PERMISO_MSG = "No tienes permiso para previsualizar este laboratorio."


class VerificarFlagPreviewQuery:
    """
    Verifica si `valor` coincide con la flag de la sección — solo para que
    admin/instructor dueño confirmen que la configuraron bien antes de
    aprobar. A diferencia de `ValidarFlagUseCase` (Progress), no persiste
    intentos ni aplica rate limiting: no es una superficie expuesta a
    estudiantes.
    """

    def __init__(self, laboratorio_repository: ILaboratorioRepository):
        self._repo = laboratorio_repository

    def execute(self, input_dto: VerificarFlagPreviewDTO) -> bool:
        laboratorio = self._repo.get_by_id(input_dto.laboratorio_id)
        if laboratorio is None:
            raise NotFoundError(_LAB_NO_ENCONTRADO_MSG)

        es_admin = input_dto.actor_rol == "administrador"
        es_dueno = (
            input_dto.actor_rol == "instructor"
            and laboratorio.instructor_id == input_dto.actor_id
        )
        if not (es_admin or es_dueno):
            raise ForbiddenError(_SIN_PERMISO_MSG)

        seccion = self._repo.get_seccion_by_id(input_dto.seccion_id)
        if seccion is None or seccion.laboratorio_id != laboratorio.id:
            raise NotFoundError(_SECCION_NO_ENCONTRADA_MSG)

        flag = self._repo.get_flag_by_seccion(seccion.id)
        if flag is None:
            raise NotFoundError(_SIN_FLAG_MSG)

        return check_password(input_dto.valor, flag.hash)
