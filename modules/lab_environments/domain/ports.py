from typing import Protocol


class IContenedorProvider(Protocol):
    """
    Puerto hacia el motor de contenedores real — Application/Domain nunca
    importan `docker` (SDK) directamente, así el motor de orquestación es
    intercambiable (Docker de un solo host hoy; Kubernetes u otro más
    adelante) sin tocar los casos de uso.
    """

    def iniciar(self, imagen: str) -> str:
        """Crea y arranca un contenedor descartable a partir de `imagen`. Devuelve su id."""
        ...

    def detener(self, container_id: str) -> None:
        """Detiene y elimina el contenedor. Idempotente (no falla si ya no existe)."""
        ...

    def esta_vivo(self, container_id: str) -> bool: ...
