from rest_framework.pagination import LimitOffsetPagination


class ListaPagination(LimitOffsetPagination):
    """
    Para vistas cuya `Application` ya devuelve una lista materializada de
    DTOs, no un queryset (backend.md §2: Application nunca expone el
    queryset del ORM a Presentation) — `CursorPagination` (el default
    global, ver `REST_FRAMEWORK.DEFAULT_PAGINATION_CLASS`) necesita un
    queryset real porque llama `.order_by()` sobre él, así que no aplica.

    Usada por `ViewSet.list()` planos (no `GenericViewSet`), que no
    heredan `self.paginate_queryset()` — hay que instanciar y llamar esto
    a mano, mismo patrón que ya tenía `LaboratorioViewSet`.
    """

    default_limit = 20
    max_limit = 100
