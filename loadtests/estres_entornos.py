"""
Estrés de entornos de práctica reales (lab_environments): N estudiantes
piden su contenedor al mismo tiempo — mide cuántos llegan a `activo`, cuánto
tardan (p50/p95/máx), cuántos fallan (`error`) y cuántos rechaza el cupo
(429, LAB_ENV_MAX_CONCURRENTES). Es el escenario de "abrir una sala de
clase": todos arrancan su entorno en el mismo minuto.

Requiere `preparar_carga --desbloquear-practica` (la sección práctica tiene
que estar desbloqueada para poder iniciar el entorno).

Uso (dentro del contenedor web, que ya tiene `requests`):
    docker compose exec web python loadtests/estres_entornos.py --n 20
    docker compose exec web python loadtests/estres_entornos.py --detener
"""

import argparse
import json
import statistics
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests

API = "/api/v1"


def _cargar(path: str) -> dict:
    return json.loads(Path(path).read_text())


def _arrancar(host: str, est: dict, seccion_id: str, timeout_s: float) -> dict:
    headers = {"Authorization": f"Bearer {est['token']}"}
    base = f"{host}{API}/lab-environments/{est['asignacion_id']}/sections/{seccion_id}"
    t0 = time.monotonic()
    r = requests.post(f"{base}/start/", headers=headers, timeout=30)
    if r.status_code == 429:
        return {"resultado": "sin_cupo", "segundos": time.monotonic() - t0}
    if r.status_code != 200:
        return {"resultado": f"http_{r.status_code}", "segundos": time.monotonic() - t0}

    while time.monotonic() - t0 < timeout_s:
        estado = requests.get(f"{base}/status/", headers=headers, timeout=30).json()
        if estado.get("activo") and estado.get("estado") == "activo":
            return {"resultado": "activo", "segundos": time.monotonic() - t0}
        if not estado.get("activo"):
            return {"resultado": "error", "segundos": time.monotonic() - t0}
        time.sleep(1)
    return {"resultado": "timeout", "segundos": time.monotonic() - t0}


def _detener_todos(host: str, datos: dict, seccion_id: str) -> int:
    detenidos = 0
    for est in datos["estudiantes"]:
        headers = {"Authorization": f"Bearer {est['token']}"}
        base = f"{host}{API}/lab-environments/{est['asignacion_id']}/sections/{seccion_id}"
        estado = requests.get(f"{base}/status/", headers=headers, timeout=30).json()
        if estado.get("activo") and estado.get("id"):
            requests.post(f"{host}{API}/lab-environments/{estado['id']}/stop/", headers=headers, timeout=60)
            detenidos += 1
    return detenidos


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=10, help="estudiantes que arrancan a la vez")
    parser.add_argument("--host", default="http://localhost:8000")
    parser.add_argument("--datos", default="loadtests/datos_carga.json")
    parser.add_argument("--timeout", type=float, default=120)
    parser.add_argument("--detener", action="store_true", help="solo apaga los entornos activos")
    args = parser.parse_args()

    datos = _cargar(args.datos)
    seccion = next(s["id"] for s in datos["secciones"] if s["tiene_practica"])

    if args.detener:
        print(f"detenidos: {_detener_todos(args.host, datos, seccion)}")
        return

    estudiantes = datos["estudiantes"][: args.n]
    t0 = time.monotonic()
    with ThreadPoolExecutor(max_workers=len(estudiantes)) as pool:
        resultados = list(
            pool.map(lambda e: _arrancar(args.host, e, seccion, args.timeout), estudiantes)
        )
    total = time.monotonic() - t0

    conteo: dict[str, int] = {}
    for r in resultados:
        conteo[r["resultado"]] = conteo.get(r["resultado"], 0) + 1
    activos = sorted(r["segundos"] for r in resultados if r["resultado"] == "activo")

    print(json.dumps(conteo))
    if activos:
        p95 = activos[min(len(activos) - 1, int(len(activos) * 0.95))]
        print(
            f"tiempo a 'activo': p50={statistics.median(activos):.1f}s "
            f"p95={p95:.1f}s max={activos[-1]:.1f}s"
        )
    print(f"duración total del escenario: {total:.1f}s")


if __name__ == "__main__":
    main()
