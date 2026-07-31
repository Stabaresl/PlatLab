import uuid

import pytest

from modules.laboratories.application.dtos import ListarLaboratoriosFiltroDTO
from modules.laboratories.application.queries.listar_laboratorios import (
    ListarLaboratoriosQuery,
)
from modules.laboratories.domain.entities import Laboratorio
from modules.laboratories.domain.value_objects import (
    EstadoLaboratorio,
    NivelDificultad,
    TipoLaboratorio,
)
from modules.laboratories.infrastructure.repositories import LaboratorioRepository


def _crear_lab(repo: LaboratorioRepository, **overrides) -> Laboratorio:
    # `visible_en_catalogo` no lo acepta `add()` (una creación nunca nace ya
    # visible en catálogo, ver `LaboratorioRepository.add`) — se aplica
    # después vía `update()`, igual que `CambiarVisibilidadCatalogoUseCase`.
    visible_en_catalogo = overrides.pop("visible_en_catalogo", None)
    defaults = dict(
        nombre="Lab Catalogo",
        descripcion="desc",
        nivel_dificultad=NivelDificultad.BASICO,
        estado=EstadoLaboratorio.PUBLICADO,
        tipo=TipoLaboratorio.PREDETERMINADO,
        temas=[],
    )
    defaults.update(overrides)
    lab = repo.add(Laboratorio(**defaults))
    if visible_en_catalogo is not None:
        lab.visible_en_catalogo = visible_en_catalogo
        lab = repo.update(lab)
    return lab


@pytest.mark.django_db
def test_catalogo_publico_solo_predeterminados_publicados():
    repo = LaboratorioRepository()
    _crear_lab(repo, nombre="Visible Publico")
    _crear_lab(repo, nombre="Borrador Oculto", estado=EstadoLaboratorio.BORRADOR)
    _crear_lab(
        repo,
        nombre="Personalizado Oculto",
        tipo=TipoLaboratorio.PERSONALIZADO,
        instructor_id=uuid.uuid4(),
    )

    resultados = ListarLaboratoriosQuery(repo).execute(ListarLaboratoriosFiltroDTO())

    nombres = [r.nombre for r in resultados]
    assert "Visible Publico" in nombres
    assert "Borrador Oculto" not in nombres
    assert "Personalizado Oculto" not in nombres


@pytest.mark.django_db
def test_catalogo_publico_incluye_personalizado_con_visible_en_catalogo():
    repo = LaboratorioRepository()
    _crear_lab(
        repo,
        nombre="Personalizado Visible",
        tipo=TipoLaboratorio.PERSONALIZADO,
        instructor_id=uuid.uuid4(),
        visible_en_catalogo=True,
    )
    _crear_lab(
        repo,
        nombre="Personalizado No Visible",
        tipo=TipoLaboratorio.PERSONALIZADO,
        instructor_id=uuid.uuid4(),
    )

    resultados = ListarLaboratoriosQuery(repo).execute(ListarLaboratoriosFiltroDTO())

    nombres = [r.nombre for r in resultados]
    assert "Personalizado Visible" in nombres
    assert "Personalizado No Visible" not in nombres


@pytest.mark.django_db
def test_catalogo_filtra_por_dificultad():
    repo = LaboratorioRepository()
    _crear_lab(repo, nombre="Lab Basico Filtro", nivel_dificultad=NivelDificultad.BASICO)
    _crear_lab(repo, nombre="Lab Avanzado Filtro", nivel_dificultad=NivelDificultad.AVANZADO)

    resultados = ListarLaboratoriosQuery(repo).execute(
        ListarLaboratoriosFiltroDTO(dificultad="avanzado")
    )

    nombres = [r.nombre for r in resultados]
    assert "Lab Avanzado Filtro" in nombres
    assert "Lab Basico Filtro" not in nombres


@pytest.mark.django_db
def test_catalogo_filtra_por_tema():
    repo = LaboratorioRepository()
    _crear_lab(repo, nombre="Lab Redes Filtro", temas=["redes"])
    _crear_lab(repo, nombre="Lab Web Filtro", temas=["web"])

    resultados = ListarLaboratoriosQuery(repo).execute(ListarLaboratoriosFiltroDTO(tema="redes"))

    nombres = [r.nombre for r in resultados]
    assert "Lab Redes Filtro" in nombres
    assert "Lab Web Filtro" not in nombres


@pytest.mark.django_db
def test_catalogo_instructor_ve_su_borrador_no_el_ajeno():
    repo = LaboratorioRepository()
    instructor_id = uuid.uuid4()
    _crear_lab(
        repo,
        nombre="Propio Borrador",
        tipo=TipoLaboratorio.PERSONALIZADO,
        estado=EstadoLaboratorio.BORRADOR,
        instructor_id=instructor_id,
    )
    _crear_lab(
        repo,
        nombre="Ajeno Borrador",
        tipo=TipoLaboratorio.PERSONALIZADO,
        estado=EstadoLaboratorio.BORRADOR,
        instructor_id=uuid.uuid4(),
    )

    resultados = ListarLaboratoriosQuery(repo).execute(
        ListarLaboratoriosFiltroDTO(instructor_id=instructor_id)
    )

    nombres = [r.nombre for r in resultados]
    assert "Propio Borrador" in nombres
    assert "Ajeno Borrador" not in nombres


@pytest.mark.django_db
def test_catalogo_agrega_inscrito_para_estudiante():
    class _FakeInscripcion:
        def esta_inscrito(self, estudiante_id, laboratorio_id):
            return True

    repo = LaboratorioRepository()
    _crear_lab(repo, nombre="Lab Inscripcion")

    resultados = ListarLaboratoriosQuery(
        repo, estado_inscripcion_provider=_FakeInscripcion()
    ).execute(ListarLaboratoriosFiltroDTO(estudiante_id=uuid.uuid4()))

    assert resultados[0].inscrito is True


@pytest.mark.django_db
def test_catalogo_sin_estudiante_no_agrega_inscrito():
    repo = LaboratorioRepository()
    _crear_lab(repo, nombre="Lab Sin Inscripcion")

    resultados = ListarLaboratoriosQuery(repo).execute(ListarLaboratoriosFiltroDTO())

    assert resultados[0].inscrito is None
