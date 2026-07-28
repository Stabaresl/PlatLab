import uuid

from modules.laboratories.domain.entities import Flag, Laboratorio, Seccion
from modules.laboratories.domain.exceptions import OrigenInvalidoParaDuplicarError
from modules.laboratories.domain.value_objects import EstadoLaboratorio, TipoLaboratorio


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
