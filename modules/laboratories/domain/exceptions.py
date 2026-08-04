from modules.shared.domain.exceptions import BusinessRuleViolationError, ForbiddenError


class CannotEditPredeterminadoError(ForbiddenError):
    """
    UC-05 E1 / seguridad.md §1: un Instructor intenta editar
    directamente un laboratorio `predeterminado` (solo Administrador
    puede) — debe duplicarlo primero (HI-03) para tener su propia copia
    editable.
    """


class PublishValidationError(BusinessRuleViolationError):
    """
    UC-04 E2: se intenta publicar (`borrador` -> `publicado`) un
    laboratorio con alguna sección práctica sin flag asociada.
    """


class OrigenInvalidoParaDuplicarError(BusinessRuleViolationError):
    """
    UC-05 precondición / base-de-datos.md "laboratories_laboratorio":
    solo se puede duplicar un laboratorio `predeterminado` — un
    `personalizado` no es un origen válido.
    """


class ImagenPracticaNoPermitidaError(BusinessRuleViolationError):
    """
    seguridad.md — `imagen_practica` no puede ser texto libre: se pasa
    directo a `containers.run()` (lab_environments/docker_provider.py) al
    arrancar el entorno de un estudiante. Una cuenta de instructor
    comprometida no puede apuntar una sección a una imagen arbitraria —
    solo a las que ya están en `IMAGENES_PRACTICA_PERMITIDAS`.
    """
