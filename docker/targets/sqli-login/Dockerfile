# Objetivo de práctica "SQL Injection: Bypass de Login" — usado por
# lab_environments (modules/lab_environments) para dar a cada estudiante
# un contenedor descartable y aislado (sin red externa) con un shell real
# (docker exec) y el objetivo vulnerable corriendo en 127.0.0.1:5000.
FROM python:3.12-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends bash curl sqlite3 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY app.py /app/app.py
COPY notes.txt /app/notes.txt

# Le permite a lab_environments saber cuándo el objetivo ya está
# escuchando (evita la carrera "el estudiante escribe un comando antes de
# que la app interna termine de levantar" — ver docker_provider.py).
HEALTHCHECK --interval=1s --timeout=2s --retries=5 --start-period=5s \
    CMD curl -sf http://127.0.0.1:5000/login.php || exit 1

# El servidor vulnerable corre en foreground como PID 1; el estudiante
# interactúa vía sesiones `docker exec -it <id> bash` separadas, que el
# backend abre bajo demanda (una por conexión de terminal).
CMD ["python3", "/app/app.py"]
