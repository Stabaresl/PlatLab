"""
Instalación local / aula (platlab.ps1, platlab.sh, docker-compose.local.yml).

Mismo endurecimiento que producción (DEBUG apagado, sin páginas de error con
trazas, clickjacking bloqueado) pero sobre HTTP dentro de la red local: no hay
dominio para pedir un certificado, así que cookies `Secure`, redirect a HTTPS
y HSTS romperían el login al entrar por IP. Para internet usar `prod.py`.
"""

from .base import *  # noqa
from .base import env

DEBUG = False

# Django no está publicado: solo el gateway (Caddy) llega a web:8000. Quien
# entra lo hace por localhost o por la IP del equipo anfitrión, que cambia
# con el DHCP del aula; la plataforma no arma URLs absolutas a partir del
# Host (no hay enlaces por correo), así que no hay envenenamiento de Host
# que proteger y fijar IPs aquí solo produciría errores 400 al cambiar de red.
ALLOWED_HOSTS = env.list('PLATLAB_ALLOWED_HOSTS', default=['*'])

X_FRAME_OPTIONS = 'DENY'
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'
