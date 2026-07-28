import uuid

import pytest
from django.contrib.auth.hashers import check_password

from modules.laboratories.application.dtos import DefinirFlagDTO
from modules.laboratories.application.use_cases.definir_flag import DefinirFlagUseCase
from modules.laboratories.domain.entities import Laboratorio, Seccion
from modules.laboratories.domain.value_objects import (
    EstadoLaboratorio,
    NivelDificultad,
    TipoLaboratorio,
)
from modules.laboratories.infrastructure.repositories import LaboratorioRepository
from modules.shared.domain.exceptions import (
    BusinessRuleViolationError,
    ForbiddenError,
    NotFoundError,
)
from modules.shared.infrastructure.event_dispatcher import EventDispatcher
from modules.shared.infrastructure.unit_of_work import BaseUnitOfWork


def _build_use_case():
    return DefinirFlagUseCase(
        unit_of_work=BaseUnitOfWork(),
        event_dispatcher=EventDispatcher(),
        laboratorio_repository=LaboratorioRepository(),
    )


def _crear_lab_con_seccion_practica(instructor_id: uuid.UUID) -> tuple[Laboratorio, Seccion]:
    repo = LaboratorioRepository()
    lab = repo.add(
        Laboratorio(
            nombre="Lab Flag",
            descripcion="desc",
            nivel_dificultad=NivelDificultad.BASICO,
            estado=EstadoLaboratorio.BORRADOR,
            tipo=TipoLaboratorio.PERSONALIZADO,
            instructor_id=instructor_id,
        )
    )
    seccion = repo.add_seccion(
        Seccion(
            laboratorio_id=lab.id,
            titulo="Practica 1",
            contenido_teorico="...",
            orden=1,
            tiene_practica=True,
        )
    )
    return lab, seccion


@pytest.mark.django_db
def test_definir_flag_exitoso_persiste_hash_no_valor_en_claro():
    instructor_id = uuid.uuid4()
    lab, seccion = _crear_lab_con_seccion_practica(instructor_id)

    resultado = _build_use_case().execute(
        DefinirFlagDTO(
            laboratorio_id=lab.id,
            seccion_id=seccion.id,
            valor="FLAG{secreta}",
            actor_id=instructor_id,
            actor_rol="instructor",
            pista="pista 1",
            paso_a_paso="paso a paso 1",
        )
    )

    assert resultado.seccion_id == seccion.id
    flag = LaboratorioRepository().get_flag_by_seccion(seccion.id)
    assert flag is not None
    assert flag.hash != "FLAG{secreta}"
    assert check_password("FLAG{secreta}", flag.hash)
    assert flag.ayuda.pista == "pista 1"
    assert flag.ayuda.paso_a_paso == "paso a paso 1"


@pytest.mark.django_db
def test_definir_flag_actualiza_si_ya_existia():
    instructor_id = uuid.uuid4()
    lab, seccion = _crear_lab_con_seccion_practica(instructor_id)
    dto_base = dict(
        laboratorio_id=lab.id,
        seccion_id=seccion.id,
        actor_id=instructor_id,
        actor_rol="instructor",
    )
    _build_use_case().execute(DefinirFlagDTO(valor="FLAG{primera}", **dto_base))

    _build_use_case().execute(DefinirFlagDTO(valor="FLAG{segunda}", **dto_base))

    flag = LaboratorioRepository().get_flag_by_seccion(seccion.id)
    assert check_password("FLAG{segunda}", flag.hash)
    assert not check_password("FLAG{primera}", flag.hash)


@pytest.mark.django_db
def test_definir_flag_instructor_ajeno_lanza_forbidden():
    lab, seccion = _crear_lab_con_seccion_practica(uuid.uuid4())

    with pytest.raises(ForbiddenError):
        _build_use_case().execute(
            DefinirFlagDTO(
                laboratorio_id=lab.id,
                seccion_id=seccion.id,
                valor="FLAG{x}",
                actor_id=uuid.uuid4(),
                actor_rol="instructor",
            )
        )


@pytest.mark.django_db
def test_definir_flag_rol_estudiante_lanza_forbidden():
    lab, seccion = _crear_lab_con_seccion_practica(uuid.uuid4())

    with pytest.raises(ForbiddenError):
        _build_use_case().execute(
            DefinirFlagDTO(
                laboratorio_id=lab.id,
                seccion_id=seccion.id,
                valor="FLAG{x}",
                actor_id=uuid.uuid4(),
                actor_rol="estudiante",
            )
        )


@pytest.mark.django_db
def test_definir_flag_administrador_puede_editar_laboratorio_ajeno():
    lab, seccion = _crear_lab_con_seccion_practica(uuid.uuid4())

    resultado = _build_use_case().execute(
        DefinirFlagDTO(
            laboratorio_id=lab.id,
            seccion_id=seccion.id,
            valor="FLAG{admin}",
            actor_id=uuid.uuid4(),
            actor_rol="administrador",
        )
    )

    assert resultado.seccion_id == seccion.id


@pytest.mark.django_db
def test_definir_flag_laboratorio_inexistente_lanza_not_found():
    with pytest.raises(NotFoundError):
        _build_use_case().execute(
            DefinirFlagDTO(
                laboratorio_id=uuid.uuid4(),
                seccion_id=uuid.uuid4(),
                valor="FLAG{x}",
                actor_id=uuid.uuid4(),
                actor_rol="instructor",
            )
        )


@pytest.mark.django_db
def test_definir_flag_seccion_inexistente_lanza_not_found():
    instructor_id = uuid.uuid4()
    lab, _ = _crear_lab_con_seccion_practica(instructor_id)

    with pytest.raises(NotFoundError):
        _build_use_case().execute(
            DefinirFlagDTO(
                laboratorio_id=lab.id,
                seccion_id=uuid.uuid4(),
                valor="FLAG{x}",
                actor_id=instructor_id,
                actor_rol="instructor",
            )
        )


@pytest.mark.django_db
def test_definir_flag_seccion_sin_practica_lanza_business_rule():
    instructor_id = uuid.uuid4()
    repo = LaboratorioRepository()
    lab = repo.add(
        Laboratorio(
            nombre="Lab Sin Practica",
            descripcion="desc",
            nivel_dificultad=NivelDificultad.BASICO,
            estado=EstadoLaboratorio.BORRADOR,
            tipo=TipoLaboratorio.PERSONALIZADO,
            instructor_id=instructor_id,
        )
    )
    seccion = repo.add_seccion(
        Seccion(
            laboratorio_id=lab.id,
            titulo="Solo teoria",
            contenido_teorico="...",
            orden=1,
            tiene_practica=False,
        )
    )

    with pytest.raises(BusinessRuleViolationError):
        _build_use_case().execute(
            DefinirFlagDTO(
                laboratorio_id=lab.id,
                seccion_id=seccion.id,
                valor="FLAG{x}",
                actor_id=instructor_id,
                actor_rol="instructor",
            )
        )
