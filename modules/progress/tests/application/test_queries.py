import uuid

import pytest
from django.contrib.auth.hashers import make_password

from modules.laboratories.domain.entities import Examen, Flag, Laboratorio, Pregunta, Seccion
from modules.laboratories.domain.value_objects import (
    AyudaProgresiva,
    EstadoLaboratorio,
    NivelDificultad,
    PasoGuia,
    TipoLaboratorio,
    TipoPregunta,
)
from modules.laboratories.infrastructure.repositories import LaboratorioRepository
from modules.progress.application.dtos import (
    ObtenerContenidoSeccionDTO,
    ObtenerExamenDTO,
    ObtenerHistorialDTO,
    ObtenerPistaDTO,
    ObtenerProgresoDTO,
)
from modules.progress.application.queries.obtener_contenido_seccion import (
    ObtenerContenidoSeccionQuery,
)
from modules.progress.application.queries.obtener_examen import ObtenerExamenQuery
from modules.progress.application.queries.obtener_historial import ObtenerHistorialQuery
from modules.progress.application.queries.obtener_pista import ObtenerPistaQuery
from modules.progress.application.queries.obtener_progreso import ObtenerProgresoQuery
from modules.progress.domain.entities import (
    HistorialCompletitud,
    IntentoFlag,
    Progreso,
    ProgresoSeccion,
)
from modules.progress.domain.exceptions import SeccionBloqueadaError
from modules.progress.domain.value_objects import EstadoProgresoSeccion
from modules.progress.infrastructure.repositories import ProgresoRepository
from modules.shared.domain.exceptions import BusinessRuleViolationError, NotFoundError


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
            objetivos=["Objetivo de prueba"],
            duracion_estimada_minutos=12,
            pasos_guia=[PasoGuia(orden=1, titulo="Paso", instrucciones="<p>hacé esto</p>")],
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
    assert resultado.objetivos == ["Objetivo de prueba"]
    assert resultado.duracion_estimada_minutos == 12
    assert resultado.pasos_guia == [
        {"orden": 1, "titulo": "Paso", "instrucciones": "<p>hacé esto</p>", "comando_sugerido": None}
    ]


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


def _crear_lab_con_dos_secciones():
    lab_repo = LaboratorioRepository()
    lab = lab_repo.add(
        Laboratorio(
            nombre=f"Lab Progreso {uuid.uuid4()}",
            descripcion="desc",
            nivel_dificultad=NivelDificultad.BASICO,
            estado=EstadoLaboratorio.PUBLICADO,
            tipo=TipoLaboratorio.PREDETERMINADO,
            resumen_cierre="<p>Buen trabajo</p>",
        )
    )
    s1 = lab_repo.add_seccion(
        Seccion(laboratorio_id=lab.id, titulo="Uno", contenido_teorico="...", orden=1)
    )
    s2 = lab_repo.add_seccion(
        Seccion(
            laboratorio_id=lab.id,
            titulo="Dos",
            contenido_teorico="...",
            orden=2,
            tiene_practica=True,
        )
    )
    return lab, s1, s2


@pytest.mark.django_db
def test_obtener_progreso_devuelve_secciones_en_orden_con_estado():
    lab, s1, s2 = _crear_lab_con_dos_secciones()
    estudiante_id = uuid.uuid4()
    progreso_repo = ProgresoRepository()
    progreso = progreso_repo.add(
        Progreso(asignacion_id=uuid.uuid4(), estudiante_id=estudiante_id)
    )
    progreso_repo.add_secciones(
        [
            ProgresoSeccion(
                progreso_id=progreso.id,
                seccion_id=s1.id,
                estado=EstadoProgresoSeccion.EN_PROGRESO,
            ),
            ProgresoSeccion(
                progreso_id=progreso.id,
                seccion_id=s2.id,
                estado=EstadoProgresoSeccion.BLOQUEADA,
            ),
        ]
    )

    resultado = ObtenerProgresoQuery(progreso_repo, LaboratorioRepository()).execute(
        ObtenerProgresoDTO(asignacion_id=progreso.asignacion_id, estudiante_id=estudiante_id)
    )

    assert resultado.laboratorio_id == lab.id
    assert [s.titulo for s in resultado.secciones] == ["Uno", "Dos"]
    assert resultado.secciones[0].estado == "en_progreso"
    assert resultado.secciones[1].estado == "bloqueada"
    assert resultado.secciones_completas is False
    assert resultado.resumen_cierre == "<p>Buen trabajo</p>"
    assert resultado.examen_disponible is False


@pytest.mark.django_db
def test_obtener_progreso_secciones_completas_cuando_todas_completadas():
    _, s1, s2 = _crear_lab_con_dos_secciones()
    estudiante_id = uuid.uuid4()
    progreso_repo = ProgresoRepository()
    progreso = progreso_repo.add(
        Progreso(asignacion_id=uuid.uuid4(), estudiante_id=estudiante_id)
    )
    progreso_repo.add_secciones(
        [
            ProgresoSeccion(
                progreso_id=progreso.id,
                seccion_id=s1.id,
                estado=EstadoProgresoSeccion.COMPLETADA,
            ),
            ProgresoSeccion(
                progreso_id=progreso.id,
                seccion_id=s2.id,
                estado=EstadoProgresoSeccion.COMPLETADA,
            ),
        ]
    )

    resultado = ObtenerProgresoQuery(progreso_repo, LaboratorioRepository()).execute(
        ObtenerProgresoDTO(asignacion_id=progreso.asignacion_id, estudiante_id=estudiante_id)
    )

    assert resultado.secciones_completas is True


@pytest.mark.django_db
def test_obtener_progreso_ajeno_lanza_not_found():
    _, s1, _ = _crear_lab_con_dos_secciones()
    progreso_repo = ProgresoRepository()
    progreso = progreso_repo.add(
        Progreso(asignacion_id=uuid.uuid4(), estudiante_id=uuid.uuid4())
    )
    progreso_repo.add_secciones(
        [
            ProgresoSeccion(
                progreso_id=progreso.id,
                seccion_id=s1.id,
                estado=EstadoProgresoSeccion.EN_PROGRESO,
            )
        ]
    )

    with pytest.raises(NotFoundError):
        ObtenerProgresoQuery(progreso_repo, LaboratorioRepository()).execute(
            ObtenerProgresoDTO(asignacion_id=progreso.asignacion_id, estudiante_id=uuid.uuid4())
        )


@pytest.mark.django_db
def test_obtener_examen_con_secciones_incompletas_lanza_business_rule():
    _, s1, s2 = _crear_lab_con_dos_secciones()
    estudiante_id = uuid.uuid4()
    progreso_repo = ProgresoRepository()
    progreso = progreso_repo.add(
        Progreso(asignacion_id=uuid.uuid4(), estudiante_id=estudiante_id)
    )
    progreso_repo.add_secciones(
        [
            ProgresoSeccion(
                progreso_id=progreso.id,
                seccion_id=s1.id,
                estado=EstadoProgresoSeccion.COMPLETADA,
            ),
            ProgresoSeccion(
                progreso_id=progreso.id,
                seccion_id=s2.id,
                estado=EstadoProgresoSeccion.EN_PROGRESO,
            ),
        ]
    )

    with pytest.raises(BusinessRuleViolationError):
        ObtenerExamenQuery(progreso_repo, LaboratorioRepository()).execute(
            ObtenerExamenDTO(asignacion_id=progreso.asignacion_id, estudiante_id=estudiante_id)
        )


@pytest.mark.django_db
def test_obtener_examen_devuelve_preguntas_sin_respuesta():
    lab, s1, s2 = _crear_lab_con_dos_secciones()
    lab_repo = LaboratorioRepository()
    examen = lab_repo.add_examen(Examen(laboratorio_id=lab.id))
    pregunta = lab_repo.add_pregunta(
        Pregunta(
            examen_id=examen.id,
            enunciado="¿2+2?",
            tipo=TipoPregunta.OPCION_MULTIPLE,
            respuesta_hash=make_password("4"),
            opciones=["3", "4", "5"],
        )
    )
    estudiante_id = uuid.uuid4()
    progreso_repo = ProgresoRepository()
    progreso = progreso_repo.add(
        Progreso(asignacion_id=uuid.uuid4(), estudiante_id=estudiante_id)
    )
    progreso_repo.add_secciones(
        [
            ProgresoSeccion(
                progreso_id=progreso.id,
                seccion_id=s1.id,
                estado=EstadoProgresoSeccion.COMPLETADA,
            ),
            ProgresoSeccion(
                progreso_id=progreso.id,
                seccion_id=s2.id,
                estado=EstadoProgresoSeccion.COMPLETADA,
            ),
        ]
    )

    resultado = ObtenerExamenQuery(progreso_repo, lab_repo).execute(
        ObtenerExamenDTO(asignacion_id=progreso.asignacion_id, estudiante_id=estudiante_id)
    )

    assert resultado.examen_id == examen.id
    assert len(resultado.preguntas) == 1
    assert resultado.preguntas[0].id == pregunta.id
    assert resultado.preguntas[0].enunciado == "¿2+2?"
    assert resultado.preguntas[0].opciones == ["3", "4", "5"]
    assert not hasattr(resultado.preguntas[0], "respuesta_hash")
