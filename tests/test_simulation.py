from pathlib import Path
from subprocess import CompletedProcess

import pytest
from pydantic import ValidationError

from app.schemas import SimulationInput
from app.simulation import OpenModelicaError, run_simulation


def test_input_rejects_non_positive_pressure_drop():
    with pytest.raises(ValidationError):
        SimulationInput(pressure_drop_bar=0)


def test_missing_omc_has_clear_error(monkeypatch):
    monkeypatch.setattr("app.simulation.shutil.which", lambda _: None)
    monkeypatch.setattr("app.simulation.WINDOWS_OMC_PATHS", ())

    with pytest.raises(OpenModelicaError, match="omc není dostupný"):
        run_simulation(SimulationInput())


def test_simulation_maps_openmodelica_result(monkeypatch):
    monkeypatch.setattr("app.simulation.shutil.which", lambda _: "/usr/bin/omc")

    def fake_run(*_args, cwd: Path, **_kwargs):
        (cwd / "WaterPipe_res.csv").write_text(
            "time,volumeFlow,massFlow,velocity,reynolds,frictionFactor,rho,mu\n"
            "1,0.001,0.998,2.04,50800,0.023,998,0.001\n",
            encoding="utf-8",
        )
        return CompletedProcess([], 0, "", "")

    monkeypatch.setattr("app.simulation.subprocess.run", fake_run)
    result = run_simulation(SimulationInput())

    assert result.volume_flow_m3_h == pytest.approx(3.6)
    assert result.flow_regime == "turbulentní"
    assert len(result.pressure_profile) == 21
    assert result.pressure_profile[-1].pressure_drop_bar == 1
