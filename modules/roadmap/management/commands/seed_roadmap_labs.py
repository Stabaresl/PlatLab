"""
Comando de datos demo para el roadmap: crea 8 laboratorios `predeterminado`
nivel `basico`, repartidos en 3 categorías, para poder probar de punta a
punta el camino estilo "mapa de niveles" (orden, bloqueo por
prerequisitos, inscripción) sin cargar nada a mano.

Reutiliza el admin demo de `seed_demo_data.py` (`admin@platlab.demo`) si
ya existe, si no lo crea con las mismas credenciales. Es idempotente por
nombre de laboratorio y de categoría: correrlo una segunda vez no
duplica nada.

Uso:
    docker compose exec web python manage.py seed_roadmap_labs
"""

from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand

from modules.laboratories.application.dtos import (
    CrearLaboratorioDTO,
    CrearSeccionDTO,
    DefinirFlagDTO,
    PublicarLaboratorioDTO,
)
from modules.laboratories.application.use_cases.crear_laboratorio import CrearLaboratorioUseCase
from modules.laboratories.application.use_cases.crear_seccion import CrearSeccionUseCase
from modules.laboratories.application.use_cases.definir_flag import DefinirFlagUseCase
from modules.laboratories.application.use_cases.publicar_laboratorio import (
    PublicarLaboratorioUseCase,
)
from modules.laboratories.domain.value_objects import ComandoSimulado, EntornoPractica, TipoLaboratorio
from modules.laboratories.infrastructure.repositories import LaboratorioRepository
from modules.roadmap.application.dtos import AgregarNodoDTO, CrearCategoriaDTO
from modules.roadmap.application.use_cases.agregar_nodo import AgregarNodoUseCase
from modules.roadmap.application.use_cases.crear_categoria import CrearCategoriaUseCase
from modules.roadmap.infrastructure.repositories import (
    CategoriaRoadmapRepository,
    NodoRoadmapRepository,
)
from modules.shared.domain.exceptions import DomainError
from modules.shared.infrastructure.event_dispatcher import EventDispatcher
from modules.shared.infrastructure.unit_of_work import BaseUnitOfWork
from modules.users.domain.entities import User
from modules.users.domain.value_objects import Email, Rol
from modules.users.infrastructure.repositories import UserRepository

_ADMIN = {
    "email": "admin@platlab.demo",
    "password": "Admin1234",
    "nombre_completo": "Admin Demo",
}

# categoria -> [ (nombre, descripcion, temas, teoria, practica) ]
_CATEGORIAS = [
    {
        "nombre": "Fundamentos de Redes",
        "labs": [
            {
                "nombre": "Introducción a TCP/IP",
                "descripcion": "Recorré las capas del modelo TCP/IP y practicá identificar puertos y protocolos comunes.",
                "temas": ["redes", "tcp-ip", "fundamentos"],
                "teoria_titulo": "El modelo TCP/IP",
                "teoria": (
                    "<h3>Las cuatro capas</h3>"
                    "<p>TCP/IP organiza la comunicación en red en capas: Acceso a Red, Internet, "
                    "Transporte y Aplicación. Cada una resuelve un problema distinto — desde cómo "
                    "viajan los bits por el cable hasta cómo un navegador le habla a un servidor web.</p>"
                    "<h3>Puertos comunes</h3>"
                    "<p>Un puerto identifica qué servicio de una máquina recibe el tráfico: 22 (SSH), "
                    "80 (HTTP), 443 (HTTPS), 53 (DNS). Reconocerlos es el primer paso de cualquier "
                    "reconocimiento.</p>"
                ),
                "practica_titulo": "Identificando servicios expuestos",
                "practica": (
                    "<p>Tenés acceso a una consola de práctica contra una máquina objetivo. Usá los "
                    "comandos sugeridos para descubrir qué puerto expone un servicio no estándar y "
                    "conseguir la flag que devuelve.</p>"
                ),
                "comandos": [
                    ("whoami", "estudiante"),
                    (
                        "nmap -p- 192.168.56.20",
                        "PORT     STATE SERVICE\n22/tcp   open  ssh\n80/tcp   open  http\n"
                        "31337/tcp open  unknown",
                    ),
                    (
                        "nc 192.168.56.20 31337",
                        "Bienvenido al puerto secreto.\nFLAG{tcp_ip_puertos_101}",
                    ),
                ],
                "flag": "FLAG{tcp_ip_puertos_101}",
                "pista": "nmap con -p- escanea los 65535 puertos, no solo los comunes.",
            },
            {
                "nombre": "Escaneo de Puertos con Nmap",
                "descripcion": "Lanzá un escaneo Nmap básico contra un objetivo y capturá la flag oculta en un puerto no estándar.",
                "temas": ["redes", "nmap", "reconocimiento"],
                "teoria_titulo": "Reconocimiento activo con Nmap",
                "teoria": (
                    "<h3>¿Qué es Nmap?</h3>"
                    "<p>Nmap es la herramienta de referencia para reconocimiento de red: descubre "
                    "hosts vivos, puertos abiertos y hasta versiones de servicio (<code>-sV</code>).</p>"
                    "<h3>Buenas prácticas</h3>"
                    "<p>Un escaneo agresivo genera mucho ruido — en un pentest real siempre se hace "
                    "con autorización explícita del dueño del sistema.</p>"
                ),
                "practica_titulo": "Escaneo con detección de versión",
                "practica": (
                    "<p>Escaneá el objetivo con detección de versión de servicio y encontrá el "
                    "servicio mal configurado que expone la flag en su banner.</p>"
                ),
                "comandos": [
                    (
                        "nmap -sV 192.168.56.21",
                        "PORT    STATE SERVICE VERSION\n21/tcp  open  ftp     vsftpd 2.3.4 "
                        "(FLAG{nmap_sv_banner_grab})\n22/tcp  open  ssh     OpenSSH 8.9",
                    ),
                ],
                "flag": "FLAG{nmap_sv_banner_grab}",
                "pista": "El flag -sV muestra el banner de versión de cada servicio — a veces incluye info que no debería.",
            },
            {
                "nombre": "Sniffing de Tráfico Básico",
                "descripcion": "Inspeccioná una captura simulada de tráfico HTTP en claro para extraer credenciales filtradas.",
                "temas": ["redes", "wireshark", "sniffing"],
                "teoria_titulo": "Tráfico en claro y sniffing",
                "teoria": (
                    "<h3>El problema del HTTP sin cifrar</h3>"
                    "<p>Cuando el tráfico viaja sin TLS, cualquiera con acceso al segmento de red "
                    "puede capturarlo y leerlo — incluyendo credenciales enviadas en un formulario "
                    "de login.</p>"
                    "<h3>Por qué HTTPS importa</h3>"
                    "<p>TLS cifra el contenido de la conexión, así que aunque alguien capture los "
                    "paquetes, no puede leer las credenciales dentro.</p>"
                ),
                "practica_titulo": "Analizando una captura",
                "practica": (
                    "<p>Tenés acceso a un volcado de tráfico capturado en un segmento de red "
                    "compartido. Buscá el paquete que contiene un login enviado por HTTP en claro.</p>"
                ),
                "comandos": [
                    (
                        "cat captura.pcap.txt | grep -A2 POST",
                        "POST /login HTTP/1.1\nHost: intranet.local\n"
                        "username=admin&password=FLAG{sniff_http_plaintext}",
                    ),
                ],
                "flag": "FLAG{sniff_http_plaintext}",
                "pista": "Buscá el método POST en la captura — ahí suele viajar el formulario de login.",
            },
        ],
    },
    {
        "nombre": "Seguridad Web",
        "labs": [
            {
                "nombre": "SQL Injection: Nivel Básico",
                "descripcion": "Bypasseá un login vulnerable con una inyección SQL clásica en un formulario simulado.",
                "temas": ["web", "sqli", "owasp"],
                "teoria_titulo": "Inyección SQL 101",
                "teoria": (
                    "<h3>El patrón vulnerable</h3>"
                    "<p>Cuando la entrada del usuario se concatena directo en una consulta SQL, un "
                    "atacante puede alterar la lógica de esa consulta.</p>"
                ),
                "practica_titulo": "Bypass de login",
                "practica": (
                    "<p>El backend arma la consulta concatenando el campo usuario sin sanitizar. "
                    "Encontrá una entrada que te autentique sin conocer ninguna contraseña real.</p>"
                ),
                "comandos": [
                    (
                        "curl -s http://192.168.56.30/login.php --data-urlencode \"username=' OR '1'='1' -- \" --data-urlencode 'password=x'",
                        "Bienvenido, admin. FLAG{sqli_basico_bypass}",
                    ),
                ],
                "flag": "FLAG{sqli_basico_bypass}",
                "pista": "Un comentario SQL (-- ) al final del username neutraliza la verificación de contraseña.",
            },
            {
                "nombre": "Cross-Site Scripting Reflejado",
                "descripcion": "Inyectá un payload XSS reflejado para robar una cookie de sesión simulada.",
                "temas": ["web", "xss", "owasp"],
                "teoria_titulo": "XSS reflejado",
                "teoria": (
                    "<h3>¿Qué es XSS?</h3>"
                    "<p>Cross-Site Scripting ocurre cuando una aplicación refleja entrada del "
                    "usuario en el HTML de la página sin sanitizarla, permitiendo ejecutar "
                    "JavaScript arbitrario en el navegador de otra persona.</p>"
                ),
                "practica_titulo": "Robando una cookie simulada",
                "practica": (
                    "<p>El parámetro de búsqueda del sitio se refleja sin escapar en la página de "
                    "resultados. Construí un payload que ejecute JavaScript.</p>"
                ),
                "comandos": [
                    (
                        "curl -s \"http://192.168.56.31/buscar?q=<script>alert(1)</script>\"",
                        "<div>Resultados para: <script>alert(1)</script></div>\n"
                        "<!-- payload reflejado sin escapar -->\nFLAG{xss_reflejado_basico}",
                    ),
                ],
                "flag": "FLAG{xss_reflejado_basico}",
                "pista": "Si el parámetro q aparece tal cual en el HTML de respuesta, probá con una etiqueta <script>.",
            },
        ],
    },
    {
        "nombre": "Criptografía Aplicada",
        "labs": [
            {
                "nombre": "Cifrado César y Frecuencia",
                "descripcion": "Descifrá un mensaje cifrado con César usando análisis de frecuencia para obtener la flag.",
                "temas": ["criptografia", "cifrado-clasico"],
                "teoria_titulo": "El cifrado César",
                "teoria": (
                    "<h3>Cifrado por desplazamiento</h3>"
                    "<p>El cifrado César desplaza cada letra del alfabeto un número fijo de "
                    "posiciones. Es trivial de romper por fuerza bruta (solo 25 desplazamientos "
                    "posibles) o por análisis de frecuencia de letras.</p>"
                ),
                "practica_titulo": "Descifrando el mensaje",
                "practica": (
                    "<p>Recibiste un mensaje cifrado con César. Probá los desplazamientos hasta "
                    "encontrar el que produce texto legible.</p>"
                ),
                "comandos": [
                    (
                        "cat mensaje_cifrado.txt",
                        "IODJ{fhvdu_hv_wulyldo}",
                    ),
                    (
                        "echo 'IODJ{fhvdu_hv_wulylro}' | tr 'A-Za-z' 'X-ZA-WX-za-wx'",
                        "FLAG{cesar_es_trivial}",
                    ),
                ],
                "flag": "FLAG{cesar_es_trivial}",
                "pista": "El desplazamiento correcto es 3 — el clásico usado por Julio César.",
            },
            {
                "nombre": "Hashes y Fuerza Bruta Básica",
                "descripcion": "Crackeá un hash MD5 débil contra una wordlist pequeña provista en el entorno simulado.",
                "temas": ["criptografia", "hashing", "fuerza-bruta"],
                "teoria_titulo": "Hashing y por qué MD5 ya no alcanza",
                "teoria": (
                    "<h3>Hashes no son cifrado</h3>"
                    "<p>Un hash es una función de un solo sentido — no se \"descifra\", se "
                    "reconstruye probando candidatos (fuerza bruta o diccionario) y comparando los "
                    "hashes resultantes.</p>"
                    "<h3>MD5 está roto</h3>"
                    "<p>MD5 es rápido de calcular, lo que lo hace pésimo para contraseñas: permite "
                    "probar millones de candidatos por segundo.</p>"
                ),
                "practica_titulo": "Crackeando el hash",
                "practica": (
                    "<p>Tenés un hash MD5 y una wordlist pequeña. Encontrá qué palabra de la lista "
                    "produce ese hash.</p>"
                ),
                "comandos": [
                    ("cat wordlist.txt", "123456\npassword\nflagcrypto\nadmin"),
                    (
                        "for w in $(cat wordlist.txt); do echo -n \"$w -> \"; echo -n $w | md5sum; done",
                        "123456 -> 49ba59abbe56e057...\npassword -> 5f4dcc3b5aa765d6...\n"
                        "flagcrypto -> e8b1a6f... (coincide con el hash objetivo)\n"
                        "FLAG{md5_wordlist_crack}",
                    ),
                ],
                "flag": "FLAG{md5_wordlist_crack}",
                "pista": "Probá cada palabra de la wordlist con md5sum y comparala contra el hash objetivo.",
            },
            {
                "nombre": "Introducción a Cifrado Asimétrico",
                "descripcion": "Interpretá un intercambio de claves RSA simplificado y recuperá un mensaje cifrado.",
                "temas": ["criptografia", "rsa", "asimetrico"],
                "teoria_titulo": "Cifrado asimétrico y RSA",
                "teoria": (
                    "<h3>Dos claves, no una</h3>"
                    "<p>A diferencia del cifrado simétrico (una sola clave compartida), RSA usa un "
                    "par: una clave pública para cifrar y una privada para descifrar — nunca hace "
                    "falta compartir la privada.</p>"
                    "<h3>Uso real</h3>"
                    "<p>RSA es la base de HTTPS/TLS y de SSH para el intercambio inicial de claves.</p>"
                ),
                "practica_titulo": "Descifrando con la clave privada",
                "practica": (
                    "<p>Tenés un mensaje cifrado y la clave privada correspondiente. Usá el "
                    "entorno de práctica para descifrarlo.</p>"
                ),
                "comandos": [
                    ("cat mensaje.enc", "8a3f...c91e (binario cifrado con RSA-2048)"),
                    (
                        "openssl rsautl -decrypt -inkey clave_privada.pem -in mensaje.enc",
                        "FLAG{rsa_asimetrico_intro}",
                    ),
                ],
                "flag": "FLAG{rsa_asimetrico_intro}",
                "pista": "openssl rsautl -decrypt necesita la clave privada, nunca la pública.",
            },
        ],
    },
]


def _use_case_kwargs(laboratorio_repository):
    return {
        "unit_of_work": BaseUnitOfWork(),
        "event_dispatcher": EventDispatcher(),
        "laboratorio_repository": laboratorio_repository,
    }


class Command(BaseCommand):
    help = "Crea 8 laboratorios predeterminado (básico) en 3 categorías del roadmap, para probarlo de punta a punta."

    def handle(self, *args, **options):
        admin = self._admin_demo()
        laboratorio_repository = LaboratorioRepository()
        categoria_repository = CategoriaRoadmapRepository()
        nodo_repository = NodoRoadmapRepository()

        for categoria_data in _CATEGORIAS:
            categoria = self._buscar_o_crear_categoria(categoria_repository, categoria_data["nombre"], admin)

            for posicion, lab_data in enumerate(categoria_data["labs"]):
                laboratorio = self._buscar_template_existente(laboratorio_repository, lab_data["nombre"])
                if laboratorio is None:
                    laboratorio = self._crear_laboratorio(laboratorio_repository, admin, lab_data)
                    self.stdout.write(self.style.SUCCESS(f"+ laboratorio creado: {lab_data['nombre']}"))
                else:
                    self.stdout.write(f"= laboratorio ya existe: {lab_data['nombre']}")

                if nodo_repository.get_by_laboratorio(laboratorio.id) is None:
                    AgregarNodoUseCase(
                        unit_of_work=BaseUnitOfWork(),
                        event_dispatcher=EventDispatcher(),
                        categoria_repository=categoria_repository,
                        nodo_repository=nodo_repository,
                        laboratorio_repository=laboratorio_repository,
                    ).execute(
                        AgregarNodoDTO(
                            categoria_id=categoria.id,
                            laboratorio_id=laboratorio.id,
                            posicion=posicion,
                            actor_id=admin.id,
                            actor_rol="administrador",
                        )
                    )
                    self.stdout.write(
                        self.style.SUCCESS(f"  -> agregado a '{categoria.nombre}' en posición {posicion}")
                    )
                else:
                    self.stdout.write(f"  = ya estaba en el roadmap")

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("Listo — roadmap sembrado."))

    # -- helpers -------------------------------------------------------------

    def _admin_demo(self):
        user_repository = UserRepository()
        existente = user_repository.get_by_email(_ADMIN["email"])
        if existente:
            self.stdout.write(f"= admin demo ya existe: {_ADMIN['email']}")
            return existente
        creado = user_repository.add(
            User(
                email=Email(_ADMIN["email"]),
                nombre_completo=_ADMIN["nombre_completo"],
                rol=Rol.ADMINISTRADOR,
                password_hash=make_password(_ADMIN["password"]),
            )
        )
        self.stdout.write(self.style.SUCCESS(f"+ admin demo creado: {_ADMIN['email']} / {_ADMIN['password']}"))
        return creado

    def _buscar_o_crear_categoria(self, categoria_repository, nombre, admin):
        existente = categoria_repository.get_by_nombre(nombre)
        if existente:
            self.stdout.write(f"= categoría ya existe: {nombre}")
            return existente
        resultado = CrearCategoriaUseCase(
            unit_of_work=BaseUnitOfWork(),
            event_dispatcher=EventDispatcher(),
            categoria_repository=categoria_repository,
        ).execute(CrearCategoriaDTO(nombre=nombre, actor_id=admin.id, actor_rol="administrador"))
        self.stdout.write(self.style.SUCCESS(f"+ categoría creada: {nombre}"))
        return categoria_repository.get_by_id(resultado.id)

    def _buscar_template_existente(self, laboratorio_repository, nombre):
        candidatos = laboratorio_repository.find_catalogo(nombre=nombre)
        return next(
            (
                lab
                for lab in candidatos
                if lab.nombre == nombre and lab.tipo == TipoLaboratorio.PREDETERMINADO
            ),
            None,
        )

    def _crear_laboratorio(self, laboratorio_repository, admin, lab_data):
        kwargs = _use_case_kwargs(laboratorio_repository)

        laboratorio = CrearLaboratorioUseCase(**kwargs).execute(
            CrearLaboratorioDTO(
                nombre=lab_data["nombre"],
                descripcion=lab_data["descripcion"],
                nivel_dificultad="basico",
                actor_id=admin.id,
                actor_rol="administrador",
                temas=lab_data["temas"],
            )
        )

        CrearSeccionUseCase(**kwargs).execute(
            CrearSeccionDTO(
                laboratorio_id=laboratorio.id,
                titulo=lab_data["teoria_titulo"],
                contenido_teorico=lab_data["teoria"],
                orden=1,
                actor_id=admin.id,
                actor_rol="administrador",
                tiene_practica=False,
                duracion_estimada_minutos=8,
            )
        )

        seccion_practica = CrearSeccionUseCase(**kwargs).execute(
            CrearSeccionDTO(
                laboratorio_id=laboratorio.id,
                titulo=lab_data["practica_titulo"],
                contenido_teorico=lab_data["practica"],
                orden=2,
                actor_id=admin.id,
                actor_rol="administrador",
                tiene_practica=True,
                duracion_estimada_minutos=15,
                entorno_practica=EntornoPractica(
                    prompt="estudiante@labs:~$",
                    banner="Consola de práctica simulada — no ejecuta comandos reales.",
                    comandos=[
                        ComandoSimulado(comando=c, salida=s) for c, s in lab_data["comandos"]
                    ],
                ),
            )
        )

        DefinirFlagUseCase(**kwargs).execute(
            DefinirFlagDTO(
                laboratorio_id=laboratorio.id,
                seccion_id=seccion_practica.id,
                valor=lab_data["flag"],
                actor_id=admin.id,
                actor_rol="administrador",
                pista=lab_data["pista"],
            )
        )

        try:
            PublicarLaboratorioUseCase(**kwargs).execute(
                PublicarLaboratorioDTO(
                    laboratorio_id=laboratorio.id, actor_id=admin.id, actor_rol="administrador"
                )
            )
        except DomainError as exc:
            self.stdout.write(self.style.WARNING(f"  ! no se pudo publicar {lab_data['nombre']}: {exc.message}"))

        return laboratorio_repository.get_by_id(laboratorio.id)
