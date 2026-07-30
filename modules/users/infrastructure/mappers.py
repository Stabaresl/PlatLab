from modules.users.domain.entities import (
    ProveedorAutenticacion,
    ProveedorTipo,
    SolicitudInstructor,
    User,
)
from modules.users.domain.value_objects import Email, Rol, SolicitudInstructorEstado
from modules.users.infrastructure.models import (
    ProveedorAutenticacionModel,
    SolicitudInstructorModel,
    UserModel,
)


def user_to_entity(model: UserModel) -> User:
    return User(
        id=model.id,
        email=Email(model.email),
        nombre_completo=model.nombre_completo,
        rol=Rol(model.rol),
        username=model.username,
        password_hash=model.password_hash,
        is_active=model.is_active,
        date_joined=model.date_joined,
        last_login=model.last_login,
    )


def user_to_model(entity: User) -> UserModel:
    return UserModel(
        id=entity.id,
        email=str(entity.email),
        nombre_completo=entity.nombre_completo,
        rol=entity.rol.value,
        username=entity.username,
        password_hash=entity.password_hash,
        is_active=entity.is_active,
        last_login=entity.last_login,
    )


def proveedor_to_entity(model: ProveedorAutenticacionModel) -> ProveedorAutenticacion:
    return ProveedorAutenticacion(
        id=model.id,
        user_id=model.user_id,
        proveedor=ProveedorTipo(model.proveedor),
        proveedor_uid=model.proveedor_uid,
        created_at=model.created_at,
    )


def proveedor_to_model(entity: ProveedorAutenticacion) -> ProveedorAutenticacionModel:
    return ProveedorAutenticacionModel(
        id=entity.id,
        user_id=entity.user_id,
        proveedor=entity.proveedor.value,
        proveedor_uid=entity.proveedor_uid,
    )


def solicitud_instructor_to_entity(model: SolicitudInstructorModel) -> SolicitudInstructor:
    return SolicitudInstructor(
        id=model.id,
        user_id=model.user_id,
        orcid=model.orcid,
        nombre_declarado=model.nombre_declarado,
        tipo=model.tipo,
        institucion=model.institucion,
        especialidades=model.especialidades,
        motivacion=model.motivacion,
        estado=SolicitudInstructorEstado(model.estado),
        motivo_rechazo=model.motivo_rechazo,
        resultado_verificacion=model.resultado_verificacion,
        created_at=model.created_at,
        resolved_at=model.resolved_at,
    )


def solicitud_instructor_to_model(entity: SolicitudInstructor) -> SolicitudInstructorModel:
    return SolicitudInstructorModel(
        id=entity.id,
        user_id=entity.user_id,
        orcid=entity.orcid,
        nombre_declarado=entity.nombre_declarado,
        tipo=entity.tipo,
        institucion=entity.institucion,
        especialidades=entity.especialidades,
        motivacion=entity.motivacion,
        estado=entity.estado.value,
        motivo_rechazo=entity.motivo_rechazo,
        resultado_verificacion=entity.resultado_verificacion,
        resolved_at=entity.resolved_at,
    )
