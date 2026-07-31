from modules.gamification.domain.entities import (
    Cosmetico,
    CosmeticoDesbloqueado,
    Logro,
    LogroDesbloqueado,
    PerfilJugador,
    Titulo,
    TituloDesbloqueado,
    XpOtorgado,
)
from modules.gamification.domain.value_objects import (
    AvatarTipo,
    RarezaCosmetico,
    TipoCosmetico,
    TipoCriterioLogro,
)
from modules.gamification.infrastructure.models import (
    CosmeticoDesbloqueadoModel,
    CosmeticoModel,
    LogroDesbloqueadoModel,
    LogroModel,
    PerfilJugadorModel,
    TituloDesbloqueadoModel,
    TituloModel,
    XpOtorgadoModel,
)


def perfil_to_entity(model: PerfilJugadorModel) -> PerfilJugador:
    return PerfilJugador(
        id=model.id,
        estudiante_id=model.estudiante_id,
        xp=model.xp,
        nivel=model.nivel,
        avatar_tipo=AvatarTipo(model.avatar_tipo),
        avatar_valor=model.avatar_valor,
        created_at=model.created_at,
    )


def xp_otorgado_to_entity(model: XpOtorgadoModel) -> XpOtorgado:
    return XpOtorgado(
        id=model.id,
        estudiante_id=model.estudiante_id,
        laboratorio_id=model.laboratorio_id,
        xp=model.xp,
        fecha=model.fecha,
    )


def logro_to_entity(model: LogroModel) -> Logro:
    return Logro(
        id=model.id,
        clave=model.clave,
        nombre=model.nombre,
        descripcion=model.descripcion,
        tipo_criterio=TipoCriterioLogro(model.tipo_criterio),
        criterio_valor=model.criterio_valor,
        rareza=RarezaCosmetico(model.rareza),
    )


def logro_desbloqueado_to_entity(model: LogroDesbloqueadoModel) -> LogroDesbloqueado:
    return LogroDesbloqueado(
        id=model.id, estudiante_id=model.estudiante_id, logro_id=model.logro_id, fecha=model.fecha
    )


def cosmetico_to_entity(model: CosmeticoModel) -> Cosmetico:
    return Cosmetico(
        id=model.id,
        clave=model.clave,
        nombre=model.nombre,
        tipo=TipoCosmetico(model.tipo),
        rareza=RarezaCosmetico(model.rareza),
        color=model.color,
        logro_requerido_id=model.logro_requerido_id,
    )


def cosmetico_desbloqueado_to_entity(model: CosmeticoDesbloqueadoModel) -> CosmeticoDesbloqueado:
    return CosmeticoDesbloqueado(
        id=model.id,
        estudiante_id=model.estudiante_id,
        cosmetico_id=model.cosmetico_id,
        equipado=model.equipado,
        fecha=model.fecha,
    )


def titulo_to_entity(model: TituloModel) -> Titulo:
    return Titulo(
        id=model.id,
        clave=model.clave,
        nombre=model.nombre,
        descripcion=model.descripcion,
        rareza=RarezaCosmetico(model.rareza),
        logro_requerido_id=model.logro_requerido_id,
    )


def titulo_desbloqueado_to_entity(model: TituloDesbloqueadoModel) -> TituloDesbloqueado:
    return TituloDesbloqueado(
        id=model.id,
        estudiante_id=model.estudiante_id,
        titulo_id=model.titulo_id,
        equipado=model.equipado,
        fecha=model.fecha,
    )
