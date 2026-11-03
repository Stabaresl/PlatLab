from modules.shared.domain.exceptions import ForbiddenError
from modules.users.application.dtos import SolicitudInstructorAdminItemDTO
from modules.users.domain.repositories import ISolicitudInstructorRepository, IUserRepository
from modules.users.domain.value_objects import Rol

_SIN_PERMISO_MSG = "Solo un administrador puede revisar solicitudes de instructor."


class ListarSolicitudesInstructorQuery:
    """
    Cola de revisión del admin: cada solicitud con los datos de la cuenta
    que la hizo (nombre, correo, antigüedad) junto a lo que declaró (ORCID,
    tipo, institución, motivación) y lo que encontró OpenAlex — para que el
    admin compare ambas fuentes antes de decidir.
    """

    def __init__(
        self,
        solicitud_repository: ISolicitudInstructorRepository,
        user_repository: IUserRepository,
    ):
        self._solicitud_repository = solicitud_repository
        self._user_repository = user_repository

    def execute(self, actor_rol: str, estado: str | None = "pendiente") -> list[SolicitudInstructorAdminItemDTO]:
        if actor_rol != Rol.ADMINISTRADOR.value:
            raise ForbiddenError(_SIN_PERMISO_MSG)

        solicitudes = self._solicitud_repository.find_por_estado(estado)
        usuarios = self._user_repository.get_by_ids(list({s.user_id for s in solicitudes}))

        items = []
        for s in solicitudes:
            usuario = usuarios.get(s.user_id)
            items.append(
                SolicitudInstructorAdminItemDTO(
                    id=s.id,
                    estado=s.estado.value,
                    orcid=s.orcid,
                    tipo=s.tipo,
                    institucion=s.institucion,
                    especialidades=s.especialidades,
                    motivacion=s.motivacion,
                    nombre_declarado=s.nombre_declarado,
                    usuario_id=s.user_id,
                    usuario_email=str(usuario.email) if usuario else None,
                    usuario_nombre=usuario.nombre_completo if usuario else None,
                    usuario_desde=usuario.date_joined if usuario else None,
                    resultado_openalex=s.resultado_verificacion,
                    motivo_rechazo=s.motivo_rechazo,
                    created_at=s.created_at,
                    resolved_at=s.resolved_at,
                )
            )
        return items
