import math
from pathlib import Path

from pydantic import BaseModel, Field

from app.modelica_runner import OpenModelicaError, run_model

MODEL_FILE = Path(__file__).resolve().parents[2] / "modelica" / "GardenIrrigation.mo"

BED_SPECS = (
    ("A", "A", 6.55, 5, 6.0, 1.6 * 6.0),
    ("B", "A", 4.55, 6, 13.0, 2.0 * 13.0),
    ("C", "A", 7.55, 2, 14.0, 0.5 * 14.0),
    ("D", "A", 6.55, 5, 9.0, 1.5 * 9.0),
    ("E", "B", 7.95, 5, 3.0, math.pi * 1.5**2),
    ("F", "B", 7.05, 5, 3.2, 1.4 * 3.2),
    ("G", "B", 6.55, 3, 2.5, 1.0 * 2.5),
    ("H", "B", 3.70, 3, 2.4, 0.75 * 2.4),
    ("I", "B", 5.20, 3, 1.7, 0.9 * 1.7),
    ("J", "B", 5.20, 3, 2.0, 1.0 * 2.0),
)


class GardenIrrigationInput(BaseModel):
    tank_water_level_m: float = Field(1.0, ge=0, le=20)
    tank_area_m2: float = Field(2.0, gt=0.1, le=20)
    irrigation_duration_min: float = Field(60.0, gt=0, le=720)
    filter_head_loss_m: float = Field(0.2, ge=0, le=10)
    main_diameter_mm: float = Field(25.0, gt=5, le=100)
    row_inner_diameter_mm: float = Field(13.6, gt=3, le=30)
    dripper_spacing_m: float = Field(0.33, gt=0.05, le=2)
    nominal_emitter_flow_l_h: float = Field(2.0, gt=0, le=20)
    nominal_emitter_pressure_bar: float = Field(1.0, gt=0.001, le=10)
    emitter_exponent: float = Field(0.5, ge=0.1, le=1.5)
    opening_a: float = Field(1.0, ge=0, le=1)
    opening_b: float = Field(1.0, ge=0, le=1)
    opening_c: float = Field(1.0, ge=0, le=1)
    opening_d: float = Field(1.0, ge=0, le=1)
    opening_e: float = Field(1.0, ge=0, le=1)
    opening_f: float = Field(1.0, ge=0, le=1)
    opening_g: float = Field(1.0, ge=0, le=1)
    opening_h: float = Field(1.0, ge=0, le=1)
    opening_i: float = Field(1.0, ge=0, le=1)
    opening_j: float = Field(1.0, ge=0, le=1)


class IrrigationBedResult(BaseModel):
    id: str
    zone: str
    elevation_drop_m: float
    area_m2: float
    row_count: int
    row_length_m: float
    emitter_count: int
    valve_opening: float
    inlet_pressure_bar: float
    row_end_pressure_bar: float
    bed_flow_l_min: float
    row_flow_l_h: float
    average_emitter_flow_l_h: float
    water_delivered_l: float
    relative_delivery_percent: float


class IrrigationRowResult(BaseModel):
    bed_id: str
    row_number: int
    length_m: float
    emitter_count: int
    flow_l_h: float
    start_pressure_bar: float
    end_pressure_bar: float
    average_emitter_flow_l_h: float
    relative_unevenness_percent: float


class GardenIrrigationResult(BaseModel):
    total_flow_l_min: float
    pressure_after_filter_bar: float
    total_water_l: float
    tank_level_end_estimated_m: float
    emitter_uniformity_percent: float | None
    beds: list[IrrigationBedResult]
    rows: list[IrrigationRowResult]
    warnings: list[str]


def _opening(data: GardenIrrigationInput, bed_id: str) -> float:
    return getattr(data, f"opening_{bed_id.lower()}")


def run_simulation(data: GardenIrrigationInput) -> GardenIrrigationResult:
    openings = {bed_id: _opening(data, bed_id) for bed_id, *_ in BED_SPECS}
    result_rows = run_model(
        model_name="GardenIrrigation",
        model_file=MODEL_FILE,
        overrides={
            "tankWaterLevel": data.tank_water_level_m,
            "tankArea": data.tank_area_m2,
            "irrigationDuration": data.irrigation_duration_min * 60,
            "filterHeadLoss": data.filter_head_loss_m,
            "mainDiameter": data.main_diameter_mm / 1_000,
            "rowDiameter": data.row_inner_diameter_mm / 1_000,
            "dripperSpacing": data.dripper_spacing_m,
            "nominalEmitterFlow": data.nominal_emitter_flow_l_h / 3_600_000,
            "nominalEmitterPressure": data.nominal_emitter_pressure_bar * 100_000,
            "emitterExponent": data.emitter_exponent,
            **{f"valve{bed_id}": opening for bed_id, opening in openings.items()},
        },
        stop_time=1,
        intervals=1,
    )

    result = result_rows[-1]
    required = ("totalFlow", "pressureAfterFilter", "tankLevelEndEstimated")
    required += tuple(
        f"{name}[{index}]"
        for index in range(1, 11)
        for name in (
            "bedFlow",
            "rowFlow",
            "bedInletPressure",
            "rowEndPressure",
            "averageEmitterFlow",
            "waterDelivered",
        )
    )
    try:
        for name in required:
            result[name]
    except KeyError as exc:
        raise OpenModelicaError(f"Ve výsledku chybí proměnná {exc.args[0]}.") from exc

    active_emitter_total = sum(
        row_count * (math.floor(row_length / data.dripper_spacing_m) + 1)
        for bed_id, _zone, _drop, row_count, row_length, _area in BED_SPECS
        if openings[bed_id] > 0.0001
    )
    total_flow = result["totalFlow"]
    beds: list[IrrigationBedResult] = []
    rows: list[IrrigationRowResult] = []
    emitter_flows: list[float] = []

    for index, spec in enumerate(BED_SPECS, start=1):
        bed_id, zone, elevation_drop, row_count, row_length, area = spec
        emitter_count_per_row = math.floor(row_length / data.dripper_spacing_m) + 1
        bed_emitter_count = row_count * emitter_count_per_row
        bed_flow = result[f"bedFlow[{index}]"]
        row_flow_l_h = result[f"rowFlow[{index}]"] * 3_600_000
        emitter_flow_l_h = result[f"averageEmitterFlow[{index}]"] * 3_600_000
        if openings[bed_id] > 0.0001:
            emitter_flows.append(emitter_flow_l_h)
        target_share = (
            bed_emitter_count / active_emitter_total
            if openings[bed_id] > 0.0001 and active_emitter_total
            else 0
        )
        actual_share = bed_flow / total_flow if total_flow > 0 else 0
        relative_delivery = actual_share / target_share * 100 if target_share else 0
        inlet_pressure_bar = result[f"bedInletPressure[{index}]"] / 100_000
        end_pressure_bar = result[f"rowEndPressure[{index}]"] / 100_000

        beds.append(
            IrrigationBedResult(
                id=bed_id,
                zone=zone,
                elevation_drop_m=elevation_drop,
                area_m2=area,
                row_count=row_count,
                row_length_m=row_length,
                emitter_count=bed_emitter_count,
                valve_opening=openings[bed_id],
                inlet_pressure_bar=inlet_pressure_bar,
                row_end_pressure_bar=end_pressure_bar,
                bed_flow_l_min=bed_flow * 60_000,
                row_flow_l_h=row_flow_l_h,
                average_emitter_flow_l_h=emitter_flow_l_h,
                water_delivered_l=result[f"waterDelivered[{index}]"],
                relative_delivery_percent=relative_delivery,
            )
        )
        rows.extend(
            IrrigationRowResult(
                bed_id=bed_id,
                row_number=row_number,
                length_m=row_length,
                emitter_count=emitter_count_per_row,
                flow_l_h=row_flow_l_h,
                start_pressure_bar=inlet_pressure_bar,
                end_pressure_bar=end_pressure_bar,
                average_emitter_flow_l_h=emitter_flow_l_h,
                relative_unevenness_percent=0,
            )
            for row_number in range(1, row_count + 1)
        )

    warnings: list[str] = []
    if not emitter_flows:
        warnings.append("Všechny vstupní ventily jsou zavřené.")
    if result["tankLevelEndEstimated"] <= 0 and total_flow > 0:
        warnings.append("Pro zadanou dobu nestačí zásoba vody v IBC nádržích.")
    low_pressure_beds = [
        bed.id
        for bed in beds
        if bed.valve_opening > 0.0001 and bed.inlet_pressure_bar < 0.05
    ]
    if low_pressure_beds:
        warnings.append(
            "Velmi nízký tlak na vstupu záhonů: " + ", ".join(low_pressure_beds) + "."
        )
    warnings.append(
        "První verze používá ustálený průtok; pokles hladiny je orientační bilance."
    )

    uniformity = None
    if emitter_flows and max(emitter_flows) > 0:
        uniformity = min(emitter_flows) / max(emitter_flows) * 100
    return GardenIrrigationResult(
        total_flow_l_min=total_flow * 60_000,
        pressure_after_filter_bar=result["pressureAfterFilter"] / 100_000,
        total_water_l=sum(bed.water_delivered_l for bed in beds),
        tank_level_end_estimated_m=result["tankLevelEndEstimated"],
        emitter_uniformity_percent=uniformity,
        beds=beds,
        rows=rows,
        warnings=warnings,
    )
