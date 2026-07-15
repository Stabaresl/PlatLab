from django.core.files.base import ContentFile
from django.core.files.storage import default_storage


class StorageClient:
    """
    Wrapper sobre el storage de archivos de Django (`default_storage`).
    Hoy: filesystem local (`MEDIA_ROOT`, dev). En producción se reemplaza
    por S3/MinIO configurando `STORAGES` en settings — este cliente no
    cambia, solo cambia el backend que Django resuelve por debajo
    (RNF-08.1).

    Usado por `storage_adapter.py` (Reports, adjuntos — con su propia
    validación de MIME real y límite de tamaño encima de este cliente).
    """

    def save(self, path: str, content: bytes) -> str:
        return default_storage.save(path, ContentFile(content))

    def url(self, path: str) -> str:
        return default_storage.url(path)

    def delete(self, path: str) -> None:
        default_storage.delete(path)

    def exists(self, path: str) -> bool:
        return default_storage.exists(path)

    def size(self, path: str) -> int:
        return default_storage.size(path)
