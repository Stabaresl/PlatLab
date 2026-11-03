"""
Prepara datos para las pruebas de carga/estrés (`loadtests/`): crea N
estudiantes de prueba ya inscritos en el laboratorio demo con entorno real
("SQL Injection: Bypass de Login", sembrado por `seed_demo_data`) y escribe
un JSON con un token de acceso de larga duración por usuario.

Por qué tokens "minteados" acá y no un login real por usuario simulado:
`AuthRateLimiter` limita login/refresh a 10 por minuto por IP, y todos los
usuarios virtuales de Locust salen de la misma IP — con login real, la
prueba mediría el rate limiter, no la API. El login se prueba aparte, a un
ritmo por debajo del límite.

Solo para entornos locales/de prueba: se niega a correr con DEBUG=False
salvo que se pase --force.

Uso:
    docker compose exec web python manage.py preparar_carga --estudiantes 300 \\
        --salida loadtests/datos_carga.json --desbloquear-practica
"""

import json
import uuid
from datetime import timedelta
from pathlib import Path

from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand, CommandError
from rest_framework_simplejwt.tokens import AccessToken

from modules.assignments.application.dtos import InscribirseLaboratorioDTO
from modules.assignments.application.use_cases.inscribirse_laboratorio import (
    InscribirseLaboratorioUseCase,
)
from modules.assignments.infrastructure.repositories import AsignacionRepository
from modules.audit.infrastructure.models import RegistroAuditoriaModel
from modules.laboratories.domain.value_objects import TipoLaboratorio
from modules.laboratories.infrastructure.repositories import LaboratorioRepository
from modules.progress.application.dtos import CompletarSeccionTeoricaDTO
from modules.progress.application.use_cases.completar_seccion_teorica import (
    CompletarSeccionTeoricaUseCase,
)
from modules.progress.infrastructure.repositories import ProgresoRepository
from modules.shared.infrastructure.event_dispatcher import EventDispatcher
from modules.shared.infrastructure.unit_of_work import BaseUnitOfWork
from modules.users.domain.entities import User
from modules.users.domain.value_objects import Email, Rol
from modules.users.infrastructure.repositories import UserRepository

_LAB_NOMBRE = "SQL Injection: Bypass de Login"
_PASSWORD_CARGA = "Carga12345"
_DOMINIO = "carga.platlab.test"


def _token(user_id: uuid.UUID, rol: str, horas: int) -> str:
    access = AccessToken()
    access["sub"] = str(user_id)
    access["rol"] = rol
    access.set_exp(lifetime=timedelta(hours=horas))
    return str(access)


class Command(BaseCommand):
    help = "Crea estudiantes de prueba inscritos y exporta tokens para loadtests/."

    def add_arguments(self, parser):
        parser.add_argument("--estudiantes", type=int, default=200)
        parser.add_argument("--salida", default="loadtests/datos_carga.json")
        parser.add_argument("--horas-token", type=int, default=6)
        parser.add_argument(
            "--desbloquear-practica",
            action="store_true",
            help="Completa la sección teórica inicial para que la práctica (entorno real) quede desbloqueada.",
        )
        parser.add_argument(
            "--audit-filas",
            type=int,
            default=0,
            help="Inserta N filas sintéticas de auditoría (mide el costo de listar sin paginar en BD).",
        )
        parser.add_argument("--force", action="store_true")

    def handle(self, *args, **options):
        if not settings.DEBUG and not options["force"]:
            raise CommandError("DEBUG=False: este comando es solo para entornos de prueba (usa --force).")

        lab_repo = LaboratorioRepository()
        laboratorio = next(
            (
                lab
                for lab in lab_repo.find_catalogo(nombre=_LAB_NOMBRE)
                if lab.nombre == _LAB_NOMBRE and lab.tipo == TipoLaboratorio.PREDETERMINADO
            ),
            None,
        )
        if laboratorio is None:
            raise CommandError("No existe el laboratorio demo: corré antes `seed_demo_data`.")
        secciones = lab_repo.get_secciones(laboratorio.id)

        user_repo = UserRepository()
        asignacion_repo = AsignacionRepository()
        progreso_repo = ProgresoRepository()
        password_hash = make_password(_PASSWORD_CARGA)  # un solo hash: PBKDF2 por usuario tardaría minutos

        estudiantes = []
        for i in range(options["estudiantes"]):
            email = f"est{i:04d}@{_DOMINIO}"
            user = user_repo.get_by_email(email) or user_repo.add(
                User(
                    email=Email(email),
                    nombre_completo=f"Estudiante Carga {i:04d}",
                    rol=Rol.ESTUDIANTE,
                    password_hash=password_hash,
                )
            )

            asignacion = next(
                (
                    a
                    for a in asignacion_repo.find_por_estudiante(user.id)
                    if a.laboratorio_id == laboratorio.id and a.esta_vigente()
                ),
                None,
            )
            if asignacion is None:
                resultado = InscribirseLaboratorioUseCase(
                    unit_of_work=BaseUnitOfWork(),
                    event_dispatcher=EventDispatcher(),
                    asignacion_repository=asignacion_repo,
                    laboratorio_repository=lab_repo,
                    progreso_repository=progreso_repo,
                ).execute(
                    InscribirseLaboratorioDTO(
                        laboratorio_id=laboratorio.id, actor_id=user.id, actor_rol="estudiante"
                    )
                )
                asignacion_id = resultado.id
            else:
                asignacion_id = asignacion.id

            if options["desbloquear_practica"] and secciones and not secciones[0].tiene_practica:
                CompletarSeccionTeoricaUseCase(
                    unit_of_work=BaseUnitOfWork(),
                    event_dispatcher=EventDispatcher(),
                    progreso_repository=progreso_repo,
                    laboratorio_repository=lab_repo,
                ).execute(
                    CompletarSeccionTeoricaDTO(
                        asignacion_id=asignacion_id,
                        seccion_id=secciones[0].id,
                        estudiante_id=user.id,
                    )
                )

            estudiantes.append(
                {
                    "email": email,
                    "token": _token(user.id, "estudiante", options["horas_token"]),
                    "asignacion_id": str(asignacion_id),
                }
            )
            if (i + 1) % 50 == 0:
                self.stdout.write(f"  {i + 1} estudiantes listos")

        otros = {}
        for rol, email in (
            ("instructor", "instructor@platlab.demo"),
            ("administrador", "admin@platlab.demo"),
        ):
            u = user_repo.get_by_email(email)
            if u is not None:
                otros[rol] = _token(u.id, rol, options["horas_token"])

        if options["audit_filas"]:
            RegistroAuditoriaModel.objects.bulk_create(
                [
                    RegistroAuditoriaModel(
                        actor_id=None,
                        accion="carga_sintetica",
                        entidad_tipo="carga",
                        entidad_id=uuid.uuid4(),
                    )
                    for _ in range(options["audit_filas"])
                ],
                batch_size=5000,
            )
            self.stdout.write(f"+ {options['audit_filas']} filas de auditoría sintéticas")

        datos = {
            "laboratorio_id": str(laboratorio.id),
            "secciones": [
                {"id": str(s.id), "orden": s.orden, "tiene_practica": s.tiene_practica}
                for s in secciones
            ],
            "password": _PASSWORD_CARGA,
            "estudiantes": estudiantes,
            **otros,
        }
        salida = Path(options["salida"])
        salida.parent.mkdir(parents=True, exist_ok=True)
        salida.write_text(json.dumps(datos, indent=2))
        self.stdout.write(self.style.SUCCESS(f"Listo: {len(estudiantes)} estudiantes -> {salida}"))
