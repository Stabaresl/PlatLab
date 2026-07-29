import uuid
from dataclasses import dataclass

from modules.progress.domain.entities import ProgresoSeccion
from modules.progress.domain.exceptions import SeccionNoPerteneceAProgresoError
from modules.progress.domain.value_objects import ContadorFallos, EstadoProgresoSeccion, Puntaje


class GestorDeSecuencia:
    """
    dominio.md §5: coordina dos instancias de `ProgresoSeccion` dentro
    del mismo agregado `Progreso` para desbloquear la siguiente sección
    cuando la actual pasa a `completada` (dominio.md §3, secuencialidad
    obligatoria). Recibe la lista de secciones ya ordenada por
    Application — el orden real vive en `Seccion.orden` (módulo
    Laboratories); Progress no lo conoce ni lo persiste ("id suelto",
    Arquitectura §8).
    """

    def completar_y_desbloquear_siguiente(
        self, secciones_ordenadas: list[ProgresoSeccion], seccion_id: uuid.UUID
    ) -> list[ProgresoSeccion]:
        """
        Marca `completada` la sección indicada y, si existe, desbloquea
        la siguiente en la lista. Devuelve solo las instancias que
        cambiaron de estado (para que Application persista únicamente
        esas, sin reescribir todo el set).
        """
        indice = next(
            (i for i, s in enumerate(secciones_ordenadas) if s.seccion_id == seccion_id), None
        )
        if indice is None:
            raise SeccionNoPerteneceAProgresoError("La sección no pertenece a este progreso.")

        modificadas = []
        actual = secciones_ordenadas[indice]
        actual.completar()
        modificadas.append(actual)

        if indice + 1 < len(secciones_ordenadas):
            siguiente = secciones_ordenadas[indice + 1]
            siguiente.desbloquear()
            modificadas.append(siguiente)

        return modificadas

    def laboratorio_completado(self, secciones: list[ProgresoSeccion]) -> bool:
        """El examen final solo se habilita cuando todas están `completada` (dominio.md §3)."""
        return all(s.estado == EstadoProgresoSeccion.COMPLETADA for s in secciones)


@dataclass(frozen=True)
class ResultadoValidacionFlag:
    correcta: bool
    contador: ContadorFallos
    pista_desbloqueada: bool
    paso_a_paso_desbloqueado: bool


class ValidadorDeFlag:
    """
    dominio.md §5: decide el efecto de un intento de flag sobre el
    `ContadorFallos` de esa sección y sobre la ayuda progresiva (HE-06,
    5/15 fallos). La comparación de hash real (bcrypt, tiempo constante,
    seguridad.md §4) vive en Application (`ValidarFlagUseCase`) — este
    servicio es agnóstico de Django y solo conoce el resultado booleano
    de esa comparación, cruzando así `Laboratorio` (Flag) y `Progreso`
    (ContadorFallos) sin que ninguno de los dos agregados dependa del
    otro directamente.
    """

    def procesar_intento(
        self, correcta: bool, contador_actual: ContadorFallos
    ) -> ResultadoValidacionFlag:
        contador = contador_actual if correcta else contador_actual.incrementar()
        return ResultadoValidacionFlag(
            correcta=correcta,
            contador=contador,
            pista_desbloqueada=contador.debe_mostrar_pista,
            paso_a_paso_desbloqueado=contador.debe_mostrar_paso_a_paso,
        )


class CalificadorDeExamen:
    """
    HE-09/HI-08, dominio.md §5: agrega en un `Puntaje` los resultados
    booleanos (correcta/incorrecta) de cada pregunta del examen. La
    comparación real contra `Pregunta.respuesta_hash` -distinta por tipo
    de pregunta, Strategy- vive en Application (`EnviarExamenUseCase`,
    mismo patrón que `ValidarFlagUseCase` con `Flag.hash`): este servicio
    es agnóstico de Django/hashing y del módulo Laboratories, cruzando
    ambos agregados solo a través de esta lista de booleanos ya
    evaluados.
    """

    def calificar(self, resultados: list[bool]) -> Puntaje:
        correctas = sum(1 for r in resultados if r)
        return Puntaje(correctas=correctas, total=len(resultados))
