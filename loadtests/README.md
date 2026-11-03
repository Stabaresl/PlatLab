# Pruebas de carga y estrés — PlatLAB

Miden los RNF de rendimiento (RNF-02): ≥100 usuarios concurrentes sin
degradación, carga de página ≤3 s, validación de flag <1 s, y la capacidad
de entornos Docker reales (una sala de clase arrancando a la vez).

## 1. Preparar datos (una vez por corrida)

Con el stack arriba (`docker compose up -d`) y los seeds cargados
(`seed_demo_data`, `seed_roadmap_labs`, `seed_labs_expansion`,
`seed_gamification_catalog`):

```bash
docker compose exec web python manage.py preparar_carga \
    --estudiantes 300 --desbloquear-practica --audit-filas 50000
```

Crea 300 estudiantes inscritos en el laboratorio demo y escribe
`loadtests/datos_carga.json` (tokens de 6 h — no se commitea). Los tokens se
generan directamente porque el rate limit de login (10/min por IP) bloquearía
a cientos de usuarios simulados que salen de la misma IP.

## 2. Carga y estrés HTTP (Locust)

Locust corre en un contenedor dentro de la red de compose (en Git Bash de
Windows anteponer `MSYS_NO_PATHCONV=1` y usar `$(pwd -W)`):

```bash
# Carga: 100 usuarios, 150 s
docker run --rm --network platlab_default -v "$(pwd)/loadtests:/mnt/locust" \
  -e DATOS_CARGA=/mnt/locust/datos_carga.json locustio/locust:2.32.4 \
  -f /mnt/locust/locustfile.py --headless -u 100 -r 10 -t 150s \
  --host http://web:8000 --csv /mnt/locust/resultados/carga100 --only-summary

# Estrés: rampa hasta 1000 usuarios (4 procesos de Locust)
docker run --rm --network platlab_default -v "$(pwd)/loadtests:/mnt/locust" \
  -e DATOS_CARGA=/mnt/locust/datos_carga.json locustio/locust:2.32.4 \
  -f /mnt/locust/locustfile.py --headless --processes 4 -u 1000 -r 8 -t 160s \
  --host http://web:8000 --csv /mnt/locust/resultados/estres1000 --csv-full-history --only-summary
```

## 3. Estrés de entornos Docker (sala de clase)

N estudiantes pulsan "Iniciar entorno" al mismo tiempo:

```bash
docker compose exec web python loadtests/estres_entornos.py --n 100
docker compose exec web python loadtests/estres_entornos.py --detener
```

Si N supera `LAB_ENV_MAX_CONCURRENTES`, el resto recibe 429 (cupo).

## Resultados de referencia (laptop 12 CPU / 8 GB en WSL2, nov 2026)

| Escenario | Antes de optimizar | Después |
|---|---|---|
| 100 usuarios — p50 / p95 / p99 | 470 ms / 2,7 s / 4,2 s | 14 ms / 51 ms / 240 ms |
| 300 usuarios — errores / p95 | 6 % (500) / 8,8 s | 0 % / 75 ms |
| Punto de saturación | ~70 usuarios, ~30 req/s | ~600 usuarios, ~220 req/s (4 procesos web) |
| Validar flag bajo carga (p50) | 760 ms (100 usr) – 5,2 s (300 usr) | 30 ms |
| `/audit/` con 50k filas | 1,0–1,7 s | 14 ms |
| 100 entornos a la vez — p95 hasta terminal | 148 s | 21 s |
| CPU en reposo con 100 contenedores | 439 % | 17 % |
| RAM por contenedor de práctica | ~14 MiB | ~14 MiB |
