from pathlib import Path

from pydantic import BaseModel, Field

from app.modelica_runner import OpenModelicaError, run_model

MODEL_FILE = Path(__file__).resolve().parents[2] / "modelica" / "TwoTanks.mo"


class TwoTanksInput(BaseModel):
    tank1_diameter_m: float = Field(0.8, gt=0.05, le=20)
    tank2_diameter_m: float = Field(0.8, gt=0.05, le=20)
    tank1_initial_level_m: float = Field(1.2, gt=0, le=20)
    tank2_initial_level_m: float = Field(0.3, gt=0, le=20)
    pipe_length_m: float = Field(3.0, gt=0.01, le=10_000)
    pipe_diameter_mm: float = Field(25.0, gt=0.1, le=5_000)
    roughness_mm: float = Field(0.0015, ge=0, le=10)
    temperature_c: float = Field(20.0, ge=0.01, le=95)
    duration_s: float = Field(900.0, gt=0.1, le=86_400)


class TwoTanksPoint(BaseModel):
    time_s: float
    tank1_level_m: float
    tank2_level_m: float
    volume_flow_m3_h: float
    velocity_m_s: float


class TwoTanksResult(BaseModel):
    points: list[TwoTanksPoint]
    maximum_flow_m3_h: float
    final_tank1_level_m: float
    final_tank2_level_m: float
    equilibrium_level_m: float
    settling_time_s: float | None


def _settling_time(points: list[TwoTanksPoint]) -> float | None:
    for index, point in enumerate(points):
        remaining = points[index:]
        levels_close = all(
            abs(item.tank1_level_m - item.tank2_level_m) < 0.001 for item in remaining
        )
        flow_small = all(abs(item.volume_flow_m3_h) < 0.001 for item in remaining)
        if levels_close and flow_small:
            return point.time_s
    return None


def run_simulation(data: TwoTanksInput) -> TwoTanksResult:
    rows = run_model(
        model_name="TwoTanks",
        model_file=MODEL_FILE,
        overrides={
            "tank1Diameter": data.tank1_diameter_m,
            "tank2Diameter": data.tank2_diameter_m,
            "initialLevel1": data.tank1_initial_level_m,
            "initialLevel2": data.tank2_initial_level_m,
            "pipeLength": data.pipe_length_m,
            "pipeDiameter": data.pipe_diameter_mm / 1_000,
            "roughness": data.roughness_mm / 1_000,
            "temperatureC": data.temperature_c,
        },
        stop_time=data.duration_s,
        intervals=400,
    )

    required = ("time", "level1", "level2", "volumeFlow", "velocity")
    try:
        for name in required:
            rows[-1][name]
        points = [
            TwoTanksPoint(
                time_s=row["time"],
                tank1_level_m=row["level1"],
                tank2_level_m=row["level2"],
                volume_flow_m3_h=row["volumeFlow"] * 3_600,
                velocity_m_s=row["velocity"],
            )
            for row in rows
        ]
    except KeyError as exc:
        raise OpenModelicaError(f"Ve výsledku chybí proměnná {exc.args[0]}.") from exc

    area1 = 3.141592653589793 * data.tank1_diameter_m**2 / 4
    area2 = 3.141592653589793 * data.tank2_diameter_m**2 / 4
    equilibrium = (
        area1 * data.tank1_initial_level_m + area2 * data.tank2_initial_level_m
    ) / (area1 + area2)
    return TwoTanksResult(
        points=points,
        maximum_flow_m3_h=max(abs(point.volume_flow_m3_h) for point in points),
        final_tank1_level_m=points[-1].tank1_level_m,
        final_tank2_level_m=points[-1].tank2_level_m,
        equilibrium_level_m=equilibrium,
        settling_time_s=_settling_time(points),
    )
