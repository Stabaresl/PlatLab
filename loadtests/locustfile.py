"""
Pruebas de carga/estrés de PlatLAB (RNF-02: ≥100 usuarios concurrentes sin
degradación, carga de página ≤3 s, validación de flag <1 s).

Antes de correr: `python manage.py preparar_carga --estudiantes N
--desbloquear-practica` (crea los usuarios y `datos_carga.json`). Ver
`loadtests/README.md` para los comandos completos.

Mezcla de usuarios (pesos relativos, aproximan el uso real de una clase):
  - EstudianteUser (6): dashboard, progreso, contenido de sección, campana
    de notificaciones (poll cada 60 s en el frontend), perfil de
    gamificación, intentos de flag.
  - VisitanteUser (3): landing pública — catálogo, detalle, TOC, roadmap.
  - InstructorUser (1): panel y seguimiento de estudiantes.
  - AdminUser (1): dashboard, usuarios, auditoría, cola de revisión.
"""

import itertools
import json
import os
import random
from pathlib import Path

from locust import HttpUser, between, task

_DATOS = json.loads(
    Path(os.environ.get("DATOS_CARGA", Path(__file__).with_name("datos_carga.json"))).read_text()
)
_ESTUDIANTES = itertools.cycle(_DATOS["estudiantes"])
_LAB_ID = _DATOS["laboratorio_id"]
_SECCIONES = _DATOS["secciones"]
_SECCION_TEORIA = next((s["id"] for s in _SECCIONES if not s["tiene_practica"]), _SECCIONES[0]["id"])
_SECCION_PRACTICA = next((s["id"] for s in _SECCIONES if s["tiene_practica"]), None)

API = "/api/v1"
# Locust apunta a http://web:8000 dentro de la red de compose; Django
# rechaza (400 DisallowedHost) cualquier Host fuera de ALLOWED_HOSTS.
_HOST_HEADER = os.environ.get("HOST_HEADER", "localhost")


class _Base(HttpUser):
    abstract = True

    def on_start(self):
        self.client.headers["Host"] = _HOST_HEADER


class EstudianteUser(_Base):
    weight = 6
    wait_time = between(1, 3)

    def on_start(self):
        super().on_start()
        datos = next(_ESTUDIANTES)
        self.asig = datos["asignacion_id"]
        self.client.headers["Authorization"] = f"Bearer {datos['token']}"

    @task(2)
    def dashboard_asignaciones(self):
        self.client.get(f"{API}/assignments/", name="/assignments/")

    @task(3)
    def progreso(self):
        self.client.get(f"{API}/progress/{self.asig}/", name="/progress/[asig]/")

    @task(3)
    def contenido_seccion(self):
        self.client.get(
            f"{API}/progress/{self.asig}/sections/{_SECCION_TEORIA}/",
            name="/progress/[asig]/sections/[sec]/",
        )

    @task(2)
    def notificaciones(self):
        self.client.get(f"{API}/notifications/?limit=50", name="/notifications/")

    @task(2)
    def perfil_gamificacion(self):
        self.client.get(f"{API}/gamification/me/", name="/gamification/me/")

    @task(2)
    def catalogo(self):
        self.client.get(f"{API}/laboratories/", name="/laboratories/")

    @task(1)
    def roadmap(self):
        self.client.get(f"{API}/roadmap/", name="/roadmap/")

    @task(1)
    def intento_flag(self):
        if _SECCION_PRACTICA is None:
            return
        # Flag incorrecta a propósito: mide el costo de la validación
        # (PBKDF2) sin completar la sección, así la prueba es repetible.
        with self.client.post(
            f"{API}/progress/{self.asig}/sections/{_SECCION_PRACTICA}/flag/",
            json={"valor": f"FLAG{{intento_{random.randint(0, 10**6)}}}"},
            name="/progress/[asig]/sections/[sec]/flag/",
            catch_response=True,
        ) as resp:
            # 403 = sección bloqueada (preparar_carga sin --desbloquear-practica),
            # 429 = rate limit por usuario+sección: ambos son respuestas
            # esperadas del sistema, no fallas de capacidad.
            if resp.status_code in (200, 403, 429):
                resp.success()


class VisitanteUser(_Base):
    weight = 3
    wait_time = between(1, 4)

    @task(1)
    def health(self):
        self.client.get(f"{API}/health/", name="/health/")

    @task(4)
    def catalogo(self):
        self.client.get(f"{API}/laboratories/", name="/laboratories/ (anon)")

    @task(2)
    def detalle(self):
        self.client.get(f"{API}/laboratories/{_LAB_ID}/", name="/laboratories/[id]/")
        self.client.get(f"{API}/laboratories/{_LAB_ID}/toc/", name="/laboratories/[id]/toc/")

    @task(2)
    def roadmap(self):
        self.client.get(f"{API}/roadmap/", name="/roadmap/ (anon)")


class InstructorUser(_Base):
    weight = 1
    wait_time = between(2, 5)

    def on_start(self):
        super().on_start()
        token = _DATOS.get("instructor")
        if token:
            self.client.headers["Authorization"] = f"Bearer {token}"

    @task(2)
    def panel(self):
        self.client.get(f"{API}/assignments/dashboard/", name="/assignments/dashboard/")

    @task(2)
    def estudiantes(self):
        self.client.get(f"{API}/assignments/students", name="/assignments/students")

    @task(1)
    def asignaciones(self):
        self.client.get(f"{API}/assignments/", name="/assignments/ (instr)")


class AdminUser(_Base):
    weight = 1
    wait_time = between(2, 5)

    def on_start(self):
        super().on_start()
        token = _DATOS.get("administrador")
        if token:
            self.client.headers["Authorization"] = f"Bearer {token}"

    @task(2)
    def dashboard(self):
        self.client.get(f"{API}/users/dashboard/", name="/users/dashboard/")

    @task(1)
    def usuarios(self):
        self.client.get(f"{API}/users/?limit=100", name="/users/")

    @task(1)
    def auditoria(self):
        self.client.get(f"{API}/audit/", name="/audit/")

    @task(1)
    def cola_revision(self):
        self.client.get(f"{API}/laboratories/review-queue/", name="/laboratories/review-queue/")
