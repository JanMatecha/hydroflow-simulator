import csv
import shutil
import subprocess
import tempfile
from pathlib import Path

from app.schemas import SimulationInput, SimulationPoint, SimulationResult

MODEL_FILE = Path(__file__).resolve().parent.parent / "modelica" / "TwoTanks.mo"
WINDOWS_OMC_PATHS = (
    Path(r"C:\Program Files\OpenModelica1.27.0-64bit\bin\omc.exe"),
    Path(r"C:\Program Files\OpenModelica1.26.0-64bit\bin\omc.exe"),
)


class OpenModelicaError(RuntimeError):
    """Chyba vzniklá při spuštění nebo čtení výsledku OpenModelicy."""


def _modelica_number(value: float) -> str:
    return format(value, ".17g")


def _read_rows(result_file: Path) -> list[dict[str, float]]:
    try:
        with result_file.open(encoding="utf-8", newline="") as stream:
            rows = [
                {key: float(value) for key, value in row.items() if key}
                for row in csv.DictReader(stream)
            ]
        if not rows:
            raise OpenModelicaError("OpenModelica nevytvořila žádná výsledná data.")
        deduplicated: list[dict[str, float]] = []
        for row in rows:
            if deduplicated and row.get("time") == deduplicated[-1].get("time"):
                deduplicated[-1] = row
            else:
                deduplicated.append(row)
        return deduplicated
    except (OSError, ValueError) as exc:
        raise OpenModelicaError("Výsledek OpenModelicy se nepodařilo načíst.") from exc


def _find_omc() -> str | None:
    command = shutil.which("omc")
    if command:
        return command
    return next((str(path) for path in WINDOWS_OMC_PATHS if path.is_file()), None)


def _settling_time(points: list[SimulationPoint]) -> float | None:
    for index, point in enumerate(points):
        remaining = points[index:]
        levels_close = all(
            abs(item.tank1_level_m - item.tank2_level_m) < 0.001 for item in remaining
        )
        flow_small = all(abs(item.volume_flow_m3_h) < 0.001 for item in remaining)
        if levels_close and flow_small:
            return point.time_s
    return None


def run_simulation(data: SimulationInput) -> SimulationResult:
    omc_command = _find_omc()
    if omc_command is None:
        raise OpenModelicaError("Příkaz omc není dostupný.")

    overrides = {
        "tank1Diameter": data.tank1_diameter_m,
        "tank2Diameter": data.tank2_diameter_m,
        "initialLevel1": data.tank1_initial_level_m,
        "initialLevel2": data.tank2_initial_level_m,
        "pipeLength": data.pipe_length_m,
        "pipeDiameter": data.pipe_diameter_mm / 1_000,
        "roughness": data.roughness_mm / 1_000,
        "temperatureC": data.temperature_c,
    }
    override_text = ",".join(
        f"{name}={_modelica_number(value)}" for name, value in overrides.items()
    )

    with tempfile.TemporaryDirectory(prefix="hydroflow-") as work_dir_text:
        work_dir = Path(work_dir_text)
        model_file = work_dir / MODEL_FILE.name
        shutil.copy2(MODEL_FILE, model_file)
        script = work_dir / "simulate.mos"
        script.write_text(
            f'loadFile("{model_file.as_posix()}");\n'
            "simulate(TwoTanks, startTime=0, "
            f"stopTime={_modelica_number(data.duration_s)}, numberOfIntervals=400, "
            f'outputFormat="csv", simflags="-override {override_text}");\n'
            "getErrorString();\n",
            encoding="utf-8",
        )
        try:
            process = subprocess.run(
                [omc_command, str(script)],
                cwd=work_dir,
                capture_output=True,
                text=True,
                timeout=60,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise OpenModelicaError("Simulaci se nepodařilo spustit.") from exc

        result_file = work_dir / "TwoTanks_res.csv"
        if process.returncode != 0 or not result_file.exists():
            details = (process.stderr or process.stdout).strip()
            raise OpenModelicaError(
                f"OpenModelica simulaci nedokončila. {details[-500:]}"
            )
        rows = _read_rows(result_file)

    required = ("time", "level1", "level2", "volumeFlow", "velocity")
    try:
        points = [
            SimulationPoint(
                time_s=row["time"],
                tank1_level_m=row["level1"],
                tank2_level_m=row["level2"],
                volume_flow_m3_h=row["volumeFlow"] * 3_600,
                velocity_m_s=row["velocity"],
            )
            for row in rows
        ]
        for name in required:
            rows[-1][name]
    except KeyError as exc:
        raise OpenModelicaError(f"Ve výsledku chybí proměnná {exc.args[0]}.") from exc

    area1 = 3.141592653589793 * data.tank1_diameter_m**2 / 4
    area2 = 3.141592653589793 * data.tank2_diameter_m**2 / 4
    equilibrium = (
        area1 * data.tank1_initial_level_m + area2 * data.tank2_initial_level_m
    ) / (area1 + area2)
    return SimulationResult(
        points=points,
        maximum_flow_m3_h=max(abs(point.volume_flow_m3_h) for point in points),
        final_tank1_level_m=points[-1].tank1_level_m,
        final_tank2_level_m=points[-1].tank2_level_m,
        equilibrium_level_m=equilibrium,
        settling_time_s=_settling_time(points),
    )
