from modules.notifications.application.dtos import ListarNotificacionesDTO, NotificacionResultDTO
from modules.notifications.domain.repositories import INotificacionRepository


class ListarNotificacionesQuery:
    """api.md §9 `GET /notifications/?leida=` — el usuario ve solo las propias."""

    def __init__(self, notificacion_repository: INotificacionRepository):
        self._repo = notificacion_repository

    def execute(self, input_dto: ListarNotificacionesDTO) -> list[NotificacionResultDTO]:
        return self.execute_paginado(input_dto, limit=None, offset=0)[0]

    def execute_paginado(
        self, input_dto: ListarNotificacionesDTO, limit: int | None, offset: int
    ) -> tuple[list[NotificacionResultDTO], int]:
        """Paginado en BD — la campana del frontend consulta esto cada 60 s por usuario conectado."""
        notificaciones = self._repo.find_por_usuario(
            input_dto.user_id, leida=input_dto.leida, limit=limit, offset=offset
        )
        total = (
            self._repo.contar_por_usuario(input_dto.user_id, leida=input_dto.leida)
            if limit is not None
            else len(notificaciones)
        )
        return self._a_items(notificaciones), total

    def _a_items(self, notificaciones) -> list[NotificacionResultDTO]:
        return [
            NotificacionResultDTO(
                id=n.id,
                tipo=n.tipo.value,
                mensaje=n.mensaje,
                canal=n.canal.value,
                leida=n.leida,
                entidad_tipo=n.entidad_tipo,
                entidad_id=n.entidad_id,
                fecha_creacion=n.fecha_creacion,
            )
            for n in notificaciones
        ]
