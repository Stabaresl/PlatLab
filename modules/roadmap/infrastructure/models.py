import uuid

from django.db import models


class CategoriaRoadmapModel(models.Model):
    """Una pista del roadmap (ej. "Seguridad Web") — ver `domain/entities.py::CategoriaRoadmap`."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nombre = models.CharField(max_length=100, unique=True)
    orden = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "roadmap_categoria"
        ordering = ["orden"]

    def __str__(self) -> str:
        return self.nombre


class NodoRoadmapModel(models.Model):
    """
    Un laboratorio ubicado dentro de una `CategoriaRoadmapModel` en una
    posición — ver `domain/entities.py::NodoRoadmap`.

    `laboratorio_id`: id suelto (Arquitectura §8, Roadmap no depende de
    Laboratories a nivel de FK) — único porque un laboratorio solo puede
    estar en un nodo. `(categoria, posicion)` único y `DEFERRED`: los
    casos de uso de inserción/reordenamiento (`agregar_nodo`,
    `reordenar_nodo`) desplazan varias filas dentro de la misma
    transacción y transitoriamente pisan una posición ya ocupada hasta
    terminar el shift — con la restricción `DEFERRED`, Postgres la
    evalúa recién al hacer commit, no fila por fila.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    categoria = models.ForeignKey(
        CategoriaRoadmapModel, on_delete=models.CASCADE, related_name="nodos"
    )
    laboratorio_id = models.UUIDField(unique=True)
    posicion = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "roadmap_nodo"
        ordering = ["posicion"]
        constraints = [
            models.UniqueConstraint(
                fields=["categoria", "posicion"],
                deferrable=models.Deferrable.DEFERRED,
                name="uq_roadmap_nodo_categoria_posicion",
            ),
        ]
        indexes = [
            models.Index(fields=["categoria", "posicion"], name="idx_roadmap_nodo_cat_pos"),
        ]

    def __str__(self) -> str:
        return f"NodoRoadmap(categoria={self.categoria_id}, posicion={self.posicion})"
