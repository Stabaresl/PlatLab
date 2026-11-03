FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Sin build-essential/libpq-dev: todas las dependencias tienen wheels para
# Python 3.12 (psycopg[binary] trae su propia libpq) — imagen ~200 MB más
# chica y builds más rápidos para quien instala el proyecto por primera vez.
RUN apt-get update \
    && apt-get install -y --no-install-recommends netcat-traditional \
    && rm -rf /var/lib/apt/lists/*

COPY requirements/ requirements/
ARG REQUIREMENTS_FILE=requirements/dev.txt
# -c constraints.txt: congela también las dependencias transitivas (ver el
# encabezado de ese archivo).
RUN pip install --no-cache-dir -r ${REQUIREMENTS_FILE} -c requirements/constraints.txt

COPY . .

RUN chmod +x /app/docker/entrypoint.sh

ENTRYPOINT ["/app/docker/entrypoint.sh"]
CMD ["uvicorn", "config.asgi:application", "--host", "0.0.0.0", "--port", "8000", "--lifespan", "off"]
