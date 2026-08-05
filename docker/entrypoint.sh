#!/bin/sh
set -e

if [ -n "$POSTGRES_HOST" ]; then
  echo "Esperando a PostgreSQL en $POSTGRES_HOST:$POSTGRES_PORT..."
  while ! nc -z "$POSTGRES_HOST" "$POSTGRES_PORT"; do
    sleep 0.5
  done
  echo "PostgreSQL disponible."
fi

python manage.py migrate --noinput

if [ "$DJANGO_SETTINGS_MODULE" = "config.settings.prod" ]; then
  python manage.py collectstatic --noinput
fi

exec "$@"
