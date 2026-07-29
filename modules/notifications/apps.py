from django.apps import AppConfig


class NotificationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'modules.notifications'

    def ready(self):
        from modules.notifications.infrastructure.event_listeners import registrar_listeners
        from modules.shared.infrastructure.event_dispatcher import EventDispatcher

        registrar_listeners(EventDispatcher())
