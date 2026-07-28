import uuid

from modules.laboratories.application.dtos import (
    LaboratorioListItemDTO,
    ListarLaboratoriosFiltroDTO,
)
from modules.laboratories.domain.entities import Laboratorio
from modules.laboratories.domain.ports import IEstadoInscripcionProvider, SinInscripcionProvider
from modules.laboratories.domain.repositories import ILaboratorioRepository
from modules.laboratories.domain.specifications import PorDificultad, PorTema, Specification


class ListarLaboratoriosQuery:
    """
    HV-02/HE-02/HI-01: catálogo de laboratorios. La visibilidad
    (predeterminado+publicado siempre; + propios si es instructor) la
    resuelve el repositorio a nivel de query (usa los índices de
    rendimiento, base-de-datos.md §7) — esta Query solo traduce filtros
    (`Specification`) y agrega el estado de inscripción cuando aplica
    (HE-02). Es una Query de solo lectura: no usa `BaseUseCase`
    (`UnitOfWork`/eventos no aplican, backend.md §2).
    """

    def __init__(
        self,
        laboratorio_repository: ILaboratorioRepository,
        estado_inscripcion_provider: IEstadoInscripcionProvider | None = None,
    ):
        self._repo = laboratorio_repository
        self._inscripcion = estado_inscripcion_provider or SinInscripcionProvider()

    def execute(self, filtro: ListarLaboratoriosFiltroDTO) -> list[LaboratorioListItemDTO]:
        especificacion = self._construir_especificacion(filtro)
        filtros_repo = especificacion.aplicar({}) if especificacion else {}

        laboratorios = self._repo.find_catalogo(instructor_id=filtro.instructor_id, **filtros_repo)
        return [self._a_list_item(lab, filtro.estudiante_id) for lab in laboratorios]

    def _construir_especificacion(
        self, filtro: ListarLaboratoriosFiltroDTO
    ) -> Specification | None:
        especificacion: Specification | None = None
        if filtro.dificultad:
            especificacion = PorDificultad(filtro.dificultad)
        if filtro.tema:
            tema_spec = PorTema(filtro.tema)
            especificacion = especificacion & tema_spec if especificacion else tema_spec
        return especificacion

    def _a_list_item(
        self, laboratorio: Laboratorio, estudiante_id: uuid.UUID | None
    ) -> LaboratorioListItemDTO:
        inscrito = None
        if estudiante_id is not None:
            inscrito = self._inscripcion.esta_inscrito(estudiante_id, laboratorio.id)
        return LaboratorioListItemDTO(
            id=laboratorio.id,
            nombre=laboratorio.nombre,
            descripcion=laboratorio.descripcion,
            nivel_dificultad=laboratorio.nivel_dificultad.value,
            estado=laboratorio.estado.value,
            temas=laboratorio.temas,
            inscrito=inscrito,
        )
