from enum import Enum


class EstadoAsignacion(str, Enum):
    PENDIENTE = "pendiente"
    ACEPTADA = "aceptada"
    RECHAZADA = "rechazada"
    ACTIVA = "activa"
    VENCIDA = "vencida"
