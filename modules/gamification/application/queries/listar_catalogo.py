from modules.gamification.application.dtos import (
    CatalogoCosmeticoItemDTO,
    CatalogoLogroItemDTO,
    CatalogoTituloItemDTO,
)
from modules.gamification.domain.repositories import ICosmeticoRepository, ILogroRepository, ITituloRepository


class ListarCatalogoQuery:
    """Catálogo completo de logros/cosméticos/títulos — para mostrar en el perfil qué existe aunque esté bloqueado."""

    def __init__(
        self,
        logro_repository: ILogroRepository,
        cosmetico_repository: ICosmeticoRepository,
        titulo_repository: ITituloRepository,
    ):
        self._logro_repository = logro_repository
        self._cosmetico_repository = cosmetico_repository
        self._titulo_repository = titulo_repository

    def execute(
        self,
    ) -> tuple[list[CatalogoLogroItemDTO], list[CatalogoCosmeticoItemDTO], list[CatalogoTituloItemDTO]]:
        logros = [
            CatalogoLogroItemDTO(
                id=l.id, clave=l.clave, nombre=l.nombre, descripcion=l.descripcion, rareza=l.rareza.value
            )
            for l in self._logro_repository.find_todos()
        ]
        cosmeticos = [
            CatalogoCosmeticoItemDTO(
                id=c.id,
                clave=c.clave,
                nombre=c.nombre,
                tipo=c.tipo.value,
                rareza=c.rareza.value,
                color=c.color,
                logro_requerido_id=c.logro_requerido_id,
            )
            for c in self._cosmetico_repository.find_todos()
        ]
        titulos = [
            CatalogoTituloItemDTO(
                id=t.id,
                clave=t.clave,
                nombre=t.nombre,
                descripcion=t.descripcion,
                rareza=t.rareza.value,
                logro_requerido_id=t.logro_requerido_id,
            )
            for t in self._titulo_repository.find_todos()
        ]
        return logros, cosmeticos, titulos
