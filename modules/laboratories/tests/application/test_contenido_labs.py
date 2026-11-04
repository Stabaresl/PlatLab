"""El contenido estilo AWS de los laboratorios: que esté completo, sea resoluble y se aplique bien."""

import io
import json
import re

import pytest
from django.core.management import call_command

from modules.laboratories.infrastructure.content_sanitizer import sanitizar_contenido_html
from modules.laboratories.infrastructure.models import ExamenModel, LaboratorioModel, PreguntaModel, SeccionModel
from modules.laboratories.management.commands.actualizar_contenido_labs import LABS

_FLAG = re.compile(r"FLAG\{[a-z0-9_]+\}")


@pytest.mark.parametrize("lab", LABS, ids=[lab["nombre"] for lab in LABS])
def test_cada_laboratorio_trae_guia_completa(lab):
    teoria, practica = lab["secciones"]
    assert teoria["objetivos"] and teoria["html"]
    assert practica["objetivos"] and len(practica["pasos"]) >= 4
    for titulo, instrucciones, comando, esperado in practica["pasos"]:
        assert titulo and instrucciones and comando and esperado, titulo
    assert lab["flag"]["pista"] and lab["flag"]["paso_a_paso"]
    assert lab["resumen_cierre"]


@pytest.mark.parametrize("lab", LABS, ids=[lab["nombre"] for lab in LABS])
def test_la_flag_existe_dentro_de_la_maquina_simulada(lab):
    """La flag tiene que estar en el escenario o en el guion: si no, la práctica no se puede resolver."""
    if lab.get("flag_derivada"):
        pytest.skip("la flag se obtiene transformando un dato (ej. descifrando), no está escrita")
    entorno = json.dumps(lab["secciones"][1]["entorno"], ensure_ascii=False)
    assert _FLAG.search(entorno), "la consola simulada no entrega ninguna flag"


@pytest.mark.parametrize("lab", LABS, ids=[lab["nombre"] for lab in LABS])
def test_examen_con_respuestas_validas(lab):
    for p in lab["examen"]:
        if p["tipo"] == "opcion_multiple":
            assert p["respuesta"] in p["opciones"], p["enunciado"]
        else:
            assert p["respuesta"].strip()


@pytest.mark.parametrize("lab", LABS, ids=[lab["nombre"] for lab in LABS])
def test_el_html_sobrevive_al_sanitizador(lab):
    """Avisos, tablas y código deben quedar tal cual: si el sanitizador los quita, la guía se rompe."""
    for seccion in lab["secciones"]:
        limpio = sanitizar_contenido_html(seccion["html"])
        for marca in ('class="nota"', 'class="aviso"', 'class="tip"', 'class="escenario"', "<table>"):
            assert (marca in seccion["html"]) == (marca in limpio), marca


@pytest.mark.django_db
def test_actualizar_contenido_aplica_guia_escenario_y_examen():
    call_command("seed_roadmap_labs", stdout=io.StringIO())
    call_command("actualizar_contenido_labs", "--solo", "Introducción a TCP/IP", stdout=io.StringIO())
    call_command("actualizar_contenido_labs", "--solo", "Introducción a TCP/IP", stdout=io.StringIO())  # idempotente

    lab = LaboratorioModel.objects.get(nombre="Introducción a TCP/IP", tipo="predeterminado")
    practica = SeccionModel.objects.get(laboratorio_id=lab.id, tiene_practica=True)
    assert len(practica.pasos_guia) == 6
    assert practica.pasos_guia[-1]["resultado_esperado"]
    assert practica.entorno_practica["escenario"]["red"][0]["ip"] == "192.168.56.20"
    examen = ExamenModel.objects.get(laboratorio_id=lab.id)
    assert PreguntaModel.objects.filter(examen_id=examen.id).count() == 4
