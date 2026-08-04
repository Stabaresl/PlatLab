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

# RNF estabilidad: sin límites, una tarea colgada (ej. una llamada a
# Docker que nunca responde en el reaper) ocupa ese worker para siempre.
# `acks_late` + `reject_on_worker_lost` hacen que una tarea que estaba
# corriendo cuando el worker murió se reencole en otro worker en vez de
# perderse — seguro acá porque todas las tareas son idempotentes
# (reintentar "aprovisionar"/"reap" un entorno que ya se resolvió no hace
# nada, ver los guard clauses en cada caso de uso). Cada tarea puede
# pisar `task_time_limit` si necesita algo más corto (ver
# aprovisionar_entorno_task).
app.conf.update(
    task_time_limit=300,
    task_soft_time_limit=240,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
)

app.autodiscover_tasks()
# `autodiscover_tasks()` sin argumentos solo busca `<app>.tasks` en la
# raíz de cada app instalada — nuestros módulos de tareas viven en
# `infrastructure/` (y con nombres distintos, ej. `celery_tasks.py` en
# Notifications), por lo que se registran explícitamente acá.
app.conf.imports = (
    'modules.assignments.infrastructure.tasks',
    'modules.notifications.infrastructure.celery_tasks',
    'modules.lab_environments.infrastructure.tasks',
    'modules.users.infrastructure.celery_tasks',
)

# RF-32, UC-07: revisa asignaciones vencidas cada 15 minutos (frecuencia
# indicativa de casos-de-uso.md, ajustable vía este schedule sin tocar
# el job ni el caso de uso).
app.conf.beat_schedule = {
    'cerrar-asignaciones-vencidas': {
        'task': 'modules.assignments.infrastructure.tasks.cerrar_asignaciones_vencidas_task',
        'schedule': 900.0,
    },
    # Entornos de práctica reales: se revisan más seguido que las
    # asignaciones (su ciclo de vida es de minutos, no de semanas) — sin
    # esto, un contenedor olvidado sigue consumiendo CPU/memoria del host
    # indefinidamente.
    'reap-entornos-inactivos': {
        'task': 'modules.lab_environments.infrastructure.tasks.reap_idle_environments_task',
        'schedule': 120.0,
    },
}
