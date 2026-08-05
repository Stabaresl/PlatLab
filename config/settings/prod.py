from .base import *  # noqa
from .base import env

DEBUG = False

if not ALLOWED_HOSTS:
    raise Exception('ALLOWED_HOSTS debe estar definido explícitamente en producción')

# Caddy (docker-compose.prod.yml) termina TLS y reenvía por HTTP dentro de
# la red interna de compose — sin esto, Django ve cada request como HTTP y
# SECURE_SSL_REDIRECT lo manda de vuelta a HTTPS en loop infinito. Caddy
# setea X-Forwarded-Proto automáticamente en todo proxy_reverse.
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
X_FRAME_OPTIONS = 'DENY'
