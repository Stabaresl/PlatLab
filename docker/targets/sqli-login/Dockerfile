# Objetivo de práctica "SQL Injection: Bypass de Login" — usado por
# lab_environments (modules/lab_environments) para dar a cada estudiante
# un contenedor descartable y aislado (sin red externa) con un shell real
# (docker exec) y el objetivo vulnerable corriendo en 127.0.0.1:5000.
FROM python:3.12-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends bash curl sqlite3 \
    && rm -rf /var/lib/apt/lists/* \
    # seguridad.md — el objetivo vulnerable no corre como root: si el
    # estudiante (o el flujo de exec_interactivo) escapa del proceso
    # esperado, no gana automáticamente privilegios de root dentro del
    # contenedor (que ya está aislado de red y con cap_drop=ALL, ver
    # docker_provider.py — esto es una capa más, no la única).
    && useradd --no-create-home --shell /bin/bash platlab

WORKDIR /app
COPY app.py /app/app.py
COPY notes.txt /app/notes.txt
RUN chown -R platlab:platlab /app

# Le permite a lab_environments saber cuándo el objetivo ya está
# escuchando (evita la carrera "el estudiante escribe un comando antes de
# que la app interna termine de levantar" — ver docker_provider.py).
#
# --start-interval=1s chequea cada segundo SOLO durante el arranque (para
# detectar "listo" rápido); después, cada 30 s. Antes era --interval=1s
# permanente: un `curl` por segundo en cada contenedor, ~5% de CPU por
# contenedor inactivo — con 100 estudiantes, 4.4 núcleos ocupados sin que
# nadie escribiera un comando (medido en loadtests/estres_entornos.py).
HEALTHCHECK --interval=30s --timeout=2s --retries=3 --start-period=15s --start-interval=1s \
    CMD curl -sf http://127.0.0.1:5000/login.php || exit 1

USER platlab

# El servidor vulnerable corre en foreground como PID 1; el estudiante
# interactúa vía sesiones `docker exec -it <id> bash` separadas, que el
# backend abre bajo demanda (una por conexión de terminal) — heredan el
# mismo usuario no-root de arriba.
CMD ["python3", "/app/app.py"]
