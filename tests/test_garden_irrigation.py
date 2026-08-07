import pytest
from pydantic import ValidationError

from app.models.garden_irrigation import GardenIrrigationInput, run_simulation


def test_input_rejects_valve_opening_above_one():
    with pytest.raises(ValidationError):
        GardenIrrigationInput(opening_a=1.01)


def test_simulation_passes_parameters_and_maps_all_beds(monkeypatch):
    captured = {}

    def fake_run_model(**kwargs):
        captured.update(kwargs)
        row = {
            "time": 1,
            "totalFlow": 0.001,
            "pressureAfterFilter": 8_000,
            "tankLevelEndEstimated": 0.7,
        }
        for index in range(1, 11):
            row[f"bedFlow[{index}]"] = 0.0001
            row[f"rowFlow[{index}]"] = 0.00002
            row[f"bedInletPressure[{index}]"] = 60_000
            row[f"rowEndPressure[{index}]"] = 55_000
            row[f"averageEmitterFlow[{index}]"] = 5e-7
            row[f"waterDelivered[{index}]"] = 6
        return [row]

    monkeypatch.setattr("app.models.garden_irrigation.run_model", fake_run_model)
    result = run_simulation(
        GardenIrrigationInput(
            tank_water_level_m=1.2,
            irrigation_duration_min=30,
            opening_a=0.5,
        )
    )

    assert captured["model_name"] == "GardenIrrigation"
    assert captured["overrides"]["tankWaterLevel"] == pytest.approx(1.2)
    assert captured["overrides"]["irrigationDuration"] == pytest.approx(1_800)
    assert captured["overrides"]["valveA"] == pytest.approx(0.5)
    assert result.total_flow_l_min == pytest.approx(60)
    assert len(result.beds) == 10
    assert len(result.rows) == 40
    assert result.beds[0].id == "A"
    assert result.beds[-1].id == "J"
