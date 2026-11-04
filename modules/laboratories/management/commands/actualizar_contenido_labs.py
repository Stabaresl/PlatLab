"""
Pone al día el contenido de los laboratorios predeterminados con el formato de
guía estilo AWS: escenario, objetivos, tareas numeradas con comando y resultado
esperado, una consola simulada con su máquina (archivos, red, servicios), ayuda
progresiva de la flag, examen final y conclusión.

Actualiza en su lugar (mismas secciones, mismos ids, mismas flags), así que se
puede correr sobre una instalación con estudiantes a mitad de camino sin perder
su avance. Es idempotente. Lo corre el instalador después de los seeds.

Uso:
    docker compose exec web python manage.py actualizar_contenido_labs
    docker compose exec web python manage.py actualizar_contenido_labs --solo "Introducción a TCP/IP"
"""

from dataclasses import replace

from django.core.management.base import BaseCommand
from django.db import transaction

from modules.laboratories.application.dtos import AgregarPreguntaDTO, CrearExamenDTO
from modules.laboratories.application.use_cases.agregar_pregunta import AgregarPreguntaUseCase
from modules.laboratories.application.use_cases.crear_examen import CrearExamenUseCase
from modules.laboratories.domain.value_objects import (
    AyudaProgresiva,
    ComandoSimulado,
    EntornoPractica,
    PasoGuia,
    TipoLaboratorio,
)
from modules.laboratories.infrastructure.cached_laboratorio_repository import CachedLaboratorioRepository
from modules.laboratories.infrastructure.content_sanitizer import sanitizar_contenido_html
from modules.laboratories.infrastructure.models import LaboratorioModel
from modules.laboratories.infrastructure.repositories import LaboratorioRepository
from modules.shared.infrastructure.event_dispatcher import EventDispatcher
from modules.shared.infrastructure.unit_of_work import BaseUnitOfWork
from modules.users.infrastructure.repositories import UserRepository

from ._contenido_cripto import LABS as LABS_CRIPTO
from ._contenido_redes import LABS as LABS_REDES
from ._contenido_web import LABS as LABS_WEB

LABS = [*LABS_REDES, *LABS_WEB, *LABS_CRIPTO]
_INSTRUCTOR_DEMO = "instructor@platlab.demo"


def _entorno(datos: dict | None) -> EntornoPractica | None:
    if not datos:
        return None
    return EntornoPractica(
        prompt=datos.get("prompt", "estudiante@kali:~$"),
        banner=datos.get("banner", ""),
        comandos=[ComandoSimulado.desde_dict(c) for c in datos.get("comandos", [])],
        escenario=datos.get("escenario") or {},
    )


def _pasos(pasos: list[tuple]) -> list[PasoGuia]:
    return [
        PasoGuia(
            orden=i + 1,
            titulo=titulo,
            instrucciones=sanitizar_contenido_html(instrucciones),
            comando_sugerido=comando,
            resultado_esperado=esperado,
        )
        for i, (titulo, instrucciones, comando, esperado) in enumerate(pasos)
    ]


class Command(BaseCommand):
    help = "Actualiza los laboratorios predeterminados con guías paso a paso, consola realista y examen."

    def add_arguments(self, parser):
        parser.add_argument("--solo", help="Nombre exacto de un laboratorio para actualizar solo ese.")

    def handle(self, *args, **options):
        repo = LaboratorioRepository()
        admin = UserRepository().get_by_email("admin@platlab.demo")
        instructor_demo = UserRepository().get_by_email(_INSTRUCTOR_DEMO)
        objetivo = options.get("solo")
        actualizados = 0

        for datos in LABS:
            if objetivo and datos["nombre"] != objetivo:
                continue
            plantilla = LaboratorioModel.objects.filter(
                nombre=datos["nombre"], tipo=TipoLaboratorio.PREDETERMINADO.value
            ).first()
            if plantilla is None:
                self.stdout.write(self.style.WARNING(f"! no existe «{datos['nombre']}»: corre antes los seeds."))
                continue

            labs = [repo.get_by_id(plantilla.id)]
            # La copia demo del instructor (seed_demo_data) es la que tiene asignada el
            # estudiante demo: se actualiza igual para que vea la guía nueva.
            if instructor_demo:
                labs += [
                    repo.get_by_id(c.id)
                    for c in LaboratorioModel.objects.filter(origen_id=plantilla.id, instructor_id=instructor_demo.id)
                ]

            for lab in labs:
                with transaction.atomic():
                    self._actualizar(repo, lab, datos)
                actualizados += 1
                tipo = "copia del instructor demo" if lab.tipo != TipoLaboratorio.PREDETERMINADO else "plantilla"
                self.stdout.write(self.style.SUCCESS(f"+ {datos['nombre']} ({tipo})"))

            if datos.get("examen") and admin is not None:
                self._crear_examen(repo, plantilla.id, datos["examen"], admin.id)

        CachedLaboratorioRepository(repo).invalidar_catalogo()
        self.stdout.write(self.style.SUCCESS(f"Listo — {actualizados} laboratorio(s) actualizados."))

    def _actualizar(self, repo: LaboratorioRepository, lab, datos: dict) -> None:
        lab.descripcion = datos["descripcion"]
        lab.resumen_cierre = sanitizar_contenido_html(datos["resumen_cierre"])
        repo.update(lab)

        secciones = sorted(repo.get_secciones(lab.id), key=lambda s: s.orden)
        for seccion, sdatos in zip(secciones, datos["secciones"], strict=False):
            entorno = _entorno(sdatos.get("entorno"))
            actualizada = replace(
                seccion,
                titulo=sdatos["titulo"],
                contenido_teorico=sanitizar_contenido_html(sdatos["html"]),
                objetivos=sdatos["objetivos"],
                duracion_estimada_minutos=sdatos["duracion"],
                pasos_guia=_pasos(sdatos.get("pasos", [])),
                entorno_practica=entorno if entorno is not None else seccion.entorno_practica,
            )
            repo.update_seccion(actualizada)

            if seccion.tiene_practica and datos.get("flag"):
                flag = repo.get_flag_by_seccion(seccion.id)
                if flag is not None:
                    ayuda = AyudaProgresiva(pista=datos["flag"]["pista"], paso_a_paso=datos["flag"]["paso_a_paso"])
                    repo.save_flag(replace(flag, ayuda=ayuda))
        if len(secciones) != len(datos["secciones"]):
            self.stdout.write(
                self.style.WARNING(
                    f"  ! «{lab.nombre}» tiene {len(secciones)} secciones y el contenido trae "
                    f"{len(datos['secciones'])}: se actualizaron las que coinciden por orden."
                )
            )

    def _crear_examen(self, repo: LaboratorioRepository, laboratorio_id, preguntas: list[dict], admin_id) -> None:
        if repo.get_examen_by_laboratorio(laboratorio_id) is not None:
            return
        kwargs = {
            "unit_of_work": BaseUnitOfWork(),
            "event_dispatcher": EventDispatcher(),
            "laboratorio_repository": repo,
        }
        CrearExamenUseCase(**kwargs).execute(
            CrearExamenDTO(laboratorio_id=laboratorio_id, actor_id=admin_id, actor_rol="administrador")
        )
        for p in preguntas:
            AgregarPreguntaUseCase(**kwargs).execute(
                AgregarPreguntaDTO(
                    laboratorio_id=laboratorio_id,
                    enunciado=p["enunciado"],
                    tipo=p["tipo"],
                    respuesta=p["respuesta"],
                    opciones=p.get("opciones"),
                    actor_id=admin_id,
                    actor_rol="administrador",
                )
            )
        self.stdout.write(f"  + examen con {len(preguntas)} preguntas")
