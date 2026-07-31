from modules.laboratories.domain.entities import (
    DockerfileSeccion,
    Examen,
    Flag,
    Laboratorio,
    Pregunta,
    Seccion,
)
from modules.laboratories.domain.value_objects import (
    AyudaProgresiva,
    ComandoSimulado,
    EntornoPractica,
    EstadoLaboratorio,
    NivelDificultad,
    PasoGuia,
    TipoLaboratorio,
    TipoPregunta,
)
from modules.laboratories.infrastructure.models import (
    DockerfileSeccionModel,
    ExamenModel,
    FlagModel,
    LaboratorioModel,
    PreguntaModel,
    SeccionModel,
)


def laboratorio_to_entity(model: LaboratorioModel) -> Laboratorio:
    return Laboratorio(
        id=model.id,
        nombre=model.nombre,
        descripcion=model.descripcion,
        nivel_dificultad=NivelDificultad(model.nivel_dificultad),
        estado=EstadoLaboratorio(model.estado),
        tipo=TipoLaboratorio(model.tipo),
        temas=[tema.nombre for tema in model.temas.all()],
        origen_id=model.origen_id,
        instructor_id=model.instructor_id,
        resumen_cierre=model.resumen_cierre,
        motivo_rechazo=model.motivo_rechazo,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def dockerfile_seccion_to_entity(model: DockerfileSeccionModel) -> DockerfileSeccion:
    return DockerfileSeccion(
        id=model.id,
        seccion_id=model.seccion_id,
        archivo_url=model.archivo_url,
        nombre_archivo=model.nombre_archivo,
        tamano_kb=model.tamano_kb,
        created_at=model.created_at,
    )


def entorno_practica_to_entity(data: dict | None) -> EntornoPractica | None:
    if not data:
        return None
    return EntornoPractica(
        prompt=data.get("prompt") or "root@lab:~#",
        banner=data.get("banner") or "",
        comandos=[
            ComandoSimulado(comando=c["comando"], salida=c["salida"])
            for c in data.get("comandos", [])
        ],
    )


def entorno_practica_to_dict(entorno: EntornoPractica | None) -> dict | None:
    if entorno is None:
        return None
    return {
        "prompt": entorno.prompt,
        "banner": entorno.banner,
        "comandos": [{"comando": c.comando, "salida": c.salida} for c in entorno.comandos],
    }


def pasos_guia_to_entity(data: list[dict] | None) -> list[PasoGuia]:
    return [
        PasoGuia(
            orden=p["orden"],
            titulo=p["titulo"],
            instrucciones=p["instrucciones"],
            comando_sugerido=p.get("comando_sugerido"),
        )
        for p in (data or [])
    ]


def pasos_guia_to_list(pasos: list[PasoGuia]) -> list[dict]:
    return [
        {
            "orden": p.orden,
            "titulo": p.titulo,
            "instrucciones": p.instrucciones,
            "comando_sugerido": p.comando_sugerido,
        }
        for p in pasos
    ]


def seccion_to_entity(model: SeccionModel) -> Seccion:
    return Seccion(
        id=model.id,
        laboratorio_id=model.laboratorio_id,
        titulo=model.titulo,
        contenido_teorico=model.contenido_teorico,
        orden=model.orden,
        tiene_practica=model.tiene_practica,
        objetivos=model.objetivos,
        duracion_estimada_minutos=model.duracion_estimada_minutos,
        pasos_guia=pasos_guia_to_entity(model.pasos_guia),
        entorno_practica=entorno_practica_to_entity(model.entorno_practica),
        imagen_practica=model.imagen_practica,
    )


def flag_to_entity(model: FlagModel) -> Flag:
    return Flag(
        id=model.id,
        seccion_id=model.seccion_id,
        hash=model.hash,
        ayuda=AyudaProgresiva(pista=model.pista_texto, paso_a_paso=model.paso_a_paso_texto),
    )


def examen_to_entity(model: ExamenModel) -> Examen:
    return Examen(id=model.id, laboratorio_id=model.laboratorio_id)


def pregunta_to_entity(model: PreguntaModel) -> Pregunta:
    return Pregunta(
        id=model.id,
        examen_id=model.examen_id,
        enunciado=model.enunciado,
        tipo=TipoPregunta(model.tipo),
        respuesta_hash=model.respuesta_hash,
        opciones=model.opciones,
    )
