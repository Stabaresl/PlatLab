from django.urls import re_path

from modules.lab_environments.presentation.consumers import TerminalConsumer

websocket_urlpatterns = [
    re_path(
        r"^ws/lab-environments/(?P<entorno_id>[0-9a-fA-F-]+)/terminal/$",
        TerminalConsumer.as_asgi(),
    ),
]
