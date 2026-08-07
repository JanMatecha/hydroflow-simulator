from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.modelica_runner import OpenModelicaError
from app.models.garden_irrigation import (
    GardenIrrigationInput,
    GardenIrrigationResult,
)
from app.models.garden_irrigation import (
    run_simulation as run_garden_irrigation,
)
from app.models.two_tanks import (
    TwoTanksInput,
    TwoTanksResult,
)
from app.models.two_tanks import (
    run_simulation as run_two_tanks,
)
from app.models.water_pipe import (
    WaterPipeInput,
    WaterPipeResult,
)
from app.models.water_pipe import (
    run_simulation as run_water_pipe,
)

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(title="HydroFlow", version="0.3.0")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")


class ModelInfo(BaseModel):
    id: str
    name: str
    description: str


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(
        BASE_DIR / "static" / "index.html",
        headers={"Cache-Control": "no-store, max-age=0"},
    )


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/models", response_model=list[ModelInfo])
def models() -> list[ModelInfo]:
    return [
        ModelInfo(
            id="two-tanks",
            name="Dvě propojené nádoby",
            description="Nestacionární vyrovnávání hladin podle Bernoulliho rovnice.",
        ),
        ModelInfo(
            id="water-pipe",
            name="Samostatná trubka",
            description="Ustálené proudění v rovné kruhové trubce.",
        ),
        ModelInfo(
            id="garden-irrigation",
            name="Kapková závlaha",
            description="Gravitační závlaha deseti záhonů ze dvou IBC nádrží.",
        ),
    ]


def _run_two_tanks(data: TwoTanksInput) -> TwoTanksResult:
    try:
        return run_two_tanks(data)
    except OpenModelicaError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.post("/api/models/two-tanks/simulations", response_model=TwoTanksResult)
def simulate_two_tanks(data: TwoTanksInput) -> TwoTanksResult:
    return _run_two_tanks(data)


@app.post("/api/models/water-pipe/simulations", response_model=WaterPipeResult)
def simulate_water_pipe(data: WaterPipeInput) -> WaterPipeResult:
    try:
        return run_water_pipe(data)
    except OpenModelicaError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.post(
    "/api/models/garden-irrigation/simulations",
    response_model=GardenIrrigationResult,
)
def simulate_garden_irrigation(
    data: GardenIrrigationInput,
) -> GardenIrrigationResult:
    try:
        return run_garden_irrigation(data)
    except OpenModelicaError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.post("/api/simulations", response_model=TwoTanksResult, deprecated=True)
def simulate(data: TwoTanksInput) -> TwoTanksResult:
    """Původní endpoint zachovaný pro existující klienty."""

    return _run_two_tanks(data)
