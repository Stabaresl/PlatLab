import uuid

import pytest

from modules.shared.domain.exceptions import NotFoundError
from modules.shared.infrastructure.event_dispatcher import EventDispatcher
from modules.shared.infrastructure.unit_of_work import BaseUnitOfWork
from modules.users.application.dtos import ProcesarVerificacionInstructorDTO
from modules.users.application.use_cases.procesar_verificacion_instructor import (
    ProcesarVerificacionInstructorUseCase,
)
from modules.users.domain.entities import SolicitudInstructor, User
from modules.users.domain.value_objects import Email, Rol, SolicitudInstructorEstado
from modules.users.domain.verificacion_academica import ResultadoVerificacionAcademica
from modules.users.infrastructure.repositories import SolicitudInstructorRepository, UserRepository


def _crear_estudiante(email: str) -> User:
    return UserRepository().add(
        User(email=Email(email), nombre_completo="Ada Lovelace", rol=Rol.ESTUDIANTE)
    )


def _crear_solicitud_pendiente(usuario: User, orcid: str = "0000-0000-0000-0000") -> SolicitudInstructor:
    return SolicitudInstructorRepository().add(
        SolicitudInstructor(
            user_id=usuario.id,
            orcid=orcid,
            nombre_declarado=usuario.nombre_completo,
            tipo="investigador",
        )
    )


def _uc():
    return ProcesarVerificacionInstructorUseCase(
        unit_of_work=BaseUnitOfWork(),
        event_dispatcher=EventDispatcher(),
        solicitud_repository=SolicitudInstructorRepository(),
        user_repository=UserRepository(),
    )


@pytest.mark.django_db
def test_verificacion_exitosa_aprueba_solicitud_y_asciende_a_instructor():
    usuario = _crear_estudiante("ok@uni.edu")
    solicitud = _crear_solicitud_pendiente(usuario)

    resultado = _uc().execute(
        ProcesarVerificacionInstructorDTO(
            solicitud_id=solicitud.id,
            resultado=ResultadoVerificacionAcademica(
                encontrado=True, coincide_nombre=True, works_count=2, nombre_openalex="Ada Lovelace"
            ),
        )
    )

    assert resultado.estado == "aprobada"
    actualizado = UserRepository().get_by_id(usuario.id)
    assert actualizado.rol == Rol.INSTRUCTOR


@pytest.mark.django_db
def test_orcid_no_encontrado_rechaza_sin_ascender():
    usuario = _crear_estudiante("noenc@uni.edu")
    solicitud = _crear_solicitud_pendiente(usuario)

    resultado = _uc().execute(
        ProcesarVerificacionInstructorDTO(
            solicitud_id=solicitud.id,
            resultado=ResultadoVerificacionAcademica(
                encontrado=False, coincide_nombre=False, works_count=0, nombre_openalex=None
            ),
        )
    )

    assert resultado.estado == "rechazada"
    assert resultado.motivo_rechazo
    actualizado = UserRepository().get_by_id(usuario.id)
    assert actualizado.rol == Rol.ESTUDIANTE


@pytest.mark.django_db
def test_nombre_no_coincide_rechaza():
    usuario = _crear_estudiante("nomatch@uni.edu")
    solicitud = _crear_solicitud_pendiente(usuario)

    resultado = _uc().execute(
        ProcesarVerificacionInstructorDTO(
            solicitud_id=solicitud.id,
            resultado=ResultadoVerificacionAcademica(
                encontrado=True, coincide_nombre=False, works_count=5, nombre_openalex="Otro Nombre"
            ),
        )
    )

    assert resultado.estado == "rechazada"


@pytest.mark.django_db
def test_sin_publicaciones_rechaza():
    usuario = _crear_estudiante("sinpub@uni.edu")
    solicitud = _crear_solicitud_pendiente(usuario)

    resultado = _uc().execute(
        ProcesarVerificacionInstructorDTO(
            solicitud_id=solicitud.id,
            resultado=ResultadoVerificacionAcademica(
                encontrado=True, coincide_nombre=True, works_count=0, nombre_openalex="Ada Lovelace"
            ),
        )
    )

    assert resultado.estado == "rechazada"


@pytest.mark.django_db
def test_solicitud_ya_resuelta_es_idempotente():
    usuario = _crear_estudiante("idem@uni.edu")
    solicitud = _crear_solicitud_pendiente(usuario)
    resultado_ok = ResultadoVerificacionAcademica(
        encontrado=True, coincide_nombre=True, works_count=1, nombre_openalex="Ada Lovelace"
    )
    dto = ProcesarVerificacionInstructorDTO(solicitud_id=solicitud.id, resultado=resultado_ok)

    primera = _uc().execute(dto)
    segunda = _uc().execute(dto)

    assert primera.estado == "aprobada"
    assert segunda.estado == "aprobada"


@pytest.mark.django_db
def test_solicitud_inexistente_lanza_not_found():
    with pytest.raises(NotFoundError):
        _uc().execute(
            ProcesarVerificacionInstructorDTO(
                solicitud_id=uuid.uuid4(),
                resultado=ResultadoVerificacionAcademica(
                    encontrado=True, coincide_nombre=True, works_count=1, nombre_openalex="X"
                ),
            )
        )
