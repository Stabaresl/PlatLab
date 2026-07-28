import uuid

from modules.laboratories.domain.entities import Laboratorio
from modules.laboratories.domain.value_objects import (
    EstadoLaboratorio,
    NivelDificultad,
    TipoLaboratorio,
)
from modules.laboratories.infrastructure.cached_laboratorio_repository import (
    CachedLaboratorioRepository,
)


class _FakeRepo:
    def __init__(self, resultado):
        self.resultado = resultado
        self.llamadas = 0

    def find_catalogo(self, instructor_id=None, nivel_dificultad=None, tema=None):
        self.llamadas += 1
        return self.resultado

    def get_by_id(self, laboratorio_id):
        raise NotImplementedError

    def get_secciones(self, laboratorio_id):
        raise NotImplementedError


def _lab(nombre: str, tema: str) -> Laboratorio:
    return Laboratorio(
        nombre=nombre,
        descripcion="desc",
        nivel_dificultad=NivelDificultad.BASICO,
        estado=EstadoLaboratorio.PUBLICADO,
        tipo=TipoLaboratorio.PREDETERMINADO,
        temas=[tema],
    )


def test_find_catalogo_usa_cache_en_la_segunda_llamada():
    tema = f"cache-tema-{uuid.uuid4()}"
    lab = _lab(f"Lab Cache {uuid.uuid4()}", tema)
    fake_repo = _FakeRepo([lab])
    cached = CachedLaboratorioRepository(fake_repo)

    primera = cached.find_catalogo(tema=tema)
    segunda = cached.find_catalogo(tema=tema)

    assert fake_repo.llamadas == 1  # la segunda vino del cache, no llamó al repo real
    assert primera[0].id == segunda[0].id == lab.id
    assert primera[0].nombre == segunda[0].nombre == lab.nombre


def test_find_catalogo_distingue_cache_por_filtros():
    tema = f"cache-tema-{uuid.uuid4()}"
    lab = _lab(f"Lab Cache Distinto {uuid.uuid4()}", tema)
    fake_repo = _FakeRepo([lab])
    cached = CachedLaboratorioRepository(fake_repo)

    cached.find_catalogo(tema=tema, nivel_dificultad="basico")
    cached.find_catalogo(tema=tema, nivel_dificultad="avanzado")

    assert fake_repo.llamadas == 2  # claves de cache distintas, no debe reusar


def test_get_by_id_y_get_secciones_no_pasan_por_cache():
    class _RepoConMarca:
        def find_catalogo(self, **kwargs):
            return []

        def get_by_id(self, laboratorio_id):
            return "marca_get_by_id"

        def get_secciones(self, laboratorio_id):
            return "marca_get_secciones"

    cached = CachedLaboratorioRepository(_RepoConMarca())

    assert cached.get_by_id(uuid.uuid4()) == "marca_get_by_id"
    assert cached.get_secciones(uuid.uuid4()) == "marca_get_secciones"
