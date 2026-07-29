"""
Settings de test: hereda de `dev.py` pero corre Celery en modo síncrono
(`ALWAYS_EAGER`) para que los tests no dependan de un broker Redis real
ni de un worker corriendo — necesario desde Sprint 5, donde Notifications
y Audit escuchan eventos que cualquier caso de uso puede disparar
(`EventDispatcher`, ahora singleton por proceso).
"""
from config.settings.dev import *  # noqa

CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
