import uuid
from dataclasses import dataclass
from datetime import datetime

from modules.progress.domain.entities import ProgresoSeccion
from modules.progress.domain.exceptions import SeccionNoPerteneceAProgresoError
from modules.progress.domain.value_objects import (
    ESPERA_TRAS_INTENTOS,
    MAX_INTENTOS_EXAMEN,
    PUNTAJE_APROBACION,
    ContadorFallos,
    EstadoIntentosExamen,
    EstadoProgresoSeccion,
    Puntaje,
)


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


class PoliticaDeIntentosExamen:
    """
    Regla del examen final: 3 intentos; si los 3 se reprueban seguidos, el
    examen queda bloqueado 24 h desde el último y después se abre un ciclo
    nuevo de 3. Aprobar reinicia la cuenta (se puede volver a presentar
    para mejorar la nota, con la misma regla).

    Recibe `(fecha, puntaje)` de cada intento ya calificado —incluidos los
    abandonados, que valen 0— y no depende de Django.
    """

    def evaluar(self, intentos: list[tuple[datetime, float]], ahora: datetime) -> EstadoIntentosExamen:
        fallos_seguidos = 0
        ultimo_fallo: datetime | None = None
        aprobado = False
        mejor: float | None = None

        for fecha, puntaje in sorted(intentos, key=lambda i: i[0]):
            # Un ciclo bloqueado que ya cumplió la espera no cuenta para el siguiente.
            if fallos_seguidos >= MAX_INTENTOS_EXAMEN and ultimo_fallo and fecha >= ultimo_fallo + ESPERA_TRAS_INTENTOS:
                fallos_seguidos = 0
            mejor = puntaje if mejor is None else max(mejor, puntaje)
            if puntaje >= PUNTAJE_APROBACION:
                aprobado = True
                fallos_seguidos = 0
            else:
                fallos_seguidos += 1
                ultimo_fallo = fecha

        bloqueado_hasta = None
        if fallos_seguidos >= MAX_INTENTOS_EXAMEN and ultimo_fallo is not None:
            fin_espera = ultimo_fallo + ESPERA_TRAS_INTENTOS
            if ahora < fin_espera:
                bloqueado_hasta = fin_espera
            else:
                fallos_seguidos = 0

        return EstadoIntentosExamen(
            intentos_restantes=0 if bloqueado_hasta else MAX_INTENTOS_EXAMEN - fallos_seguidos,
            bloqueado_hasta=bloqueado_hasta,
            aprobado=aprobado,
            intentos_realizados=len(intentos),
            mejor_puntaje=mejor,
        )
