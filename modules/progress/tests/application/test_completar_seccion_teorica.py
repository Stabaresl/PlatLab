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
from modules.progress.application.dtos import CompletarSeccionTeoricaDTO
from modules.progress.application.use_cases.completar_seccion_teorica import (
    CompletarSeccionTeoricaUseCase,
)
from modules.progress.domain.entities import Progreso, ProgresoSeccion
from modules.progress.domain.exceptions import SeccionBloqueadaError, SeccionRequierePracticaError
from modules.progress.domain.value_objects import EstadoProgresoSeccion
from modules.progress.infrastructure.repositories import ProgresoRepository
from modules.shared.domain.exceptions import NotFoundError
from modules.shared.infrastructure.event_dispatcher import EventDispatcher
from modules.shared.infrastructure.unit_of_work import BaseUnitOfWork


def _crear_lab(secciones_spec: list[bool]) -> tuple[Laboratorio, list[Seccion]]:
    """`secciones_spec`: una entrada por sección, True si tiene práctica (con flag)."""
    lab_repo = LaboratorioRepository()
    lab = lab_repo.add(
        Laboratorio(
            nombre=f"Lab Teorico {uuid.uuid4()}",
            descripcion="desc",
            nivel_dificultad=NivelDificultad.BASICO,
            estado=EstadoLaboratorio.PUBLICADO,
            tipo=TipoLaboratorio.PREDETERMINADO,
        )
    )
    secciones = []
    for i, tiene_practica in enumerate(secciones_spec):
        seccion = lab_repo.add_seccion(
            Seccion(
                laboratorio_id=lab.id,
                titulo=f"Seccion {i + 1}",
                contenido_teorico="contenido",
                orden=i + 1,
                tiene_practica=tiene_practica,
            )
        )
        if tiene_practica:
            lab_repo.save_flag(
                Flag(
                    seccion_id=seccion.id,
                    hash=make_password("FLAG{x}"),
                    ayuda=AyudaProgresiva(pista="pista", paso_a_paso="paso a paso"),
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
    return CompletarSeccionTeoricaUseCase(
        unit_of_work=BaseUnitOfWork(),
        event_dispatcher=EventDispatcher(),
        progreso_repository=ProgresoRepository(),
        laboratorio_repository=LaboratorioRepository(),
    )


@pytest.mark.django_db
def test_completar_seccion_teorica_desbloquea_siguiente():
    _, secciones = _crear_lab([False, True])
    progreso, estudiante_id = _crear_progreso(secciones)

    resultado = _build_use_case().execute(
        CompletarSeccionTeoricaDTO(
            asignacion_id=progreso.asignacion_id,
            seccion_id=secciones[0].id,
            estudiante_id=estudiante_id,
        )
    )

    assert resultado.seccion_desbloqueada == secciones[1].id

    repo = ProgresoRepository()
    primera = repo.get_seccion(progreso.id, secciones[0].id)
    segunda = repo.get_seccion(progreso.id, secciones[1].id)
    assert primera.estado == EstadoProgresoSeccion.COMPLETADA
    assert segunda.estado == EstadoProgresoSeccion.EN_PROGRESO


@pytest.mark.django_db
def test_completar_seccion_teorica_ultima_seccion_sin_examen_registra_historial():
    _, secciones = _crear_lab([False])
    progreso, estudiante_id = _crear_progreso(secciones)

    resultado = _build_use_case().execute(
        CompletarSeccionTeoricaDTO(
            asignacion_id=progreso.asignacion_id,
            seccion_id=secciones[0].id,
            estudiante_id=estudiante_id,
        )
    )

    assert resultado.seccion_desbloqueada is None
    historial = ProgresoRepository().get_historial(progreso.id)
    assert len(historial) == 1


@pytest.mark.django_db
def test_completar_seccion_teorica_es_idempotente():
    _, secciones = _crear_lab([False, True])
    progreso, estudiante_id = _crear_progreso(secciones)
    dto = CompletarSeccionTeoricaDTO(
        asignacion_id=progreso.asignacion_id,
        seccion_id=secciones[0].id,
        estudiante_id=estudiante_id,
    )

    primero = _build_use_case().execute(dto)
    segundo = _build_use_case().execute(dto)

    assert primero.seccion_desbloqueada == secciones[1].id
    assert segundo.seccion_desbloqueada is None
    segunda = ProgresoRepository().get_seccion(progreso.id, secciones[1].id)
    assert segunda.estado == EstadoProgresoSeccion.EN_PROGRESO


@pytest.mark.django_db
def test_completar_seccion_con_practica_lanza_error():
    _, secciones = _crear_lab([True])
    progreso, estudiante_id = _crear_progreso(secciones)

    with pytest.raises(SeccionRequierePracticaError):
        _build_use_case().execute(
            CompletarSeccionTeoricaDTO(
                asignacion_id=progreso.asignacion_id,
                seccion_id=secciones[0].id,
                estudiante_id=estudiante_id,
            )
        )


@pytest.mark.django_db
def test_completar_seccion_bloqueada_lanza_error():
    _, secciones = _crear_lab([False, False])
    progreso, estudiante_id = _crear_progreso(secciones)

    with pytest.raises(SeccionBloqueadaError):
        _build_use_case().execute(
            CompletarSeccionTeoricaDTO(
                asignacion_id=progreso.asignacion_id,
                seccion_id=secciones[1].id,
                estudiante_id=estudiante_id,
            )
        )


@pytest.mark.django_db
def test_completar_seccion_progreso_inexistente_lanza_not_found():
    with pytest.raises(NotFoundError):
        _build_use_case().execute(
            CompletarSeccionTeoricaDTO(
                asignacion_id=uuid.uuid4(),
                seccion_id=uuid.uuid4(),
                estudiante_id=uuid.uuid4(),
            )
        )


@pytest.mark.django_db
def test_completar_seccion_otro_estudiante_lanza_not_found():
    _, secciones = _crear_lab([False])
    progreso, _ = _crear_progreso(secciones)

    with pytest.raises(NotFoundError):
        _build_use_case().execute(
            CompletarSeccionTeoricaDTO(
                asignacion_id=progreso.asignacion_id,
                seccion_id=secciones[0].id,
                estudiante_id=uuid.uuid4(),
            )
        )
