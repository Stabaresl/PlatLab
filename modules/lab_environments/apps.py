from django.apps import AppConfig


class LabEnvironmentsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'modules.lab_environments'

    def ready(self):
        from modules.lab_environments.infrastructure.event_listeners import registrar_listeners
        from modules.shared.infrastructure.event_dispatcher import EventDispatcher

        registrar_listeners(EventDispatcher())
