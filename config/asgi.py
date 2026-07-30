"""
ASGI config for config project — sirve HTTP (Django/DRF, sin cambios) y
WebSocket (Channels, `modules.lab_environments` — terminal de los entornos
de práctica reales) en un solo proceso Daphne.

`get_asgi_application()` DEBE llamarse antes de importar cualquier cosa
que toque modelos de Django (routing de Channels incluido) — si no, falla
con `AppRegistryNotReady`. Ver
https://channels.readthedocs.io/en/stable/installation.html
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')

django_asgi_app = get_asgi_application()

from channels.routing import ProtocolTypeRouter, URLRouter  # noqa: E402

from modules.lab_environments.presentation.routing import websocket_urlpatterns  # noqa: E402
from modules.lab_environments.presentation.ws_auth_middleware import JWTAuthMiddleware  # noqa: E402

application = ProtocolTypeRouter({
    'http': django_asgi_app,
    'websocket': JWTAuthMiddleware(URLRouter(websocket_urlpatterns)),
})
