from django.apps import AppConfig


class AuditConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'modules.audit'

    def ready(self):
        from modules.audit.infrastructure.event_listeners import registrar_listeners
        from modules.shared.infrastructure.event_dispatcher import EventDispatcher

        registrar_listeners(EventDispatcher())
