import uuid

from modules.laboratories.domain.entities import Flag, Laboratorio, Seccion
from modules.laboratories.domain.exceptions import (
    ImagenPracticaNoPermitidaError,
    OrigenInvalidoParaDuplicarError,
    PublishValidationError,
)
from modules.laboratories.domain.value_objects import (
    IMAGENES_PRACTICA_PERMITIDAS,
    EstadoLaboratorio,
    TipoLaboratorio,
)

_FLAGS_FALTANTES_MSG = "Todas las secciones con práctica necesitan una flag antes de publicar."
_IMAGEN_NO_PERMITIDA_MSG = "Esa imagen de práctica no está permitida."


def validar_imagen_practica_permitida(imagen: str | None) -> None:
    """
    Llamada desde `CrearSeccionUseCase`/`EditarSeccionUseCase` antes de
    guardar. `None` es válido (una sección sin práctica no necesita
    imagen) — lo que se rechaza es un valor que no está en la allowlist.
    """
    if imagen is not None and imagen not in IMAGENES_PRACTICA_PERMITIDAS:
        raise ImagenPracticaNoPermitidaError(
            _IMAGEN_NO_PERMITIDA_MSG, details=[{"imagen_practica": imagen}]
        )


def validar_laboratorio_publicable(
    secciones: list[Seccion], flags_por_seccion: dict[uuid.UUID, Flag]
) -> None:
    """
    UC-04 E2: toda sección con `tiene_practica=True` necesita una `Flag`
    asociada. Reutilizada tanto por `PublicarLaboratorioUseCase` (admin
    publica su propio predeterminado) como por
    `SolicitarRevisionLaboratorioUseCase` (instructor manda a revisión) —
    no tiene sentido dejar avanzar un laboratorio incompleto en ninguno de
    los dos flujos.
    """
    faltantes = [
        s
        for s in secciones
        if s.tiene_practica and flags_por_seccion.get(s.id) is None
    ]
    if faltantes:
        raise PublishValidationError(
            _FLAGS_FALTANTES_MSG,
            details=[{"seccion_id": str(s.id), "titulo": s.titulo} for s in faltantes],
        )


class DuplicadorDeLaboratorio:
    """
    dominio.md §5: crea una copia `personalizado` a partir de un
    `predeterminado`, preservando la inmutabilidad del original (RF-31,
    UC-05). Construye las entidades en memoria — no persiste nada;
    Application (`DuplicarLaboratorioUseCase`) las guarda vía el
    repositorio dentro de una única transacción (UoW).
    """

    def duplicar(
        self,
        original: Laboratorio,
        secciones: list[Seccion],
        flags_por_seccion: dict[uuid.UUID, Flag],
        instructor_id: uuid.UUID,
    ) -> tuple[Laboratorio, list[Seccion], list[Flag]]:
        if original.tipo != TipoLaboratorio.PREDETERMINADO:
            raise OrigenInvalidoParaDuplicarError(
                "Solo se puede duplicar un laboratorio predeterminado."
            )

        copia = Laboratorio(
            nombre=original.nombre,
            descripcion=original.descripcion,
            nivel_dificultad=original.nivel_dificultad,
            estado=EstadoLaboratorio.BORRADOR,
            tipo=TipoLaboratorio.PERSONALIZADO,
            temas=list(original.temas),
            origen_id=original.id,
            instructor_id=instructor_id,
            resumen_cierre=original.resumen_cierre,
        )

        secciones_copiadas = []
        flags_copiadas = []
        for seccion in secciones:
            nueva_seccion = Seccion(
                laboratorio_id=copia.id,
                titulo=seccion.titulo,
                contenido_teorico=seccion.contenido_teorico,
                orden=seccion.orden,
                tiene_practica=seccion.tiene_practica,
                objetivos=list(seccion.objetivos),
                duracion_estimada_minutos=seccion.duracion_estimada_minutos,
                pasos_guia=list(seccion.pasos_guia),
                entorno_practica=seccion.entorno_practica,
                imagen_practica=seccion.imagen_practica,
            )
            secciones_copiadas.append(nueva_seccion)

            flag_original = flags_por_seccion.get(seccion.id)
            if flag_original is not None:
                flags_copiadas.append(
                    Flag(
                        seccion_id=nueva_seccion.id,
                        hash=flag_original.hash,
                        ayuda=flag_original.ayuda,
                    )
                )

        return copia, secciones_copiadas, flags_copiadas
