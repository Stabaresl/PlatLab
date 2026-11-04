"""
Sala de prueba lista para usar: la abre el instructor demo sobre «Introducción
a TCP/IP» con el código fijo PRUEBA, así se puede probar el flujo completo
(entrar con código, trabajar, ver el tablero) sin crear nada a mano.

Solo tiene sentido con las cuentas demo activas (instalación en modo local).
Idempotente: si la sala ya existe no hace nada.

Uso:
    docker compose exec web python manage.py seed_sala_demo
"""

from django.core.management.base import BaseCommand

from modules.laboratories.infrastructure.models import LaboratorioModel
from modules.rooms.domain.entities import Sala
from modules.rooms.infrastructure.repositories import SalaRepository
from modules.users.infrastructure.repositories import UserRepository

CODIGO_DEMO = "PRUEBA"
_LAB = "Introducción a TCP/IP"


class Command(BaseCommand):
    help = "Crea la sala demo (código PRUEBA) del instructor demo."

    def handle(self, *args, **options):
        repo = SalaRepository()
        if repo.get_by_codigo(CODIGO_DEMO):
            self.stdout.write(f"= la sala demo ya existe (código {CODIGO_DEMO})")
            return
        instructor = UserRepository().get_by_email("instructor@platlab.demo")
        lab = LaboratorioModel.objects.filter(nombre=_LAB, tipo="predeterminado", estado="publicado").first()
        if instructor is None or lab is None:
            self.stdout.write(self.style.WARNING("! faltan el instructor demo o el laboratorio: corre antes los seeds."))
            return
        repo.add(
            Sala(
                nombre="Sala de prueba · Redes",
                descripcion="Sala de demostración: entra con el código PRUEBA desde la cuenta de estudiante.",
                laboratorio_id=lab.id,
                anfitrion_id=instructor.id,
                codigo=CODIGO_DEMO,
                capacidad=100,
            )
        )
        self.stdout.write(self.style.SUCCESS(f"+ sala demo creada (código {CODIGO_DEMO})"))
