import uuid

from django.db import IntegrityError
from django.db.models import F, Max

from modules.roadmap.domain.entities import CategoriaRoadmap, NodoRoadmap
from modules.roadmap.domain.exceptions import PosicionInvalidaError
from modules.roadmap.infrastructure.mappers import categoria_to_entity, nodo_to_entity
from modules.roadmap.infrastructure.models import CategoriaRoadmapModel, NodoRoadmapModel
from modules.shared.domain.exceptions import ConflictError

_NODO_DUPLICADO_MSG = (
    "Ya se insertó otro laboratorio en esa posición al mismo tiempo — reintentá."
)


class CategoriaRoadmapRepository:
    """Implementación de `ICategoriaRoadmapRepository` sobre PostgreSQL vía el ORM de Django."""

    def add(self, categoria: CategoriaRoadmap) -> CategoriaRoadmap:
        model = CategoriaRoadmapModel.objects.create(
            id=categoria.id, nombre=categoria.nombre, orden=categoria.orden
        )
        return categoria_to_entity(model)

    def get_by_id(self, categoria_id: uuid.UUID) -> CategoriaRoadmap | None:
        model = CategoriaRoadmapModel.objects.filter(id=categoria_id).first()
        return categoria_to_entity(model) if model else None

    def get_by_nombre(self, nombre: str) -> CategoriaRoadmap | None:
        model = CategoriaRoadmapModel.objects.filter(nombre__iexact=nombre).first()
        return categoria_to_entity(model) if model else None

    def find_todas(self) -> list[CategoriaRoadmap]:
        return [categoria_to_entity(m) for m in CategoriaRoadmapModel.objects.order_by("orden")]

    def siguiente_orden(self) -> int:
        actual = CategoriaRoadmapModel.objects.aggregate(m=Max("orden"))["m"]
        return 0 if actual is None else actual + 1


class NodoRoadmapRepository:
    """
    Implementación de `INodoRoadmapRepository`. Los métodos de
    inserción/movimiento reindexan con `.update(posicion=F("posicion") ± 1)`
    (una sola sentencia SQL atómica por shift, sin traer filas a Python)
    dentro de la transacción que ya abre `BaseUnitOfWork` alrededor de
    `_execute_domain_logic` — el `UniqueConstraint` `DEFERRED` en
    `(categoria, posicion)` tolera que, a mitad de esa transacción, dos
    filas temporalmente compartan posición mientras se termina el shift;
    Postgres solo la valida al hacer commit. Una colisión real entre dos
    admins arrastrando a la vez en la misma categoría al mismo tiempo se
    traduce a `ConflictError` (que el llamador debería poder reintentar).
    """

    def get_by_id(self, nodo_id: uuid.UUID) -> NodoRoadmap | None:
        model = NodoRoadmapModel.objects.filter(id=nodo_id).first()
        return nodo_to_entity(model) if model else None

    def get_by_laboratorio(self, laboratorio_id: uuid.UUID) -> NodoRoadmap | None:
        model = NodoRoadmapModel.objects.filter(laboratorio_id=laboratorio_id).first()
        return nodo_to_entity(model) if model else None

    def find_por_categoria(self, categoria_id: uuid.UUID) -> list[NodoRoadmap]:
        modelos = NodoRoadmapModel.objects.filter(categoria_id=categoria_id).order_by("posicion")
        return [nodo_to_entity(m) for m in modelos]

    def find_todos(self) -> list[NodoRoadmap]:
        return [nodo_to_entity(m) for m in NodoRoadmapModel.objects.order_by("categoria", "posicion")]

    def find_laboratorio_ids_asignados(self) -> set[uuid.UUID]:
        return set(NodoRoadmapModel.objects.values_list("laboratorio_id", flat=True))

    def insertar_en_posicion(
        self, categoria_id: uuid.UUID, laboratorio_id: uuid.UUID, posicion: int
    ) -> NodoRoadmap:
        if posicion < 0:
            raise PosicionInvalidaError("La posición de un nodo no puede ser negativa.")
        try:
            NodoRoadmapModel.objects.filter(
                categoria_id=categoria_id, posicion__gte=posicion
            ).update(posicion=F("posicion") + 1)
            model = NodoRoadmapModel.objects.create(
                categoria_id=categoria_id, laboratorio_id=laboratorio_id, posicion=posicion
            )
        except IntegrityError as exc:
            raise ConflictError(_NODO_DUPLICADO_MSG) from exc
        return nodo_to_entity(model)

    def mover(self, nodo_id: uuid.UUID, categoria_id: uuid.UUID, posicion: int) -> NodoRoadmap:
        if posicion < 0:
            raise PosicionInvalidaError("La posición de un nodo no puede ser negativa.")

        nodo = NodoRoadmapModel.objects.select_for_update().get(id=nodo_id)
        origen_categoria_id = nodo.categoria_id
        origen_posicion = nodo.posicion

        if origen_categoria_id == categoria_id and origen_posicion == posicion:
            return nodo_to_entity(nodo)

        try:
            if origen_categoria_id == categoria_id:
                if posicion < origen_posicion:
                    NodoRoadmapModel.objects.filter(
                        categoria_id=categoria_id, posicion__gte=posicion, posicion__lt=origen_posicion
                    ).exclude(id=nodo_id).update(posicion=F("posicion") + 1)
                else:
                    NodoRoadmapModel.objects.filter(
                        categoria_id=categoria_id, posicion__gt=origen_posicion, posicion__lte=posicion
                    ).exclude(id=nodo_id).update(posicion=F("posicion") - 1)
            else:
                # Cierra el hueco en la pista de origen y abre uno en la de destino.
                NodoRoadmapModel.objects.filter(
                    categoria_id=origen_categoria_id, posicion__gt=origen_posicion
                ).update(posicion=F("posicion") - 1)
                NodoRoadmapModel.objects.filter(
                    categoria_id=categoria_id, posicion__gte=posicion
                ).update(posicion=F("posicion") + 1)

            nodo.categoria_id = categoria_id
            nodo.posicion = posicion
            nodo.save(update_fields=["categoria", "posicion"])
        except IntegrityError as exc:
            raise ConflictError(_NODO_DUPLICADO_MSG) from exc

        return nodo_to_entity(nodo)

    def quitar(self, nodo_id: uuid.UUID) -> None:
        nodo = NodoRoadmapModel.objects.select_for_update().get(id=nodo_id)
        categoria_id = nodo.categoria_id
        posicion = nodo.posicion
        nodo.delete()
        NodoRoadmapModel.objects.filter(categoria_id=categoria_id, posicion__gt=posicion).update(
            posicion=F("posicion") - 1
        )
