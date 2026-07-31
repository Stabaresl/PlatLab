import uuid

import pytest

from modules.laboratories.application.dtos import CrearLaboratorioDTO, EditarLaboratorioDTO
from modules.laboratories.application.use_cases.crear_laboratorio import CrearLaboratorioUseCase
from modules.laboratories.application.use_cases.editar_laboratorio import EditarLaboratorioUseCase
from modules.laboratories.domain.entities import Laboratorio
from modules.laboratories.domain.exceptions import CannotEditPredeterminadoError
from modules.laboratories.domain.value_objects import (
    EstadoLaboratorio,
    NivelDificultad,
    TipoLaboratorio,
)
from modules.laboratories.infrastructure.repositories import LaboratorioRepository
from modules.shared.domain.exceptions import ForbiddenError, ValidationError
from modules.shared.infrastructure.event_dispatcher import EventDispatcher
from modules.shared.infrastructure.unit_of_work import BaseUnitOfWork


def _crear_uc():
    return CrearLaboratorioUseCase(
        unit_of_work=BaseUnitOfWork(),
        event_dispatcher=EventDispatcher(),
        laboratorio_repository=LaboratorioRepository(),
    )


def _editar_uc():
    return EditarLaboratorioUseCase(
        unit_of_work=BaseUnitOfWork(),
        event_dispatcher=EventDispatcher(),
        laboratorio_repository=LaboratorioRepository(),
    )


@pytest.mark.django_db
def test_crear_laboratorio_instructor_crea_personalizado_propio():
    instructor_id = uuid.uuid4()

    resultado = _crear_uc().execute(
        CrearLaboratorioDTO(
            nombre="Lab Nuevo",
            descripcion="desc",
            nivel_dificultad="basico",
            actor_id=instructor_id,
            actor_rol="instructor",
            resumen_cierre="<p>Cierre</p><script>alert(1)</script>",
        )
    )

    assert resultado.estado == "borrador"
    assert resultado.tipo == "personalizado"
    guardado = LaboratorioRepository().get_by_id(resultado.id)
    assert guardado.instructor_id == instructor_id
    assert "<script>" not in guardado.resumen_cierre
    assert "<p>Cierre</p>" in guardado.resumen_cierre


@pytest.mark.django_db
def test_crear_laboratorio_administrador_crea_predeterminado_sin_dueno():
    resultado = _crear_uc().execute(
        CrearLaboratorioDTO(
            nombre="Lab Admin",
            descripcion="desc",
            nivel_dificultad="basico",
            actor_id=uuid.uuid4(),
            actor_rol="administrador",
        )
    )

    assert resultado.tipo == "predeterminado"
    guardado = LaboratorioRepository().get_by_id(resultado.id)
    assert guardado.instructor_id is None


@pytest.mark.django_db
def test_crear_laboratorio_estudiante_lanza_forbidden():
    with pytest.raises(ForbiddenError):
        _crear_uc().execute(
            CrearLaboratorioDTO(
                nombre="Lab",
                descripcion="desc",
                nivel_dificultad="basico",
                actor_id=uuid.uuid4(),
                actor_rol="estudiante",
            )
        )


@pytest.mark.django_db
def test_crear_laboratorio_dificultad_invalida_lanza_validation_error():
    with pytest.raises(ValidationError):
        _crear_uc().execute(
            CrearLaboratorioDTO(
                nombre="Lab",
                descripcion="desc",
                nivel_dificultad="invalida",
                actor_id=uuid.uuid4(),
                actor_rol="instructor",
            )
        )


@pytest.mark.django_db
def test_editar_laboratorio_instructor_dueno_actualiza_metadatos():
    instructor_id = uuid.uuid4()
    repo = LaboratorioRepository()
    lab = repo.add(
        Laboratorio(
            nombre="Original",
            descripcion="desc",
            nivel_dificultad=NivelDificultad.BASICO,
            estado=EstadoLaboratorio.BORRADOR,
            tipo=TipoLaboratorio.PERSONALIZADO,
            instructor_id=instructor_id,
        )
    )

    resultado = _editar_uc().execute(
        EditarLaboratorioDTO(
            laboratorio_id=lab.id,
            actor_id=instructor_id,
            actor_rol="instructor",
            nombre="Editado",
            resumen_cierre="<p>Nuevo cierre</p><script>x()</script>",
        )
    )

    assert resultado.nombre == "Editado"
    guardado = repo.get_by_id(lab.id)
    assert "<script>" not in guardado.resumen_cierre
    assert "<p>Nuevo cierre</p>" in guardado.resumen_cierre


@pytest.mark.django_db
def test_editar_laboratorio_instructor_ajeno_lanza_forbidden():
    repo = LaboratorioRepository()
    lab = repo.add(
        Laboratorio(
            nombre="Original",
            descripcion="desc",
            nivel_dificultad=NivelDificultad.BASICO,
            estado=EstadoLaboratorio.BORRADOR,
            tipo=TipoLaboratorio.PERSONALIZADO,
            instructor_id=uuid.uuid4(),
        )
    )

    with pytest.raises(ForbiddenError):
        _editar_uc().execute(
            EditarLaboratorioDTO(
                laboratorio_id=lab.id,
                actor_id=uuid.uuid4(),
                actor_rol="instructor",
                nombre="Hackeado",
            )
        )


@pytest.mark.django_db
def test_editar_laboratorio_instructor_no_puede_editar_predeterminado():
    repo = LaboratorioRepository()
    lab = repo.add(
        Laboratorio(
            nombre="Predeterminado",
            descripcion="desc",
            nivel_dificultad=NivelDificultad.BASICO,
            estado=EstadoLaboratorio.PUBLICADO,
            tipo=TipoLaboratorio.PREDETERMINADO,
        )
    )

    with pytest.raises(CannotEditPredeterminadoError):
        _editar_uc().execute(
            EditarLaboratorioDTO(
                laboratorio_id=lab.id,
                actor_id=uuid.uuid4(),
                actor_rol="instructor",
                nombre="x",
            )
        )


@pytest.mark.django_db
def test_editar_laboratorio_administrador_no_puede_editar_personalizado():
    repo = LaboratorioRepository()
    lab = repo.add(
        Laboratorio(
            nombre="Personalizado",
            descripcion="desc",
            nivel_dificultad=NivelDificultad.BASICO,
            estado=EstadoLaboratorio.BORRADOR,
            tipo=TipoLaboratorio.PERSONALIZADO,
            instructor_id=uuid.uuid4(),
        )
    )

    with pytest.raises(ForbiddenError):
        _editar_uc().execute(
            EditarLaboratorioDTO(
                laboratorio_id=lab.id,
                actor_id=uuid.uuid4(),
                actor_rol="administrador",
                nombre="x",
            )
        )


@pytest.mark.django_db
def test_editar_laboratorio_administrador_edita_predeterminado():
    repo = LaboratorioRepository()
    lab = repo.add(
        Laboratorio(
            nombre="Predeterminado",
            descripcion="desc",
            nivel_dificultad=NivelDificultad.BASICO,
            estado=EstadoLaboratorio.BORRADOR,
            tipo=TipoLaboratorio.PREDETERMINADO,
        )
    )

    resultado = _editar_uc().execute(
        EditarLaboratorioDTO(
            laboratorio_id=lab.id,
            actor_id=uuid.uuid4(),
            actor_rol="administrador",
            nombre="Editado por Admin",
        )
    )

    assert resultado.nombre == "Editado por Admin"
