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

    OJO: paginar así una lista ya materializada sigue trayendo la tabla
    entera a memoria en cada request. Para colecciones que crecen sin
    límite (auditoría, notificaciones, usuarios) usar `parametros_pagina`
    + `respuesta_paginada`, que paginan en la base de datos.
    """

    default_limit = 20
    max_limit = 100


def parametros_pagina(request) -> tuple[int, int]:
    """`(limit, offset)` saneados desde `?limit=&offset=` — mismos topes que `ListaPagination`."""
    paginator = ListaPagination()
    limit = paginator.get_limit(request) or paginator.default_limit
    offset = paginator.get_offset(request)
    return limit, offset


def respuesta_paginada(request, resultados: list, total: int, limit: int, offset: int):
    """
    Misma forma de respuesta que `ListaPagination` (`count`/`next`/
    `previous`/`results`), pero para resultados que ya vienen paginados
    desde la base de datos (el repositorio aplicó LIMIT/OFFSET y contó
    el total con COUNT) — el frontend no nota la diferencia.
    """
    paginator = ListaPagination()
    paginator.request = request
    paginator.limit = limit
    paginator.offset = offset
    paginator.count = total
    return paginator.get_paginated_response(resultados)
