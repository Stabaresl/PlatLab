import uuid

from django.db.models import Q

from modules.laboratories.domain.entities import Flag, Laboratorio, Seccion
from modules.laboratories.infrastructure.mappers import (
    flag_to_entity,
    laboratorio_to_entity,
    seccion_to_entity,
)
from modules.laboratories.infrastructure.models import (
    FlagModel,
    LaboratorioModel,
    SeccionModel,
    TemaModel,
)


class LaboratorioRepository:
    """
    Implementación de `ILaboratorioRepository`
    (modules.laboratories.domain.repositories) sobre PostgreSQL vía el ORM
    de Django — traduce entidad <-> modelo con `mappers.py` en cada
    operación.
    """

    def find_catalogo(
        self,
        instructor_id: uuid.UUID | None = None,
        nivel_dificultad: str | None = None,
        tema: str | None = None,
    ) -> list[Laboratorio]:
        visibilidad = Q(
            estado=LaboratorioModel.Estado.PUBLICADO, tipo=LaboratorioModel.Tipo.PREDETERMINADO
        )
        if instructor_id is not None:
            visibilidad |= Q(tipo=LaboratorioModel.Tipo.PERSONALIZADO, instructor_id=instructor_id)

        queryset = LaboratorioModel.objects.filter(visibilidad)
        if nivel_dificultad is not None:
            queryset = queryset.filter(nivel_dificultad=nivel_dificultad)
        if tema is not None:
            queryset = queryset.filter(temas__nombre__iexact=tema)

        queryset = queryset.distinct().order_by("nombre").prefetch_related("temas")
        return [laboratorio_to_entity(m) for m in queryset]

    def get_by_id(self, laboratorio_id: uuid.UUID) -> Laboratorio | None:
        model = LaboratorioModel.objects.filter(id=laboratorio_id).prefetch_related("temas").first()
        return laboratorio_to_entity(model) if model else None

    def update(self, laboratorio: Laboratorio) -> Laboratorio:
        model = LaboratorioModel.objects.get(id=laboratorio.id)
        model.nombre = laboratorio.nombre
        model.descripcion = laboratorio.descripcion
        model.nivel_dificultad = laboratorio.nivel_dificultad.value
        model.estado = laboratorio.estado.value
        model.save()

        temas_modelo = [
            TemaModel.objects.get_or_create(nombre=nombre)[0] for nombre in laboratorio.temas
        ]
        model.temas.set(temas_modelo)
        return laboratorio_to_entity(model)

    def get_secciones(self, laboratorio_id: uuid.UUID) -> list[Seccion]:
        modelos = SeccionModel.objects.filter(laboratorio_id=laboratorio_id).order_by("orden")
        return [seccion_to_entity(m) for m in modelos]

    def add(self, laboratorio: Laboratorio) -> Laboratorio:
        model = LaboratorioModel.objects.create(
            id=laboratorio.id,
            nombre=laboratorio.nombre,
            descripcion=laboratorio.descripcion,
            nivel_dificultad=laboratorio.nivel_dificultad.value,
            estado=laboratorio.estado.value,
            tipo=laboratorio.tipo.value,
            origen_id=laboratorio.origen_id,
            instructor_id=laboratorio.instructor_id,
        )
        if laboratorio.temas:
            temas_modelo = [
                TemaModel.objects.get_or_create(nombre=nombre)[0] for nombre in laboratorio.temas
            ]
            model.temas.set(temas_modelo)
        return laboratorio_to_entity(model)

    def add_seccion(self, seccion: Seccion) -> Seccion:
        model = SeccionModel.objects.create(
            id=seccion.id,
            laboratorio_id=seccion.laboratorio_id,
            titulo=seccion.titulo,
            contenido_teorico=seccion.contenido_teorico,
            orden=seccion.orden,
            tiene_practica=seccion.tiene_practica,
        )
        return seccion_to_entity(model)

    def get_seccion_by_id(self, seccion_id: uuid.UUID) -> Seccion | None:
        model = SeccionModel.objects.filter(id=seccion_id).first()
        return seccion_to_entity(model) if model else None

    def update_seccion(self, seccion: Seccion) -> Seccion:
        model = SeccionModel.objects.get(id=seccion.id)
        model.titulo = seccion.titulo
        model.contenido_teorico = seccion.contenido_teorico
        model.orden = seccion.orden
        model.tiene_practica = seccion.tiene_practica
        model.save()
        return seccion_to_entity(model)

    def get_flag_by_seccion(self, seccion_id: uuid.UUID) -> Flag | None:
        model = FlagModel.objects.filter(seccion_id=seccion_id).first()
        return flag_to_entity(model) if model else None

    def save_flag(self, flag: Flag) -> Flag:
        model, _ = FlagModel.objects.update_or_create(
            seccion_id=flag.seccion_id,
            defaults={
                "hash": flag.hash,
                "pista_texto": flag.ayuda.pista,
                "paso_a_paso_texto": flag.ayuda.paso_a_paso,
            },
        )
        return flag_to_entity(model)
