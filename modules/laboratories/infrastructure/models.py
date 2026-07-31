import uuid

from django.db import models


class TemaModel(models.Model):
    """Catálogo de temas (base-de-datos.md §1: evita grupos repetitivos)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nombre = models.CharField(max_length=100, unique=True)

    class Meta:
        db_table = "laboratories_tema"

    def __str__(self) -> str:
        return self.nombre


class LaboratorioModel(models.Model):
    class NivelDificultad(models.TextChoices):
        BASICO = "basico", "Básico"
        INTERMEDIO = "intermedio", "Intermedio"
        AVANZADO = "avanzado", "Avanzado"

    class Estado(models.TextChoices):
        BORRADOR = "borrador", "Borrador"
        EN_REVISION = "en_revision", "En revisión"
        PUBLICADO = "publicado", "Publicado"

    class Tipo(models.TextChoices):
        PREDETERMINADO = "predeterminado", "Predeterminado"
        PERSONALIZADO = "personalizado", "Personalizado"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField()
    nivel_dificultad = models.CharField(max_length=20, choices=NivelDificultad.choices)
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.BORRADOR)
    tipo = models.CharField(max_length=20, choices=Tipo.choices)
    temas = models.ManyToManyField(
        TemaModel,
        related_name="laboratorios",
        db_table="laboratories_laboratorio_tema",
        blank=True,
    )
    # origen_id/instructor_id: id suelto (sin FK), aislamiento entre
    # agregados/módulos (Arquitectura §8, base-de-datos.md §7). origen sí
    # apunta a este mismo modelo (auto-referencia, mismo agregado
    # conceptual "Laboratorio", permitida).
    origen = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="copias",
    )
    instructor_id = models.UUIDField(null=True, blank=True)
    # Cierre estilo "Conclusion" de AWS Academy, mostrado al completar
    # todas las secciones (ver ProgresoOverviewDTO en Progress).
    resumen_cierre = models.TextField(blank=True, default="")
    motivo_rechazo = models.TextField(null=True, blank=True)
    # Opt-in de un `personalizado` al catálogo público — ver docstring de
    # `Laboratorio.es_visible_para` (domain/entities.py).
    visible_en_catalogo = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "laboratories_laboratorio"
        indexes = [
            models.Index(fields=["estado", "nivel_dificultad"], name="idx_lab_estado_dificultad"),
            models.Index(fields=["tipo", "instructor_id"], name="idx_lab_tipo_instructor"),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(tipo="predeterminado", instructor_id__isnull=True)
                | ~models.Q(tipo="predeterminado"),
                name="ck_lab_predet_sin_instructor",
            ),
            models.CheckConstraint(
                condition=models.Q(tipo="personalizado") | models.Q(origen__isnull=True),
                name="ck_lab_origen_si_personalizado",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.nombre} ({self.tipo}/{self.estado})"


class SeccionModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    laboratorio = models.ForeignKey(
        LaboratorioModel, on_delete=models.CASCADE, related_name="secciones"
    )
    titulo = models.CharField(max_length=200)
    contenido_teorico = models.TextField()
    orden = models.PositiveIntegerField()
    tiene_practica = models.BooleanField(default=False)
    # Objetivos de aprendizaje (lista corta de strings) y duración
    # estimada — encabezado estilo AWS Academy antes del contenido.
    objetivos = models.JSONField(default=list, blank=True)
    duracion_estimada_minutos = models.PositiveIntegerField(default=15)
    # [{"orden": int, "titulo": str, "instrucciones": str, "comando_sugerido": str | None}, ...]
    pasos_guia = models.JSONField(default=list, blank=True)
    # {"prompt": str, "banner": str, "comandos": [{"comando": str, "salida": str}, ...]}
    entorno_practica = models.JSONField(null=True, blank=True)
    # Imagen Docker del entorno de práctica real (lab_environments), ej.
    # "platlab-target-sqli:latest". Null = sección sin entorno real.
    imagen_practica = models.CharField(max_length=200, null=True, blank=True)

    class Meta:
        db_table = "laboratories_seccion"
        constraints = [
            models.UniqueConstraint(
                fields=["laboratorio", "orden"], name="uq_seccion_laboratorio_orden"
            ),
        ]
        ordering = ["orden"]

    def __str__(self) -> str:
        return f"{self.orden}. {self.titulo}"


class DockerfileSeccionModel(models.Model):
    """Dockerfile/contexto de build subido por el instructor — relación 1:1 con SeccionModel."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    seccion = models.OneToOneField(
        SeccionModel, on_delete=models.CASCADE, related_name="dockerfile"
    )
    archivo_url = models.CharField(max_length=500)
    nombre_archivo = models.CharField(max_length=255)
    tamano_kb = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "laboratories_dockerfile_seccion"

    def __str__(self) -> str:
        return f"Dockerfile de {self.seccion_id}"


class FlagModel(models.Model):
    """base-de-datos.md "laboratories_flag": relación 1:1 con SeccionModel."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    seccion = models.OneToOneField(SeccionModel, on_delete=models.CASCADE, related_name="flag")
    hash = models.CharField(max_length=255)
    pista_texto = models.TextField(null=True, blank=True)
    paso_a_paso_texto = models.TextField(null=True, blank=True)

    class Meta:
        db_table = "laboratories_flag"

    def __str__(self) -> str:
        return f"Flag(seccion={self.seccion_id})"


class ExamenModel(models.Model):
    """
    HE-09/HI-08, base-de-datos.md "laboratories_examen": 1:1 con
    Laboratorio, opcional en `personalizado` (UC-03 A2).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    laboratorio = models.OneToOneField(
        LaboratorioModel, on_delete=models.CASCADE, related_name="examen"
    )

    class Meta:
        db_table = "laboratories_examen"

    def __str__(self) -> str:
        return f"Examen(laboratorio={self.laboratorio_id})"


class PreguntaModel(models.Model):
    """base-de-datos.md "laboratories_pregunta"."""

    class Tipo(models.TextChoices):
        OPCION_MULTIPLE = "opcion_multiple", "Opción múltiple"
        ABIERTA = "abierta", "Abierta"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    examen = models.ForeignKey(ExamenModel, on_delete=models.CASCADE, related_name="preguntas")
    enunciado = models.TextField()
    tipo = models.CharField(max_length=20, choices=Tipo.choices)
    # opciones: solo si tipo=opcion_multiple (validado en el dominio, Pregunta.__post_init__).
    opciones = models.JSONField(null=True, blank=True)
    respuesta_hash = models.CharField(max_length=255)

    class Meta:
        db_table = "laboratories_pregunta"

    def __str__(self) -> str:
        return f"Pregunta(examen={self.examen_id}, tipo={self.tipo})"
