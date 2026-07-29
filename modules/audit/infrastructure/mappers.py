from modules.audit.domain.entities import RegistroAuditoria
from modules.audit.infrastructure.models import RegistroAuditoriaModel


def registro_to_entity(model: RegistroAuditoriaModel) -> RegistroAuditoria:
    return RegistroAuditoria(
        id=model.id,
        actor_id=model.actor_id,
        accion=model.accion,
        entidad_tipo=model.entidad_tipo,
        entidad_id=model.entidad_id,
        ip=model.ip,
        timestamp=model.timestamp,
    )
