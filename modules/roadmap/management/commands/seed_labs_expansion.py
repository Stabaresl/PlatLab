"""
Expansión del roadmap demo para producción: agrega 3 laboratorios
`predeterminado` nuevos (uno por categoría, variando la dificultad —
`seed_roadmap_labs.py` dejaba las 9 en "básico" parejo) y engancha al
roadmap el laboratorio con entorno Docker real
("SQL Injection: Bypass de Login", sembrado por
`seed_docker_lab.py`/manual, backed por `docker/targets/sqli-login`)
que existía en el catálogo pero sin nodo — quedaba invisible en el
mapa de niveles.

Idempotente por nombre de laboratorio y de nodo, igual que
`seed_roadmap_labs.py`: correrlo de nuevo no duplica nada.

Uso:
    docker compose exec web python manage.py seed_labs_expansion
"""

from django.core.management.base import BaseCommand

from modules.laboratories.application.dtos import (
    CrearLaboratorioDTO,
    CrearSeccionDTO,
    DefinirFlagDTO,
    EditarLaboratorioDTO,
    PublicarLaboratorioDTO,
)
from modules.laboratories.application.use_cases.crear_laboratorio import CrearLaboratorioUseCase
from modules.laboratories.application.use_cases.crear_seccion import CrearSeccionUseCase
from modules.laboratories.application.use_cases.definir_flag import DefinirFlagUseCase
from modules.laboratories.application.use_cases.editar_laboratorio import EditarLaboratorioUseCase
from modules.laboratories.application.use_cases.publicar_laboratorio import (
    PublicarLaboratorioUseCase,
)
from modules.laboratories.domain.value_objects import ComandoSimulado, EntornoPractica, TipoLaboratorio
from modules.laboratories.infrastructure.repositories import LaboratorioRepository
from modules.roadmap.application.dtos import AgregarNodoDTO
from modules.roadmap.application.use_cases.agregar_nodo import AgregarNodoUseCase
from modules.roadmap.infrastructure.repositories import (
    CategoriaRoadmapRepository,
    NodoRoadmapRepository,
)
from modules.shared.domain.exceptions import DomainError
from modules.shared.infrastructure.event_dispatcher import EventDispatcher
from modules.shared.infrastructure.unit_of_work import BaseUnitOfWork
from modules.users.domain.value_objects import Email
from modules.users.infrastructure.repositories import UserRepository

_ADMIN_EMAIL = "admin@platlab.demo"

# Nombre exacto del laboratorio real (Docker) creado a mano en una
# sesión anterior — sin nodo de roadmap hasta ahora.
_LAB_REAL_DOCKER_NOMBRE = "SQL Injection: Bypass de Login"

# `seed_roadmap_labs.py` publicó las 9 labs originales todas en "basico"
# parejo — acá subimos a "intermedio" las dos que ya requieren un paso
# lógico extra (fuerza bruta contra wordlist, descifrado RSA con clave
# provista) para que el filtro/badge de dificultad del catálogo tenga
# variación real.
_AJUSTES_DIFICULTAD = {
    "Hashes y Fuerza Bruta Básica": "intermedio",
    "Introducción a Cifrado Asimétrico": "intermedio",
}

# categoria -> (posicion, lab_data | None si es el enganche del lab real)
_NUEVOS = {
    "Fundamentos de Redes": {
        "posicion": 2,
        "lab": {
            "nombre": "ARP Spoofing: Detectando un Man-in-the-Middle",
            "descripcion": "Analizá una tabla ARP envenenada para detectar un ataque de intermediario en la red local.",
            "nivel_dificultad": "intermedio",
            "temas": ["redes", "arp-spoofing", "mitm"],
            "teoria_titulo": "ARP y su punto débil",
            "teoria": (
                "<h3>Cómo funciona ARP</h3>"
                "<p>El protocolo ARP traduce direcciones IP a direcciones MAC dentro de una red "
                "local, pero no autentica las respuestas: cualquier host puede anunciar \"yo soy "
                "esa IP\" y los demás le creen sin verificar.</p>"
                "<h3>El ataque</h3>"
                "<p>Un atacante envenena la tabla ARP de la víctima y del gateway para que ambos "
                "direccionen su tráfico a través de la máquina atacante — un clásico "
                "Man-in-the-Middle.</p>"
            ),
            "practica_titulo": "Leyendo una tabla ARP envenenada",
            "practica": (
                "<p>Tenés acceso a la tabla ARP de una máquina víctima. Encontrá la entrada "
                "sospechosa: dos IPs distintas resolviendo a la misma dirección MAC.</p>"
            ),
            "comandos": [
                (
                    "arp -a",
                    "gateway.local (192.168.56.1) at aa:bb:cc:00:11:22\n"
                    "impresora.local (192.168.56.50) at aa:bb:cc:00:11:22\n"
                    "-- misma MAC para dos IPs distintas: una de las dos está falsificada.",
                ),
                (
                    "cat /var/log/arpwatch.log | tail -3",
                    "changed ethernet address 192.168.56.1 aa:bb:cc:00:11:22 (era 11:22:33:44:55:66)\n"
                    "FLAG{arp_spoof_mitm_detectado}",
                ),
            ],
            "flag": "FLAG{arp_spoof_mitm_detectado}",
            "pista": "Si dos IPs distintas apuntan a la misma MAC, una de las dos resoluciones es falsa.",
        },
    },
    "Seguridad Web": {
        "posicion": 2,
        "lab": None,  # engancha el laboratorio real (Docker), no crea uno nuevo
    },
    "Seguridad Web - avanzado": {
        "categoria_real": "Seguridad Web",
        "posicion": 3,
        "lab": {
            "nombre": "Inyección SQL a Ciegas (Blind SQLi)",
            "descripcion": "Sin mensajes de error visibles, extraé un dato de la base con inyección SQL ciega basada en booleanos.",
            "nivel_dificultad": "avanzado",
            "temas": ["web", "sqli", "blind", "owasp"],
            "teoria_titulo": "SQLi a ciegas",
            "teoria": (
                "<h3>Cuando no hay mensaje de error</h3>"
                "<p>Muchas aplicaciones ocultan los errores de base de datos, pero la consulta "
                "sigue siendo vulnerable: si la página responde distinto según si la condición "
                "inyectada es verdadera o falsa, se puede extraer datos char por char.</p>"
                "<h3>Boolean-based blind</h3>"
                "<p>Se inyectan condiciones como <code>AND SUBSTRING(password,1,1)='a'</code> y se "
                "observa si la respuesta cambia (por ejemplo, \"login válido\" vs. \"credenciales "
                "inválidas\") para inferir el valor de a uno.</p>"
            ),
            "practica_titulo": "Extrayendo un carácter a la vez",
            "practica": (
                "<p>El formulario no muestra errores SQL, pero responde \"Usuario existe\" o "
                "\"Usuario no encontrado\" según la condición. Usá eso para confirmar el primer "
                "carácter de una flag oculta en la tabla.</p>"
            ),
            "comandos": [
                (
                    "curl -s http://192.168.56.32/login.php --data-urlencode \"username=admin' AND SUBSTRING((SELECT flag FROM secretos),1,1)='F' -- \"",
                    "Usuario existe.",
                ),
                (
                    "curl -s http://192.168.56.32/login.php --data-urlencode \"username=admin' AND SUBSTRING((SELECT flag FROM secretos),1,1)='X' -- \"",
                    "Usuario no encontrado.",
                ),
                (
                    "# repitiendo el proceso carácter por carácter contra la tabla secretos...",
                    "FLAG{blind_sqli_boolean_based}",
                ),
            ],
            "flag": "FLAG{blind_sqli_boolean_based}",
            "pista": "\"Usuario existe\" = la condición fue verdadera. Iterá letra por letra y posición por posición.",
        },
    },
    "Criptografía Aplicada": {
        "posicion": 3,
        "lab": {
            "nombre": "Esteganografía: Mensajes Ocultos en Imágenes",
            "descripcion": "Extraé un mensaje oculto en los metadatos y bits menos significativos de una imagen.",
            "nivel_dificultad": "intermedio",
            "temas": ["criptografia", "esteganografia", "forense"],
            "teoria_titulo": "Esteganografía vs. criptografía",
            "teoria": (
                "<h3>Ocultar en vez de cifrar</h3>"
                "<p>La criptografía protege el contenido de un mensaje; la esteganografía oculta "
                "que el mensaje existe. Una técnica común es esconder datos en los bits menos "
                "significativos (LSB) de los píxeles de una imagen — el cambio es invisible al "
                "ojo humano.</p>"
                "<h3>Dónde buscar</h3>"
                "<p>Además del contenido de píxeles, los metadatos EXIF de un archivo también son "
                "un escondite habitual para datos que no deberían estar ahí.</p>"
            ),
            "practica_titulo": "Extrayendo el mensaje oculto",
            "practica": (
                "<p>Tenés una imagen sospechosa. Inspeccioná sus metadatos y extraé los bits "
                "ocultos para reconstruir la flag.</p>"
            ),
            "comandos": [
                (
                    "exiftool captura_sospechosa.png",
                    "Comment: mensaje codificado en LSB del canal azul, primeros 200px",
                ),
                (
                    "python3 extraer_lsb.py captura_sospechosa.png --canal azul --n 200",
                    "Decodificando bits menos significativos...\nFLAG{esteganografia_lsb_oculta}",
                ),
            ],
            "flag": "FLAG{esteganografia_lsb_oculta}",
            "pista": "Revisá primero los metadatos (EXIF/Comment) — a veces indican dónde y cómo está escondido el mensaje.",
        },
    },
}


def _use_case_kwargs(laboratorio_repository):
    return {
        "unit_of_work": BaseUnitOfWork(),
        "event_dispatcher": EventDispatcher(),
        "laboratorio_repository": laboratorio_repository,
    }


class Command(BaseCommand):
    help = "Agrega laboratorios nuevos (con dificultad variada) y engancha el lab Docker real al roadmap."

    def handle(self, *args, **options):
        user_repository = UserRepository()
        admin = user_repository.get_by_email(_ADMIN_EMAIL)
        if admin is None:
            self.stdout.write(self.style.ERROR(
                f"No existe el admin demo ({_ADMIN_EMAIL}). Corré antes: manage.py seed_roadmap_labs"
            ))
            return

        laboratorio_repository = LaboratorioRepository()
        categoria_repository = CategoriaRoadmapRepository()
        nodo_repository = NodoRoadmapRepository()

        for entry_key, entry in _NUEVOS.items():
            categoria_nombre = entry.get("categoria_real", entry_key)
            categoria = categoria_repository.get_by_nombre(categoria_nombre)
            if categoria is None:
                self.stdout.write(self.style.ERROR(f"No existe la categoría '{categoria_nombre}' — saltando."))
                continue

            if entry["lab"] is None:
                laboratorio = self._buscar_template_existente(laboratorio_repository, _LAB_REAL_DOCKER_NOMBRE)
                if laboratorio is None:
                    self.stdout.write(self.style.ERROR(
                        f"No se encontró el laboratorio real '{_LAB_REAL_DOCKER_NOMBRE}' — saltando enganche."
                    ))
                    continue
                nombre_log = _LAB_REAL_DOCKER_NOMBRE
            else:
                lab_data = entry["lab"]
                laboratorio = self._buscar_template_existente(laboratorio_repository, lab_data["nombre"])
                if laboratorio is None:
                    laboratorio = self._crear_laboratorio(laboratorio_repository, admin, lab_data)
                    self.stdout.write(self.style.SUCCESS(f"+ laboratorio creado: {lab_data['nombre']}"))
                else:
                    self.stdout.write(f"= laboratorio ya existe: {lab_data['nombre']}")
                nombre_log = lab_data["nombre"]

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
                        posicion=entry["posicion"],
                        actor_id=admin.id,
                        actor_rol="administrador",
                    )
                )
                self.stdout.write(self.style.SUCCESS(
                    f"  -> agregado a '{categoria_nombre}' en posición {entry['posicion']}"
                ))
            else:
                self.stdout.write(f"  = '{nombre_log}' ya estaba en el roadmap")

        for nombre, nuevo_nivel in _AJUSTES_DIFICULTAD.items():
            laboratorio = self._buscar_template_existente(laboratorio_repository, nombre)
            if laboratorio is None:
                self.stdout.write(self.style.ERROR(f"No se encontró '{nombre}' para ajustar dificultad."))
                continue
            if laboratorio.nivel_dificultad.value == nuevo_nivel:
                self.stdout.write(f"= '{nombre}' ya está en dificultad '{nuevo_nivel}'")
                continue
            EditarLaboratorioUseCase(
                unit_of_work=BaseUnitOfWork(),
                event_dispatcher=EventDispatcher(),
                laboratorio_repository=laboratorio_repository,
            ).execute(
                EditarLaboratorioDTO(
                    laboratorio_id=laboratorio.id,
                    actor_id=admin.id,
                    actor_rol="administrador",
                    nivel_dificultad=nuevo_nivel,
                )
            )
            self.stdout.write(self.style.SUCCESS(f"  -> '{nombre}' ahora es '{nuevo_nivel}'"))

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("Listo — roadmap expandido."))

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
                nivel_dificultad=lab_data["nivel_dificultad"],
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
                duracion_estimada_minutos=18,
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
