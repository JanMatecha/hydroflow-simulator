import csv
import shutil
import subprocess
import tempfile
from pathlib import Path

from app.schemas import PressurePoint, SimulationInput, SimulationResult

MODEL_FILE = Path(__file__).resolve().parent.parent / "modelica" / "WaterPipe.mo"
WINDOWS_OMC_PATHS = (
    Path(r"C:\Program Files\OpenModelica1.27.0-64bit\bin\omc.exe"),
    Path(r"C:\Program Files\OpenModelica1.26.0-64bit\bin\omc.exe"),
)


class OpenModelicaError(RuntimeError):
    """Chyba vzniklá při spuštění nebo čtení výsledku OpenModelicy."""


def _modelica_number(value: float) -> str:
    return format(value, ".17g")


def _read_last_row(result_file: Path) -> dict[str, float]:
    try:
        with result_file.open(encoding="utf-8", newline="") as stream:
            rows = list(csv.DictReader(stream))
        if not rows:
            raise OpenModelicaError("OpenModelica nevytvořila žádná výsledná data.")
        return {key: float(value) for key, value in rows[-1].items() if key}
    except (OSError, ValueError) as exc:
        raise OpenModelicaError("Výsledek OpenModelicy se nepodařilo načíst.") from exc


def _find_omc() -> str | None:
    command = shutil.which("omc")
    if command:
        return command
    return next((str(path) for path in WINDOWS_OMC_PATHS if path.is_file()), None)


def run_simulation(data: SimulationInput) -> SimulationResult:
    omc_command = _find_omc()
    if omc_command is None:
        raise OpenModelicaError("Příkaz omc není dostupný. Spusťte aplikaci v Dockeru.")

    overrides = {
        "pressureDrop": data.pressure_drop_bar * 100_000,
        "pipeLength": data.length_m,
        "diameter": data.diameter_mm / 1_000,
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
            "simulate(WaterPipe, startTime=0, stopTime=1, numberOfIntervals=1, "
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

        result_file = work_dir / "WaterPipe_res.csv"
        if process.returncode != 0 or not result_file.exists():
            details = (process.stderr or process.stdout).strip()
            raise OpenModelicaError(
                f"OpenModelica simulaci nedokončila. {details[-500:]}"
            )
        result = _read_last_row(result_file)

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
        values = {name: result[name] for name in required}
    except KeyError as exc:
        raise OpenModelicaError(f"Ve výsledku chybí proměnná {exc.args[0]}.") from exc

    profile = [
        PressurePoint(
            distance_m=data.length_m * step / 20,
            pressure_drop_bar=data.pressure_drop_bar * step / 20,
        )
        for step in range(21)
    ]
    reynolds = values["reynolds"]
    if reynolds < 2_300:
        regime = "laminární"
    elif reynolds < 4_000:
        regime = "přechodové"
    else:
        regime = "turbulentní"
    return SimulationResult(
        volume_flow_m3_h=values["volumeFlow"] * 3_600,
        mass_flow_kg_s=values["massFlow"],
        velocity_m_s=values["velocity"],
        reynolds_number=reynolds,
        flow_regime=regime,
        friction_factor=values["frictionFactor"],
        density_kg_m3=values["rho"],
        dynamic_viscosity_pa_s=values["mu"],
        pressure_profile=profile,
    )
