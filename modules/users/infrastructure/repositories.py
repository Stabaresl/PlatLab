import uuid

from django.db.models import Count, Q

from modules.users.domain.entities import ProveedorAutenticacion, SolicitudInstructor, User
from modules.users.domain.value_objects import SolicitudInstructorEstado
from modules.users.infrastructure.mappers import (
    proveedor_to_entity,
    proveedor_to_model,
    solicitud_instructor_to_entity,
    solicitud_instructor_to_model,
    user_to_entity,
    user_to_model,
)
from modules.users.infrastructure.models import (
    ProveedorAutenticacionModel,
    SolicitudInstructorModel,
    UserModel,
)


class UserRepository:
    """
    Implementación de `IUserRepository` (modules.users.domain.repositories)
    sobre PostgreSQL vía el ORM de Django. Traduce entidad <-> modelo con
    `mappers.py` en cada operación — el resto del sistema nunca ve
    `UserModel` directamente, solo la entidad `User`.
    """

    def get_by_id(self, user_id: uuid.UUID) -> User | None:
        model = UserModel.objects.filter(id=user_id).first()
        return user_to_entity(model) if model else None

    def _filtrar(self, nombre, rol, activo):
        queryset = UserModel.objects.all()
        if nombre:
            # Un solo cuadro de búsqueda en el panel del admin: nombre o correo.
            queryset = queryset.filter(Q(nombre_completo__icontains=nombre) | Q(email__icontains=nombre))
        if rol:
            queryset = queryset.filter(rol=rol)
        if activo is not None:
            queryset = queryset.filter(is_active=activo)
        return queryset

    def find_all(
        self,
        nombre: str | None = None,
        rol: str | None = None,
        activo: bool | None = None,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[User]:
        queryset = self._filtrar(nombre, rol, activo).order_by("nombre_completo", "id")
        if limit is not None:
            queryset = queryset[offset : offset + limit]
        return [user_to_entity(m) for m in queryset]

    def contar(
        self, nombre: str | None = None, rol: str | None = None, activo: bool | None = None
    ) -> int:
        return self._filtrar(nombre, rol, activo).count()

    def contar_por_rol(self) -> dict[str, int]:
        filas = UserModel.objects.values("rol").annotate(total=Count("id"))
        return {fila["rol"]: fila["total"] for fila in filas}

    def get_by_ids(self, user_ids: list[uuid.UUID]) -> dict[uuid.UUID, User]:
        if not user_ids:
            return {}
        return {m.id: user_to_entity(m) for m in UserModel.objects.filter(id__in=user_ids)}

    def get_by_email(self, email: str) -> User | None:
        # iexact: el correo no distingue mayúsculas — "Ana@x.com" y
        # "ana@x.com" son la misma persona (evita cuentas duplicadas y que el
        # login falle por una mayúscula, ej. un email de OAuth).
        model = UserModel.objects.filter(email__iexact=email.strip()).first()
        return user_to_entity(model) if model else None

    def get_by_username(self, username: str) -> User | None:
        model = UserModel.objects.filter(username=username).first()
        return user_to_entity(model) if model else None

    def exists_by_email(self, email: str) -> bool:
        return UserModel.objects.filter(email__iexact=email.strip()).exists()

    def add(self, user: User) -> User:
        model = user_to_model(user)
        model.save()
        return user_to_entity(model)

    def update(self, user: User) -> User:
        model = UserModel.objects.get(id=user.id)
        model.email = str(user.email)
        model.nombre_completo = user.nombre_completo
        model.rol = user.rol.value
        model.username = user.username
        model.password_hash = user.password_hash
        model.is_active = user.is_active
        model.last_login = user.last_login
        model.save()
        return user_to_entity(model)

    def add_proveedor(self, proveedor: ProveedorAutenticacion) -> ProveedorAutenticacion:
        model = proveedor_to_model(proveedor)
        model.save()
        return proveedor_to_entity(model)

    def get_proveedores_by_user_id(self, user_id: uuid.UUID) -> list[ProveedorAutenticacion]:
        models = ProveedorAutenticacionModel.objects.filter(user_id=user_id)
        return [proveedor_to_entity(m) for m in models]

    def get_by_proveedor(self, proveedor: str, proveedor_uid: str) -> User | None:
        vinculo = ProveedorAutenticacionModel.objects.filter(
            proveedor=proveedor, proveedor_uid=proveedor_uid
        ).first()
        if not vinculo:
            return None
        return self.get_by_id(vinculo.user_id)


class SolicitudInstructorRepository:
    """Implementación de `ISolicitudInstructorRepository` sobre PostgreSQL."""

    def get_by_id(self, solicitud_id: uuid.UUID) -> SolicitudInstructor | None:
        model = SolicitudInstructorModel.objects.filter(id=solicitud_id).first()
        return solicitud_instructor_to_entity(model) if model else None

    def get_pendiente_by_user_id(self, user_id: uuid.UUID) -> SolicitudInstructor | None:
        model = SolicitudInstructorModel.objects.filter(
            user_id=user_id, estado=SolicitudInstructorEstado.PENDIENTE.value
        ).first()
        return solicitud_instructor_to_entity(model) if model else None

    def get_ultima_by_user_id(self, user_id: uuid.UUID) -> SolicitudInstructor | None:
        model = (
            SolicitudInstructorModel.objects.filter(user_id=user_id)
            .order_by("-created_at")
            .first()
        )
        return solicitud_instructor_to_entity(model) if model else None

    def find_por_estado(self, estado: str | None) -> list[SolicitudInstructor]:
        """Cola de revisión del admin: más antiguas primero (orden de llegada)."""
        queryset = SolicitudInstructorModel.objects.all()
        if estado:
            queryset = queryset.filter(estado=estado)
        return [solicitud_instructor_to_entity(m) for m in queryset.order_by("created_at")[:200]]

    def add(self, solicitud: SolicitudInstructor) -> SolicitudInstructor:
        model = solicitud_instructor_to_model(solicitud)
        model.save()
        return solicitud_instructor_to_entity(model)

    def update(self, solicitud: SolicitudInstructor) -> SolicitudInstructor:
        model = SolicitudInstructorModel.objects.get(id=solicitud.id)
        model.estado = solicitud.estado.value
        model.motivo_rechazo = solicitud.motivo_rechazo
        model.resultado_verificacion = solicitud.resultado_verificacion
        model.resolved_at = solicitud.resolved_at
        model.revisada_por_id = solicitud.revisada_por_id
        model.save()
        return solicitud_instructor_to_entity(model)
