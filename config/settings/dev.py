from .base import *  # noqa
from .base import env

DEBUG = True

if not ALLOWED_HOSTS:
    ALLOWED_HOSTS = ['localhost', '127.0.0.1']
