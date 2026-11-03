import uuid

import pytest

from modules.audit.infrastructure.repositories import AuditoriaRepository
from modules.notifications.infrastructure.repositories import NotificacionRepository
from modules.shared.domain.exceptions import (
    ConflictError,
    ForbiddenError,
    NotFoundError,
    ValidationError,
)
from modules.shared.infrastructure.event_dispatcher import EventDispatcher
from modules.shared.infrastructure.unit_of_work import BaseUnitOfWork
from modules.users.application.dtos import ResolverSolicitudInstructorDTO, SolicitarInstructorDTO
from modules.users.application.queries.listar_solicitudes_instructor import (
    ListarSolicitudesInstructorQuery,
)
from modules.users.application.use_cases.resolver_solicitud_instructor import (
    ResolverSolicitudInstructorUseCase,
)
from modules.users.application.use_cases.solicitar_convertirse_en_instructor import (
    SolicitarConvertirseEnInstructorUseCase,
)
from modules.users.domain.entities import SolicitudInstructor, User
from modules.users.domain.value_objects import Email, Rol
from modules.users.infrastructure import openalex_adapter
from modules.users.infrastructure.repositories import SolicitudInstructorRepository, UserRepository

_ORCID_VALIDO = "0000-0000-0000-0000"


def _crear_usuario(email: str, nombre: str = "Ada Lovelace", rol: Rol = Rol.ESTUDIANTE) -> User:
    return UserRepository().add(User(email=Email(email), nombre_completo=nombre, rol=rol))


def _crear_estudiante(email: str, nombre: str = "Ada Lovelace") -> User:
    return _crear_usuario(email, nombre)


def _uc():
    return SolicitarConvertirseEnInstructorUseCase(
        unit_of_work=BaseUnitOfWork(),
        event_dispatcher=EventDispatcher(),
        user_repository=UserRepository(),
        solicitud_repository=SolicitudInstructorRepository(),
    )


def _resolver_uc():
    return ResolverSolicitudInstructorUseCase(
        unit_of_work=BaseUnitOfWork(),
        event_dispatcher=EventDispatcher(),
        solicitud_repository=SolicitudInstructorRepository(),
        user_repository=UserRepository(),
    )


def _solicitud_pendiente(usuario: User) -> SolicitudInstructor:
    return SolicitudInstructorRepository().add(
        SolicitudInstructor(
            user_id=usuario.id,
            orcid=_ORCID_VALIDO,
            nombre_declarado=usuario.nombre_completo,
            tipo="investigador",
        )
    )


class _FakeResponse:
    def __init__(self, status_code=200, json_data=None):
        self.status_code = status_code
        self._json = json_data or {}

    def json(self):
        return self._json

    def raise_for_status(self):
        pass


def _openalex_responde(monkeypatch, display_name: str, works_count: int = 4):
    monkeypatch.setattr(
        openalex_adapter.requests,
        "get",
        lambda url, params, timeout: _FakeResponse(
            200, {"display_name": display_name, "works_count": works_count}
        ),
    )


# --- Solicitar ---------------------------------------------------------------


@pytest.mark.django_db
def test_no_estudiante_lanza_forbidden():
    with pytest.raises(ForbiddenError):
        _uc().execute(
            SolicitarInstructorDTO(
                actor_id=uuid.uuid4(), actor_rol="instructor", orcid=_ORCID_VALIDO, tipo="investigador"
            )
        )


@pytest.mark.django_db
def test_orcid_con_formato_invalido_lanza_validation_error():
    usuario = _crear_estudiante("malorcid@uni.edu")

    with pytest.raises(ValidationError):
        _uc().execute(
            SolicitarInstructorDTO(
                actor_id=usuario.id, actor_rol="estudiante", orcid="no-es-un-orcid", tipo="investigador"
            )
        )


@pytest.mark.django_db
def test_solicitud_pendiente_existente_lanza_conflict():
    usuario = _crear_estudiante("pendiente@uni.edu")
    _solicitud_pendiente(usuario)

    with pytest.raises(ConflictError):
        _uc().execute(
            SolicitarInstructorDTO(
                actor_id=usuario.id, actor_rol="estudiante", orcid=_ORCID_VALIDO, tipo="investigador"
            )
        )


@pytest.mark.django_db
def test_openalex_coincidente_no_aprueba_solo_deja_evidencia(monkeypatch):
    """
    Con `CELERY_TASK_ALWAYS_EAGER` (config/settings/test.py) el listener ->
    tarea OpenAlex corre antes de que `execute()` retorne. Aunque OpenAlex
    confirme ORCID y nombre, la solicitud sigue pendiente: solo un admin la
    aprueba (OpenAlex no prueba que la persona sea dueña del ORCID).
    """
    usuario = _crear_estudiante("valido@uni.edu", nombre="Ada Lovelace")
    _openalex_responde(monkeypatch, "Ada Lovelace", works_count=4)

    resultado = _uc().execute(
        SolicitarInstructorDTO(
            actor_id=usuario.id, actor_rol="estudiante", orcid=_ORCID_VALIDO, tipo="investigador"
        )
    )

    solicitud = SolicitudInstructorRepository().get_by_id(resultado.id)
    assert solicitud.estado.value == "pendiente"
    assert solicitud.resultado_verificacion["encontrado"] is True
    assert solicitud.resultado_verificacion["coincide_nombre"] is True
    assert solicitud.resultado_verificacion["works_count"] == 4
    assert UserRepository().get_by_id(usuario.id).rol == Rol.ESTUDIANTE


@pytest.mark.django_db
def test_openalex_con_nombre_distinto_tampoco_rechaza_solo(monkeypatch):
    usuario = _crear_estudiante("distinto@uni.edu", nombre="Ada Lovelace")
    _openalex_responde(monkeypatch, "Persona Distinta")

    resultado = _uc().execute(
        SolicitarInstructorDTO(
            actor_id=usuario.id, actor_rol="estudiante", orcid=_ORCID_VALIDO, tipo="investigador"
        )
    )

    solicitud = SolicitudInstructorRepository().get_by_id(resultado.id)
    assert solicitud.estado.value == "pendiente"
    assert solicitud.resultado_verificacion["coincide_nombre"] is False
    assert solicitud.resultado_verificacion["nombre_openalex"] == "Persona Distinta"


@pytest.mark.django_db
def test_nueva_solicitud_notifica_a_los_admins_activos(monkeypatch):
    _openalex_responde(monkeypatch, "Grace Hopper")
    admin = _crear_usuario(f"admin_{uuid.uuid4()}@uni.edu", "Admin", Rol.ADMINISTRADOR)
    usuario = _crear_estudiante(f"aviso_{uuid.uuid4()}@uni.edu", nombre="Grace Hopper")

    _uc().execute(
        SolicitarInstructorDTO(
            actor_id=usuario.id, actor_rol="estudiante", orcid=_ORCID_VALIDO, tipo="docente"
        )
    )

    avisos = NotificacionRepository().find_por_usuario(admin.id)
    assert [a.tipo.value for a in avisos] == ["solicitud_instructor"]
    assert "Grace Hopper" in avisos[0].mensaje


# --- Resolver (admin) --------------------------------------------------------


@pytest.mark.django_db
def test_admin_aprueba_asciende_a_instructor_y_queda_auditado():
    admin = _crear_usuario(f"admin_{uuid.uuid4()}@uni.edu", "Admin", Rol.ADMINISTRADOR)
    usuario = _crear_estudiante(f"aprobar_{uuid.uuid4()}@uni.edu")
    solicitud = _solicitud_pendiente(usuario)

    resultado = _resolver_uc().execute(
        ResolverSolicitudInstructorDTO(
            solicitud_id=solicitud.id, actor_id=admin.id, actor_rol="administrador", aprobar=True
        )
    )

    assert resultado.estado == "aprobada"
    assert UserRepository().get_by_id(usuario.id).rol == Rol.INSTRUCTOR
    guardada = SolicitudInstructorRepository().get_by_id(solicitud.id)
    assert guardada.revisada_por_id == admin.id
    assert guardada.resolved_at is not None
    registros = AuditoriaRepository().find_todos(accion="instructor_verification_approved")
    assert [r.actor_id for r in registros] == [admin.id]
    avisos = NotificacionRepository().find_por_usuario(usuario.id)
    assert [a.tipo.value for a in avisos] == ["instructor_aprobado"]


@pytest.mark.django_db
def test_admin_rechaza_con_motivo_y_el_estudiante_lo_recibe():
    admin = _crear_usuario(f"admin_{uuid.uuid4()}@uni.edu", "Admin", Rol.ADMINISTRADOR)
    usuario = _crear_estudiante(f"rechazar_{uuid.uuid4()}@uni.edu")
    solicitud = _solicitud_pendiente(usuario)

    resultado = _resolver_uc().execute(
        ResolverSolicitudInstructorDTO(
            solicitud_id=solicitud.id,
            actor_id=admin.id,
            actor_rol="administrador",
            aprobar=False,
            motivo="  El ORCID no corresponde a tu nombre.  ",
        )
    )

    assert resultado.estado == "rechazada"
    assert resultado.motivo_rechazo == "El ORCID no corresponde a tu nombre."
    assert UserRepository().get_by_id(usuario.id).rol == Rol.ESTUDIANTE
    avisos = NotificacionRepository().find_por_usuario(usuario.id)
    assert avisos[0].tipo.value == "instructor_rechazado"
    assert "El ORCID no corresponde a tu nombre." in avisos[0].mensaje


@pytest.mark.django_db
def test_rechazar_sin_motivo_lanza_validation_error():
    usuario = _crear_estudiante(f"sinmotivo_{uuid.uuid4()}@uni.edu")
    solicitud = _solicitud_pendiente(usuario)

    with pytest.raises(ValidationError):
        _resolver_uc().execute(
            ResolverSolicitudInstructorDTO(
                solicitud_id=solicitud.id,
                actor_id=uuid.uuid4(),
                actor_rol="administrador",
                aprobar=False,
                motivo="   ",
            )
        )


@pytest.mark.django_db
def test_solo_admin_puede_resolver():
    usuario = _crear_estudiante(f"noadmin_{uuid.uuid4()}@uni.edu")
    solicitud = _solicitud_pendiente(usuario)

    with pytest.raises(ForbiddenError):
        _resolver_uc().execute(
            ResolverSolicitudInstructorDTO(
                solicitud_id=solicitud.id, actor_id=uuid.uuid4(), actor_rol="instructor", aprobar=True
            )
        )


@pytest.mark.django_db
def test_no_se_resuelve_dos_veces():
    usuario = _crear_estudiante(f"dosveces_{uuid.uuid4()}@uni.edu")
    solicitud = _solicitud_pendiente(usuario)
    dto = ResolverSolicitudInstructorDTO(
        solicitud_id=solicitud.id, actor_id=uuid.uuid4(), actor_rol="administrador", aprobar=True
    )
    _resolver_uc().execute(dto)

    with pytest.raises(ConflictError):
        _resolver_uc().execute(dto)


@pytest.mark.django_db
def test_resolver_solicitud_inexistente_lanza_not_found():
    with pytest.raises(NotFoundError):
        _resolver_uc().execute(
            ResolverSolicitudInstructorDTO(
                solicitud_id=uuid.uuid4(), actor_id=uuid.uuid4(), actor_rol="administrador", aprobar=True
            )
        )


# --- Cola de revisión (admin) ------------------------------------------------


@pytest.mark.django_db
def test_listar_solicitudes_junta_datos_del_usuario_y_openalex():
    usuario = _crear_estudiante(f"cola_{uuid.uuid4()}@uni.edu", nombre="Katherine Johnson")
    solicitud = _solicitud_pendiente(usuario)
    solicitud.resultado_verificacion = {"encontrado": True, "coincide_nombre": True, "works_count": 12}
    SolicitudInstructorRepository().update(solicitud)

    items = ListarSolicitudesInstructorQuery(SolicitudInstructorRepository(), UserRepository()).execute(
        actor_rol="administrador"
    )

    item = next(i for i in items if i.id == solicitud.id)
    assert item.usuario_email == str(usuario.email)
    assert item.usuario_nombre == "Katherine Johnson"
    assert item.resultado_openalex["works_count"] == 12
    assert item.estado == "pendiente"


@pytest.mark.django_db
def test_listar_solicitudes_no_admin_lanza_forbidden():
    with pytest.raises(ForbiddenError):
        ListarSolicitudesInstructorQuery(SolicitudInstructorRepository(), UserRepository()).execute(
            actor_rol="estudiante"
        )
