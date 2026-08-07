"""Zpětně kompatibilní importy původního modulu simulace."""

from app.modelica_runner import OpenModelicaError
from app.models.two_tanks import run_simulation

__all__ = ["OpenModelicaError", "run_simulation"]
