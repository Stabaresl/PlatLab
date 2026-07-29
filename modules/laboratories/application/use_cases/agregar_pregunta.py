from django.contrib.auth.hashers import make_password

from modules.laboratories.application.dtos import AgregarPreguntaDTO, PreguntaResultDTO
from modules.laboratories.domain.entities import Pregunta
from modules.laboratories.domain.repositories import ILaboratorioRepository
from modules.laboratories.domain.value_objects import TipoLaboratorio, TipoPregunta
from modules.shared.application.base_use_case import BaseUseCase
from modules.shared.domain.domain_event import DomainEvent
from modules.shared.domain.exceptions import ForbiddenError, NotFoundError, ValidationError

_LAB_NO_ENCONTRADO_MSG = "Laboratorio no encontrado."
_SIN_PERMISO_MSG = "No tienes permiso para editar este laboratorio."
_EXAMEN_NO_ENCONTRADO_MSG = "Este laboratorio todavía no tiene examen. Créalo primero."
_TIPO_INVALIDO_MSG = "Tipo de pregunta inválido."


class AgregarPreguntaUseCase(BaseUseCase[AgregarPreguntaDTO, PreguntaResultDTO]):
    """
    HE-09/HI-08, api.md §5 `POST /laboratories/{id}/exam/questions/`.
    `respuesta` nunca se persiste en claro (mismo patrón que
    `DefinirFlagUseCase`): se hashea el identificador de la opción
    correcta (`opcion_multiple`) o el texto normalizado -trim + lower-
    (`abierta`), para que `CalificadorDeExamen` (Progress) pueda
    comparar en tiempo de calificación sin exponer la respuesta.
    """

    def __init__(
        self,
        unit_of_work,
        event_dispatcher,
        laboratorio_repository: ILaboratorioRepository,
    ):
        super().__init__(unit_of_work, event_dispatcher)
        self._laboratorio_repository = laboratorio_repository

    def _validate(self, input_dto: AgregarPreguntaDTO) -> None:
        laboratorio = self._laboratorio_repository.get_by_id(input_dto.laboratorio_id)
        if laboratorio is None:
            raise NotFoundError(_LAB_NO_ENCONTRADO_MSG)

        if input_dto.actor_rol == "instructor":
            if laboratorio.instructor_id != input_dto.actor_id:
                raise ForbiddenError(_SIN_PERMISO_MSG)
        elif input_dto.actor_rol == "administrador":
            if laboratorio.tipo != TipoLaboratorio.PREDETERMINADO:
                raise ForbiddenError(_SIN_PERMISO_MSG)
        else:
            raise ForbiddenError(_SIN_PERMISO_MSG)

        examen = self._laboratorio_repository.get_examen_by_laboratorio(
            input_dto.laboratorio_id
        )
        if examen is None:
            raise NotFoundError(_EXAMEN_NO_ENCONTRADO_MSG)

        try:
            self._tipo = TipoPregunta(input_dto.tipo)
        except ValueError as exc:
            raise ValidationError(_TIPO_INVALIDO_MSG) from exc

        self._examen = examen

    def _execute_domain_logic(
        self, input_dto: AgregarPreguntaDTO
    ) -> tuple[PreguntaResultDTO, list[DomainEvent]]:
        respuesta = (
            input_dto.respuesta.strip().lower()
            if self._tipo == TipoPregunta.ABIERTA
            else input_dto.respuesta
        )
        pregunta = Pregunta(
            examen_id=self._examen.id,
            enunciado=input_dto.enunciado,
            tipo=self._tipo,
            respuesta_hash=make_password(respuesta),
            opciones=input_dto.opciones,
        )
        guardada = self._laboratorio_repository.add_pregunta(pregunta)

        result = PreguntaResultDTO(
            id=guardada.id,
            examen_id=guardada.examen_id,
            enunciado=guardada.enunciado,
            tipo=guardada.tipo.value,
            opciones=guardada.opciones,
        )
        return result, []
