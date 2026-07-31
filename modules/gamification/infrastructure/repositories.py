import uuid

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
from modules.gamification.infrastructure.mappers import (
    cosmetico_desbloqueado_to_entity,
    cosmetico_to_entity,
    logro_desbloqueado_to_entity,
    logro_to_entity,
    perfil_to_entity,
    titulo_desbloqueado_to_entity,
    titulo_to_entity,
    xp_otorgado_to_entity,
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


class PerfilJugadorRepository:
    def get_by_estudiante(self, estudiante_id: uuid.UUID) -> PerfilJugador | None:
        model = PerfilJugadorModel.objects.filter(estudiante_id=estudiante_id).first()
        return perfil_to_entity(model) if model else None

    def add(self, perfil: PerfilJugador) -> PerfilJugador:
        model = PerfilJugadorModel.objects.create(
            id=perfil.id,
            estudiante_id=perfil.estudiante_id,
            xp=perfil.xp,
            nivel=perfil.nivel,
            avatar_tipo=perfil.avatar_tipo.value,
            avatar_valor=perfil.avatar_valor,
        )
        return perfil_to_entity(model)

    def update(self, perfil: PerfilJugador) -> PerfilJugador:
        model = PerfilJugadorModel.objects.get(id=perfil.id)
        model.xp = perfil.xp
        model.nivel = perfil.nivel
        model.avatar_tipo = perfil.avatar_tipo.value
        model.avatar_valor = perfil.avatar_valor
        model.save(update_fields=["xp", "nivel", "avatar_tipo", "avatar_valor"])
        return perfil_to_entity(model)


class XpOtorgadoRepository:
    def existe(self, estudiante_id: uuid.UUID, laboratorio_id: uuid.UUID) -> bool:
        return XpOtorgadoModel.objects.filter(
            estudiante_id=estudiante_id, laboratorio_id=laboratorio_id
        ).exists()

    def add(self, xp_otorgado: XpOtorgado) -> XpOtorgado:
        model = XpOtorgadoModel.objects.create(
            id=xp_otorgado.id,
            estudiante_id=xp_otorgado.estudiante_id,
            laboratorio_id=xp_otorgado.laboratorio_id,
            xp=xp_otorgado.xp,
        )
        return xp_otorgado_to_entity(model)

    def contar_por_estudiante(self, estudiante_id: uuid.UUID) -> int:
        return XpOtorgadoModel.objects.filter(estudiante_id=estudiante_id).count()

    def find_laboratorio_ids_por_estudiante(self, estudiante_id: uuid.UUID) -> set[uuid.UUID]:
        return set(
            XpOtorgadoModel.objects.filter(estudiante_id=estudiante_id).values_list(
                "laboratorio_id", flat=True
            )
        )


class LogroRepository:
    def find_todos(self) -> list[Logro]:
        return [logro_to_entity(m) for m in LogroModel.objects.all()]

    def get_by_id(self, logro_id: uuid.UUID) -> Logro | None:
        model = LogroModel.objects.filter(id=logro_id).first()
        return logro_to_entity(model) if model else None

    def get_by_clave(self, clave: str) -> Logro | None:
        model = LogroModel.objects.filter(clave=clave).first()
        return logro_to_entity(model) if model else None

    def add(self, logro: Logro) -> Logro:
        model = LogroModel.objects.create(
            id=logro.id,
            clave=logro.clave,
            nombre=logro.nombre,
            descripcion=logro.descripcion,
            tipo_criterio=logro.tipo_criterio.value,
            criterio_valor=logro.criterio_valor,
            rareza=logro.rareza.value,
        )
        return logro_to_entity(model)

    def find_por_tipo(self, tipo_criterio: str) -> list[Logro]:
        return [logro_to_entity(m) for m in LogroModel.objects.filter(tipo_criterio=tipo_criterio)]


class LogroDesbloqueadoRepository:
    def existe(self, estudiante_id: uuid.UUID, logro_id: uuid.UUID) -> bool:
        return LogroDesbloqueadoModel.objects.filter(
            estudiante_id=estudiante_id, logro_id=logro_id
        ).exists()

    def add(self, desbloqueo: LogroDesbloqueado) -> LogroDesbloqueado:
        model = LogroDesbloqueadoModel.objects.create(
            id=desbloqueo.id, estudiante_id=desbloqueo.estudiante_id, logro_id=desbloqueo.logro_id
        )
        return logro_desbloqueado_to_entity(model)

    def find_por_estudiante(self, estudiante_id: uuid.UUID) -> list[LogroDesbloqueado]:
        modelos = LogroDesbloqueadoModel.objects.filter(estudiante_id=estudiante_id)
        return [logro_desbloqueado_to_entity(m) for m in modelos]


class CosmeticoRepository:
    def find_todos(self) -> list[Cosmetico]:
        return [cosmetico_to_entity(m) for m in CosmeticoModel.objects.all()]

    def get_by_id(self, cosmetico_id: uuid.UUID) -> Cosmetico | None:
        model = CosmeticoModel.objects.filter(id=cosmetico_id).first()
        return cosmetico_to_entity(model) if model else None

    def get_by_clave(self, clave: str) -> Cosmetico | None:
        model = CosmeticoModel.objects.filter(clave=clave).first()
        return cosmetico_to_entity(model) if model else None

    def add(self, cosmetico: Cosmetico) -> Cosmetico:
        model = CosmeticoModel.objects.create(
            id=cosmetico.id,
            clave=cosmetico.clave,
            nombre=cosmetico.nombre,
            tipo=cosmetico.tipo.value,
            rareza=cosmetico.rareza.value,
            color=cosmetico.color,
            logro_requerido_id=cosmetico.logro_requerido_id,
        )
        return cosmetico_to_entity(model)

    def find_por_logro(self, logro_id: uuid.UUID) -> list[Cosmetico]:
        return [cosmetico_to_entity(m) for m in CosmeticoModel.objects.filter(logro_requerido_id=logro_id)]


class CosmeticoDesbloqueadoRepository:
    def get_by_id(self, desbloqueo_id: uuid.UUID) -> CosmeticoDesbloqueado | None:
        model = CosmeticoDesbloqueadoModel.objects.filter(id=desbloqueo_id).first()
        return cosmetico_desbloqueado_to_entity(model) if model else None

    def existe(self, estudiante_id: uuid.UUID, cosmetico_id: uuid.UUID) -> bool:
        return CosmeticoDesbloqueadoModel.objects.filter(
            estudiante_id=estudiante_id, cosmetico_id=cosmetico_id
        ).exists()

    def add(self, desbloqueo: CosmeticoDesbloqueado) -> CosmeticoDesbloqueado:
        model = CosmeticoDesbloqueadoModel.objects.create(
            id=desbloqueo.id,
            estudiante_id=desbloqueo.estudiante_id,
            cosmetico_id=desbloqueo.cosmetico_id,
            equipado=desbloqueo.equipado,
        )
        return cosmetico_desbloqueado_to_entity(model)

    def find_por_estudiante(self, estudiante_id: uuid.UUID) -> list[CosmeticoDesbloqueado]:
        modelos = CosmeticoDesbloqueadoModel.objects.filter(estudiante_id=estudiante_id)
        return [cosmetico_desbloqueado_to_entity(m) for m in modelos]

    def update(self, desbloqueo: CosmeticoDesbloqueado) -> CosmeticoDesbloqueado:
        model = CosmeticoDesbloqueadoModel.objects.get(id=desbloqueo.id)
        model.equipado = desbloqueo.equipado
        model.save(update_fields=["equipado"])
        return cosmetico_desbloqueado_to_entity(model)


class TituloRepository:
    def find_todos(self) -> list[Titulo]:
        return [titulo_to_entity(m) for m in TituloModel.objects.all()]

    def get_by_id(self, titulo_id: uuid.UUID) -> Titulo | None:
        model = TituloModel.objects.filter(id=titulo_id).first()
        return titulo_to_entity(model) if model else None

    def get_by_clave(self, clave: str) -> Titulo | None:
        model = TituloModel.objects.filter(clave=clave).first()
        return titulo_to_entity(model) if model else None

    def add(self, titulo: Titulo) -> Titulo:
        model = TituloModel.objects.create(
            id=titulo.id,
            clave=titulo.clave,
            nombre=titulo.nombre,
            descripcion=titulo.descripcion,
            rareza=titulo.rareza.value,
            logro_requerido_id=titulo.logro_requerido_id,
        )
        return titulo_to_entity(model)

    def find_por_logro(self, logro_id: uuid.UUID) -> list[Titulo]:
        return [titulo_to_entity(m) for m in TituloModel.objects.filter(logro_requerido_id=logro_id)]


class TituloDesbloqueadoRepository:
    def get_by_id(self, desbloqueo_id: uuid.UUID) -> TituloDesbloqueado | None:
        model = TituloDesbloqueadoModel.objects.filter(id=desbloqueo_id).first()
        return titulo_desbloqueado_to_entity(model) if model else None

    def existe(self, estudiante_id: uuid.UUID, titulo_id: uuid.UUID) -> bool:
        return TituloDesbloqueadoModel.objects.filter(
            estudiante_id=estudiante_id, titulo_id=titulo_id
        ).exists()

    def add(self, desbloqueo: TituloDesbloqueado) -> TituloDesbloqueado:
        model = TituloDesbloqueadoModel.objects.create(
            id=desbloqueo.id,
            estudiante_id=desbloqueo.estudiante_id,
            titulo_id=desbloqueo.titulo_id,
            equipado=desbloqueo.equipado,
        )
        return titulo_desbloqueado_to_entity(model)

    def find_por_estudiante(self, estudiante_id: uuid.UUID) -> list[TituloDesbloqueado]:
        modelos = TituloDesbloqueadoModel.objects.filter(estudiante_id=estudiante_id)
        return [titulo_desbloqueado_to_entity(m) for m in modelos]

    def update(self, desbloqueo: TituloDesbloqueado) -> TituloDesbloqueado:
        model = TituloDesbloqueadoModel.objects.get(id=desbloqueo.id)
        model.equipado = desbloqueo.equipado
        model.save(update_fields=["equipado"])
        return titulo_desbloqueado_to_entity(model)
