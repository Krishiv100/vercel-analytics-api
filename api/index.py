from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import json
from pathlib import Path
import math

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)

class AnalyticsRequest(BaseModel):
    regions: List[str]
    threshold_ms: float


def load_telemetry():
    file_path = Path(__file__).parent / "telemetry.json"
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, dict):
        for key in ["data", "records", "telemetry"]:
            if key in data:
                return data[key]

    return data


telemetry = load_telemetry()


def percentile_95(values):
    values = sorted(values)
    if not values:
        return 0

    k = math.ceil(0.95 * len(values)) - 1
    return values[k]


@app.get("/")
def home():
    return {"message": "Analytics API running"}


@app.post("/analytics")
def analytics(req: AnalyticsRequest):
    result = {}

    for region in req.regions:
        rows = [
            r for r in telemetry
            if str(r.get("region", "")).lower() == region.lower()
        ]

        latencies = [
            float(r.get("latency_ms", r.get("latency", 0)))
            for r in rows
        ]

        uptimes = [
            float(r.get("uptime", r.get("uptime_pct", 0)))
            for r in rows
        ]

        breaches = sum(1 for x in latencies if x > req.threshold_ms)

        result[region] = {
            "avg_latency": round(sum(latencies) / len(latencies), 2) if latencies else 0,
            "p95_latency": round(percentile_95(latencies), 2) if latencies else 0,
            "avg_uptime": round(sum(uptimes) / len(uptimes), 2) if uptimes else 0,
            "breaches": breaches
        }

    return result
