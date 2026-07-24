from .base import *  # noqa
from .base import env

DEBUG = False

if not ALLOWED_HOSTS:
    raise Exception('ALLOWED_HOSTS debe estar definido explícitamente en producción')

SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
X_FRAME_OPTIONS = 'DENY'
