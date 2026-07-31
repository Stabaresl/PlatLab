import markdown

# "tables" queda fuera a propósito: el whitelist de `sanitizar_contenido_html`
# no incluye tags de tabla, así que un <table> generado ahí se perdería al
# sanitizar — mejor no ofrecer una sintaxis que se vería rota.
_EXTENSIONS = ["fenced_code", "sane_lists"]


def renderizar_markdown(texto: str) -> str:
    """
    Convierte el Markdown que escribe/sube el instructor (teoría, pasos de
    la guía, resumen de cierre) a HTML. El resultado nunca se persiste tal
    cual: siempre pasa después por `sanitizar_contenido_html` — el Markdown
    puede traer HTML embebido, así que esta función por sí sola no es
    suficiente barrera de seguridad.
    """
    return markdown.markdown(texto or "", extensions=_EXTENSIONS)
