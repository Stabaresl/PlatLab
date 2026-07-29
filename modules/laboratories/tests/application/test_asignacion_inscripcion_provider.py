import uuid

import pytest

from modules.assignments.domain.entities import Asignacion
from modules.assignments.infrastructure.repositories import AsignacionRepository
from modules.laboratories.infrastructure.asignacion_inscripcion_provider import (
    AsignacionInscripcionProvider,
)


@pytest.mark.django_db
def test_esta_inscrito_true_con_asignacion_vigente():
    estudiante_id = uuid.uuid4()
    laboratorio_id = uuid.uuid4()
    AsignacionRepository().add(
        Asignacion(
            estudiante_id=estudiante_id, laboratorio_id=laboratorio_id, instructor_id=uuid.uuid4()
        )
    )

    provider = AsignacionInscripcionProvider()

    assert provider.esta_inscrito(estudiante_id, laboratorio_id) is True


@pytest.mark.django_db
def test_esta_inscrito_false_sin_asignacion():
    provider = AsignacionInscripcionProvider()

    assert provider.esta_inscrito(uuid.uuid4(), uuid.uuid4()) is False
