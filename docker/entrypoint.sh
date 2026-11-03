#!/bin/sh
set -e

if [ -n "$POSTGRES_HOST" ]; then
  echo "Esperando a PostgreSQL en $POSTGRES_HOST:$POSTGRES_PORT..."
  while ! nc -z "$POSTGRES_HOST" "$POSTGRES_PORT"; do
    sleep 0.5
  done
  echo "PostgreSQL disponible."
fi

# Solo el servicio que tenga RUN_MIGRATIONS=1 (web, ver docker-compose.yml)
# migra: si web/worker/beat migran a la vez sobre una base vacía, chocan
# creando las mismas tablas en Postgres (primer arranque de un clon nuevo)
# y el worker se cae con MigrationSchemaMissing.
if [ "${RUN_MIGRATIONS:-0}" = "1" ]; then
  python manage.py migrate --noinput

  # Estáticos del admin de Django (whitenoise) — solo sin DEBUG; en dev los
  # sirve runserver/uvicorn directo desde cada app.
  if [ "$DJANGO_SETTINGS_MODULE" = "config.settings.prod" ] || [ "$DJANGO_SETTINGS_MODULE" = "config.settings.local" ]; then
    python manage.py collectstatic --noinput
  fi
fi

exec "$@"
