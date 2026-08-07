import csv
import shutil
import subprocess
import tempfile
from pathlib import Path

WINDOWS_OMC_PATHS = (
    Path(r"C:\Program Files\OpenModelica1.27.0-64bit\bin\omc.exe"),
    Path(r"C:\Program Files\OpenModelica1.26.0-64bit\bin\omc.exe"),
)


class OpenModelicaError(RuntimeError):
    """Chyba při spuštění nebo čtení výsledku OpenModelicy."""


def modelica_number(value: float) -> str:
    return format(value, ".17g")


def find_omc() -> str | None:
    command = shutil.which("omc")
    if command:
        return command
    return next((str(path) for path in WINDOWS_OMC_PATHS if path.is_file()), None)


def _read_rows(result_file: Path) -> list[dict[str, float]]:
    try:
        with result_file.open(encoding="utf-8", newline="") as stream:
            rows = [
                {key: float(value) for key, value in row.items() if key}
                for row in csv.DictReader(stream)
            ]
    except (OSError, TypeError, ValueError) as exc:
        raise OpenModelicaError("Výsledek OpenModelicy se nepodařilo načíst.") from exc

    if not rows:
        raise OpenModelicaError("OpenModelica nevytvořila žádná výsledná data.")

    deduplicated: list[dict[str, float]] = []
    for row in rows:
        if deduplicated and row.get("time") == deduplicated[-1].get("time"):
            deduplicated[-1] = row
        else:
            deduplicated.append(row)
    return deduplicated


def run_model(
    *,
    model_name: str,
    model_file: Path,
    overrides: dict[str, float],
    stop_time: float,
    intervals: int,
) -> list[dict[str, float]]:
    """Spustí Modelica model a vrátí řádky z výsledného CSV."""

    omc_command = find_omc()
    if omc_command is None:
        raise OpenModelicaError("Příkaz omc není dostupný.")
    if not model_file.is_file():
        raise OpenModelicaError(f"Soubor modelu {model_file.name} nebyl nalezen.")

    override_text = ",".join(
        f"{name}={modelica_number(value)}" for name, value in overrides.items()
    )
    with tempfile.TemporaryDirectory(prefix="hydroflow-") as work_dir_text:
        work_dir = Path(work_dir_text)
        local_model_file = work_dir / model_file.name
        shutil.copy2(model_file, local_model_file)
        script = work_dir / "simulate.mos"
        script.write_text(
            f'loadFile("{local_model_file.as_posix()}");\n'
            f"simulate({model_name}, startTime=0, "
            f"stopTime={modelica_number(stop_time)}, "
            f'numberOfIntervals={intervals}, outputFormat="csv", '
            f'simflags="-override {override_text}");\n'
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

        result_file = work_dir / f"{model_name}_res.csv"
        if process.returncode != 0 or not result_file.exists():
            details = (process.stderr or process.stdout).strip()
            suffix = f" {details[-500:]}" if details else ""
            raise OpenModelicaError(
                f"OpenModelica simulaci modelu {model_name} nedokončila.{suffix}"
            )
        return _read_rows(result_file)
