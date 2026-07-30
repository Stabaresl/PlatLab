from django.apps import AppConfig


class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'modules.users'

    def ready(self):
        from modules.shared.infrastructure.event_dispatcher import EventDispatcher
        from modules.users.infrastructure.event_listeners import registrar_listeners

        registrar_listeners(EventDispatcher())
