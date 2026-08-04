import uuid

import pytest

from modules.laboratories.domain.entities import Laboratorio, Seccion
from modules.laboratories.domain.value_objects import (
    EstadoLaboratorio,
    NivelDificultad,
    TipoLaboratorio,
)
from modules.laboratories.infrastructure.repositories import LaboratorioRepository
from modules.lab_environments.application.dtos import DetenerEntornoDTO, IniciarEntornoDTO
from modules.lab_environments.application.use_cases.aprovisionar_entorno import (
    AprovisionarEntornoUseCase,
)
from modules.lab_environments.application.use_cases.detener_entorno import DetenerEntornoUseCase
from modules.lab_environments.application.use_cases.iniciar_entorno import IniciarEntornoUseCase
from modules.lab_environments.domain.entities import EntornoActivo
from modules.lab_environments.domain.exceptions import (
    EntornoNoDisponibleError,
    SeccionNoDisponibleError,
    SeccionSinEntornoRealError,
)
from modules.lab_environments.domain.value_objects import EstadoEntorno
from modules.lab_environments.infrastructure.repositories import EntornoRepository
from modules.lab_environments.tests.application.conftest import FakeContenedorProvider
from modules.progress.domain.entities import Progreso, ProgresoSeccion
from modules.progress.domain.value_objects import EstadoProgresoSeccion
from modules.progress.infrastructure.repositories import ProgresoRepository
from modules.shared.domain.exceptions import NotFoundError
from modules.shared.infrastructure.event_dispatcher import EventDispatcher
from modules.shared.infrastructure.unit_of_work import BaseUnitOfWork


def _crear_lab_con_seccion_practica(imagen_practica="platlab-target-sqli:latest"):
    lab_repo = LaboratorioRepository()
    lab = lab_repo.add(
        Laboratorio(
            nombre=f"Lab Entorno {uuid.uuid4()}",
            descripcion="desc",
            nivel_dificultad=NivelDificultad.BASICO,
            estado=EstadoLaboratorio.PUBLICADO,
            tipo=TipoLaboratorio.PREDETERMINADO,
        )
    )
    seccion = lab_repo.add_seccion(
        Seccion(
            laboratorio_id=lab.id,
            titulo="Practica",
            contenido_teorico="...",
            orden=1,
            tiene_practica=True,
            imagen_practica=imagen_practica,
        )
    )
    return lab, seccion


def _crear_progreso(seccion, estudiante_id, estado=EstadoProgresoSeccion.EN_PROGRESO):
    progreso_repo = ProgresoRepository()
    progreso = progreso_repo.add(Progreso(asignacion_id=uuid.uuid4(), estudiante_id=estudiante_id))
    progreso_repo.add_secciones(
        [ProgresoSeccion(progreso_id=progreso.id, seccion_id=seccion.id, estado=estado)]
    )
    return progreso


def _build_iniciar_uc(**overrides):
    kwargs = dict(
        unit_of_work=BaseUnitOfWork(),
        event_dispatcher=EventDispatcher(),
        entorno_repository=EntornoRepository(),
        progreso_repository=ProgresoRepository(),
        laboratorio_repository=LaboratorioRepository(),
        max_concurrentes=5,
    )
    kwargs.update(overrides)
    return IniciarEntornoUseCase(**kwargs)


# ---------------------------------------------------------------------------
# IniciarEntornoUseCase — ya NO llama a Docker (RNF rendimiento): crea el
# EntornoActivo en `iniciando` y dispara EntornoAprovisionamientoSolicitado.
# Como los tests corren con CELERY_TASK_ALWAYS_EAGER (config/settings/test.py),
# el listener -> aprovisionar_entorno_task -> AprovisionarEntornoUseCase
# corren síncronos dentro del mismo execute() que dispara el evento — por
# eso estos tests usan el fixture `fake_docker` (conftest.py) para no
# depender de Docker real, mismo criterio que test_solicitar_instructor.py.
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_iniciar_entorno_termina_activo_via_tarea_asincrona_eager(fake_docker):
    estudiante_id = uuid.uuid4()
    lab, seccion = _crear_lab_con_seccion_practica()
    progreso = _crear_progreso(seccion, estudiante_id)

    resultado = _build_iniciar_uc().execute(
        IniciarEntornoDTO(asignacion_id=progreso.asignacion_id, seccion_id=seccion.id, estudiante_id=estudiante_id)
    )

    # El DTO se arma dentro de _execute_domain_logic, ANTES del dispatch
    # del evento — en ese punto el entorno todavía está en `iniciando`.
    assert resultado.estado == EstadoEntorno.INICIANDO.value

    # Pero para cuando execute() ya retornó, la tarea eager ya corrió de
    # punta a punta contra el Docker fake.
    guardado = EntornoRepository().get_by_id(resultado.id)
    assert guardado.estado == EstadoEntorno.ACTIVO
    assert guardado.container_id == fake_docker.iniciados[0]
    assert guardado.estudiante_id == estudiante_id


@pytest.mark.django_db
def test_iniciar_entorno_reconecta_a_uno_existente_en_vez_de_duplicar(fake_docker):
    estudiante_id = uuid.uuid4()
    lab, seccion = _crear_lab_con_seccion_practica()
    progreso = _crear_progreso(seccion, estudiante_id)
    dto = IniciarEntornoDTO(asignacion_id=progreso.asignacion_id, seccion_id=seccion.id, estudiante_id=estudiante_id)

    primero = _build_iniciar_uc().execute(dto)
    segundo = _build_iniciar_uc().execute(dto)

    assert primero.id == segundo.id
    assert len(fake_docker.iniciados) == 1
    assert EntornoRepository().contar_activos() == 1


@pytest.mark.django_db
def test_iniciar_entorno_seccion_sin_imagen_lanza_error():
    estudiante_id = uuid.uuid4()
    lab, seccion = _crear_lab_con_seccion_practica(imagen_practica=None)
    progreso = _crear_progreso(seccion, estudiante_id)

    with pytest.raises(SeccionSinEntornoRealError):
        _build_iniciar_uc().execute(
            IniciarEntornoDTO(asignacion_id=progreso.asignacion_id, seccion_id=seccion.id, estudiante_id=estudiante_id)
        )


@pytest.mark.django_db
def test_iniciar_entorno_seccion_bloqueada_lanza_error():
    estudiante_id = uuid.uuid4()
    lab, seccion = _crear_lab_con_seccion_practica()
    progreso = _crear_progreso(seccion, estudiante_id, estado=EstadoProgresoSeccion.BLOQUEADA)

    with pytest.raises(SeccionNoDisponibleError):
        _build_iniciar_uc().execute(
            IniciarEntornoDTO(asignacion_id=progreso.asignacion_id, seccion_id=seccion.id, estudiante_id=estudiante_id)
        )


@pytest.mark.django_db
def test_iniciar_entorno_otro_estudiante_lanza_not_found():
    lab, seccion = _crear_lab_con_seccion_practica()
    progreso = _crear_progreso(seccion, uuid.uuid4())

    with pytest.raises(NotFoundError):
        _build_iniciar_uc().execute(
            IniciarEntornoDTO(asignacion_id=progreso.asignacion_id, seccion_id=seccion.id, estudiante_id=uuid.uuid4())
        )


@pytest.mark.django_db
def test_iniciar_entorno_sin_cupo_lanza_rate_limited(fake_docker):
    estudiante_id = uuid.uuid4()
    lab, seccion = _crear_lab_con_seccion_practica()
    progreso = _crear_progreso(seccion, estudiante_id)

    # Ocupa el único cupo disponible con OTRO estudiante/sección.
    lab2, seccion2 = _crear_lab_con_seccion_practica()
    progreso2 = _crear_progreso(seccion2, uuid.uuid4())
    _build_iniciar_uc(max_concurrentes=1).execute(
        IniciarEntornoDTO(asignacion_id=progreso2.asignacion_id, seccion_id=seccion2.id, estudiante_id=progreso2.estudiante_id)
    )

    with pytest.raises(EntornoNoDisponibleError):
        _build_iniciar_uc(max_concurrentes=1).execute(
            IniciarEntornoDTO(asignacion_id=progreso.asignacion_id, seccion_id=seccion.id, estudiante_id=estudiante_id)
        )


# ---------------------------------------------------------------------------
# AprovisionarEntornoUseCase en aislamiento — construye el EntornoActivo
# directo por repositorio (sin pasar por IniciarEntornoUseCase/eventos)
# para no depender de Celery ni de la cadena completa.
# ---------------------------------------------------------------------------


def _crear_entorno_iniciando(seccion, progreso, estudiante_id) -> EntornoActivo:
    return EntornoRepository().add(
        EntornoActivo(
            seccion_id=seccion.id,
            progreso_id=progreso.id,
            estudiante_id=estudiante_id,
            container_id="",
        )
    )


@pytest.mark.django_db
def test_aprovisionar_entorno_marca_activo_con_container_id():
    estudiante_id = uuid.uuid4()
    lab, seccion = _crear_lab_con_seccion_practica()
    progreso = _crear_progreso(seccion, estudiante_id)
    entorno = _crear_entorno_iniciando(seccion, progreso, estudiante_id)
    provider = FakeContenedorProvider()

    AprovisionarEntornoUseCase(
        unit_of_work=BaseUnitOfWork(), entorno_repository=EntornoRepository(), contenedor_provider=provider
    ).execute(entorno.id, seccion.imagen_practica)

    guardado = EntornoRepository().get_by_id(entorno.id)
    assert guardado.estado == EstadoEntorno.ACTIVO
    assert guardado.container_id == provider.iniciados[0]


@pytest.mark.django_db
def test_aprovisionar_entorno_falla_docker_marca_error():
    estudiante_id = uuid.uuid4()
    lab, seccion = _crear_lab_con_seccion_practica()
    progreso = _crear_progreso(seccion, estudiante_id)
    entorno = _crear_entorno_iniciando(seccion, progreso, estudiante_id)
    provider = FakeContenedorProvider(falla_al_iniciar=True)

    AprovisionarEntornoUseCase(
        unit_of_work=BaseUnitOfWork(), entorno_repository=EntornoRepository(), contenedor_provider=provider
    ).execute(entorno.id, seccion.imagen_practica)

    guardado = EntornoRepository().get_by_id(entorno.id)
    assert guardado.estado == EstadoEntorno.ERROR


@pytest.mark.django_db
def test_aprovisionar_entorno_ya_detenido_no_hace_nada():
    """
    Carrera: el estudiante detiene el entorno (o el reaper lo alcanza)
    antes de que la tarea de Celery corra — no hay nada que aprovisionar.
    """
    estudiante_id = uuid.uuid4()
    lab, seccion = _crear_lab_con_seccion_practica()
    progreso = _crear_progreso(seccion, estudiante_id)
    entorno = _crear_entorno_iniciando(seccion, progreso, estudiante_id)
    entorno.marcar_detenido()
    EntornoRepository().update(entorno)
    provider = FakeContenedorProvider()

    AprovisionarEntornoUseCase(
        unit_of_work=BaseUnitOfWork(), entorno_repository=EntornoRepository(), contenedor_provider=provider
    ).execute(entorno.id, seccion.imagen_practica)

    assert provider.iniciados == []
    guardado = EntornoRepository().get_by_id(entorno.id)
    assert guardado.estado == EstadoEntorno.DETENIDO


# ---------------------------------------------------------------------------
# DetenerEntornoUseCase
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_detener_entorno_iniciando_no_llama_a_docker_y_marca_detenido():
    estudiante_id = uuid.uuid4()
    lab, seccion = _crear_lab_con_seccion_practica()
    progreso = _crear_progreso(seccion, estudiante_id)
    entorno = _crear_entorno_iniciando(seccion, progreso, estudiante_id)
    provider = FakeContenedorProvider()

    DetenerEntornoUseCase(
        unit_of_work=BaseUnitOfWork(), entorno_repository=EntornoRepository(), contenedor_provider=provider
    ).execute(DetenerEntornoDTO(entorno_id=entorno.id, estudiante_id=estudiante_id))

    assert provider.detenidos == []
    guardado = EntornoRepository().get_by_id(entorno.id)
    assert guardado.estado == EstadoEntorno.DETENIDO


@pytest.mark.django_db
def test_detener_entorno_activo_apaga_contenedor_y_marca_detenido(fake_docker):
    estudiante_id = uuid.uuid4()
    lab, seccion = _crear_lab_con_seccion_practica()
    progreso = _crear_progreso(seccion, estudiante_id)
    creado = _build_iniciar_uc().execute(
        IniciarEntornoDTO(asignacion_id=progreso.asignacion_id, seccion_id=seccion.id, estudiante_id=estudiante_id)
    )

    DetenerEntornoUseCase(
        unit_of_work=BaseUnitOfWork(), entorno_repository=EntornoRepository(), contenedor_provider=fake_docker
    ).execute(DetenerEntornoDTO(entorno_id=creado.id, estudiante_id=estudiante_id))

    assert fake_docker.detenidos == fake_docker.iniciados
    guardado = EntornoRepository().get_by_id(creado.id)
    assert guardado.estado == EstadoEntorno.DETENIDO


@pytest.mark.django_db
def test_detener_entorno_otro_estudiante_lanza_not_found():
    estudiante_id = uuid.uuid4()
    lab, seccion = _crear_lab_con_seccion_practica()
    progreso = _crear_progreso(seccion, estudiante_id)
    entorno = _crear_entorno_iniciando(seccion, progreso, estudiante_id)
    provider = FakeContenedorProvider()

    with pytest.raises(NotFoundError):
        DetenerEntornoUseCase(
            unit_of_work=BaseUnitOfWork(), entorno_repository=EntornoRepository(), contenedor_provider=provider
        ).execute(DetenerEntornoDTO(entorno_id=entorno.id, estudiante_id=uuid.uuid4()))
