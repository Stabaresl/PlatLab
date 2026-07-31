import uuid

from django.db import models


class PerfilJugadorModel(models.Model):
    class AvatarTipo(models.TextChoices):
        PRESET = "preset", "Preset"
        SUBIDO = "subido", "Subido"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    estudiante_id = models.UUIDField(unique=True)
    xp = models.PositiveIntegerField(default=0)
    nivel = models.PositiveIntegerField(default=1)
    avatar_tipo = models.CharField(max_length=10, choices=AvatarTipo.choices, default=AvatarTipo.PRESET)
    avatar_valor = models.CharField(max_length=500, default="operador_nocturno")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "gamification_perfil_jugador"

    def __str__(self) -> str:
        return f"PerfilJugador(estudiante={self.estudiante_id}, nivel={self.nivel})"


class XpOtorgadoModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    estudiante_id = models.UUIDField()
    laboratorio_id = models.UUIDField()
    xp = models.PositiveIntegerField()
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "gamification_xp_otorgado"
        constraints = [
            models.UniqueConstraint(
                fields=["estudiante_id", "laboratorio_id"], name="uq_xp_estudiante_laboratorio"
            ),
        ]
        indexes = [
            models.Index(fields=["estudiante_id"], name="idx_xp_estudiante"),
        ]


class LogroModel(models.Model):
    class TipoCriterio(models.TextChoices):
        PRIMER_LABORATORIO = "primer_laboratorio", "Primer laboratorio"
        N_LABORATORIOS = "n_laboratorios", "N laboratorios"
        CATEGORIA_ROADMAP_COMPLETA = "categoria_roadmap_completa", "Categoría de roadmap completa"

    class Rareza(models.TextChoices):
        COMUN = "comun", "Común"
        POCO_COMUN = "poco_comun", "Poco común"
        RARO = "raro", "Raro"
        EPICO = "epico", "Épico"
        LEGENDARIO = "legendario", "Legendario"
        MITICO = "mitico", "Mítico"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    clave = models.CharField(max_length=100, unique=True)
    nombre = models.CharField(max_length=150)
    descripcion = models.TextField()
    tipo_criterio = models.CharField(max_length=30, choices=TipoCriterio.choices)
    criterio_valor = models.CharField(max_length=100, null=True, blank=True)
    rareza = models.CharField(max_length=20, choices=Rareza.choices)

    class Meta:
        db_table = "gamification_logro"

    def __str__(self) -> str:
        return self.nombre


class LogroDesbloqueadoModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    estudiante_id = models.UUIDField()
    logro = models.ForeignKey(LogroModel, on_delete=models.CASCADE, related_name="desbloqueos")
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "gamification_logro_desbloqueado"
        constraints = [
            models.UniqueConstraint(fields=["estudiante_id", "logro"], name="uq_logro_estudiante"),
        ]


class CosmeticoModel(models.Model):
    class Tipo(models.TextChoices):
        HOODIE = "hoodie", "Hoodie"
        GAFAS = "gafas", "Gafas"
        MASCARA = "mascara", "Máscara"
        AURA = "aura", "Aura"
        INSIGNIA = "insignia", "Insignia"
        MOCHILA = "mochila", "Mochila"
        GUANTES = "guantes", "Guantes"
        ZAPATOS = "zapatos", "Zapatos"
        GORRA = "gorra", "Gorra"
        AUDIFONOS = "audifonos", "Audífonos"
        MARCO = "marco", "Marco"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    clave = models.CharField(max_length=100, unique=True)
    nombre = models.CharField(max_length=150)
    tipo = models.CharField(max_length=20, choices=Tipo.choices)
    rareza = models.CharField(max_length=20, choices=LogroModel.Rareza.choices)
    color = models.CharField(max_length=30)
    logro_requerido = models.ForeignKey(
        LogroModel, on_delete=models.CASCADE, related_name="cosmeticos"
    )

    class Meta:
        db_table = "gamification_cosmetico"

    def __str__(self) -> str:
        return self.nombre


class CosmeticoDesbloqueadoModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    estudiante_id = models.UUIDField()
    cosmetico = models.ForeignKey(
        CosmeticoModel, on_delete=models.CASCADE, related_name="desbloqueos"
    )
    equipado = models.BooleanField(default=False)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "gamification_cosmetico_desbloqueado"
        constraints = [
            models.UniqueConstraint(
                fields=["estudiante_id", "cosmetico"], name="uq_cosmetico_estudiante"
            ),
        ]
        indexes = [
            models.Index(fields=["estudiante_id"], name="idx_cosmetico_desb_estudiante"),
        ]


class TituloModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    clave = models.CharField(max_length=100, unique=True)
    nombre = models.CharField(max_length=150)
    descripcion = models.TextField()
    rareza = models.CharField(max_length=20, choices=LogroModel.Rareza.choices)
    logro_requerido = models.ForeignKey(
        LogroModel, on_delete=models.CASCADE, related_name="titulos"
    )

    class Meta:
        db_table = "gamification_titulo"

    def __str__(self) -> str:
        return self.nombre


class TituloDesbloqueadoModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    estudiante_id = models.UUIDField()
    titulo = models.ForeignKey(TituloModel, on_delete=models.CASCADE, related_name="desbloqueos")
    equipado = models.BooleanField(default=False)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "gamification_titulo_desbloqueado"
        constraints = [
            models.UniqueConstraint(
                fields=["estudiante_id", "titulo"], name="uq_titulo_estudiante"
            ),
        ]
        indexes = [
            models.Index(fields=["estudiante_id"], name="idx_titulo_desb_estudiante"),
        ]
