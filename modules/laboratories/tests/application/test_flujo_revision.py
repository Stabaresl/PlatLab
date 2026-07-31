import uuid

import pytest
from django.contrib.auth.hashers import make_password

from modules.laboratories.application.dtos import (
    AprobarLaboratorioDTO,
    RechazarLaboratorioDTO,
    SolicitarRevisionLaboratorioDTO,
)
from modules.laboratories.application.use_cases.aprobar_laboratorio import (
    AprobarLaboratorioUseCase,
)
from modules.laboratories.application.use_cases.rechazar_laboratorio import (
    RechazarLaboratorioUseCase,
)
from modules.laboratories.application.use_cases.solicitar_revision_laboratorio import (
    SolicitarRevisionLaboratorioUseCase,
)
from modules.laboratories.domain.entities import Flag, Laboratorio, Seccion
from modules.laboratories.domain.exceptions import PublishValidationError
from modules.laboratories.domain.value_objects import (
    EstadoLaboratorio,
    NivelDificultad,
    TipoLaboratorio,
)
from modules.laboratories.infrastructure.repositories import LaboratorioRepository
from modules.shared.domain.exceptions import ConflictError, ForbiddenError, ValidationError
from modules.shared.infrastructure.event_dispatcher import EventDispatcher
from modules.shared.infrastructure.unit_of_work import BaseUnitOfWork


def _repo():
    return LaboratorioRepository()


def _solicitar_uc():
    return SolicitarRevisionLaboratorioUseCase(
        unit_of_work=BaseUnitOfWork(), event_dispatcher=EventDispatcher(), laboratorio_repository=_repo()
    )


def _aprobar_uc():
    return AprobarLaboratorioUseCase(
        unit_of_work=BaseUnitOfWork(), event_dispatcher=EventDispatcher(), laboratorio_repository=_repo()
    )


def _rechazar_uc():
    return RechazarLaboratorioUseCase(
        unit_of_work=BaseUnitOfWork(), event_dispatcher=EventDispatcher(), laboratorio_repository=_repo()
    )


def _crear_lab_personalizado_con_flag(instructor_id: uuid.UUID) -> Laboratorio:
    lab = _repo().add(
        Laboratorio(
            nombre="Lab Revision",
            descripcion="desc",
            nivel_dificultad=NivelDificultad.BASICO,
            estado=EstadoLaboratorio.BORRADOR,
            tipo=TipoLaboratorio.PERSONALIZADO,
            instructor_id=instructor_id,
        )
    )
    seccion = _repo().add_seccion(
        Seccion(laboratorio_id=lab.id, titulo="Practica", contenido_teorico="...", orden=1, tiene_practica=True)
    )
    _repo().save_flag(Flag(seccion_id=seccion.id, hash=make_password("FLAG{x}")))
    return lab


@pytest.mark.django_db
def test_solicitar_revision_exitoso_pasa_a_en_revision():
    instructor_id = uuid.uuid4()
    lab = _crear_lab_personalizado_con_flag(instructor_id)

    resultado = _solicitar_uc().execute(
        SolicitarRevisionLaboratorioDTO(
            laboratorio_id=lab.id, actor_id=instructor_id, actor_rol="instructor"
        )
    )

    assert resultado.estado == "en_revision"


@pytest.mark.django_db
def test_solicitar_revision_sin_flags_lanza_publish_validation_error():
    instructor_id = uuid.uuid4()
    lab = _repo().add(
        Laboratorio(
            nombre="Lab Sin Flag",
            descripcion="desc",
            nivel_dificultad=NivelDificultad.BASICO,
            estado=EstadoLaboratorio.BORRADOR,
            tipo=TipoLaboratorio.PERSONALIZADO,
            instructor_id=instructor_id,
        )
    )
    _repo().add_seccion(
        Seccion(laboratorio_id=lab.id, titulo="Practica", contenido_teorico="...", orden=1, tiene_practica=True)
    )

    with pytest.raises(PublishValidationError):
        _solicitar_uc().execute(
            SolicitarRevisionLaboratorioDTO(
                laboratorio_id=lab.id, actor_id=instructor_id, actor_rol="instructor"
            )
        )


@pytest.mark.django_db
def test_solicitar_revision_instructor_ajeno_lanza_forbidden():
    lab = _crear_lab_personalizado_con_flag(uuid.uuid4())

    with pytest.raises(ForbiddenError):
        _solicitar_uc().execute(
            SolicitarRevisionLaboratorioDTO(
                laboratorio_id=lab.id, actor_id=uuid.uuid4(), actor_rol="instructor"
            )
        )


@pytest.mark.django_db
def test_solicitar_revision_ya_en_revision_lanza_conflict():
    instructor_id = uuid.uuid4()
    lab = _crear_lab_personalizado_con_flag(instructor_id)
    dto = SolicitarRevisionLaboratorioDTO(
        laboratorio_id=lab.id, actor_id=instructor_id, actor_rol="instructor"
    )
    _solicitar_uc().execute(dto)

    with pytest.raises(ConflictError):
        _solicitar_uc().execute(dto)


@pytest.mark.django_db
def test_aprobar_exitoso_publica_y_no_admin_forbidden():
    instructor_id = uuid.uuid4()
    lab = _crear_lab_personalizado_con_flag(instructor_id)
    _solicitar_uc().execute(
        SolicitarRevisionLaboratorioDTO(
            laboratorio_id=lab.id, actor_id=instructor_id, actor_rol="instructor"
        )
    )

    with pytest.raises(ForbiddenError):
        _aprobar_uc().execute(
            AprobarLaboratorioDTO(laboratorio_id=lab.id, actor_id=instructor_id, actor_rol="instructor")
        )

    resultado = _aprobar_uc().execute(
        AprobarLaboratorioDTO(laboratorio_id=lab.id, actor_id=uuid.uuid4(), actor_rol="administrador")
    )
    assert resultado.estado == "publicado"


@pytest.mark.django_db
def test_aprobar_lab_en_borrador_lanza_conflict():
    instructor_id = uuid.uuid4()
    lab = _crear_lab_personalizado_con_flag(instructor_id)

    with pytest.raises(ConflictError):
        _aprobar_uc().execute(
            AprobarLaboratorioDTO(laboratorio_id=lab.id, actor_id=uuid.uuid4(), actor_rol="administrador")
        )


@pytest.mark.django_db
def test_rechazar_exitoso_vuelve_a_borrador_con_motivo():
    instructor_id = uuid.uuid4()
    lab = _crear_lab_personalizado_con_flag(instructor_id)
    _solicitar_uc().execute(
        SolicitarRevisionLaboratorioDTO(
            laboratorio_id=lab.id, actor_id=instructor_id, actor_rol="instructor"
        )
    )

    resultado = _rechazar_uc().execute(
        RechazarLaboratorioDTO(
            laboratorio_id=lab.id,
            motivo="Falta más contenido teórico",
            actor_id=uuid.uuid4(),
            actor_rol="administrador",
        )
    )

    assert resultado.estado == "borrador"
    guardado = _repo().get_by_id(lab.id)
    assert guardado.motivo_rechazo == "Falta más contenido teórico"


@pytest.mark.django_db
def test_rechazar_sin_motivo_lanza_validation_error():
    instructor_id = uuid.uuid4()
    lab = _crear_lab_personalizado_con_flag(instructor_id)
    _solicitar_uc().execute(
        SolicitarRevisionLaboratorioDTO(
            laboratorio_id=lab.id, actor_id=instructor_id, actor_rol="instructor"
        )
    )

    with pytest.raises(ValidationError):
        _rechazar_uc().execute(
            RechazarLaboratorioDTO(
                laboratorio_id=lab.id, motivo="   ", actor_id=uuid.uuid4(), actor_rol="administrador"
            )
        )


@pytest.mark.django_db
def test_reenviar_a_revision_limpia_motivo_rechazo():
    instructor_id = uuid.uuid4()
    lab = _crear_lab_personalizado_con_flag(instructor_id)
    _solicitar_uc().execute(
        SolicitarRevisionLaboratorioDTO(
            laboratorio_id=lab.id, actor_id=instructor_id, actor_rol="instructor"
        )
    )
    _rechazar_uc().execute(
        RechazarLaboratorioDTO(
            laboratorio_id=lab.id, motivo="Corregir esto", actor_id=uuid.uuid4(), actor_rol="administrador"
        )
    )

    _solicitar_uc().execute(
        SolicitarRevisionLaboratorioDTO(
            laboratorio_id=lab.id, actor_id=instructor_id, actor_rol="instructor"
        )
    )

    guardado = _repo().get_by_id(lab.id)
    assert guardado.motivo_rechazo is None
