"""Zpětně kompatibilní názvy schémat původního API."""

from app.models.two_tanks import (
    TwoTanksInput as SimulationInput,
)
from app.models.two_tanks import (
    TwoTanksPoint as SimulationPoint,
)
from app.models.two_tanks import (
    TwoTanksResult as SimulationResult,
)

__all__ = ["SimulationInput", "SimulationPoint", "SimulationResult"]
