import uuid

from django.db import models


class UserModel(models.Model):
    class Rol(models.TextChoices):
        ESTUDIANTE = "estudiante", "Estudiante"
        INSTRUCTOR = "instructor", "Instructor"
        ADMINISTRADOR = "administrador", "Administrador"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(max_length=255, unique=True)
    username = models.CharField(max_length=50, unique=True, null=True, blank=True)
    nombre_completo = models.CharField(max_length=200)
    password_hash = models.CharField(max_length=255, null=True, blank=True)
    rol = models.CharField(max_length=20, choices=Rol.choices, default=Rol.ESTUDIANTE)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "users_user"

    def __str__(self) -> str:
        return f"{self.email} ({self.rol})"


class ProveedorAutenticacionModel(models.Model):
    class Proveedor(models.TextChoices):
        EMAIL = "email", "Email"
        GOOGLE = "google", "Google"
        GITHUB = "github", "GitHub"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        UserModel, on_delete=models.CASCADE, related_name="proveedores"
    )
    proveedor = models.CharField(max_length=20, choices=Proveedor.choices)
    proveedor_uid = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "users_proveedorautenticacion"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "proveedor"], name="uq_user_proveedor"
            ),
            models.UniqueConstraint(
                fields=["proveedor", "proveedor_uid"], name="uq_proveedor_uid"
            ),
        ]

    def __str__(self) -> str:
        return f"{self.user_id} -> {self.proveedor}"
