from subprocess import CompletedProcess

import pytest

from app.modelica_runner import OpenModelicaError, run_model


def test_missing_omc_has_clear_error(monkeypatch, tmp_path):
    model_file = tmp_path / "Example.mo"
    model_file.write_text("model Example end Example;", encoding="utf-8")
    monkeypatch.setattr("app.modelica_runner.find_omc", lambda: None)

    with pytest.raises(OpenModelicaError, match="omc není dostupný"):
        run_model(
            model_name="Example",
            model_file=model_file,
            overrides={},
            stop_time=1,
            intervals=1,
        )


def test_runner_passes_overrides_to_openmodelica(monkeypatch, tmp_path):
    model_file = tmp_path / "Example.mo"
    model_file.write_text("model Example end Example;", encoding="utf-8")
    captured = {}
    monkeypatch.setattr("app.modelica_runner.find_omc", lambda: "omc")

    def fake_run(command, *, cwd, **_kwargs):
        captured["command"] = command
        captured["script"] = (cwd / "simulate.mos").read_text(encoding="utf-8")
        (cwd / "Example_res.csv").write_text("time,value\n0,42\n", encoding="utf-8")
        return CompletedProcess(command, 0, "", "")

    monkeypatch.setattr("app.modelica_runner.subprocess.run", fake_run)
    rows = run_model(
        model_name="Example",
        model_file=model_file,
        overrides={"diameter": 0.025, "pressureDrop": 100_000},
        stop_time=2,
        intervals=20,
    )

    assert captured["command"][0] == "omc"
    assert "numberOfIntervals=20" in captured["script"]
    assert "diameter=0.025000000000000001" in captured["script"]
    assert "pressureDrop=100000" in captured["script"]
    assert rows == [{"time": 0.0, "value": 42.0}]
