"""
Comando de datos demo: siembra el catálogo fijo de logros, cosméticos y
títulos (v1 no tiene UI de admin para crearlos, ver plan) con temática
de ciberseguridad. Idempotente por `clave`.

Uso:
    docker compose exec web python manage.py seed_gamification_catalog
"""

from django.core.management.base import BaseCommand

from modules.gamification.domain.entities import Cosmetico, Logro, Titulo
from modules.gamification.domain.value_objects import RarezaCosmetico, TipoCosmetico, TipoCriterioLogro
from modules.gamification.infrastructure.repositories import (
    CosmeticoRepository,
    LogroRepository,
    TituloRepository,
)
from modules.roadmap.infrastructure.repositories import CategoriaRoadmapRepository

# claves de logro "categoria_roadmap_completa" -> nombre de la categoría
# de roadmap correspondiente (las 3 sembradas por seed_roadmap_labs).
_CATEGORIAS_ROADMAP = {
    "categoria_fundamentos_redes_completa": "Fundamentos de Redes",
    "categoria_seguridad_web_completa": "Seguridad Web",
    "categoria_criptografia_completa": "Criptografía Aplicada",
}

_LOGROS = [
    {
        "clave": "primer_laboratorio",
        "nombre": "Primer Hackeo",
        "descripcion": "Completaste tu primer laboratorio en GAIA.",
        "tipo_criterio": TipoCriterioLogro.PRIMER_LABORATORIO,
        "criterio_valor": None,
        "rareza": RarezaCosmetico.COMUN,
    },
    {
        "clave": "5_laboratorios",
        "nombre": "Cazador de Bugs",
        "descripcion": "Completaste 5 laboratorios.",
        "tipo_criterio": TipoCriterioLogro.N_LABORATORIOS,
        "criterio_valor": "5",
        "rareza": RarezaCosmetico.POCO_COMUN,
    },
    {
        "clave": "10_laboratorios",
        "nombre": "Analista de Seguridad",
        "descripcion": "Completaste 10 laboratorios.",
        "tipo_criterio": TipoCriterioLogro.N_LABORATORIOS,
        "criterio_valor": "10",
        "rareza": RarezaCosmetico.RARO,
    },
    {
        "clave": "25_laboratorios",
        "nombre": "Leyenda de GAIA",
        "descripcion": "Completaste 25 laboratorios.",
        "tipo_criterio": TipoCriterioLogro.N_LABORATORIOS,
        "criterio_valor": "25",
        "rareza": RarezaCosmetico.MITICO,
    },
    {
        "clave": "categoria_fundamentos_redes_completa",
        "nombre": "Maestro de Redes",
        "descripcion": 'Completaste todos los laboratorios de la pista "Fundamentos de Redes" del roadmap.',
        "tipo_criterio": TipoCriterioLogro.CATEGORIA_ROADMAP_COMPLETA,
        "criterio_valor": None,  # se resuelve en tiempo de ejecución contra el roadmap ya sembrado
        "rareza": RarezaCosmetico.EPICO,
    },
    {
        "clave": "categoria_seguridad_web_completa",
        "nombre": "Especialista Web",
        "descripcion": 'Completaste todos los laboratorios de la pista "Seguridad Web" del roadmap.',
        "tipo_criterio": TipoCriterioLogro.CATEGORIA_ROADMAP_COMPLETA,
        "criterio_valor": None,
        "rareza": RarezaCosmetico.EPICO,
    },
    {
        "clave": "categoria_criptografia_completa",
        "nombre": "Maestro Criptógrafo",
        "descripcion": 'Completaste todos los laboratorios de la pista "Criptografía Aplicada" del roadmap.',
        "tipo_criterio": TipoCriterioLogro.CATEGORIA_ROADMAP_COMPLETA,
        "criterio_valor": None,
        "rareza": RarezaCosmetico.EPICO,
    },
]

# cada cosmético apunta a la `clave` del logro que lo desbloquea
_COSMETICOS = [
    {
        "clave": "hoodie_kali",
        "nombre": "Hoodie Kali Linux",
        "tipo": TipoCosmetico.HOODIE,
        "rareza": RarezaCosmetico.COMUN,
        "color": "51,214,159",
        "logro_clave": "primer_laboratorio",
    },
    {
        "clave": "insignia_primer_hackeo",
        "nombre": "Insignia: Primer Hackeo",
        "tipo": TipoCosmetico.INSIGNIA,
        "rareza": RarezaCosmetico.COMUN,
        "color": "56,214,245",
        "logro_clave": "primer_laboratorio",
    },
    {
        "clave": "marco_circuito",
        "nombre": "Marco Circuito",
        "tipo": TipoCosmetico.MARCO,
        "rareza": RarezaCosmetico.COMUN,
        "color": "56,214,245",
        "logro_clave": "primer_laboratorio",
    },
    {
        "clave": "guantes_negros",
        "nombre": "Guantes Negros",
        "tipo": TipoCosmetico.GUANTES,
        "rareza": RarezaCosmetico.POCO_COMUN,
        "color": "136,146,163",
        "logro_clave": "5_laboratorios",
    },
    {
        "clave": "insignia_cazador_bugs",
        "nombre": "Insignia: Cazador de Bugs",
        "tipo": TipoCosmetico.INSIGNIA,
        "rareza": RarezaCosmetico.POCO_COMUN,
        "color": "255,176,32",
        "logro_clave": "5_laboratorios",
    },
    {
        "clave": "marco_terminal",
        "nombre": "Marco Terminal",
        "tipo": TipoCosmetico.MARCO,
        "rareza": RarezaCosmetico.POCO_COMUN,
        "color": "51,214,159",
        "logro_clave": "5_laboratorios",
    },
    {
        "clave": "gafas_reconocimiento",
        "nombre": "Gafas de Reconocimiento",
        "tipo": TipoCosmetico.GAFAS,
        "rareza": RarezaCosmetico.RARO,
        "color": "56,214,245",
        "logro_clave": "10_laboratorios",
    },
    {
        "clave": "mochila_pentesting",
        "nombre": "Mochila de Pentesting",
        "tipo": TipoCosmetico.MOCHILA,
        "rareza": RarezaCosmetico.RARO,
        "color": "255,176,32",
        "logro_clave": "10_laboratorios",
    },
    {
        "clave": "mascara_anonima",
        "nombre": "Máscara Anónima",
        "tipo": TipoCosmetico.MASCARA,
        "rareza": RarezaCosmetico.RARO,
        "color": "230,230,230",
        "logro_clave": "10_laboratorios",
    },
    {
        "clave": "marco_alerta_roja",
        "nombre": "Marco Alerta Roja",
        "tipo": TipoCosmetico.MARCO,
        "rareza": RarezaCosmetico.RARO,
        "color": "255,71,87",
        "logro_clave": "10_laboratorios",
    },
    {
        "clave": "gorra_soc",
        "nombre": "Gorra SOC",
        "tipo": TipoCosmetico.GORRA,
        "rareza": RarezaCosmetico.EPICO,
        "color": "51,214,159",
        "logro_clave": "categoria_fundamentos_redes_completa",
    },
    {
        "clave": "audifonos_soc",
        "nombre": "Audífonos SOC",
        "tipo": TipoCosmetico.AUDIFONOS,
        "rareza": RarezaCosmetico.EPICO,
        "color": "56,214,245",
        "logro_clave": "categoria_seguridad_web_completa",
    },
    {
        "clave": "zapatos_sigilosos",
        "nombre": "Zapatos Sigilosos",
        "tipo": TipoCosmetico.ZAPATOS,
        "rareza": RarezaCosmetico.EPICO,
        "color": "186,85,255",
        "logro_clave": "categoria_criptografia_completa",
    },
    {
        "clave": "marco_dorado",
        "nombre": "Marco Dorado",
        "tipo": TipoCosmetico.MARCO,
        "rareza": RarezaCosmetico.MITICO,
        "color": "255,215,0",
        "logro_clave": "25_laboratorios",
    },
    {
        "clave": "aura_dorada",
        "nombre": "Aura Dorada",
        "tipo": TipoCosmetico.AURA,
        "rareza": RarezaCosmetico.MITICO,
        "color": "255,215,0",
        "logro_clave": "25_laboratorios",
    },
]

# cada título apunta a la `clave` del logro que lo desbloquea
_TITULOS = [
    {
        "clave": "aprendiz_hacking",
        "nombre": "Aprendiz de Hacking",
        "descripcion": "Otorgado al completar tu primer laboratorio.",
        "rareza": RarezaCosmetico.COMUN,
        "logro_clave": "primer_laboratorio",
    },
    {
        "clave": "cazador_bugs_jr",
        "nombre": "Cazador de Bugs Jr",
        "descripcion": "Otorgado al completar 5 laboratorios.",
        "rareza": RarezaCosmetico.POCO_COMUN,
        "logro_clave": "5_laboratorios",
    },
    {
        "clave": "titulo_analista_seguridad",
        "nombre": "Analista de Seguridad",
        "descripcion": "Otorgado al completar 10 laboratorios.",
        "rareza": RarezaCosmetico.RARO,
        "logro_clave": "10_laboratorios",
    },
    {
        "clave": "especialista_redes",
        "nombre": "Especialista en Redes",
        "descripcion": 'Otorgado al completar la pista "Fundamentos de Redes".',
        "rareza": RarezaCosmetico.EPICO,
        "logro_clave": "categoria_fundamentos_redes_completa",
    },
    {
        "clave": "especialista_web",
        "nombre": "Especialista Web",
        "descripcion": 'Otorgado al completar la pista "Seguridad Web".',
        "rareza": RarezaCosmetico.EPICO,
        "logro_clave": "categoria_seguridad_web_completa",
    },
    {
        "clave": "leyenda_gaia",
        "nombre": "Leyenda de GAIA",
        "descripcion": "Otorgado al completar 25 laboratorios.",
        "rareza": RarezaCosmetico.MITICO,
        "logro_clave": "25_laboratorios",
    },
]


class Command(BaseCommand):
    help = "Siembra el catálogo de logros, cosméticos y títulos de gamificación."

    def handle(self, *args, **options):
        logro_repository = LogroRepository()
        cosmetico_repository = CosmeticoRepository()
        titulo_repository = TituloRepository()
        categoria_repository = CategoriaRoadmapRepository()

        logros_creados = {}
        for data in _LOGROS:
            existente = logro_repository.get_by_clave(data["clave"])
            if existente:
                self.stdout.write(f"= logro ya existe: {data['nombre']}")
                logros_creados[data["clave"]] = existente
                continue

            criterio_valor = data["criterio_valor"]
            if data["tipo_criterio"] == TipoCriterioLogro.CATEGORIA_ROADMAP_COMPLETA:
                nombre_categoria = _CATEGORIAS_ROADMAP[data["clave"]]
                categoria = categoria_repository.get_by_nombre(nombre_categoria)
                if categoria is None:
                    self.stdout.write(
                        self.style.WARNING(
                            f'! no encontré la categoría de roadmap "{nombre_categoria}" — '
                            f"corré antes seed_roadmap_labs. Salteo el logro {data['nombre']}."
                        )
                    )
                    continue
                criterio_valor = str(categoria.id)

            creado = logro_repository.add(
                Logro(
                    clave=data["clave"],
                    nombre=data["nombre"],
                    descripcion=data["descripcion"],
                    tipo_criterio=data["tipo_criterio"],
                    criterio_valor=criterio_valor,
                    rareza=data["rareza"],
                )
            )
            logros_creados[data["clave"]] = creado
            self.stdout.write(self.style.SUCCESS(f"+ logro creado: {data['nombre']}"))

        for data in _COSMETICOS:
            if cosmetico_repository.get_by_clave(data["clave"]):
                self.stdout.write(f"= cosmético ya existe: {data['nombre']}")
                continue

            logro = logros_creados.get(data["logro_clave"])
            if logro is None:
                self.stdout.write(
                    self.style.WARNING(
                        f"! salteando {data['nombre']}: falta el logro {data['logro_clave']}"
                    )
                )
                continue

            cosmetico_repository.add(
                Cosmetico(
                    clave=data["clave"],
                    nombre=data["nombre"],
                    tipo=data["tipo"],
                    rareza=data["rareza"],
                    color=data["color"],
                    logro_requerido_id=logro.id,
                )
            )
            self.stdout.write(self.style.SUCCESS(f"+ cosmético creado: {data['nombre']}"))

        for data in _TITULOS:
            if titulo_repository.get_by_clave(data["clave"]):
                self.stdout.write(f"= título ya existe: {data['nombre']}")
                continue

            logro = logros_creados.get(data["logro_clave"])
            if logro is None:
                self.stdout.write(
                    self.style.WARNING(
                        f"! salteando {data['nombre']}: falta el logro {data['logro_clave']}"
                    )
                )
                continue

            titulo_repository.add(
                Titulo(
                    clave=data["clave"],
                    nombre=data["nombre"],
                    descripcion=data["descripcion"],
                    rareza=data["rareza"],
                    logro_requerido_id=logro.id,
                )
            )
            self.stdout.write(self.style.SUCCESS(f"+ título creado: {data['nombre']}"))

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("Listo — catálogo de gamificación sembrado."))
