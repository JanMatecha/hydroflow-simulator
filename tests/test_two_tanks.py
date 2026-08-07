import pytest
from pydantic import ValidationError

from app.models.two_tanks import TwoTanksInput, run_simulation


def test_input_rejects_non_positive_initial_level():
    with pytest.raises(ValidationError):
        TwoTanksInput(tank1_initial_level_m=0)


def test_simulation_passes_parameters_and_maps_time_series(monkeypatch):
    captured = {}

    def fake_run_model(**kwargs):
        captured.update(kwargs)
        return [
            {
                "time": 0,
                "level1": 1.2,
                "level2": 0.3,
                "volumeFlow": 0,
                "velocity": 0,
            },
            {
                "time": 10,
                "level1": 1.1,
                "level2": 0.4,
                "volumeFlow": 0.001,
                "velocity": 2.04,
            },
        ]

    monkeypatch.setattr("app.models.two_tanks.run_model", fake_run_model)
    result = run_simulation(TwoTanksInput(pipe_diameter_mm=32, duration_s=600))

    assert captured["model_name"] == "TwoTanks"
    assert captured["overrides"]["pipeDiameter"] == pytest.approx(0.032)
    assert captured["stop_time"] == 600
    assert result.maximum_flow_m3_h == pytest.approx(3.6)
    assert result.final_tank1_level_m == pytest.approx(1.1)
    assert result.final_tank2_level_m == pytest.approx(0.4)
    assert result.equilibrium_level_m == pytest.approx(0.75)
    assert result.settling_time_s is None
    assert len(result.points) == 2
