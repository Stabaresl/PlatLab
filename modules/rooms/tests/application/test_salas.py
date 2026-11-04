import uuid
from datetime import timedelta

import pytest

from modules.assignments.infrastructure.repositories import AsignacionRepository
from modules.gamification.infrastructure.repositories import (
    PerfilJugadorRepository,
    RecompensaSalaRepository,
)
from modules.laboratories.domain.entities import Laboratorio, Seccion
from modules.laboratories.domain.value_objects import (
    EstadoLaboratorio,
    NivelDificultad,
    TipoLaboratorio,
)
from modules.laboratories.infrastructure.repositories import LaboratorioRepository
from modules.progress.domain.events import ExamGraded, LabCompleted
from modules.progress.infrastructure.repositories import ProgresoRepository
from modules.rooms.application.dtos import CambiarEstadoSalaDTO, CrearSalaDTO, UnirseSalaDTO
from modules.rooms.application.queries.detalle_sala import DetalleSalaQuery, VistaPreviaSalaQuery
from modules.rooms.application.queries.listar_salas import ListarLaboratoriosParaSalaQuery, ListarSalasQuery
from modules.rooms.application.use_cases.cambiar_estado_sala import CambiarEstadoSalaUseCase
from modules.rooms.application.use_cases.crear_sala import CrearSalaUseCase
from modules.rooms.application.use_cases.unirse_sala import UnirseSalaUseCase
from modules.rooms.domain.exceptions import SalaLlenaError, SalaNoEncontradaError, SalaSinIngresosError
from modules.rooms.infrastructure.repositories import ParticipanteSalaRepository, SalaRepository
from modules.shared.domain.exceptions import (
    BusinessRuleViolationError,
    ForbiddenError,
    NotFoundError,
    ValidationError,
)
from modules.shared.domain.tiempo import ahora_utc
from modules.shared.infrastructure.event_dispatcher import EventDispatcher
from modules.shared.infrastructure.unit_of_work import BaseUnitOfWork
from modules.users.domain.entities import User
from modules.users.domain.value_objects import Email, Rol
from modules.users.infrastructure.repositories import UserRepository


def _usuario(rol: Rol, nombre: str = "Persona") -> User:
    return UserRepository().add(User(email=Email(f"{uuid.uuid4().hex[:10]}@uni.edu"), nombre_completo=nombre, rol=rol))


def _lab(secciones: int = 2, **overrides) -> Laboratorio:
    datos = dict(
        nombre=f"Lab {uuid.uuid4().hex[:6]}",
        descripcion="desc",
        nivel_dificultad=NivelDificultad.BASICO,
        estado=EstadoLaboratorio.PUBLICADO,
        tipo=TipoLaboratorio.PREDETERMINADO,
    )
    datos.update(overrides)
    repo = LaboratorioRepository()
    lab = repo.add(Laboratorio(**datos))
    for orden in range(1, secciones + 1):
        repo.add_seccion(Seccion(laboratorio_id=lab.id, titulo=f"S{orden}", contenido_teorico="<p>x</p>", orden=orden))
    return lab


def _crear(anfitrion: User, lab: Laboratorio, **kw):
    return CrearSalaUseCase(
        unit_of_work=BaseUnitOfWork(),
        event_dispatcher=EventDispatcher(),
        sala_repository=SalaRepository(),
        laboratorio_repository=LaboratorioRepository(),
        user_repository=UserRepository(),
    ).execute(
        CrearSalaDTO(
            actor_id=anfitrion.id,
            actor_rol=anfitrion.rol.value,
            nombre=kw.pop("nombre", "Sala de prueba"),
            laboratorio_id=lab.id,
            **kw,
        )
    )


def _unirse(estudiante: User, codigo: str):
    return UnirseSalaUseCase(
        unit_of_work=BaseUnitOfWork(),
        event_dispatcher=EventDispatcher(),
        sala_repository=SalaRepository(),
        participante_repository=ParticipanteSalaRepository(),
        asignacion_repository=AsignacionRepository(),
        laboratorio_repository=LaboratorioRepository(),
        progreso_repository=ProgresoRepository(),
    ).execute(UnirseSalaDTO(actor_id=estudiante.id, actor_rol="estudiante", codigo=codigo))


def _detalle(sala_id, actor: User):
    return DetalleSalaQuery(
        SalaRepository(), ParticipanteSalaRepository(), LaboratorioRepository(), ProgresoRepository(), UserRepository()
    ).execute(sala_id=sala_id, actor_id=actor.id, actor_rol=actor.rol.value)


def _terminar(asignacion_id, puntaje: float = 90.0):
    """Simula el examen aprobado de esa asignación (el listener de Rooms reparte el puesto)."""
    progreso = ProgresoRepository().get_by_asignacion(asignacion_id)
    EventDispatcher().dispatch(ExamGraded(progreso_id=progreso.id, examen_id=uuid.uuid4(), puntaje=puntaje))


# --- Crear --------------------------------------------------------------------


@pytest.mark.django_db
def test_instructor_crea_sala_con_codigo_de_6_caracteres():
    instructor = _usuario(Rol.INSTRUCTOR, "Profe Ana")
    sala = _crear(instructor, _lab(), capacidad=40)

    assert len(sala.codigo) == 6 and sala.codigo.isalnum()
    assert sala.capacidad == 40
    assert sala.estado == "abierta"
    assert sala.anfitrion_nombre == "Profe Ana"


@pytest.mark.django_db
def test_estudiante_no_puede_crear_salas():
    with pytest.raises(ForbiddenError):
        _crear(_usuario(Rol.ESTUDIANTE), _lab())


@pytest.mark.django_db
def test_no_se_crea_sala_sobre_lab_sin_publicar_ni_personalizado_ajeno():
    instructor = _usuario(Rol.INSTRUCTOR)
    with pytest.raises(NotFoundError):
        _crear(instructor, _lab(estado=EstadoLaboratorio.BORRADOR))
    ajeno = _lab(tipo=TipoLaboratorio.PERSONALIZADO, instructor_id=uuid.uuid4())
    with pytest.raises(NotFoundError):
        _crear(instructor, ajeno)
    # un admin sí puede usar el personalizado de otro instructor
    assert _crear(_usuario(Rol.ADMINISTRADOR), ajeno).laboratorio_id == ajeno.id


@pytest.mark.django_db
def test_capacidad_fuera_de_rango_y_fecha_pasada_se_rechazan():
    instructor = _usuario(Rol.INSTRUCTOR)
    with pytest.raises(ValidationError):
        _crear(instructor, _lab(), capacidad=101)
    with pytest.raises(ValidationError):
        _crear(instructor, _lab(), fecha_fin=ahora_utc() - timedelta(hours=1))


@pytest.mark.django_db
def test_laboratorios_disponibles_para_sala_respeta_alcance():
    instructor = _usuario(Rol.INSTRUCTOR)
    propio = _lab(tipo=TipoLaboratorio.PERSONALIZADO, instructor_id=instructor.id)
    ajeno = _lab(tipo=TipoLaboratorio.PERSONALIZADO, instructor_id=uuid.uuid4())
    sin_secciones = _lab(secciones=0)

    ids = {
        lab.id for lab in ListarLaboratoriosParaSalaQuery(LaboratorioRepository()).execute(instructor.id, "instructor")
    }

    assert propio.id in ids
    assert ajeno.id not in ids
    assert sin_secciones.id not in ids


# --- Unirse -------------------------------------------------------------------


@pytest.mark.django_db
def test_estudiante_se_une_con_codigo_y_recibe_su_propia_asignacion():
    instructor = _usuario(Rol.INSTRUCTOR)
    lab = _lab()
    sala = _crear(instructor, lab)
    a, b = _usuario(Rol.ESTUDIANTE), _usuario(Rol.ESTUDIANTE)

    ra = _unirse(a, sala.codigo.lower()[:3] + "-" + sala.codigo.lower()[3:])  # como lo dicte el profe
    rb = _unirse(b, sala.codigo)

    assert ra.asignacion_id != rb.asignacion_id
    asignacion = AsignacionRepository().get_by_id(ra.asignacion_id)
    assert asignacion.estado.value == "activa"
    assert asignacion.instructor_id == instructor.id
    secciones = ProgresoRepository().get_secciones(ProgresoRepository().get_by_asignacion(ra.asignacion_id).id)
    assert sorted(s.estado.value for s in secciones) == ["bloqueada", "en_progreso"]


@pytest.mark.django_db
def test_unirse_dos_veces_es_idempotente():
    sala = _crear(_usuario(Rol.INSTRUCTOR), _lab())
    est = _usuario(Rol.ESTUDIANTE)
    primero = _unirse(est, sala.codigo)
    segundo = _unirse(est, sala.codigo)

    assert segundo.ya_era_participante is True
    assert segundo.asignacion_id == primero.asignacion_id
    assert ParticipanteSalaRepository().contar(sala.id) == 1


@pytest.mark.django_db
def test_codigo_inexistente_sala_llena_y_sala_cerrada():
    with pytest.raises(SalaNoEncontradaError):
        _unirse(_usuario(Rol.ESTUDIANTE), "ZZZZZZ")

    instructor = _usuario(Rol.INSTRUCTOR)
    llena = _crear(instructor, _lab(), capacidad=1)
    _unirse(_usuario(Rol.ESTUDIANTE), llena.codigo)
    with pytest.raises(SalaLlenaError):
        _unirse(_usuario(Rol.ESTUDIANTE), llena.codigo)

    cerrada = _crear(instructor, _lab())
    CambiarEstadoSalaUseCase(BaseUnitOfWork(), EventDispatcher(), SalaRepository()).execute(
        CambiarEstadoSalaDTO(sala_id=cerrada.id, actor_id=instructor.id, actor_rol="instructor", estado="cerrada")
    )
    with pytest.raises(SalaSinIngresosError):
        _unirse(_usuario(Rol.ESTUDIANTE), cerrada.codigo)


@pytest.mark.django_db
def test_reutiliza_asignacion_vigente_del_mismo_laboratorio():
    lab = _lab()
    est = _usuario(Rol.ESTUDIANTE)
    sala1 = _crear(_usuario(Rol.INSTRUCTOR), lab)
    sala2 = _crear(_usuario(Rol.INSTRUCTOR), lab)

    r1 = _unirse(est, sala1.codigo)
    r2 = _unirse(est, sala2.codigo)

    assert r1.asignacion_id == r2.asignacion_id


@pytest.mark.django_db
def test_solo_estudiantes_se_unen():
    sala = _crear(_usuario(Rol.INSTRUCTOR), _lab())
    instructor = _usuario(Rol.INSTRUCTOR)
    with pytest.raises(ForbiddenError):
        UnirseSalaUseCase(
            BaseUnitOfWork(),
            EventDispatcher(),
            SalaRepository(),
            ParticipanteSalaRepository(),
            AsignacionRepository(),
            LaboratorioRepository(),
            ProgresoRepository(),
        ).execute(UnirseSalaDTO(actor_id=instructor.id, actor_rol="instructor", codigo=sala.codigo))


# --- Tablero, puestos y recompensas -------------------------------------------


@pytest.mark.django_db
def test_puestos_por_orden_de_llegada_con_bono_de_xp_y_logro():
    instructor = _usuario(Rol.INSTRUCTOR)
    sala = _crear(instructor, _lab(), nombre="Reto SQLi")
    a, b, c = (_usuario(Rol.ESTUDIANTE, n) for n in ("Ana", "Beto", "Caro"))
    ra, rb, _rc = (_unirse(e, sala.codigo) for e in (a, b, c))

    _terminar(rb.asignacion_id)  # Beto llega primero
    _terminar(ra.asignacion_id)
    _terminar(ra.asignacion_id)  # reintento del examen: no da otro puesto
    _terminar(_rc.asignacion_id, puntaje=40)  # Caro no aprobó: no termina

    tablero = _detalle(sala.id, instructor)
    assert [(p.nombre, p.posicion_final) for p in tablero.participantes] == [("Beto", 1), ("Ana", 2), ("Caro", None)]
    assert tablero.sala.completados == 2

    recompensas = RecompensaSalaRepository()
    assert recompensas.contar_primeros_puestos(b.id) == 1
    assert recompensas.contar_por_estudiante(a.id) == 1
    assert PerfilJugadorRepository().get_by_estudiante(b.id).xp >= 150


@pytest.mark.django_db
def test_lab_sin_examen_cuenta_al_terminar_las_secciones():
    sala = _crear(_usuario(Rol.INSTRUCTOR), _lab(secciones=1))
    est = _usuario(Rol.ESTUDIANTE)
    r = _unirse(est, sala.codigo)

    progreso = ProgresoRepository().get_by_asignacion(r.asignacion_id)
    EventDispatcher().dispatch(LabCompleted(progreso_id=progreso.id))

    assert ParticipanteSalaRepository().get(sala.id, est.id).posicion_final == 1


@pytest.mark.django_db
def test_sala_finalizada_no_reparte_puestos_ni_se_reabre():
    instructor = _usuario(Rol.INSTRUCTOR)
    sala = _crear(instructor, _lab())
    est = _usuario(Rol.ESTUDIANTE)
    r = _unirse(est, sala.codigo)
    uc = CambiarEstadoSalaUseCase(BaseUnitOfWork(), EventDispatcher(), SalaRepository())
    uc.execute(
        CambiarEstadoSalaDTO(sala_id=sala.id, actor_id=instructor.id, actor_rol="instructor", estado="finalizada")
    )

    _terminar(r.asignacion_id)

    assert ParticipanteSalaRepository().get(sala.id, est.id).posicion_final is None
    with pytest.raises(BusinessRuleViolationError):
        uc.execute(
            CambiarEstadoSalaDTO(sala_id=sala.id, actor_id=instructor.id, actor_rol="instructor", estado="abierta")
        )


@pytest.mark.django_db
def test_tablero_solo_para_anfitrion_admin_o_participantes():
    instructor = _usuario(Rol.INSTRUCTOR)
    sala = _crear(instructor, _lab())
    est = _usuario(Rol.ESTUDIANTE)
    _unirse(est, sala.codigo)

    assert _detalle(sala.id, est).participantes[0].es_yo is True
    assert _detalle(sala.id, _usuario(Rol.ADMINISTRADOR)).es_anfitrion is True
    with pytest.raises(NotFoundError):
        _detalle(sala.id, _usuario(Rol.ESTUDIANTE))
    with pytest.raises(NotFoundError):
        _detalle(sala.id, _usuario(Rol.INSTRUCTOR))  # otro instructor


@pytest.mark.django_db
def test_listar_salas_por_rol_y_vista_previa():
    instructor = _usuario(Rol.INSTRUCTOR)
    sala = _crear(instructor, _lab())
    _crear(_usuario(Rol.INSTRUCTOR), _lab())  # de otro instructor
    est = _usuario(Rol.ESTUDIANTE)

    preview = VistaPreviaSalaQuery(
        SalaRepository(), ParticipanteSalaRepository(), LaboratorioRepository(), UserRepository()
    ).execute(codigo=sala.codigo, actor_id=est.id)
    assert preview.acepta_ingresos and not preview.ya_participo and preview.participantes == 0

    r = _unirse(est, sala.codigo)
    listar = ListarSalasQuery(SalaRepository(), ParticipanteSalaRepository(), LaboratorioRepository(), UserRepository())
    assert [s.id for s in listar.execute(instructor.id, "instructor")] == [sala.id]
    mias = listar.execute(est.id, "estudiante")
    assert [s.id for s in mias] == [sala.id] and mias[0].mi_asignacion_id == r.asignacion_id
