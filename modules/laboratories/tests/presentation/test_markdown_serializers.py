from modules.laboratories.presentation.serializers import (
    CrearLaboratorioRequestSerializer,
    CrearSeccionRequestSerializer,
)


def test_crear_seccion_serializer_convierte_markdown_a_html():
    """
    El serializer solo convierte Markdown -> HTML; el saneo (quitar un
    <script> embebido, por ejemplo) sigue pasando después, en el caso de
    uso (`CrearSeccionUseCase` ya llama `sanitizar_contenido_html`) — ver
    el test end-to-end en test_autoria_views.py que cubre el pipeline
    completo vía la vista.
    """
    serializer = CrearSeccionRequestSerializer(
        data={
            "titulo": "Intro",
            "contenido_teorico": "## Título\n\nTexto con **negrita**.",
            "orden": 1,
        }
    )

    assert serializer.is_valid(), serializer.errors
    html = serializer.validated_data["contenido_teorico"]
    assert "<h2>Título</h2>" in html
    assert "<strong>negrita</strong>" in html


def test_crear_seccion_serializer_convierte_markdown_en_pasos_guia():
    serializer = CrearSeccionRequestSerializer(
        data={
            "titulo": "Practica",
            "contenido_teorico": "contenido",
            "orden": 1,
            "tiene_practica": True,
            "pasos_guia": [
                {
                    "orden": 1,
                    "titulo": "Paso 1",
                    "instrucciones": "Ejecutá `nmap` primero.",
                }
            ],
        }
    )

    assert serializer.is_valid(), serializer.errors
    paso = serializer.validated_data["pasos_guia"][0]
    assert "<code>nmap</code>" in paso.instrucciones


def test_crear_laboratorio_serializer_convierte_resumen_cierre():
    serializer = CrearLaboratorioRequestSerializer(
        data={
            "nombre": "Lab",
            "descripcion": "desc",
            "nivel_dificultad": "basico",
            "resumen_cierre": "# Resumen\n\nBuen trabajo.",
        }
    )

    assert serializer.is_valid(), serializer.errors
    assert "<h1>Resumen</h1>" in serializer.validated_data["resumen_cierre"]
