from django.apps import AppConfig


class RoomsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "modules.rooms"

    def ready(self):
        from modules.rooms.infrastructure.event_listeners import registrar_listeners
        from modules.shared.infrastructure.event_dispatcher import EventDispatcher

        registrar_listeners(EventDispatcher())
