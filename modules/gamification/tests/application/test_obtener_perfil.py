import uuid

import pytest

from modules.gamification.application.dtos import ProcesarCompletitudDTO
from modules.gamification.application.procesar_completitud import ProcesarCompletitudLaboratorio
from modules.gamification.application.queries.obtener_perfil import ObtenerPerfilQuery
from modules.gamification.domain.entities import Logro
from modules.gamification.domain.value_objects import RarezaCosmetico, TipoCriterioLogro
from modules.gamification.infrastructure.repositories import (
    CosmeticoDesbloqueadoRepository,
    CosmeticoRepository,
    LogroDesbloqueadoRepository,
    LogroRepository,
    PerfilJugadorRepository,
    TituloDesbloqueadoRepository,
    TituloRepository,
    XpOtorgadoRepository,
)
from modules.laboratories.domain.entities import Laboratorio
from modules.laboratories.domain.value_objects import EstadoLaboratorio, NivelDificultad, TipoLaboratorio
from modules.laboratories.infrastructure.repositories import LaboratorioRepository
from modules.roadmap.infrastructure.repositories import NodoRoadmapRepository
from modules.shared.domain.exceptions import ForbiddenError
from modules.shared.infrastructure.event_dispatcher import EventDispatcher
from modules.shared.infrastructure.unit_of_work import BaseUnitOfWork


def _query():
    return ObtenerPerfilQuery(
        perfil_repository=PerfilJugadorRepository(),
        xp_otorgado_repository=XpOtorgadoRepository(),
        logro_repository=LogroRepository(),
        logro_desbloqueado_repository=LogroDesbloqueadoRepository(),
        cosmetico_repository=CosmeticoRepository(),
        cosmetico_desbloqueado_repository=CosmeticoDesbloqueadoRepository(),
        titulo_repository=TituloRepository(),
        titulo_desbloqueado_repository=TituloDesbloqueadoRepository(),
        nodo_roadmap_repository=NodoRoadmapRepository(),
    )


def _crear_lab(**overrides) -> Laboratorio:
    defaults = dict(
        nombre=f"Lab {uuid.uuid4()}",
        descripcion="desc",
        nivel_dificultad=NivelDificultad.BASICO,
        estado=EstadoLaboratorio.PUBLICADO,
        tipo=TipoLaboratorio.PREDETERMINADO,
    )
    defaults.update(overrides)
    return LaboratorioRepository().add(Laboratorio(**defaults))


def _completar(estudiante_id, laboratorio_id):
    ProcesarCompletitudLaboratorio(
        unit_of_work=BaseUnitOfWork(),
        event_dispatcher=EventDispatcher(),
        perfil_repository=PerfilJugadorRepository(),
        xp_otorgado_repository=XpOtorgadoRepository(),
        logro_repository=LogroRepository(),
        logro_desbloqueado_repository=LogroDesbloqueadoRepository(),
        cosmetico_repository=CosmeticoRepository(),
        cosmetico_desbloqueado_repository=CosmeticoDesbloqueadoRepository(),
        titulo_repository=TituloRepository(),
        titulo_desbloqueado_repository=TituloDesbloqueadoRepository(),
        laboratorio_repository=LaboratorioRepository(),
        nodo_roadmap_repository=NodoRoadmapRepository(),
    ).execute(ProcesarCompletitudDTO(estudiante_id=estudiante_id, laboratorio_id=laboratorio_id))


@pytest.mark.django_db
def test_perfil_de_estudiante_sin_actividad_previa():
    estudiante_id = uuid.uuid4()

    perfil = _query().execute(estudiante_id=estudiante_id, actor_rol="estudiante")

    assert perfil.xp == 0
    assert perfil.nivel == 1
    assert perfil.cosmeticos == []
    assert perfil.titulos == []
    assert perfil.avatar_tipo == "preset"
    assert perfil.avatar_valor == "operador_nocturno"


@pytest.mark.django_db
def test_perfil_refleja_xp_y_logro_desbloqueado_tras_completar_un_lab():
    LogroRepository().add(
        Logro(
            clave="primer_laboratorio",
            nombre="Primer Hackeo",
            descripcion="desc",
            tipo_criterio=TipoCriterioLogro.PRIMER_LABORATORIO,
            rareza=RarezaCosmetico.COMUN,
        )
    )
    lab = _crear_lab()
    estudiante_id = uuid.uuid4()
    _completar(estudiante_id, lab.id)

    perfil = _query().execute(estudiante_id=estudiante_id, actor_rol="estudiante")

    assert perfil.xp == 50
    logro = next(l for l in perfil.logros if l.clave == "primer_laboratorio")
    assert logro.desbloqueado is True


@pytest.mark.django_db
def test_progreso_de_logro_n_laboratorios_no_desbloqueado():
    LogroRepository().add(
        Logro(
            clave="cinco_labs",
            nombre="Cazador de Bugs",
            descripcion="desc",
            tipo_criterio=TipoCriterioLogro.N_LABORATORIOS,
            criterio_valor="5",
            rareza=RarezaCosmetico.POCO_COMUN,
        )
    )
    lab = _crear_lab()
    estudiante_id = uuid.uuid4()
    _completar(estudiante_id, lab.id)

    perfil = _query().execute(estudiante_id=estudiante_id, actor_rol="estudiante")

    logro = next(l for l in perfil.logros if l.clave == "cinco_labs")
    assert logro.desbloqueado is False
    assert logro.progreso == "1/5"


@pytest.mark.django_db
def test_instructor_no_tiene_perfil_de_progresion():
    with pytest.raises(ForbiddenError):
        _query().execute(estudiante_id=uuid.uuid4(), actor_rol="instructor")
