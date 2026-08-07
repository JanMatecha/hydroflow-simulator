from pathlib import Path

from pydantic import BaseModel, Field

from app.modelica_runner import OpenModelicaError, run_model

MODEL_FILE = Path(__file__).resolve().parents[2] / "modelica" / "WaterPipe.mo"


class WaterPipeInput(BaseModel):
    pressure_drop_bar: float = Field(1.0, gt=0, le=100)
    length_m: float = Field(10.0, gt=0, le=100_000)
    diameter_mm: float = Field(25.0, gt=0.1, le=5_000)
    roughness_mm: float = Field(0.0015, ge=0, le=10)
    temperature_c: float = Field(20.0, ge=0.01, le=95)


class PressurePoint(BaseModel):
    distance_m: float
    pressure_drop_bar: float


class WaterPipeResult(BaseModel):
    volume_flow_m3_h: float
    mass_flow_kg_s: float
    velocity_m_s: float
    reynolds_number: float
    flow_regime: str
    friction_factor: float
    density_kg_m3: float
    viscosity_pa_s: float
    pressure_profile: list[PressurePoint]


def _flow_regime(reynolds: float) -> str:
    if reynolds < 2_300:
        return "laminární"
    if reynolds < 4_000:
        return "přechodové"
    return "turbulentní"


def run_simulation(data: WaterPipeInput) -> WaterPipeResult:
    rows = run_model(
        model_name="WaterPipe",
        model_file=MODEL_FILE,
        overrides={
            "pressureDrop": data.pressure_drop_bar * 100_000,
            "pipeLength": data.length_m,
            "diameter": data.diameter_mm / 1_000,
            "roughness": data.roughness_mm / 1_000,
            "temperatureC": data.temperature_c,
        },
        stop_time=1,
        intervals=1,
    )

    row = rows[-1]
    required = (
        "volumeFlow",
        "massFlow",
        "velocity",
        "reynolds",
        "frictionFactor",
        "rho",
        "mu",
    )
    try:
        for name in required:
            row[name]
    except KeyError as exc:
        raise OpenModelicaError(f"Ve výsledku chybí proměnná {exc.args[0]}.") from exc

    profile = [
        PressurePoint(
            distance_m=data.length_m * index / 20,
            pressure_drop_bar=data.pressure_drop_bar * index / 20,
        )
        for index in range(21)
    ]
    return WaterPipeResult(
        volume_flow_m3_h=row["volumeFlow"] * 3_600,
        mass_flow_kg_s=row["massFlow"],
        velocity_m_s=row["velocity"],
        reynolds_number=row["reynolds"],
        flow_regime=_flow_regime(row["reynolds"]),
        friction_factor=row["frictionFactor"],
        density_kg_m3=row["rho"],
        viscosity_pa_s=row["mu"],
        pressure_profile=profile,
    )
