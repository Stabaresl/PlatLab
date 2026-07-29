import uuid

import pytest

from modules.assignments.application.dtos import AceptarInvitacionDTO, RechazarInvitacionDTO
from modules.assignments.application.use_cases.aceptar_invitacion import AceptarInvitacionUseCase
from modules.assignments.application.use_cases.rechazar_invitacion import (
    RechazarInvitacionUseCase,
)
from modules.assignments.domain.entities import Asignacion
from modules.assignments.domain.value_objects import EstadoAsignacion
from modules.assignments.infrastructure.repositories import AsignacionRepository
from modules.laboratories.domain.entities import Laboratorio, Seccion
from modules.laboratories.domain.value_objects import (
    EstadoLaboratorio,
    NivelDificultad,
    TipoLaboratorio,
)
from modules.laboratories.infrastructure.repositories import LaboratorioRepository
from modules.progress.domain.value_objects import EstadoProgresoSeccion
from modules.progress.infrastructure.repositories import ProgresoRepository
from modules.shared.domain.exceptions import BusinessRuleViolationError, NotFoundError
from modules.shared.infrastructure.event_dispatcher import EventDispatcher
from modules.shared.infrastructure.unit_of_work import BaseUnitOfWork


def _aceptar_uc():
    return AceptarInvitacionUseCase(
        unit_of_work=BaseUnitOfWork(),
        event_dispatcher=EventDispatcher(),
        asignacion_repository=AsignacionRepository(),
        laboratorio_repository=LaboratorioRepository(),
        progreso_repository=ProgresoRepository(),
    )


def _rechazar_uc():
    return RechazarInvitacionUseCase(
        unit_of_work=BaseUnitOfWork(),
        event_dispatcher=EventDispatcher(),
        asignacion_repository=AsignacionRepository(),
    )


def _crear_lab_con_dos_secciones(instructor_id: uuid.UUID) -> Laboratorio:
    repo = LaboratorioRepository()
    lab = repo.add(
        Laboratorio(
            nombre="Lab Aceptar",
            descripcion="desc",
            nivel_dificultad=NivelDificultad.BASICO,
            estado=EstadoLaboratorio.PUBLICADO,
            tipo=TipoLaboratorio.PERSONALIZADO,
            instructor_id=instructor_id,
        )
    )
    repo.add_seccion(
        Seccion(laboratorio_id=lab.id, titulo="Uno", contenido_teorico="...", orden=1)
    )
    repo.add_seccion(
        Seccion(laboratorio_id=lab.id, titulo="Dos", contenido_teorico="...", orden=2)
    )
    return lab


def _crear_asignacion_pendiente(estudiante_id: uuid.UUID, laboratorio_id: uuid.UUID) -> Asignacion:
    return AsignacionRepository().add(
        Asignacion(estudiante_id=estudiante_id, laboratorio_id=laboratorio_id)
    )


@pytest.mark.django_db
def test_aceptar_invitacion_crea_progreso_con_primera_seccion_en_progreso():
    instructor_id = uuid.uuid4()
    estudiante_id = uuid.uuid4()
    lab = _crear_lab_con_dos_secciones(instructor_id)
    asignacion = _crear_asignacion_pendiente(estudiante_id, lab.id)

    resultado = _aceptar_uc().execute(
        AceptarInvitacionDTO(asignacion_id=asignacion.id, estudiante_id=estudiante_id)
    )

    assert resultado.estado == "activa"
    progreso_repo = ProgresoRepository()
    progreso = progreso_repo.get_by_asignacion(asignacion.id)
    assert progreso is not None
    assert progreso.estudiante_id == estudiante_id

    secciones = progreso_repo.get_secciones(progreso.id)
    assert len(secciones) == 2
    estados = {s.seccion_id: s.estado for s in secciones}
    laboratorio_secciones = LaboratorioRepository().get_secciones(lab.id)
    assert estados[laboratorio_secciones[0].id] == EstadoProgresoSeccion.EN_PROGRESO
    assert estados[laboratorio_secciones[1].id] == EstadoProgresoSeccion.BLOQUEADA


@pytest.mark.django_db
def test_aceptar_invitacion_ajena_lanza_not_found():
    instructor_id = uuid.uuid4()
    lab = _crear_lab_con_dos_secciones(instructor_id)
    asignacion = _crear_asignacion_pendiente(uuid.uuid4(), lab.id)

    with pytest.raises(NotFoundError):
        _aceptar_uc().execute(
            AceptarInvitacionDTO(asignacion_id=asignacion.id, estudiante_id=uuid.uuid4())
        )


@pytest.mark.django_db
def test_aceptar_invitacion_ya_respondida_lanza_business_rule():
    instructor_id = uuid.uuid4()
    estudiante_id = uuid.uuid4()
    lab = _crear_lab_con_dos_secciones(instructor_id)
    asignacion = _crear_asignacion_pendiente(estudiante_id, lab.id)
    _aceptar_uc().execute(
        AceptarInvitacionDTO(asignacion_id=asignacion.id, estudiante_id=estudiante_id)
    )

    with pytest.raises(BusinessRuleViolationError):
        _aceptar_uc().execute(
            AceptarInvitacionDTO(asignacion_id=asignacion.id, estudiante_id=estudiante_id)
        )


@pytest.mark.django_db
def test_rechazar_invitacion_exitoso():
    instructor_id = uuid.uuid4()
    estudiante_id = uuid.uuid4()
    lab = _crear_lab_con_dos_secciones(instructor_id)
    asignacion = _crear_asignacion_pendiente(estudiante_id, lab.id)

    resultado = _rechazar_uc().execute(
        RechazarInvitacionDTO(asignacion_id=asignacion.id, estudiante_id=estudiante_id)
    )

    assert resultado.estado == "rechazada"
    assert (
        AsignacionRepository().get_by_id(asignacion.id).estado == EstadoAsignacion.RECHAZADA
    )


@pytest.mark.django_db
def test_rechazar_invitacion_ajena_lanza_not_found():
    instructor_id = uuid.uuid4()
    lab = _crear_lab_con_dos_secciones(instructor_id)
    asignacion = _crear_asignacion_pendiente(uuid.uuid4(), lab.id)

    with pytest.raises(NotFoundError):
        _rechazar_uc().execute(
            RechazarInvitacionDTO(asignacion_id=asignacion.id, estudiante_id=uuid.uuid4())
        )
