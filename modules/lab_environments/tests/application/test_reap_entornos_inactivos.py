import time
import uuid
from datetime import datetime, timedelta, timezone

import pytest

from modules.lab_environments.application.use_cases.reap_entornos_inactivos import (
    ReapEntornosInactivosUseCase,
)
from modules.lab_environments.domain.entities import EntornoActivo
from modules.lab_environments.domain.value_objects import EstadoEntorno
from modules.lab_environments.infrastructure.models import EntornoActivoModel
from modules.lab_environments.infrastructure.repositories import EntornoRepository
from modules.lab_environments.tests.application.test_iniciar_detener_entorno import (
    FakeContenedorProvider,
)
from modules.shared.infrastructure.unit_of_work import BaseUnitOfWork


def _crear_entorno_con_actividad_hace(minutos: float) -> EntornoActivo:
    repo = EntornoRepository()
    entorno = repo.add(
        EntornoActivo(
            seccion_id=uuid.uuid4(),
            progreso_id=uuid.uuid4(),
            estudiante_id=uuid.uuid4(),
            container_id=f"c-{uuid.uuid4()}",
            estado=EstadoEntorno.ACTIVO,
        )
    )
    # `ultima_actividad`/`fecha_inicio` son `auto_now`/`auto_now_add` —
    # se pisan directo en el modelo para simular el paso del tiempo sin
    # depender de sleeps largos en el test.
    pasado = datetime.now(timezone.utc) - timedelta(minutes=minutos)
    EntornoActivoModel.objects.filter(id=entorno.id).update(
        ultima_actividad=pasado, fecha_inicio=pasado
    )
    return repo.get_by_id(entorno.id)


@pytest.mark.django_db
def test_reap_apaga_entorno_inactivo():
    _crear_entorno_con_actividad_hace(30)
    provider = FakeContenedorProvider()
    uc = ReapEntornosInactivosUseCase(
        unit_of_work=BaseUnitOfWork(),
        entorno_repository=EntornoRepository(),
        contenedor_provider=provider,
        idle_timeout_minutos=20,
        max_lifetime_minutos=120,
    )

    apagados = uc.execute()

    assert apagados == 1
    assert len(provider.detenidos) == 1


@pytest.mark.django_db
def test_reap_no_toca_entornos_recientes():
    _crear_entorno_con_actividad_hace(1)
    provider = FakeContenedorProvider()
    uc = ReapEntornosInactivosUseCase(
        unit_of_work=BaseUnitOfWork(),
        entorno_repository=EntornoRepository(),
        contenedor_provider=provider,
        idle_timeout_minutos=20,
        max_lifetime_minutos=120,
    )

    apagados = uc.execute()

    assert apagados == 0
    assert provider.detenidos == []


@pytest.mark.django_db
def test_reap_apaga_por_vida_maxima_aunque_este_activo():
    entorno = _crear_entorno_con_actividad_hace(1)
    # fuerza fecha_inicio muy vieja sin tocar ultima_actividad (reciente)
    EntornoActivoModel.objects.filter(id=entorno.id).update(
        fecha_inicio=datetime.now(timezone.utc) - timedelta(minutes=200)
    )
    provider = FakeContenedorProvider()
    uc = ReapEntornosInactivosUseCase(
        unit_of_work=BaseUnitOfWork(),
        entorno_repository=EntornoRepository(),
        contenedor_provider=provider,
        idle_timeout_minutos=20,
        max_lifetime_minutos=120,
    )

    apagados = uc.execute()

    assert apagados == 1
