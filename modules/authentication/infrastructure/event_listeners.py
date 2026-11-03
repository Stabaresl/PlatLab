from modules.authentication.infrastructure.refresh_token_store import RefreshTokenStore
from modules.shared.infrastructure.event_dispatcher import EventDispatcher
from modules.users.domain.events import UsuarioDeshabilitado


def _on_usuario_deshabilitado(event: UsuarioDeshabilitado) -> None:
    """
    HA-01/UC-08 A1: "el usuario deshabilitado no puede iniciar sesión" —
    tampoco debe poder seguir usando una sesión ya abierta. Revoca todas
    sus familias de refresh tokens; el access token vigente muere solo en
    ≤15 min y `RefreshTokenUseCase` ya rechaza a usuarios inactivos.
    """
    RefreshTokenStore().revoke_all_for_user(event.user_id)


def registrar_listeners(dispatcher: EventDispatcher) -> None:
    dispatcher.subscribe(UsuarioDeshabilitado, _on_usuario_deshabilitado)
