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
]
_ALLOWED_ATTRIBUTES = {
    "a": ["href", "title", "rel"],
    "img": ["src", "alt", "title"],
    "span": ["class"],
    "code": ["class"],
}
_ALLOWED_PROTOCOLS = ["http", "https", "mailto"]


def sanitizar_contenido_html(contenido_html: str) -> str:
    """
    seguridad.md §4 / UC-04 E1: sanitiza el contenido teórico (editor
    WYSIWYG) con whitelist de tags/atributos antes de persistir — nunca
    se confía en el sanitizado que haya hecho el frontend.
    """
    return bleach.clean(
        contenido_html,
        tags=_ALLOWED_TAGS,
        attributes=_ALLOWED_ATTRIBUTES,
        protocols=_ALLOWED_PROTOCOLS,
        strip=True,
    )
