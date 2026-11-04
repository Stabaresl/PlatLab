import uuid

from modules.gamification.domain.entities import (
    CosmeticoDesbloqueado,
    Logro,
    LogroDesbloqueado,
    TituloDesbloqueado,
)


def desbloquear_logro(
    estudiante_id: uuid.UUID,
    logro: Logro,
    logro_desbloqueado_repository,
    cosmetico_repository,
    cosmetico_desbloqueado_repository,
    titulo_repository,
    titulo_desbloqueado_repository,
) -> None:
    """Registra el logro y entrega los cosméticos y títulos que cuelgan de él (sin duplicar)."""
    logro_desbloqueado_repository.add(LogroDesbloqueado(estudiante_id=estudiante_id, logro_id=logro.id))
    for cosmetico in cosmetico_repository.find_por_logro(logro.id):
        if not cosmetico_desbloqueado_repository.existe(estudiante_id, cosmetico.id):
            cosmetico_desbloqueado_repository.add(
                CosmeticoDesbloqueado(estudiante_id=estudiante_id, cosmetico_id=cosmetico.id)
            )
    for titulo in titulo_repository.find_por_logro(logro.id):
        if not titulo_desbloqueado_repository.existe(estudiante_id, titulo.id):
            titulo_desbloqueado_repository.add(TituloDesbloqueado(estudiante_id=estudiante_id, titulo_id=titulo.id))
