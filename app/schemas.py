from pydantic import BaseModel, Field


class SimulationInput(BaseModel):
    tank1_diameter_m: float = Field(0.8, gt=0.05, le=20)
    tank2_diameter_m: float = Field(0.8, gt=0.05, le=20)
    tank1_initial_level_m: float = Field(1.2, gt=0, le=20)
    tank2_initial_level_m: float = Field(0.3, gt=0, le=20)
    pipe_length_m: float = Field(3.0, gt=0.01, le=10_000)
    pipe_diameter_mm: float = Field(25.0, gt=0.1, le=5_000)
    roughness_mm: float = Field(0.0015, ge=0, le=10)
    temperature_c: float = Field(20.0, ge=0.01, le=95)
    duration_s: float = Field(900.0, gt=0.1, le=86_400)


class SimulationPoint(BaseModel):
    time_s: float
    tank1_level_m: float
    tank2_level_m: float
    volume_flow_m3_h: float
    velocity_m_s: float


class SimulationResult(BaseModel):
    points: list[SimulationPoint]
    maximum_flow_m3_h: float
    final_tank1_level_m: float
    final_tank2_level_m: float
    equilibrium_level_m: float
    settling_time_s: float | None
