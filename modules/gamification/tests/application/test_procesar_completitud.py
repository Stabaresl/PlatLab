import uuid

import pytest

from modules.gamification.application.dtos import ProcesarCompletitudDTO
from modules.gamification.application.procesar_completitud import ProcesarCompletitudLaboratorio
from modules.gamification.domain.entities import Cosmetico, Logro, Titulo
from modules.gamification.domain.value_objects import RarezaCosmetico, TipoCosmetico, TipoCriterioLogro
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
from modules.roadmap.application.dtos import AgregarNodoDTO
from modules.roadmap.application.use_cases.agregar_nodo import AgregarNodoUseCase
from modules.roadmap.domain.entities import CategoriaRoadmap
from modules.roadmap.infrastructure.repositories import CategoriaRoadmapRepository, NodoRoadmapRepository
from modules.shared.infrastructure.event_dispatcher import EventDispatcher
from modules.shared.infrastructure.unit_of_work import BaseUnitOfWork


def _uc():
    return ProcesarCompletitudLaboratorio(
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


def _crear_logro(**overrides) -> Logro:
    defaults = dict(
        clave=f"logro-{uuid.uuid4()}",
        nombre="Logro de prueba",
        descripcion="desc",
        tipo_criterio=TipoCriterioLogro.PRIMER_LABORATORIO,
        criterio_valor=None,
        rareza=RarezaCosmetico.COMUN,
    )
    defaults.update(overrides)
    return LogroRepository().add(Logro(**defaults))


def _crear_cosmetico(logro_id, **overrides) -> Cosmetico:
    defaults = dict(
        clave=f"cosmetico-{uuid.uuid4()}",
        nombre="Cosmético de prueba",
        tipo=TipoCosmetico.INSIGNIA,
        rareza=RarezaCosmetico.COMUN,
        color="0,0,0",
        logro_requerido_id=logro_id,
    )
    defaults.update(overrides)
    return CosmeticoRepository().add(Cosmetico(**defaults))


def _crear_titulo(logro_id, **overrides) -> Titulo:
    defaults = dict(
        clave=f"titulo-{uuid.uuid4()}",
        nombre="Título de prueba",
        descripcion="desc",
        rareza=RarezaCosmetico.COMUN,
        logro_requerido_id=logro_id,
    )
    defaults.update(overrides)
    return TituloRepository().add(Titulo(**defaults))


@pytest.mark.django_db
def test_otorga_xp_segun_dificultad():
    lab = _crear_lab(nivel_dificultad=NivelDificultad.AVANZADO)
    estudiante_id = uuid.uuid4()

    resultado = _uc().execute(
        ProcesarCompletitudDTO(estudiante_id=estudiante_id, laboratorio_id=lab.id)
    )

    assert resultado.xp_otorgado == 150
    perfil = PerfilJugadorRepository().get_by_estudiante(estudiante_id)
    assert perfil.xp == 150


@pytest.mark.django_db
def test_es_idempotente_no_duplica_xp():
    lab = _crear_lab()
    estudiante_id = uuid.uuid4()
    _uc().execute(ProcesarCompletitudDTO(estudiante_id=estudiante_id, laboratorio_id=lab.id))

    resultado = _uc().execute(
        ProcesarCompletitudDTO(estudiante_id=estudiante_id, laboratorio_id=lab.id)
    )

    assert resultado.xp_otorgado == 0
    perfil = PerfilJugadorRepository().get_by_estudiante(estudiante_id)
    assert perfil.xp == 50  # básico, una sola vez


@pytest.mark.django_db
def test_desbloquea_logro_primer_laboratorio_y_su_cosmetico():
    logro = _crear_logro(clave="primer_laboratorio", tipo_criterio=TipoCriterioLogro.PRIMER_LABORATORIO)
    cosmetico = _crear_cosmetico(logro.id)
    lab = _crear_lab()
    estudiante_id = uuid.uuid4()

    resultado = _uc().execute(
        ProcesarCompletitudDTO(estudiante_id=estudiante_id, laboratorio_id=lab.id)
    )

    assert len(resultado.logros_desbloqueados) == 1
    assert resultado.logros_desbloqueados[0].logro_id == logro.id
    assert LogroDesbloqueadoRepository().existe(estudiante_id, logro.id)
    assert CosmeticoDesbloqueadoRepository().existe(estudiante_id, cosmetico.id)


@pytest.mark.django_db
def test_desbloquea_titulo_junto_con_el_logro():
    logro = _crear_logro(clave="primer_laboratorio", tipo_criterio=TipoCriterioLogro.PRIMER_LABORATORIO)
    titulo = _crear_titulo(logro.id)
    lab = _crear_lab()
    estudiante_id = uuid.uuid4()

    _uc().execute(ProcesarCompletitudDTO(estudiante_id=estudiante_id, laboratorio_id=lab.id))

    assert TituloDesbloqueadoRepository().existe(estudiante_id, titulo.id)


@pytest.mark.django_db
def test_logro_n_laboratorios_no_se_desbloquea_antes_del_umbral():
    logro = _crear_logro(
        clave="dos_labs", tipo_criterio=TipoCriterioLogro.N_LABORATORIOS, criterio_valor="2"
    )
    lab = _crear_lab()
    estudiante_id = uuid.uuid4()

    _uc().execute(ProcesarCompletitudDTO(estudiante_id=estudiante_id, laboratorio_id=lab.id))

    assert not LogroDesbloqueadoRepository().existe(estudiante_id, logro.id)


@pytest.mark.django_db
def test_logro_n_laboratorios_se_desbloquea_al_alcanzar_el_umbral():
    logro = _crear_logro(
        clave="dos_labs", tipo_criterio=TipoCriterioLogro.N_LABORATORIOS, criterio_valor="2"
    )
    lab_a, lab_b = _crear_lab(), _crear_lab()
    estudiante_id = uuid.uuid4()

    _uc().execute(ProcesarCompletitudDTO(estudiante_id=estudiante_id, laboratorio_id=lab_a.id))
    resultado = _uc().execute(
        ProcesarCompletitudDTO(estudiante_id=estudiante_id, laboratorio_id=lab_b.id)
    )

    assert any(l.logro_id == logro.id for l in resultado.logros_desbloqueados)


@pytest.mark.django_db
def test_logro_categoria_roadmap_completa():
    categoria = CategoriaRoadmapRepository().add(CategoriaRoadmap(nombre=f"Cat {uuid.uuid4()}"))
    lab_a, lab_b = _crear_lab(), _crear_lab()
    nodo_repo = NodoRoadmapRepository()
    agregar_uc = AgregarNodoUseCase(
        unit_of_work=BaseUnitOfWork(),
        event_dispatcher=EventDispatcher(),
        categoria_repository=CategoriaRoadmapRepository(),
        nodo_repository=nodo_repo,
        laboratorio_repository=LaboratorioRepository(),
    )
    agregar_uc.execute(AgregarNodoDTO(categoria.id, lab_a.id, 0, uuid.uuid4(), "administrador"))
    agregar_uc.execute(AgregarNodoDTO(categoria.id, lab_b.id, 1, uuid.uuid4(), "administrador"))

    logro = _crear_logro(
        clave="categoria_completa",
        tipo_criterio=TipoCriterioLogro.CATEGORIA_ROADMAP_COMPLETA,
        criterio_valor=str(categoria.id),
    )
    estudiante_id = uuid.uuid4()

    _uc().execute(ProcesarCompletitudDTO(estudiante_id=estudiante_id, laboratorio_id=lab_a.id))
    assert not LogroDesbloqueadoRepository().existe(estudiante_id, logro.id)

    resultado = _uc().execute(
        ProcesarCompletitudDTO(estudiante_id=estudiante_id, laboratorio_id=lab_b.id)
    )
    assert any(l.logro_id == logro.id for l in resultado.logros_desbloqueados)


@pytest.mark.django_db
def test_no_reprocesa_un_logro_ya_desbloqueado():
    logro = _crear_logro(clave="primer_laboratorio", tipo_criterio=TipoCriterioLogro.PRIMER_LABORATORIO)
    lab_a, lab_b = _crear_lab(), _crear_lab()
    estudiante_id = uuid.uuid4()

    _uc().execute(ProcesarCompletitudDTO(estudiante_id=estudiante_id, laboratorio_id=lab_a.id))
    resultado = _uc().execute(
        ProcesarCompletitudDTO(estudiante_id=estudiante_id, laboratorio_id=lab_b.id)
    )

    assert resultado.logros_desbloqueados == []
