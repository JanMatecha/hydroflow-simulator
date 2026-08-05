from pydantic import BaseModel, Field


class SimulationInput(BaseModel):
    pressure_drop_bar: float = Field(1.0, gt=0, le=100)
    length_m: float = Field(10.0, gt=0, le=100_000)
    diameter_mm: float = Field(25.0, gt=0.1, le=5_000)
    roughness_mm: float = Field(0.0015, ge=0, le=10)
    temperature_c: float = Field(20.0, ge=0.01, le=95)


class PressurePoint(BaseModel):
    distance_m: float
    pressure_drop_bar: float


class SimulationResult(BaseModel):
    volume_flow_m3_h: float
    mass_flow_kg_s: float
    velocity_m_s: float
    reynolds_number: float
    flow_regime: str
    friction_factor: float
    density_kg_m3: float
    dynamic_viscosity_pa_s: float
    pressure_profile: list[PressurePoint]
