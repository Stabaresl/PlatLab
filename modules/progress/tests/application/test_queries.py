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
from modules.progress.application.dtos import (
    ObtenerContenidoSeccionDTO,
    ObtenerHistorialDTO,
    ObtenerPistaDTO,
)
from modules.progress.application.queries.obtener_contenido_seccion import (
    ObtenerContenidoSeccionQuery,
)
from modules.progress.application.queries.obtener_historial import ObtenerHistorialQuery
from modules.progress.application.queries.obtener_pista import ObtenerPistaQuery
from modules.progress.domain.entities import (
    HistorialCompletitud,
    IntentoFlag,
    Progreso,
    ProgresoSeccion,
)
from modules.progress.domain.exceptions import SeccionBloqueadaError
from modules.progress.domain.value_objects import EstadoProgresoSeccion
from modules.progress.infrastructure.repositories import ProgresoRepository
from modules.shared.domain.exceptions import NotFoundError


def _crear_lab_con_seccion(tiene_practica=True, con_flag=True):
    lab_repo = LaboratorioRepository()
    lab = lab_repo.add(
        Laboratorio(
            nombre=f"Lab Query {uuid.uuid4()}",
            descripcion="desc",
            nivel_dificultad=NivelDificultad.BASICO,
            estado=EstadoLaboratorio.PUBLICADO,
            tipo=TipoLaboratorio.PREDETERMINADO,
        )
    )
    seccion = lab_repo.add_seccion(
        Seccion(
            laboratorio_id=lab.id,
            titulo="Seccion Query",
            contenido_teorico="contenido secreto",
            orden=1,
            tiene_practica=tiene_practica,
        )
    )
    if con_flag:
        lab_repo.save_flag(Flag(seccion_id=seccion.id, hash=make_password("FLAG{x}")))
    return lab, seccion


def _crear_progreso(seccion, estado=EstadoProgresoSeccion.EN_PROGRESO, estudiante_id=None):
    estudiante_id = estudiante_id or uuid.uuid4()
    progreso_repo = ProgresoRepository()
    progreso = progreso_repo.add(
        Progreso(asignacion_id=uuid.uuid4(), estudiante_id=estudiante_id)
    )
    progreso_repo.add_secciones(
        [ProgresoSeccion(progreso_id=progreso.id, seccion_id=seccion.id, estado=estado)]
    )
    return progreso, estudiante_id


@pytest.mark.django_db
def test_obtener_contenido_seccion_en_progreso_devuelve_contenido():
    _, seccion = _crear_lab_con_seccion()
    progreso, estudiante_id = _crear_progreso(seccion, EstadoProgresoSeccion.EN_PROGRESO)

    resultado = ObtenerContenidoSeccionQuery(
        ProgresoRepository(), LaboratorioRepository()
    ).execute(
        ObtenerContenidoSeccionDTO(
            asignacion_id=progreso.asignacion_id,
            seccion_id=seccion.id,
            estudiante_id=estudiante_id,
        )
    )

    assert resultado.contenido_teorico == "contenido secreto"
    assert resultado.estado == "en_progreso"


@pytest.mark.django_db
def test_obtener_contenido_seccion_bloqueada_lanza_error():
    _, seccion = _crear_lab_con_seccion()
    progreso, estudiante_id = _crear_progreso(seccion, EstadoProgresoSeccion.BLOQUEADA)

    with pytest.raises(SeccionBloqueadaError):
        ObtenerContenidoSeccionQuery(ProgresoRepository(), LaboratorioRepository()).execute(
            ObtenerContenidoSeccionDTO(
                asignacion_id=progreso.asignacion_id,
                seccion_id=seccion.id,
                estudiante_id=estudiante_id,
            )
        )


@pytest.mark.django_db
def test_obtener_contenido_seccion_otro_estudiante_lanza_not_found():
    _, seccion = _crear_lab_con_seccion()
    progreso, _ = _crear_progreso(seccion)

    with pytest.raises(NotFoundError):
        ObtenerContenidoSeccionQuery(ProgresoRepository(), LaboratorioRepository()).execute(
            ObtenerContenidoSeccionDTO(
                asignacion_id=progreso.asignacion_id,
                seccion_id=seccion.id,
                estudiante_id=uuid.uuid4(),
            )
        )


@pytest.mark.django_db
def test_obtener_pista_sin_fallos_no_muestra_ayuda():
    _, seccion = _crear_lab_con_seccion()
    progreso, estudiante_id = _crear_progreso(seccion)

    resultado = ObtenerPistaQuery(ProgresoRepository(), LaboratorioRepository()).execute(
        ObtenerPistaDTO(
            asignacion_id=progreso.asignacion_id,
            seccion_id=seccion.id,
            estudiante_id=estudiante_id,
        )
    )

    assert resultado.intentos_fallidos == 0
    assert resultado.pista_disponible is False
    assert resultado.pista is None


@pytest.mark.django_db
def test_obtener_pista_con_5_fallos_muestra_pista():
    lab_repo = LaboratorioRepository()
    _, seccion = _crear_lab_con_seccion(con_flag=False)
    lab_repo.save_flag(
        Flag(
            seccion_id=seccion.id,
            hash=make_password("FLAG{x}"),
            ayuda=AyudaProgresiva(pista="pista secreta", paso_a_paso=None),
        )
    )
    progreso, estudiante_id = _crear_progreso(seccion)
    progreso_repo = ProgresoRepository()
    for _ in range(5):
        progreso_repo.registrar_intento(
            IntentoFlag(progreso_id=progreso.id, seccion_id=seccion.id, resultado=False)
        )

    resultado = ObtenerPistaQuery(progreso_repo, lab_repo).execute(
        ObtenerPistaDTO(
            asignacion_id=progreso.asignacion_id,
            seccion_id=seccion.id,
            estudiante_id=estudiante_id,
        )
    )

    assert resultado.intentos_fallidos == 5
    assert resultado.pista_disponible is True
    assert resultado.pista == "pista secreta"


@pytest.mark.django_db
def test_obtener_historial_vacio_por_defecto():
    _, seccion = _crear_lab_con_seccion()
    progreso, estudiante_id = _crear_progreso(seccion)

    resultado = ObtenerHistorialQuery(ProgresoRepository()).execute(
        ObtenerHistorialDTO(asignacion_id=progreso.asignacion_id, estudiante_id=estudiante_id)
    )

    assert resultado == []


@pytest.mark.django_db
def test_obtener_historial_devuelve_completitudes_ordenadas():
    _, seccion = _crear_lab_con_seccion()
    progreso, estudiante_id = _crear_progreso(seccion)
    progreso_repo = ProgresoRepository()
    progreso_repo.registrar_historial(
        HistorialCompletitud(progreso_id=progreso.id, numero_intento=1, puntaje=90.0)
    )
    progreso_repo.registrar_historial(
        HistorialCompletitud(progreso_id=progreso.id, numero_intento=2, puntaje=100.0)
    )

    resultado = ObtenerHistorialQuery(progreso_repo).execute(
        ObtenerHistorialDTO(asignacion_id=progreso.asignacion_id, estudiante_id=estudiante_id)
    )

    assert [item.numero_intento for item in resultado] == [1, 2]
    assert resultado[1].puntaje == 100.0
