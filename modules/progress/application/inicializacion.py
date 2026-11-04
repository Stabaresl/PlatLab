from modules.laboratories.domain.repositories import ILaboratorioRepository
from modules.progress.domain.entities import Progreso, ProgresoSeccion
from modules.progress.domain.repositories import IProgresoRepository
from modules.progress.domain.value_objects import EstadoProgresoSeccion


def inicializar_progreso(
    asignacion_id,
    estudiante_id,
    laboratorio_id,
    laboratorio_repository: ILaboratorioRepository,
    progreso_repository: IProgresoRepository,
) -> Progreso:
    """
    Crea el `Progreso` de una asignación recién activada: la primera sección
    queda `en_progreso` y el resto `bloqueada`. Mismo arranque que hacen la
    autoinscripción y la aceptación de una invitación; lo usan las salas.
    """
    progreso = progreso_repository.add(Progreso(asignacion_id=asignacion_id, estudiante_id=estudiante_id))
    secciones = laboratorio_repository.get_secciones(laboratorio_id)
    progreso_secciones = [
        ProgresoSeccion(
            progreso_id=progreso.id,
            seccion_id=seccion.id,
            estado=EstadoProgresoSeccion.EN_PROGRESO if indice == 0 else EstadoProgresoSeccion.BLOQUEADA,
        )
        for indice, seccion in enumerate(secciones)
    ]
    if progreso_secciones:
        progreso_repository.add_secciones(progreso_secciones)
    return progreso
