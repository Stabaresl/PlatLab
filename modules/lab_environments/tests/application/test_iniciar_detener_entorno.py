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
from modules.lab_environments.application.use_cases.detener_entorno import DetenerEntornoUseCase
from modules.lab_environments.application.use_cases.iniciar_entorno import IniciarEntornoUseCase
from modules.lab_environments.domain.exceptions import (
    EntornoNoDisponibleError,
    SeccionNoDisponibleError,
    SeccionSinEntornoRealError,
)
from modules.lab_environments.domain.value_objects import EstadoEntorno
from modules.lab_environments.infrastructure.repositories import EntornoRepository
from modules.progress.domain.entities import Progreso, ProgresoSeccion
from modules.progress.domain.value_objects import EstadoProgresoSeccion
from modules.progress.infrastructure.repositories import ProgresoRepository
from modules.shared.domain.exceptions import NotFoundError
from modules.shared.infrastructure.event_dispatcher import EventDispatcher
from modules.shared.infrastructure.unit_of_work import BaseUnitOfWork


class FakeContenedorProvider:
    """Doble de prueba — no toca Docker real, para tests rápidos y deterministas."""

    def __init__(self, falla_al_iniciar: bool = False):
        self.iniciados: list[str] = []
        self.detenidos: list[str] = []
        self._falla = falla_al_iniciar
        self._contador = 0

    def iniciar(self, imagen: str) -> str:
        if self._falla:
            raise RuntimeError("docker no disponible (simulado)")
        self._contador += 1
        container_id = f"fake-container-{self._contador}"
        self.iniciados.append(container_id)
        return container_id

    def detener(self, container_id: str) -> None:
        self.detenidos.append(container_id)

    def esta_vivo(self, container_id: str) -> bool:
        return container_id in self.iniciados and container_id not in self.detenidos


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


def _build_iniciar_uc(provider, **overrides):
    kwargs = dict(
        unit_of_work=BaseUnitOfWork(),
        event_dispatcher=EventDispatcher(),
        entorno_repository=EntornoRepository(),
        progreso_repository=ProgresoRepository(),
        laboratorio_repository=LaboratorioRepository(),
        contenedor_provider=provider,
        max_concurrentes=5,
    )
    kwargs.update(overrides)
    return IniciarEntornoUseCase(**kwargs)


@pytest.mark.django_db
def test_iniciar_entorno_crea_contenedor_y_persiste():
    estudiante_id = uuid.uuid4()
    lab, seccion = _crear_lab_con_seccion_practica()
    progreso = _crear_progreso(seccion, estudiante_id)
    provider = FakeContenedorProvider()

    resultado = _build_iniciar_uc(provider).execute(
        IniciarEntornoDTO(asignacion_id=progreso.asignacion_id, seccion_id=seccion.id, estudiante_id=estudiante_id)
    )

    assert resultado.estado == EstadoEntorno.ACTIVO.value
    assert len(provider.iniciados) == 1
    guardado = EntornoRepository().get_by_id(resultado.id)
    assert guardado.container_id == provider.iniciados[0]
    assert guardado.estudiante_id == estudiante_id


@pytest.mark.django_db
def test_iniciar_entorno_reconecta_a_uno_existente_en_vez_de_duplicar():
    estudiante_id = uuid.uuid4()
    lab, seccion = _crear_lab_con_seccion_practica()
    progreso = _crear_progreso(seccion, estudiante_id)
    provider = FakeContenedorProvider()
    dto = IniciarEntornoDTO(asignacion_id=progreso.asignacion_id, seccion_id=seccion.id, estudiante_id=estudiante_id)

    primero = _build_iniciar_uc(provider).execute(dto)
    segundo = _build_iniciar_uc(provider).execute(dto)

    assert primero.id == segundo.id
    assert len(provider.iniciados) == 1


@pytest.mark.django_db
def test_iniciar_entorno_seccion_sin_imagen_lanza_error():
    estudiante_id = uuid.uuid4()
    lab, seccion = _crear_lab_con_seccion_practica(imagen_practica=None)
    progreso = _crear_progreso(seccion, estudiante_id)
    provider = FakeContenedorProvider()

    with pytest.raises(SeccionSinEntornoRealError):
        _build_iniciar_uc(provider).execute(
            IniciarEntornoDTO(asignacion_id=progreso.asignacion_id, seccion_id=seccion.id, estudiante_id=estudiante_id)
        )
    assert provider.iniciados == []


@pytest.mark.django_db
def test_iniciar_entorno_seccion_bloqueada_lanza_error():
    estudiante_id = uuid.uuid4()
    lab, seccion = _crear_lab_con_seccion_practica()
    progreso = _crear_progreso(seccion, estudiante_id, estado=EstadoProgresoSeccion.BLOQUEADA)
    provider = FakeContenedorProvider()

    with pytest.raises(SeccionNoDisponibleError):
        _build_iniciar_uc(provider).execute(
            IniciarEntornoDTO(asignacion_id=progreso.asignacion_id, seccion_id=seccion.id, estudiante_id=estudiante_id)
        )


@pytest.mark.django_db
def test_iniciar_entorno_otro_estudiante_lanza_not_found():
    lab, seccion = _crear_lab_con_seccion_practica()
    progreso = _crear_progreso(seccion, uuid.uuid4())
    provider = FakeContenedorProvider()

    with pytest.raises(NotFoundError):
        _build_iniciar_uc(provider).execute(
            IniciarEntornoDTO(asignacion_id=progreso.asignacion_id, seccion_id=seccion.id, estudiante_id=uuid.uuid4())
        )


@pytest.mark.django_db
def test_iniciar_entorno_sin_cupo_lanza_rate_limited():
    estudiante_id = uuid.uuid4()
    lab, seccion = _crear_lab_con_seccion_practica()
    progreso = _crear_progreso(seccion, estudiante_id)
    provider = FakeContenedorProvider()

    # Ocupa el único cupo disponible con OTRO estudiante/sección.
    lab2, seccion2 = _crear_lab_con_seccion_practica()
    progreso2 = _crear_progreso(seccion2, uuid.uuid4())
    _build_iniciar_uc(provider, max_concurrentes=1).execute(
        IniciarEntornoDTO(asignacion_id=progreso2.asignacion_id, seccion_id=seccion2.id, estudiante_id=progreso2.estudiante_id)
    )

    with pytest.raises(EntornoNoDisponibleError):
        _build_iniciar_uc(provider, max_concurrentes=1).execute(
            IniciarEntornoDTO(asignacion_id=progreso.asignacion_id, seccion_id=seccion.id, estudiante_id=estudiante_id)
        )


@pytest.mark.django_db
def test_iniciar_entorno_falla_docker_no_persiste_nada():
    estudiante_id = uuid.uuid4()
    lab, seccion = _crear_lab_con_seccion_practica()
    progreso = _crear_progreso(seccion, estudiante_id)
    provider = FakeContenedorProvider(falla_al_iniciar=True)

    with pytest.raises(Exception):
        _build_iniciar_uc(provider).execute(
            IniciarEntornoDTO(asignacion_id=progreso.asignacion_id, seccion_id=seccion.id, estudiante_id=estudiante_id)
        )

    assert EntornoRepository().get_activo_por_seccion(progreso.id, seccion.id) is None


@pytest.mark.django_db
def test_detener_entorno_apaga_contenedor_y_marca_detenido():
    estudiante_id = uuid.uuid4()
    lab, seccion = _crear_lab_con_seccion_practica()
    progreso = _crear_progreso(seccion, estudiante_id)
    provider = FakeContenedorProvider()
    creado = _build_iniciar_uc(provider).execute(
        IniciarEntornoDTO(asignacion_id=progreso.asignacion_id, seccion_id=seccion.id, estudiante_id=estudiante_id)
    )

    DetenerEntornoUseCase(
        unit_of_work=BaseUnitOfWork(), entorno_repository=EntornoRepository(), contenedor_provider=provider
    ).execute(DetenerEntornoDTO(entorno_id=creado.id, estudiante_id=estudiante_id))

    assert provider.detenidos == provider.iniciados
    guardado = EntornoRepository().get_by_id(creado.id)
    assert guardado.estado == EstadoEntorno.DETENIDO


@pytest.mark.django_db
def test_detener_entorno_otro_estudiante_lanza_not_found():
    estudiante_id = uuid.uuid4()
    lab, seccion = _crear_lab_con_seccion_practica()
    progreso = _crear_progreso(seccion, estudiante_id)
    provider = FakeContenedorProvider()
    creado = _build_iniciar_uc(provider).execute(
        IniciarEntornoDTO(asignacion_id=progreso.asignacion_id, seccion_id=seccion.id, estudiante_id=estudiante_id)
    )

    with pytest.raises(NotFoundError):
        DetenerEntornoUseCase(
            unit_of_work=BaseUnitOfWork(), entorno_repository=EntornoRepository(), contenedor_provider=provider
        ).execute(DetenerEntornoDTO(entorno_id=creado.id, estudiante_id=uuid.uuid4()))
