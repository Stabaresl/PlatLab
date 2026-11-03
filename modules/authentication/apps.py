from django.apps import AppConfig


class AuthenticationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'modules.authentication'

    def ready(self):
        from modules.authentication.infrastructure.event_listeners import registrar_listeners
        from modules.shared.infrastructure.event_dispatcher import EventDispatcher

        registrar_listeners(EventDispatcher())
