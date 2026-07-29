"""
Bootstrap de Celery (worker + Beat) para el proyecto. `CELERY_BROKER_URL`/
`CELERY_RESULT_BACKEND` ya están definidos en `config/settings/base.py`
(Redis, reutilizando `REDIS_URL`).
"""
import os

from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')

app = Celery('platlab')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
# `autodiscover_tasks()` sin argumentos solo busca `<app>.tasks` en la
# raíz de cada app instalada — nuestros módulos de tareas viven en
# `infrastructure/` (y con nombres distintos, ej. `celery_tasks.py` en
# Notifications), por lo que se registran explícitamente acá.
app.conf.imports = (
    'modules.assignments.infrastructure.tasks',
    'modules.notifications.infrastructure.celery_tasks',
)

# RF-32, UC-07: revisa asignaciones vencidas cada 15 minutos (frecuencia
# indicativa de casos-de-uso.md, ajustable vía este schedule sin tocar
# el job ni el caso de uso).
app.conf.beat_schedule = {
    'cerrar-asignaciones-vencidas': {
        'task': 'modules.assignments.infrastructure.tasks.cerrar_asignaciones_vencidas_task',
        'schedule': 900.0,
    },
}
