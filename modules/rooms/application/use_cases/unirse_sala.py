from modules.assignments.domain.entities import Asignacion
from modules.assignments.domain.events import AssignmentAccepted
from modules.assignments.domain.repositories import IAsignacionRepository
from modules.laboratories.domain.repositories import ILaboratorioRepository
from modules.progress.application.inicializacion import inicializar_progreso
from modules.progress.domain.repositories import IProgresoRepository
from modules.rooms.application.dtos import UnirseSalaDTO, UnirseSalaResultDTO
from modules.rooms.domain.entities import ParticipanteSala
from modules.rooms.domain.events import EstudianteSeUnioASala
from modules.rooms.domain.exceptions import SalaLlenaError, SalaNoEncontradaError, SalaSinIngresosError
from modules.rooms.domain.repositories import IParticipanteSalaRepository, ISalaRepository
from modules.rooms.domain.value_objects import normalizar_codigo
from modules.shared.application.base_use_case import BaseUseCase
from modules.shared.domain.domain_event import DomainEvent
from modules.shared.domain.exceptions import ForbiddenError

_SOLO_ESTUDIANTES_MSG = "Las salas son para estudiantes: como anfitrión las administras desde tu panel."


class UnirseSalaUseCase(BaseUseCase[UnirseSalaDTO, UnirseSalaResultDTO]):
    """
    Un estudiante entra a una sala con su código. Recibe acceso inmediato al
    laboratorio (asignación `activa` con el anfitrión como instructor y el
    cierre de la sala como vencimiento) y su `Progreso` arranca en la primera
    sección. A diferencia de la autoinscripción del catálogo, no aplica la
    regla de "un laboratorio en curso a la vez": en un aula el instructor
    decide qué se trabaja ahora.

    Si el estudiante ya tenía una asignación vigente de ese laboratorio (la
    base admite una sola por estudiante y laboratorio), se reutiliza con su
    avance; si con ella ya lo había terminado, entra marcado como
    `completado_antes` y no compite por los puestos.

    Idempotente: volver a entrar con el mismo código devuelve lo mismo.
    """

    def __init__(
        self,
        unit_of_work,
        event_dispatcher,
        sala_repository: ISalaRepository,
        participante_repository: IParticipanteSalaRepository,
        asignacion_repository: IAsignacionRepository,
        laboratorio_repository: ILaboratorioRepository,
        progreso_repository: IProgresoRepository,
    ):
        super().__init__(unit_of_work, event_dispatcher)
        self._sala_repository = sala_repository
        self._participante_repository = participante_repository
        self._asignacion_repository = asignacion_repository
        self._laboratorio_repository = laboratorio_repository
        self._progreso_repository = progreso_repository

    def _validate(self, input_dto: UnirseSalaDTO) -> None:
        if input_dto.actor_rol != "estudiante":
            raise ForbiddenError(_SOLO_ESTUDIANTES_MSG)
        sala = self._sala_repository.get_by_codigo(normalizar_codigo(input_dto.codigo))
        if sala is None:
            raise SalaNoEncontradaError()
        self._existente = self._participante_repository.get(sala.id, input_dto.actor_id)
        if self._existente is None and not sala.acepta_ingresos():
            raise SalaSinIngresosError()
        self._sala = sala

    def _execute_domain_logic(self, input_dto: UnirseSalaDTO) -> tuple[UnirseSalaResultDTO, list[DomainEvent]]:
        if self._existente is not None:
            return (
                UnirseSalaResultDTO(
                    sala_id=self._sala.id,
                    asignacion_id=self._existente.asignacion_id,
                    ya_era_participante=True,
                    completado_antes=self._existente.completado_antes,
                ),
                [],
            )

        # Bloqueo de la fila de la sala: con 100 personas entrando a la vez,
        # contar y luego insertar sin bloqueo deja pasar a más del cupo.
        sala = self._sala_repository.bloquear(self._sala.id)
        if self._participante_repository.contar(sala.id) >= sala.capacidad:
            raise SalaLlenaError(sala.capacidad)

        eventos: list[DomainEvent] = []
        asignacion = self._asignacion_repository.get_vigente(input_dto.actor_id, sala.laboratorio_id)
        completado_antes = False
        if asignacion is not None:
            completado_antes = bool(self._progreso_repository.asignaciones_con_historial([asignacion.id]))
        else:
            asignacion = self._asignacion_repository.add(
                Asignacion(
                    estudiante_id=input_dto.actor_id,
                    laboratorio_id=sala.laboratorio_id,
                    instructor_id=sala.anfitrion_id,
                    fecha_vencimiento=sala.fecha_fin,
                )
            )
            asignacion.aceptar()
            asignacion = self._asignacion_repository.update(asignacion)
            inicializar_progreso(
                asignacion.id,
                asignacion.estudiante_id,
                asignacion.laboratorio_id,
                self._laboratorio_repository,
                self._progreso_repository,
            )
            eventos.append(
                AssignmentAccepted(
                    asignacion_id=asignacion.id,
                    estudiante_id=asignacion.estudiante_id,
                    laboratorio_id=asignacion.laboratorio_id,
                )
            )

        self._participante_repository.add(
            ParticipanteSala(
                sala_id=sala.id,
                estudiante_id=input_dto.actor_id,
                asignacion_id=asignacion.id,
                completado_antes=completado_antes,
            )
        )
        eventos.append(
            EstudianteSeUnioASala(sala_id=sala.id, estudiante_id=input_dto.actor_id, anfitrion_id=sala.anfitrion_id)
        )
        return (
            UnirseSalaResultDTO(
                sala_id=sala.id,
                asignacion_id=asignacion.id,
                ya_era_participante=False,
                completado_antes=completado_antes,
            ),
            eventos,
        )
