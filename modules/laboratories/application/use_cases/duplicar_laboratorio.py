from modules.laboratories.application.dtos import DuplicarLaboratorioDTO, LaboratorioResultDTO
from modules.laboratories.domain.events import LaboratoryDuplicated
from modules.laboratories.domain.repositories import ILaboratorioRepository
from modules.laboratories.domain.services import DuplicadorDeLaboratorio
from modules.shared.application.base_use_case import BaseUseCase
from modules.shared.domain.domain_event import DomainEvent
from modules.shared.domain.exceptions import ForbiddenError, NotFoundError

_LAB_NO_ENCONTRADO_MSG = "Laboratorio no encontrado."
_SIN_PERMISO_MSG = "Solo un instructor puede duplicar laboratorios."


class DuplicarLaboratorioUseCase(BaseUseCase[DuplicarLaboratorioDTO, LaboratorioResultDTO]):
    """
    UC-05, api.md §5 `POST /laboratories/{id}/duplicate/`: crea una
    copia `personalizado` de un `predeterminado` (secciones + flags),
    propiedad del instructor que duplica. El original permanece
    inalterado (RF-31). La validación de que el origen sea realmente un
    `predeterminado` vive en `DuplicadorDeLaboratorio` (Domain).
    """

    def __init__(
        self,
        unit_of_work,
        event_dispatcher,
        laboratorio_repository: ILaboratorioRepository,
        duplicador: DuplicadorDeLaboratorio | None = None,
    ):
        super().__init__(unit_of_work, event_dispatcher)
        self._laboratorio_repository = laboratorio_repository
        self._duplicador = duplicador or DuplicadorDeLaboratorio()

    def _validate(self, input_dto: DuplicarLaboratorioDTO) -> None:
        if input_dto.actor_rol != "instructor":
            raise ForbiddenError(_SIN_PERMISO_MSG)

        laboratorio = self._laboratorio_repository.get_by_id(input_dto.laboratorio_id)
        if laboratorio is None:
            raise NotFoundError(_LAB_NO_ENCONTRADO_MSG)

        self._laboratorio = laboratorio

    def _execute_domain_logic(
        self, input_dto: DuplicarLaboratorioDTO
    ) -> tuple[LaboratorioResultDTO, list[DomainEvent]]:
        original = self._laboratorio
        secciones = self._laboratorio_repository.get_secciones(input_dto.laboratorio_id)
        flags_por_seccion = {}
        for seccion in secciones:
            flag = self._laboratorio_repository.get_flag_by_seccion(seccion.id)
            if flag is not None:
                flags_por_seccion[seccion.id] = flag

        copia, secciones_copiadas, flags_copiadas = self._duplicador.duplicar(
            original, secciones, flags_por_seccion, input_dto.actor_id
        )

        guardado = self._laboratorio_repository.add(copia)
        for seccion in secciones_copiadas:
            self._laboratorio_repository.add_seccion(seccion)
        for flag in flags_copiadas:
            self._laboratorio_repository.save_flag(flag)

        result = LaboratorioResultDTO(
            id=guardado.id,
            nombre=guardado.nombre,
            estado=guardado.estado.value,
            tipo=guardado.tipo.value,
        )
        event = LaboratoryDuplicated(
            laboratorio_id=guardado.id, origen_id=original.id, instructor_id=input_dto.actor_id
        )
        return result, [event]
