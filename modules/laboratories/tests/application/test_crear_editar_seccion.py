import uuid

import pytest

from modules.laboratories.application.dtos import CrearSeccionDTO, EditarSeccionDTO
from modules.laboratories.application.use_cases.crear_seccion import CrearSeccionUseCase
from modules.laboratories.application.use_cases.editar_seccion import EditarSeccionUseCase
from modules.laboratories.domain.entities import Laboratorio, Seccion
from modules.laboratories.domain.value_objects import (
    ComandoSimulado,
    EntornoPractica,
    EstadoLaboratorio,
    NivelDificultad,
    PasoGuia,
    TipoLaboratorio,
)
from modules.laboratories.domain.exceptions import ImagenPracticaNoPermitidaError
from modules.laboratories.infrastructure.repositories import LaboratorioRepository
from modules.shared.domain.exceptions import ConflictError, ForbiddenError, NotFoundError
from modules.shared.infrastructure.event_dispatcher import EventDispatcher
from modules.shared.infrastructure.unit_of_work import BaseUnitOfWork


def _crear_uc():
    return CrearSeccionUseCase(
        unit_of_work=BaseUnitOfWork(),
        event_dispatcher=EventDispatcher(),
        laboratorio_repository=LaboratorioRepository(),
    )


def _editar_uc():
    return EditarSeccionUseCase(
        unit_of_work=BaseUnitOfWork(),
        event_dispatcher=EventDispatcher(),
        laboratorio_repository=LaboratorioRepository(),
    )


def _crear_lab_personalizado(instructor_id: uuid.UUID) -> Laboratorio:
    return LaboratorioRepository().add(
        Laboratorio(
            nombre="Lab Seccion",
            descripcion="desc",
            nivel_dificultad=NivelDificultad.BASICO,
            estado=EstadoLaboratorio.BORRADOR,
            tipo=TipoLaboratorio.PERSONALIZADO,
            instructor_id=instructor_id,
        )
    )


@pytest.mark.django_db
def test_crear_seccion_instructor_dueno_sanitiza_contenido():
    instructor_id = uuid.uuid4()
    lab = _crear_lab_personalizado(instructor_id)

    resultado = _crear_uc().execute(
        CrearSeccionDTO(
            laboratorio_id=lab.id,
            titulo="Intro",
            contenido_teorico="<p>hola</p><script>alert(1)</script>",
            orden=1,
            actor_id=instructor_id,
            actor_rol="instructor",
        )
    )

    guardada = LaboratorioRepository().get_seccion_by_id(resultado.id)
    assert "<script>" not in guardada.contenido_teorico
    assert "<p>hola</p>" in guardada.contenido_teorico


@pytest.mark.django_db
def test_crear_seccion_instructor_ajeno_lanza_forbidden():
    lab = _crear_lab_personalizado(uuid.uuid4())

    with pytest.raises(ForbiddenError):
        _crear_uc().execute(
            CrearSeccionDTO(
                laboratorio_id=lab.id,
                titulo="Intro",
                contenido_teorico="...",
                orden=1,
                actor_id=uuid.uuid4(),
                actor_rol="instructor",
            )
        )


@pytest.mark.django_db
def test_crear_seccion_orden_duplicado_lanza_conflict():
    instructor_id = uuid.uuid4()
    lab = _crear_lab_personalizado(instructor_id)
    _crear_uc().execute(
        CrearSeccionDTO(
            laboratorio_id=lab.id,
            titulo="Uno",
            contenido_teorico="...",
            orden=1,
            actor_id=instructor_id,
            actor_rol="instructor",
        )
    )

    with pytest.raises(ConflictError):
        _crear_uc().execute(
            CrearSeccionDTO(
                laboratorio_id=lab.id,
                titulo="Dos",
                contenido_teorico="...",
                orden=1,
                actor_id=instructor_id,
                actor_rol="instructor",
            )
        )


@pytest.mark.django_db
def test_crear_seccion_laboratorio_inexistente_lanza_not_found():
    with pytest.raises(NotFoundError):
        _crear_uc().execute(
            CrearSeccionDTO(
                laboratorio_id=uuid.uuid4(),
                titulo="x",
                contenido_teorico="...",
                orden=1,
                actor_id=uuid.uuid4(),
                actor_rol="instructor",
            )
        )


@pytest.mark.django_db
def test_editar_seccion_sanitiza_y_actualiza_campos():
    instructor_id = uuid.uuid4()
    lab = _crear_lab_personalizado(instructor_id)
    lab_repo = LaboratorioRepository()
    seccion = lab_repo.add_seccion(
        Seccion(
            laboratorio_id=lab.id,
            titulo="Original",
            contenido_teorico="original",
            orden=1,
        )
    )

    resultado = _editar_uc().execute(
        EditarSeccionDTO(
            laboratorio_id=lab.id,
            seccion_id=seccion.id,
            actor_id=instructor_id,
            actor_rol="instructor",
            titulo="Nuevo",
            contenido_teorico="<b>bold</b><script>x()</script>",
        )
    )

    assert resultado.titulo == "Nuevo"
    guardada = lab_repo.get_seccion_by_id(seccion.id)
    assert "<script>" not in guardada.contenido_teorico


@pytest.mark.django_db
def test_editar_seccion_orden_duplicado_con_otra_seccion_lanza_conflict():
    instructor_id = uuid.uuid4()
    lab = _crear_lab_personalizado(instructor_id)
    lab_repo = LaboratorioRepository()
    lab_repo.add_seccion(
        Seccion(laboratorio_id=lab.id, titulo="Uno", contenido_teorico="...", orden=1)
    )
    seccion_dos = lab_repo.add_seccion(
        Seccion(laboratorio_id=lab.id, titulo="Dos", contenido_teorico="...", orden=2)
    )

    with pytest.raises(ConflictError):
        _editar_uc().execute(
            EditarSeccionDTO(
                laboratorio_id=lab.id,
                seccion_id=seccion_dos.id,
                actor_id=instructor_id,
                actor_rol="instructor",
                orden=1,
            )
        )


@pytest.mark.django_db
def test_editar_seccion_inexistente_lanza_not_found():
    instructor_id = uuid.uuid4()
    lab = _crear_lab_personalizado(instructor_id)

    with pytest.raises(NotFoundError):
        _editar_uc().execute(
            EditarSeccionDTO(
                laboratorio_id=lab.id,
                seccion_id=uuid.uuid4(),
                actor_id=instructor_id,
                actor_rol="instructor",
                titulo="x",
            )
        )


@pytest.mark.django_db
def test_crear_seccion_persiste_guia_por_pasos_objetivos_y_entorno_practica():
    instructor_id = uuid.uuid4()
    lab = _crear_lab_personalizado(instructor_id)
    entorno = EntornoPractica(
        prompt="root@target:~#",
        banner="Bienvenido",
        comandos=[ComandoSimulado(comando="ls", salida="login.php")],
    )

    resultado = _crear_uc().execute(
        CrearSeccionDTO(
            laboratorio_id=lab.id,
            titulo="Practica",
            contenido_teorico="...",
            orden=1,
            actor_id=instructor_id,
            actor_rol="instructor",
            tiene_practica=True,
            objetivos=["Objetivo uno", "Objetivo dos"],
            duracion_estimada_minutos=30,
            pasos_guia=[
                PasoGuia(
                    orden=1,
                    titulo="Paso 1",
                    instrucciones="<p>Hacé esto</p><script>alert(1)</script>",
                    comando_sugerido="ls -la",
                ),
            ],
            entorno_practica=entorno,
        )
    )

    guardada = LaboratorioRepository().get_seccion_by_id(resultado.id)
    assert guardada.objetivos == ["Objetivo uno", "Objetivo dos"]
    assert guardada.duracion_estimada_minutos == 30
    assert len(guardada.pasos_guia) == 1
    assert "<script>" not in guardada.pasos_guia[0].instrucciones
    assert "<p>Hacé esto</p>" in guardada.pasos_guia[0].instrucciones
    assert guardada.pasos_guia[0].comando_sugerido == "ls -la"
    assert guardada.entorno_practica.prompt == "root@target:~#"
    assert guardada.entorno_practica.comandos[0].comando == "ls"
    assert guardada.entorno_practica.comandos[0].salida == "login.php"


@pytest.mark.django_db
def test_editar_seccion_actualiza_pasos_guia_sanitizando():
    instructor_id = uuid.uuid4()
    lab = _crear_lab_personalizado(instructor_id)
    lab_repo = LaboratorioRepository()
    seccion = lab_repo.add_seccion(
        Seccion(laboratorio_id=lab.id, titulo="Practica", contenido_teorico="...", orden=1)
    )

    _editar_uc().execute(
        EditarSeccionDTO(
            laboratorio_id=lab.id,
            seccion_id=seccion.id,
            actor_id=instructor_id,
            actor_rol="instructor",
            pasos_guia=[
                PasoGuia(
                    orden=1,
                    titulo="Paso nuevo",
                    instrucciones="<p>ok</p><script>x()</script>",
                ),
            ],
        )
    )

    guardada = lab_repo.get_seccion_by_id(seccion.id)
    assert len(guardada.pasos_guia) == 1
    assert "<script>" not in guardada.pasos_guia[0].instrucciones


@pytest.mark.django_db
def test_editar_seccion_actualiza_entorno_practica():
    instructor_id = uuid.uuid4()
    lab = _crear_lab_personalizado(instructor_id)
    lab_repo = LaboratorioRepository()
    seccion = lab_repo.add_seccion(
        Seccion(laboratorio_id=lab.id, titulo="Practica", contenido_teorico="...", orden=1)
    )
    nuevo_entorno = EntornoPractica(
        comandos=[ComandoSimulado(comando="whoami", salida="root")]
    )

    _editar_uc().execute(
        EditarSeccionDTO(
            laboratorio_id=lab.id,
            seccion_id=seccion.id,
            actor_id=instructor_id,
            actor_rol="instructor",
            entorno_practica=nuevo_entorno,
        )
    )

    guardada = lab_repo.get_seccion_by_id(seccion.id)
    assert guardada.entorno_practica.comandos[0].comando == "whoami"


@pytest.mark.django_db
def test_editar_seccion_administrador_no_puede_editar_personalizado():
    instructor_id = uuid.uuid4()
    lab = _crear_lab_personalizado(instructor_id)
    lab_repo = LaboratorioRepository()
    seccion = lab_repo.add_seccion(
        Seccion(laboratorio_id=lab.id, titulo="Uno", contenido_teorico="...", orden=1)
    )

    with pytest.raises(ForbiddenError):
        _editar_uc().execute(
            EditarSeccionDTO(
                laboratorio_id=lab.id,
                seccion_id=seccion.id,
                actor_id=uuid.uuid4(),
                actor_rol="administrador",
                titulo="x",
            )
        )


@pytest.mark.django_db
def test_crear_seccion_rechaza_imagen_practica_fuera_de_la_allowlist():
    instructor_id = uuid.uuid4()
    lab = _crear_lab_personalizado(instructor_id)

    with pytest.raises(ImagenPracticaNoPermitidaError):
        _crear_uc().execute(
            CrearSeccionDTO(
                laboratorio_id=lab.id,
                titulo="Practica",
                contenido_teorico="...",
                orden=1,
                actor_id=instructor_id,
                actor_rol="instructor",
                imagen_practica="cualquier/imagen-arbitraria:latest",
            )
        )


@pytest.mark.django_db
def test_crear_seccion_acepta_imagen_practica_de_la_allowlist():
    instructor_id = uuid.uuid4()
    lab = _crear_lab_personalizado(instructor_id)

    resultado = _crear_uc().execute(
        CrearSeccionDTO(
            laboratorio_id=lab.id,
            titulo="Practica",
            contenido_teorico="...",
            orden=1,
            actor_id=instructor_id,
            actor_rol="instructor",
            imagen_practica="platlab-target-sqli:latest",
        )
    )

    guardada = LaboratorioRepository().get_seccion_by_id(resultado.id)
    assert guardada.imagen_practica == "platlab-target-sqli:latest"


@pytest.mark.django_db
def test_editar_seccion_rechaza_imagen_practica_fuera_de_la_allowlist():
    instructor_id = uuid.uuid4()
    lab = _crear_lab_personalizado(instructor_id)
    lab_repo = LaboratorioRepository()
    seccion = lab_repo.add_seccion(
        Seccion(laboratorio_id=lab.id, titulo="Practica", contenido_teorico="...", orden=1)
    )

    with pytest.raises(ImagenPracticaNoPermitidaError):
        _editar_uc().execute(
            EditarSeccionDTO(
                laboratorio_id=lab.id,
                seccion_id=seccion.id,
                actor_id=instructor_id,
                actor_rol="instructor",
                imagen_practica="otra/imagen-cualquiera:v1",
            )
        )
