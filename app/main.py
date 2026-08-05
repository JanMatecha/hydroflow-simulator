from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.schemas import SimulationInput, SimulationResult
from app.simulation import OpenModelicaError, run_simulation

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(title="HydroFlow", version="0.1.0")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(BASE_DIR / "static" / "index.html")


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/simulations", response_model=SimulationResult)
def simulate(data: SimulationInput) -> SimulationResult:
    try:
        return run_simulation(data)
    except OpenModelicaError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
