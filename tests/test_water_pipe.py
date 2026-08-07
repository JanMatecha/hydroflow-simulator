import pytest
from pydantic import ValidationError

from app.models.water_pipe import WaterPipeInput, run_simulation


def test_input_accepts_one_bar_and_rejects_zero():
    assert WaterPipeInput(pressure_drop_bar=1).pressure_drop_bar == 1
    with pytest.raises(ValidationError):
        WaterPipeInput(pressure_drop_bar=0)


def test_simulation_passes_parameters_and_maps_results(monkeypatch):
    captured = {}

    def fake_run_model(**kwargs):
        captured.update(kwargs)
        return [
            {
                "time": 1,
                "volumeFlow": 0.001,
                "massFlow": 0.998,
                "velocity": 2.04,
                "reynolds": 50_000,
                "frictionFactor": 0.022,
                "rho": 998.2,
                "mu": 0.001002,
            }
        ]

    monkeypatch.setattr("app.models.water_pipe.run_model", fake_run_model)
    result = run_simulation(
        WaterPipeInput(pressure_drop_bar=1, diameter_mm=25, roughness_mm=0.0015)
    )

    assert captured["model_name"] == "WaterPipe"
    assert captured["overrides"]["pressureDrop"] == 100_000
    assert captured["overrides"]["diameter"] == pytest.approx(0.025)
    assert captured["overrides"]["roughness"] == pytest.approx(0.0000015)
    assert result.volume_flow_m3_h == pytest.approx(3.6)
    assert result.flow_regime == "turbulentní"
    assert len(result.pressure_profile) == 21
    assert result.pressure_profile[-1].pressure_drop_bar == 1
