from enum import Enum
from typing import Tuple
from pydantic import BaseModel, Field


class CategoryEnum(str, Enum):
    ACCESOS_Y_SEGURIDAD = "ACCESOS_Y_SEGURIDAD"
    SOFTWARE_APLICACIONES = "SOFTWARE_APLICACIONES"
    INFRAESTRUCTURA_RED = "INFRAESTRUCTURA_RED"
    HARDWARE_EQUIPOS = "HARDWARE_EQUIPOS"
    CONSULTA_OPERATIVA = "CONSULTA_OPERATIVA"


class ImpactoEnum(str, Enum):
    ALTO = "ALTO"  # Afecta a toda la empresa
    MEDIO = "MEDIO"  # Afecta a un departamento o equipo
    BAJO = "BAJO"  # Afecta a un solo usuario


class UrgenciaEnum(str, Enum):
    ALTA = "ALTA"  # Bloqueo total de la operación
    MEDIA = "MEDIA"  # Operación degradada con alternativa temporal
    BAJA = "BAJA"  # Inconveniente menor no bloqueante


class PriorityEnum(str, Enum):
    P1 = "P1"  # Crítico
    P2 = "P2"  # Alto
    P3 = "P3"  # Medio
    P4 = "P4"  # Bajo


# Matriz fija de Prioridad (Impacto x Urgencia)
PRIORITY_MATRIX = {
    (ImpactoEnum.ALTO, UrgenciaEnum.ALTA): PriorityEnum.P1,
    (ImpactoEnum.ALTO, UrgenciaEnum.MEDIA): PriorityEnum.P2,
    (ImpactoEnum.ALTO, UrgenciaEnum.BAJA): PriorityEnum.P3,
    (ImpactoEnum.MEDIO, UrgenciaEnum.ALTA): PriorityEnum.P2,
    (ImpactoEnum.MEDIO, UrgenciaEnum.MEDIA): PriorityEnum.P3,
    (ImpactoEnum.MEDIO, UrgenciaEnum.BAJA): PriorityEnum.P4,
    (ImpactoEnum.BAJO, UrgenciaEnum.ALTA): PriorityEnum.P3,
    (ImpactoEnum.BAJO, UrgenciaEnum.MEDIA): PriorityEnum.P4,
    (ImpactoEnum.BAJO, UrgenciaEnum.BAJA): PriorityEnum.P4,
}

# SLA en horas según la prioridad
SLA_HOURS_MAP = {
    PriorityEnum.P1: 2,
    PriorityEnum.P2: 8,
    PriorityEnum.P3: 24,
    PriorityEnum.P4: 48,
}


def calculate_priority_and_sla(
    impacto: ImpactoEnum, urgencia: UrgenciaEnum
) -> Tuple[PriorityEnum, int]:
    """Calcula determinísticamente la prioridad y el SLA según la matriz de impacto y urgencia."""
    prioridad = PRIORITY_MATRIX.get(
        (impacto, urgencia), PriorityEnum.P4
    )
    sla_horas = SLA_HOURS_MAP[prioridad]
    return prioridad, sla_horas


class IncidentAnalysis(BaseModel):
    """Estructura del análisis de triaje devuelto por el LLM."""

    categoria: CategoryEnum = Field(
        ...,
        description="Categoría principal del incidente según el ámbito técnico/operativo.",
    )
    impacto: ImpactoEnum = Field(
        ...,
        description="Alcance del impacto del problema: ALTO (empresa), MEDIO (departamento), BAJO (un usuario).",
    )
    urgencia: UrgenciaEnum = Field(
        ...,
        description="Grado de urgencia: ALTA (bloqueo total), MEDIA (degradado), BAJA (no bloqueante).",
    )
    prioridad: PriorityEnum = Field(
        ...,
        description="Nivel de prioridad calculado: P1, P2, P3 o P4.",
    )
    sla_horas: int = Field(
        ...,
        description="Tiempo máximo de resolución en horas: 2 para P1, 8 para P2, 24 para P3, 48 para P4.",
    )
    resumen_ejecutivo: str = Field(
        ...,
        description="Descripción concisa y limpia del problema en 1 sola línea.",
    )
    requiere_rag: bool = Field(
        ...,
        description="True si el incidente corresponde a una duda de uso, procedimiento operativo o error conocido documentable en manuales.",
    )


class IncidentInput(BaseModel):
    """Datos iniciales recibidos desde el formulario o cliente."""

    titulo: str = Field(..., min_length=1, description="Título del incidente")
    descripcion: str = Field(
        ..., min_length=1, description="Descripción detallada del incidente"
    )
    usuario: str = Field(
        ..., min_length=1, description="Usuario que reporta el incidente"
    )
