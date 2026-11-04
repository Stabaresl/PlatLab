import bleach

_ALLOWED_TAGS = [
    "p",
    "br",
    "strong",
    "em",
    "u",
    "s",
    "ul",
    "ol",
    "li",
    "h1",
    "h2",
    "h3",
    "h4",
    "blockquote",
    "code",
    "pre",
    "a",
    "img",
    "span",
    # Estructura de guías estilo AWS: avisos (div.nota/.aviso/.tip/.importante/
    # .escenario), tablas de referencia, atajos de teclado y separadores.
    "div",
    "h5",
    "hr",
    "kbd",
    "sup",
    "sub",
    "dl",
    "dt",
    "dd",
    "table",
    "thead",
    "tbody",
    "tr",
    "th",
    "td",
]
_ALLOWED_ATTRIBUTES = {
    "a": ["href", "title", "rel"],
    "img": ["src", "alt", "title"],
    "span": ["class"],
    "code": ["class"],
    "div": ["class"],
    "p": ["class"],
    "pre": ["class"],
    "table": ["class"],
    "th": ["colspan", "rowspan"],
    "td": ["colspan", "rowspan"],
}
_ALLOWED_PROTOCOLS = ["http", "https", "mailto"]


# `class` solo con nombres conocidos: sin esto un instructor podría colar
# utilidades de Tailwind ("fixed inset-0 z-50 ...") y dibujar una capa
# encima de la plataforma (falso login, botón falso).
_CLASES_PERMITIDAS = {"nota", "aviso", "tip", "importante", "escenario", "especificaciones"}
_PREFIJOS_CLASE_PERMITIDOS = ("language-",)


def _clase_permitida(valor: str) -> bool:
    return all(c in _CLASES_PERMITIDAS or c.startswith(_PREFIJOS_CLASE_PERMITIDOS) for c in valor.split())


def _filtro_atributos(tag: str, nombre: str, valor: str) -> bool:
    if nombre == "class":
        return tag in _ALLOWED_ATTRIBUTES and "class" in _ALLOWED_ATTRIBUTES[tag] and _clase_permitida(valor)
    return nombre in _ALLOWED_ATTRIBUTES.get(tag, [])


def sanitizar_contenido_html(contenido_html: str) -> str:
    """
    seguridad.md §4 / UC-04 E1: sanitiza el contenido teórico (editor
    WYSIWYG) con whitelist de tags/atributos antes de persistir — nunca
    se confía en el sanitizado que haya hecho el frontend.
    """
    return bleach.clean(
        contenido_html,
        tags=_ALLOWED_TAGS,
        attributes=_filtro_atributos,
        protocols=_ALLOWED_PROTOCOLS,
        strip=True,
    )
