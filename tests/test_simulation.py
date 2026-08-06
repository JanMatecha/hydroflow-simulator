from pathlib import Path
from subprocess import CompletedProcess

import pytest
from pydantic import ValidationError

from app.schemas import SimulationInput
from app.simulation import OpenModelicaError, run_simulation


def test_input_rejects_non_positive_initial_level():
    with pytest.raises(ValidationError):
        SimulationInput(tank1_initial_level_m=0)


def test_missing_omc_has_clear_error(monkeypatch):
    monkeypatch.setattr("app.simulation.shutil.which", lambda _: None)
    monkeypatch.setattr("app.simulation.WINDOWS_OMC_PATHS", ())

    with pytest.raises(OpenModelicaError, match="omc není dostupný"):
        run_simulation(SimulationInput())


def test_simulation_maps_openmodelica_time_series(monkeypatch):
    monkeypatch.setattr("app.simulation.shutil.which", lambda _: "/usr/bin/omc")

    def fake_run(*_args, cwd: Path, **_kwargs):
        (cwd / "TwoTanks_res.csv").write_text(
            "time,level1,level2,volumeFlow,velocity\n"
            "0,1.2,0.3,0,0\n"
            "10,1.1,0.4,0.001,2.04\n",
            encoding="utf-8",
        )
        return CompletedProcess([], 0, "", "")

    monkeypatch.setattr("app.simulation.subprocess.run", fake_run)
    result = run_simulation(SimulationInput())

    assert result.maximum_flow_m3_h == pytest.approx(3.6)
    assert result.final_tank1_level_m == pytest.approx(1.1)
    assert result.final_tank2_level_m == pytest.approx(0.4)
    assert result.equilibrium_level_m == pytest.approx(0.75)
    assert result.settling_time_s is None
    assert len(result.points) == 2
