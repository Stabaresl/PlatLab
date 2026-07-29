import uuid

import pytest

from modules.laboratories.application.queries.obtener_detalle_laboratorio import (
    ObtenerDetalleLaboratorioQuery,
)
from modules.laboratories.application.queries.obtener_toc import ObtenerTOCQuery
from modules.laboratories.domain.entities import Laboratorio, Seccion
from modules.laboratories.domain.value_objects import (
    EstadoLaboratorio,
    NivelDificultad,
    TipoLaboratorio,
)
from modules.laboratories.infrastructure.repositories import LaboratorioRepository
from modules.shared.domain.exceptions import NotFoundError


def _crear_lab_con_secciones(repo: LaboratorioRepository, **overrides) -> Laboratorio:
    defaults = dict(
        nombre="Lab Detalle",
        descripcion="Descripcion detalle",
        nivel_dificultad=NivelDificultad.INTERMEDIO,
        estado=EstadoLaboratorio.PUBLICADO,
        tipo=TipoLaboratorio.PREDETERMINADO,
        temas=["redes", "web"],
    )
    defaults.update(overrides)
    lab = repo.add(Laboratorio(**defaults))
    repo.add_seccion(
        Seccion(
            laboratorio_id=lab.id,
            titulo="Intro",
            contenido_teorico="contenido secreto 1",
            orden=1,
            tiene_practica=False,
        )
    )
    repo.add_seccion(
        Seccion(
            laboratorio_id=lab.id,
            titulo="Practica",
            contenido_teorico="contenido secreto 2",
            orden=2,
            tiene_practica=True,
        )
    )
    return lab


@pytest.mark.django_db
def test_detalle_publicado_visible_sin_contenido_teorico():
    repo = LaboratorioRepository()
    lab = _crear_lab_con_secciones(repo)

    detalle = ObtenerDetalleLaboratorioQuery(repo).execute(lab.id)

    assert detalle.nombre == "Lab Detalle"
    assert detalle.temas == ["redes", "web"]
    assert detalle.total_secciones == 2
    assert not hasattr(detalle, "contenido_teorico")


@pytest.mark.django_db
def test_detalle_borrador_ajeno_lanza_not_found():
    repo = LaboratorioRepository()
    lab = _crear_lab_con_secciones(
        repo,
        estado=EstadoLaboratorio.BORRADOR,
        tipo=TipoLaboratorio.PERSONALIZADO,
        instructor_id=uuid.uuid4(),
    )

    with pytest.raises(NotFoundError):
        ObtenerDetalleLaboratorioQuery(repo).execute(lab.id, instructor_id=uuid.uuid4())


@pytest.mark.django_db
def test_detalle_borrador_propio_visible_para_su_instructor():
    repo = LaboratorioRepository()
    instructor_id = uuid.uuid4()
    lab = _crear_lab_con_secciones(
        repo,
        estado=EstadoLaboratorio.BORRADOR,
        tipo=TipoLaboratorio.PERSONALIZADO,
        instructor_id=instructor_id,
    )

    detalle = ObtenerDetalleLaboratorioQuery(repo).execute(lab.id, instructor_id=instructor_id)

    assert detalle.id == lab.id


@pytest.mark.django_db
def test_detalle_inexistente_lanza_not_found():
    repo = LaboratorioRepository()

    with pytest.raises(NotFoundError):
        ObtenerDetalleLaboratorioQuery(repo).execute(uuid.uuid4())


@pytest.mark.django_db
def test_toc_devuelve_solo_titulos_orden_y_tiene_practica():
    repo = LaboratorioRepository()
    lab = _crear_lab_con_secciones(repo)

    toc = ObtenerTOCQuery(repo).execute(lab.id)

    assert len(toc.secciones) == 2
    assert toc.secciones[0].titulo == "Intro"
    assert toc.secciones[0].tiene_practica is False
    assert toc.secciones[1].tiene_practica is True
    assert not hasattr(toc.secciones[0], "contenido_teorico")


@pytest.mark.django_db
def test_toc_borrador_ajeno_lanza_not_found():
    repo = LaboratorioRepository()
    lab = _crear_lab_con_secciones(
        repo,
        estado=EstadoLaboratorio.BORRADOR,
        tipo=TipoLaboratorio.PERSONALIZADO,
        instructor_id=uuid.uuid4(),
    )

    with pytest.raises(NotFoundError):
        ObtenerTOCQuery(repo).execute(lab.id)


class _FakeInscripcion:
    """Siempre responde que el par (estudiante, laboratorio) está inscrito."""

    def esta_inscrito(self, estudiante_id, laboratorio_id):
        return True


class _FakeSinInscripcion:
    def esta_inscrito(self, estudiante_id, laboratorio_id):
        return False


@pytest.mark.django_db
def test_detalle_personalizado_ajeno_visible_para_estudiante_inscrito():
    repo = LaboratorioRepository()
    lab = _crear_lab_con_secciones(
        repo,
        estado=EstadoLaboratorio.PUBLICADO,
        tipo=TipoLaboratorio.PERSONALIZADO,
        instructor_id=uuid.uuid4(),
    )

    detalle = ObtenerDetalleLaboratorioQuery(repo, _FakeInscripcion()).execute(
        lab.id, estudiante_id=uuid.uuid4()
    )

    assert detalle.id == lab.id


@pytest.mark.django_db
def test_detalle_personalizado_ajeno_sigue_oculto_sin_inscripcion_vigente():
    repo = LaboratorioRepository()
    lab = _crear_lab_con_secciones(
        repo,
        estado=EstadoLaboratorio.PUBLICADO,
        tipo=TipoLaboratorio.PERSONALIZADO,
        instructor_id=uuid.uuid4(),
    )

    with pytest.raises(NotFoundError):
        ObtenerDetalleLaboratorioQuery(repo, _FakeSinInscripcion()).execute(
            lab.id, estudiante_id=uuid.uuid4()
        )


@pytest.mark.django_db
def test_toc_personalizado_ajeno_visible_para_estudiante_inscrito():
    repo = LaboratorioRepository()
    lab = _crear_lab_con_secciones(
        repo,
        estado=EstadoLaboratorio.PUBLICADO,
        tipo=TipoLaboratorio.PERSONALIZADO,
        instructor_id=uuid.uuid4(),
    )

    toc = ObtenerTOCQuery(repo, _FakeInscripcion()).execute(lab.id, estudiante_id=uuid.uuid4())

    assert len(toc.secciones) == 2
