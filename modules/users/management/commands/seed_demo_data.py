"""
Comando de datos demo para probar el frontend sin cargar nada a mano.

Crea (si no existen todavía, por email) tres usuarios — uno por rol — y
reproduce el flujo real de la plataforma en vez de un laboratorio suelto:

1. El admin demo crea un laboratorio `predeterminado` (plantilla), con
   secciones + flag, y lo publica -> aparece en el catálogo público
   (`/laboratorios`, HV-02) para cualquiera, sin necesidad de invitación.
2. El instructor demo lo *duplica* (UC-05, igual que haría un instructor
   real desde "Ver detalle" en el catálogo) -> obtiene su propia copia
   `personalizado`, la publica y le agrega el examen (la duplicación
   copia secciones+flags pero no el examen, a propósito — el instructor
   siempre debe revisarlo/recrearlo).
3. El instructor invita al estudiante demo a *su copia* (no a la
   plantilla — un `predeterminado` no se puede asignar directamente,
   dominio.md §4) y la invitación se acepta, inicializando el progreso.

Con esto: la plantilla es visible en el catálogo para cualquier
visitante, y el estudiante ve su copia asignada en su Dashboard (antes
de este cambio, un laboratorio `personalizado` asignado no aparecía en
el catálogo público *por diseño* — es privado del instructor — pero
tampoco se podía ver su detalle/TOC desde el Dashboard del estudiante
por un bug en la visibilidad; ver `ObtenerDetalleLaboratorioQuery`).

Uso:
    docker compose exec web python manage.py seed_demo_data

Es idempotente: si ya corriste el comando antes, no duplica usuarios, la
plantilla ni la copia del instructor (aunque sí puede seguir intentando
invitar/aceptar si esos pasos anteriores no llegaron a completarse).
"""

from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand

from modules.assignments.application.dtos import AceptarInvitacionDTO, InvitarEstudiantesDTO
from modules.assignments.application.use_cases.aceptar_invitacion import (
    AceptarInvitacionUseCase,
)
from modules.assignments.application.use_cases.invitar_estudiantes import (
    InvitarEstudiantesUseCase,
)
from modules.assignments.infrastructure.repositories import AsignacionRepository
from modules.laboratories.application.dtos import (
    AgregarPreguntaDTO,
    CrearExamenDTO,
    CrearLaboratorioDTO,
    CrearSeccionDTO,
    DefinirFlagDTO,
    DuplicarLaboratorioDTO,
    PublicarLaboratorioDTO,
)
from modules.laboratories.application.use_cases.agregar_pregunta import AgregarPreguntaUseCase
from modules.laboratories.application.use_cases.crear_examen import CrearExamenUseCase
from modules.laboratories.application.use_cases.crear_laboratorio import (
    CrearLaboratorioUseCase,
)
from modules.laboratories.application.use_cases.crear_seccion import CrearSeccionUseCase
from modules.laboratories.application.use_cases.definir_flag import DefinirFlagUseCase
from modules.laboratories.application.use_cases.duplicar_laboratorio import (
    DuplicarLaboratorioUseCase,
)
from modules.laboratories.application.use_cases.publicar_laboratorio import (
    PublicarLaboratorioUseCase,
)
from modules.laboratories.domain.value_objects import TipoLaboratorio
from modules.laboratories.infrastructure.repositories import LaboratorioRepository
from modules.progress.infrastructure.repositories import ProgresoRepository
from modules.shared.domain.exceptions import DomainError
from modules.shared.infrastructure.event_dispatcher import EventDispatcher
from modules.shared.infrastructure.unit_of_work import BaseUnitOfWork
from modules.users.domain.entities import User
from modules.users.domain.value_objects import Email, Rol
from modules.users.infrastructure.repositories import UserRepository

_LAB_NOMBRE = "SQL Injection: Bypass de Login"

_DEMO_USERS = [
    {
        "email": "admin@platlab.demo",
        "password": "Admin1234",
        "nombre_completo": "Admin Demo",
        "rol": Rol.ADMINISTRADOR,
    },
    {
        "email": "instructor@platlab.demo",
        "password": "Instructor1234",
        "nombre_completo": "Instructor Demo",
        "rol": Rol.INSTRUCTOR,
    },
    {
        "email": "estudiante@platlab.demo",
        "password": "Estudiante1234",
        "nombre_completo": "Estudiante Demo",
        "rol": Rol.ESTUDIANTE,
    },
]


def _use_case_kwargs(laboratorio_repository):
    return {
        "unit_of_work": BaseUnitOfWork(),
        "event_dispatcher": EventDispatcher(),
        "laboratorio_repository": laboratorio_repository,
    }


class Command(BaseCommand):
    help = "Crea usuarios demo (admin/instructor/estudiante) y un laboratorio de ejemplo."

    def handle(self, *args, **options):
        user_repository = UserRepository()

        usuarios = {}
        for data in _DEMO_USERS:
            existente = user_repository.get_by_email(data["email"])
            if existente:
                usuarios[data["rol"]] = existente
                self.stdout.write(f"= usuario ya existe: {data['email']} ({data['rol'].value})")
                continue
            creado = user_repository.add(
                User(
                    email=Email(data["email"]),
                    nombre_completo=data["nombre_completo"],
                    rol=data["rol"],
                    password_hash=make_password(data["password"]),
                )
            )
            usuarios[data["rol"]] = creado
            self.stdout.write(
                self.style.SUCCESS(f"+ usuario creado: {data['email']} ({data['rol'].value})")
            )

        admin = usuarios[Rol.ADMINISTRADOR]
        instructor = usuarios[Rol.INSTRUCTOR]
        estudiante = usuarios[Rol.ESTUDIANTE]

        laboratorio_repository = LaboratorioRepository()

        template = self._buscar_template_existente(laboratorio_repository)
        if template:
            self.stdout.write(f"= plantilla del catálogo ya existe: {template.id}")
        else:
            template = self._crear_template_demo(laboratorio_repository, admin)
            self.stdout.write(
                self.style.SUCCESS(f"+ plantilla creada y publicada en el catálogo: {template.id}")
            )

        copia = self._buscar_copia_existente(laboratorio_repository, instructor.id, template.id)
        if copia:
            self.stdout.write(f"= copia del instructor ya existe: {copia.id}")
        else:
            copia = self._crear_copia_instructor(laboratorio_repository, instructor, template)
            msg = f"+ copia del instructor creada, publicada y con examen: {copia.id}"
            self.stdout.write(self.style.SUCCESS(msg))

        self._asignar_a_estudiante(instructor, estudiante, copia.id)

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("Listo. Credenciales de prueba:"))
        for data in _DEMO_USERS:
            self.stdout.write(f"  {data['rol'].value:<14} {data['email']:<28} {data['password']}")

    # -- plantilla (predeterminado, admin) ----------------------------------

    def _buscar_template_existente(self, laboratorio_repository: LaboratorioRepository):
        candidatos = laboratorio_repository.find_catalogo(nombre=_LAB_NOMBRE)
        return next(
            (
                lab
                for lab in candidatos
                if lab.nombre == _LAB_NOMBRE and lab.tipo == TipoLaboratorio.PREDETERMINADO
            ),
            None,
        )

    def _crear_template_demo(self, laboratorio_repository: LaboratorioRepository, admin):
        kwargs = _use_case_kwargs(laboratorio_repository)

        laboratorio = CrearLaboratorioUseCase(**kwargs).execute(
            CrearLaboratorioDTO(
                nombre=_LAB_NOMBRE,
                descripcion=(
                    "Laboratorio introductorio: identificá y explotá una vulnerabilidad "
                    "de inyección SQL en un formulario de login para omitir la autenticación."
                ),
                nivel_dificultad="basico",
                actor_id=admin.id,
                actor_rol="administrador",
                temas=["sql injection", "autenticación"],
            )
        )

        CrearSeccionUseCase(**kwargs).execute(
            CrearSeccionDTO(
                laboratorio_id=laboratorio.id,
                titulo="Introducción a SQL Injection",
                contenido_teorico=(
                    "<p>SQL Injection ocurre cuando la entrada de un usuario se concatena "
                    "directamente en una consulta SQL sin sanitizar. Esto permite alterar la "
                    "lógica de la consulta original.</p><p>En este laboratorio vas a explotar "
                    "un formulario de login vulnerable para autenticarte sin conocer una "
                    "contraseña válida.</p>"
                ),
                orden=1,
                actor_id=admin.id,
                actor_rol="administrador",
                tiene_practica=False,
            )
        )

        seccion_practica = CrearSeccionUseCase(**kwargs).execute(
            CrearSeccionDTO(
                laboratorio_id=laboratorio.id,
                titulo="Bypass de login vulnerable",
                contenido_teorico=(
                    "<p>El siguiente formulario ejecuta una consulta similar a:</p>"
                    "<pre>SELECT * FROM users WHERE username = '&lt;input&gt;' "
                    "AND password = '&lt;input&gt;'</pre>"
                    "<p>Encontrá una entrada que altere la lógica de la consulta para "
                    "autenticarte sin conocer la contraseña real.</p>"
                ),
                orden=2,
                actor_id=admin.id,
                actor_rol="administrador",
                tiene_practica=True,
            )
        )

        DefinirFlagUseCase(**kwargs).execute(
            DefinirFlagDTO(
                laboratorio_id=laboratorio.id,
                seccion_id=seccion_practica.id,
                valor="FLAG{sql_injection_1s_ez}",
                actor_id=admin.id,
                actor_rol="administrador",
                pista="Probá con una comilla simple (') en el campo de usuario y mirá qué pasa.",
                paso_a_paso=(
                    "Ingresá  ' OR '1'='1  como usuario y cualquier valor como contraseña. "
                    "La flag es FLAG{sql_injection_1s_ez}."
                ),
            )
        )

        PublicarLaboratorioUseCase(**kwargs).execute(
            PublicarLaboratorioDTO(
                laboratorio_id=laboratorio.id, actor_id=admin.id, actor_rol="administrador"
            )
        )

        return laboratorio_repository.get_by_id(laboratorio.id)

    # -- copia del instructor (personalizado, duplicada de la plantilla) ---

    def _buscar_copia_existente(
        self, laboratorio_repository: LaboratorioRepository, instructor_id, template_id
    ):
        candidatos = laboratorio_repository.find_catalogo(
            instructor_id=instructor_id, nombre=_LAB_NOMBRE
        )
        return next(
            (
                lab
                for lab in candidatos
                if lab.tipo == TipoLaboratorio.PERSONALIZADO and lab.origen_id == template_id
            ),
            None,
        )

    def _crear_copia_instructor(
        self, laboratorio_repository: LaboratorioRepository, instructor, template
    ):
        kwargs = _use_case_kwargs(laboratorio_repository)

        resultado = DuplicarLaboratorioUseCase(**kwargs).execute(
            DuplicarLaboratorioDTO(
                laboratorio_id=template.id, actor_id=instructor.id, actor_rol="instructor"
            )
        )

        PublicarLaboratorioUseCase(**kwargs).execute(
            PublicarLaboratorioDTO(
                laboratorio_id=resultado.id, actor_id=instructor.id, actor_rol="instructor"
            )
        )

        CrearExamenUseCase(**kwargs).execute(
            CrearExamenDTO(
                laboratorio_id=resultado.id, actor_id=instructor.id, actor_rol="instructor"
            )
        )

        opciones = [
            "Concatenar strings directamente en la consulta",
            "Usar prepared statements / parametrized queries",
            "Deshabilitar JavaScript en el navegador",
            "Usar solo HTTPS",
        ]
        AgregarPreguntaUseCase(**kwargs).execute(
            AgregarPreguntaDTO(
                laboratorio_id=resultado.id,
                enunciado="¿Cuál de las siguientes es una defensa efectiva contra SQL Injection?",
                tipo="opcion_multiple",
                respuesta="Usar prepared statements / parametrized queries",
                actor_id=instructor.id,
                actor_rol="instructor",
                opciones=opciones,
            )
        )
        AgregarPreguntaUseCase(**kwargs).execute(
            AgregarPreguntaDTO(
                laboratorio_id=resultado.id,
                enunciado=(
                    "¿Qué carácter se usa comúnmente para 'escapar' de una consulta SQL "
                    "vulnerable a inyección?"
                ),
                tipo="abierta",
                respuesta="'",
                actor_id=instructor.id,
                actor_rol="instructor",
            )
        )

        return laboratorio_repository.get_by_id(resultado.id)

    # -- asignación al estudiante -------------------------------------------

    def _asignar_a_estudiante(self, instructor, estudiante, laboratorio_id):
        asignacion_repository = AsignacionRepository()
        laboratorio_repository = LaboratorioRepository()
        user_repository = UserRepository()
        progreso_repository = ProgresoRepository()

        resultado = InvitarEstudiantesUseCase(
            unit_of_work=BaseUnitOfWork(),
            event_dispatcher=EventDispatcher(),
            asignacion_repository=asignacion_repository,
            laboratorio_repository=laboratorio_repository,
            user_repository=user_repository,
        ).execute(
            InvitarEstudiantesDTO(
                laboratorio_id=laboratorio_id,
                estudiantes=[str(estudiante.email)],
                actor_id=instructor.id,
                actor_rol="instructor",
            )
        )

        invitacion = resultado.invitaciones[0]
        if invitacion.resultado == "ya_vigente":
            self.stdout.write(
                "= el estudiante demo ya tenía una asignación vigente para este laboratorio"
            )
            return
        if invitacion.resultado != "invitado" or invitacion.asignacion_id is None:
            msg = f"! no se pudo invitar al estudiante demo: {invitacion.resultado}"
            self.stdout.write(self.style.WARNING(msg))
            return

        self.stdout.write(self.style.SUCCESS("+ invitación creada para el estudiante demo"))

        try:
            AceptarInvitacionUseCase(
                unit_of_work=BaseUnitOfWork(),
                event_dispatcher=EventDispatcher(),
                asignacion_repository=asignacion_repository,
                laboratorio_repository=laboratorio_repository,
                progreso_repository=progreso_repository,
            ).execute(
                AceptarInvitacionDTO(
                    asignacion_id=invitacion.asignacion_id, estudiante_id=estudiante.id
                )
            )
            self.stdout.write(self.style.SUCCESS("+ invitación aceptada (progreso inicializado)"))
        except DomainError as exc:
            self.stdout.write(
                self.style.WARNING(f"! no se pudo aceptar la invitación demo: {exc.message}")
            )
