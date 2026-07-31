from modules.laboratories.infrastructure.content_sanitizer import sanitizar_contenido_html
from modules.laboratories.infrastructure.markdown_renderer import renderizar_markdown


def test_renderizar_markdown_convierte_encabezados_y_negrita():
    html = renderizar_markdown("## Título\n\nTexto con **negrita**.")

    assert "<h2>Título</h2>" in html
    assert "<strong>negrita</strong>" in html


def test_renderizar_markdown_bloque_de_codigo_con_fenced_code():
    html = renderizar_markdown("```\nnmap -sV target\n```")

    assert "<pre>" in html
    assert "nmap -sV target" in html


def test_renderizar_markdown_lista_numerada():
    html = renderizar_markdown("1. Primero\n2. Segundo")

    assert "<ol>" in html
    assert "<li>Primero</li>" in html


def test_markdown_con_script_embebido_no_sobrevive_al_sanitizador():
    """
    El Markdown puede traer HTML embebido (incluido <script>) — el
    renderer por sí solo no filtra eso, así que siempre debe pasar
    después por `sanitizar_contenido_html` (mismo flujo que usan los
    serializers de laboratories).
    """
    html = renderizar_markdown("Texto normal.\n\n<script>alert(1)</script>")
    sano = sanitizar_contenido_html(html)

    assert "<script>" not in sano
    assert "Texto normal." in sano
