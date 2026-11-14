import json
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from src.main import run as run_pipeline
from src.repository import PriceRepository

load_dotenv()

app = FastAPI(
    title="Flight Price Radar API",
    description="API de monitoramento de passagens aéreas, histórico de tarifas e alertas.",
    version="1.0.0",
)

ROUTES_PATH = Path("src/routes.json")


class TripCreate(BaseModel):
    trip_name: str = Field(..., examples=["São Paulo -> Santiago"])
    origins: list[str] = Field(..., examples=[["GRU", "CGH"]])
    destinations: list[str] = Field(..., examples=[["SCL"]])
    departure_date: str = Field(..., examples=["2027-06-15"])
    flexible_days: int = Field(default=1, ge=0, le=3)
    target_price: float | None = Field(default=None, examples=[1100.00])


@app.get("/health", tags=["Sistema"])
def health_check():
    return {"status": "ok", "service": "flight-price-radar"}


@app.get("/trips", tags=["Viagens"])
def list_trips():
    with open(ROUTES_PATH, "r", encoding="utf-8") as f:
        trips = json.load(f)

    repo = PriceRepository()
    enriched = []
    for trip in trips:
        stats = repo.get_stats(trip["trip_name"])
        enriched.append({**trip, "stats": stats})

    return enriched


@app.post("/trips", status_code=201, tags=["Viagens"])
def add_trip(trip: TripCreate):
    with open(ROUTES_PATH, "r", encoding="utf-8") as f:
        trips = json.load(f)

    if any(t["trip_name"].lower() == trip.trip_name.lower() for t in trips):
        raise HTTPException(status_code=400, detail="Já existe uma viagem cadastrada com esse nome.")

    trips.append(trip.model_dump())
    with open(ROUTES_PATH, "w", encoding="utf-8") as f:
        json.dump(trips, f, indent=2, ensure_ascii=False)

    return {"message": "Viagem adicionada com sucesso!", "trip": trip}


@app.get("/history", tags=["Histórico"])
def get_price_history(trip_name: str | None = None, limit: int = 50):
    repo = PriceRepository()
    return repo.get_history(trip_name=trip_name, limit=limit)


@app.post("/scan", tags=["Pipeline"])
def trigger_scan():
    run_pipeline()
    return {"message": "Varredura executada com sucesso! Verifique o histórico ou o Discord."}