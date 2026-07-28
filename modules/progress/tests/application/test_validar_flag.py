import uuid

import pytest
from django.contrib.auth.hashers import make_password

from modules.laboratories.domain.entities import Flag, Laboratorio, Seccion
from modules.laboratories.domain.value_objects import (
    AyudaProgresiva,
    EstadoLaboratorio,
    NivelDificultad,
    TipoLaboratorio,
)
from modules.laboratories.infrastructure.repositories import LaboratorioRepository
from modules.progress.application.dtos import ValidarFlagDTO
from modules.progress.application.use_cases.validar_flag import ValidarFlagUseCase
from modules.progress.domain.entities import Progreso, ProgresoSeccion
from modules.progress.domain.exceptions import SeccionBloqueadaError
from modules.progress.domain.value_objects import EstadoProgresoSeccion
from modules.progress.infrastructure.repositories import ProgresoRepository
from modules.shared.domain.exceptions import NotFoundError
from modules.shared.infrastructure.event_dispatcher import EventDispatcher
from modules.shared.infrastructure.unit_of_work import BaseUnitOfWork


def _crear_lab_con_secciones(n_secciones: int, valor_flag: str = "FLAG{correcta}"):
    lab_repo = LaboratorioRepository()
    lab = lab_repo.add(
        Laboratorio(
            nombre=f"Lab Progreso {uuid.uuid4()}",
            descripcion="desc",
            nivel_dificultad=NivelDificultad.BASICO,
            estado=EstadoLaboratorio.PUBLICADO,
            tipo=TipoLaboratorio.PREDETERMINADO,
        )
    )
    secciones = []
    for i in range(n_secciones):
        seccion = lab_repo.add_seccion(
            Seccion(
                laboratorio_id=lab.id,
                titulo=f"Seccion {i + 1}",
                contenido_teorico="contenido",
                orden=i + 1,
                tiene_practica=True,
            )
        )
        lab_repo.save_flag(
            Flag(
                seccion_id=seccion.id,
                hash=make_password(valor_flag),
                ayuda=AyudaProgresiva(pista="pista de prueba", paso_a_paso="paso a paso de prueba"),
            )
        )
        secciones.append(seccion)
    return lab, secciones


def _crear_progreso(secciones, estudiante_id=None):
    estudiante_id = estudiante_id or uuid.uuid4()
    progreso_repo = ProgresoRepository()
    progreso = progreso_repo.add(
        Progreso(asignacion_id=uuid.uuid4(), estudiante_id=estudiante_id)
    )
    progreso_secciones = [
        ProgresoSeccion(
            progreso_id=progreso.id,
            seccion_id=seccion.id,
            estado=(
                EstadoProgresoSeccion.EN_PROGRESO if i == 0 else EstadoProgresoSeccion.BLOQUEADA
            ),
        )
        for i, seccion in enumerate(secciones)
    ]
    progreso_repo.add_secciones(progreso_secciones)
    return progreso, estudiante_id


def _build_use_case():
    return ValidarFlagUseCase(
        unit_of_work=BaseUnitOfWork(),
        event_dispatcher=EventDispatcher(),
        progreso_repository=ProgresoRepository(),
        laboratorio_repository=LaboratorioRepository(),
    )


@pytest.mark.django_db
def test_validar_flag_correcta_completa_seccion_y_desbloquea_siguiente():
    _, secciones = _crear_lab_con_secciones(2, valor_flag="FLAG{correcta}")
    progreso, estudiante_id = _crear_progreso(secciones)

    resultado = _build_use_case().execute(
        ValidarFlagDTO(
            asignacion_id=progreso.asignacion_id,
            seccion_id=secciones[0].id,
            valor="FLAG{correcta}",
            estudiante_id=estudiante_id,
        )
    )

    assert resultado.correcto is True
    assert resultado.seccion_desbloqueada == secciones[1].id

    repo = ProgresoRepository()
    primera = repo.get_seccion(progreso.id, secciones[0].id)
    segunda = repo.get_seccion(progreso.id, secciones[1].id)
    assert primera.estado == EstadoProgresoSeccion.COMPLETADA
    assert segunda.estado == EstadoProgresoSeccion.EN_PROGRESO


@pytest.mark.django_db
def test_validar_flag_correcta_ultima_seccion_no_desbloquea_nada():
    _, secciones = _crear_lab_con_secciones(1, valor_flag="FLAG{unica}")
    progreso, estudiante_id = _crear_progreso(secciones)

    resultado = _build_use_case().execute(
        ValidarFlagDTO(
            asignacion_id=progreso.asignacion_id,
            seccion_id=secciones[0].id,
            valor="FLAG{unica}",
            estudiante_id=estudiante_id,
        )
    )

    assert resultado.correcto is True
    assert resultado.seccion_desbloqueada is None


@pytest.mark.django_db
def test_validar_flag_incorrecta_incrementa_fallos_sin_desbloquear():
    _, secciones = _crear_lab_con_secciones(2, valor_flag="FLAG{correcta}")
    progreso, estudiante_id = _crear_progreso(secciones)

    resultado = _build_use_case().execute(
        ValidarFlagDTO(
            asignacion_id=progreso.asignacion_id,
            seccion_id=secciones[0].id,
            valor="FLAG{incorrecta}",
            estudiante_id=estudiante_id,
        )
    )

    assert resultado.correcto is False
    assert resultado.intentos_fallidos == 1
    assert resultado.pista_disponible is False

    primera = ProgresoRepository().get_seccion(progreso.id, secciones[0].id)
    assert primera.estado == EstadoProgresoSeccion.EN_PROGRESO


@pytest.mark.django_db
def test_validar_flag_incorrecta_desbloquea_pista_al_quinto_intento():
    _, secciones = _crear_lab_con_secciones(1, valor_flag="FLAG{correcta}")
    progreso, estudiante_id = _crear_progreso(secciones)
    dto = ValidarFlagDTO(
        asignacion_id=progreso.asignacion_id,
        seccion_id=secciones[0].id,
        valor="FLAG{incorrecta}",
        estudiante_id=estudiante_id,
    )
    for _ in range(4):
        _build_use_case().execute(dto)

    resultado = _build_use_case().execute(dto)

    assert resultado.intentos_fallidos == 5
    assert resultado.pista_disponible is True
    assert resultado.pista is not None


@pytest.mark.django_db
def test_validar_flag_seccion_bloqueada_lanza_error():
    _, secciones = _crear_lab_con_secciones(2, valor_flag="FLAG{correcta}")
    progreso, estudiante_id = _crear_progreso(secciones)

    with pytest.raises(SeccionBloqueadaError):
        _build_use_case().execute(
            ValidarFlagDTO(
                asignacion_id=progreso.asignacion_id,
                seccion_id=secciones[1].id,
                valor="FLAG{correcta}",
                estudiante_id=estudiante_id,
            )
        )


@pytest.mark.django_db
def test_validar_flag_progreso_inexistente_lanza_not_found():
    with pytest.raises(NotFoundError):
        _build_use_case().execute(
            ValidarFlagDTO(
                asignacion_id=uuid.uuid4(),
                seccion_id=uuid.uuid4(),
                valor="FLAG{x}",
                estudiante_id=uuid.uuid4(),
            )
        )


@pytest.mark.django_db
def test_validar_flag_otro_estudiante_lanza_not_found():
    _, secciones = _crear_lab_con_secciones(1, valor_flag="FLAG{correcta}")
    progreso, _ = _crear_progreso(secciones)

    with pytest.raises(NotFoundError):
        _build_use_case().execute(
            ValidarFlagDTO(
                asignacion_id=progreso.asignacion_id,
                seccion_id=secciones[0].id,
                valor="FLAG{correcta}",
                estudiante_id=uuid.uuid4(),
            )
        )


@pytest.mark.django_db
def test_validar_flag_sin_flag_definida_lanza_not_found():
    lab_repo = LaboratorioRepository()
    lab = lab_repo.add(
        Laboratorio(
            nombre=f"Lab Sin Flag {uuid.uuid4()}",
            descripcion="desc",
            nivel_dificultad=NivelDificultad.BASICO,
            estado=EstadoLaboratorio.PUBLICADO,
            tipo=TipoLaboratorio.PREDETERMINADO,
        )
    )
    seccion = lab_repo.add_seccion(
        Seccion(
            laboratorio_id=lab.id,
            titulo="Practica sin flag",
            contenido_teorico="...",
            orden=1,
            tiene_practica=True,
        )
    )
    progreso, estudiante_id = _crear_progreso([seccion])

    with pytest.raises(NotFoundError):
        _build_use_case().execute(
            ValidarFlagDTO(
                asignacion_id=progreso.asignacion_id,
                seccion_id=seccion.id,
                valor="FLAG{x}",
                estudiante_id=estudiante_id,
            )
        )
