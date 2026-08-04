"""
Provisioning de cuentas reales (admin + instructor) para producción —
a diferencia de `seed_demo_data.py` (contraseñas fijas y públicas en el
repo, `Admin1234`/`Instructor1234`, pensadas solo para desarrollo local),
este comando genera una contraseña aleatoria criptográficamente segura
por cuenta, la aplica, y la imprime UNA sola vez por stdout — no queda
guardada en ningún lado en texto plano (ni en el repo, ni en variables
de entorno, ni en un archivo).

Uso:
    docker compose exec web python manage.py create_production_users \\
        --admin-email admin@tudominio.com \\
        --instructor-email instructor@tudominio.com

Si una cuenta con ese email ya existe, por defecto NO se toca (para no
resetear por accidente una contraseña que ya está en uso). Pasá
--reset-password si de verdad querés rotarla.

Copiá las contraseñas impresas a un gestor de contraseñas de inmediato:
no se vuelven a mostrar (se guardan solo como hash, como cualquier
contraseña normal del sistema).
"""

import secrets
import string

from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand, CommandError

from modules.shared.domain.exceptions import ValidationError
from modules.users.domain.entities import User
from modules.users.domain.value_objects import Email, Rol
from modules.users.infrastructure.repositories import UserRepository

_ALFABETO = string.ascii_letters + string.digits + "!@#$%^&*-_="


def _generar_password(longitud: int = 20) -> str:
    return "".join(secrets.choice(_ALFABETO) for _ in range(longitud))


class Command(BaseCommand):
    help = "Crea (o rota la contraseña de) las cuentas reales de admin e instructor para producción."

    def add_arguments(self, parser):
        parser.add_argument("--admin-email", required=True)
        parser.add_argument("--admin-nombre", default="Administrador")
        parser.add_argument("--instructor-email", required=True)
        parser.add_argument("--instructor-nombre", default="Instructor")
        parser.add_argument(
            "--reset-password",
            action="store_true",
            help="Si la cuenta ya existe, generarle y aplicarle una contraseña nueva igual.",
        )

    def handle(self, *args, **options):
        user_repository = UserRepository()

        cuentas = [
            (options["admin_email"], options["admin_nombre"], Rol.ADMINISTRADOR),
            (options["instructor_email"], options["instructor_nombre"], Rol.INSTRUCTOR),
        ]

        try:
            emails_validados = [(Email(email), nombre, rol) for email, nombre, rol in cuentas]
        except ValidationError as exc:
            raise CommandError(f"Email inválido: {exc.message}") from exc

        resultados = []
        for email, nombre, rol in emails_validados:
            existente = user_repository.get_by_email(str(email))
            password = _generar_password()

            if existente is None:
                user_repository.add(
                    User(
                        email=email,
                        nombre_completo=nombre,
                        rol=rol,
                        password_hash=make_password(password),
                    )
                )
                resultados.append((str(email), rol.value, password, "creada"))
                continue

            if not options["reset_password"]:
                self.stdout.write(
                    self.style.WARNING(
                        f"= {email} ya existe ({existente.rol.value}) — no se tocó. "
                        "Usá --reset-password si querés rotarla."
                    )
                )
                continue

            existente.password_hash = make_password(password)
            user_repository.update(existente)
            resultados.append((str(email), existente.rol.value, password, "contraseña rotada"))

        if not resultados:
            self.stdout.write("Nada para mostrar — ninguna cuenta fue creada ni rotada.")
            return

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write(self.style.SUCCESS("CREDENCIALES — guardalas ahora, no se vuelven a mostrar:"))
        self.stdout.write(self.style.SUCCESS("=" * 60))
        for email, rol, password, accion in resultados:
            self.stdout.write(f"  [{accion}] {rol:<14} {email}")
            self.stdout.write(f"    contraseña: {password}")
        self.stdout.write(self.style.SUCCESS("=" * 60))
