from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import json
import math
from pathlib import Path

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_PATH = Path(__file__).parent / "telemetry.json"

with open(DATA_PATH, "r", encoding="utf-8") as f:
    telemetry = json.load(f)

def percentile_95(values):
    values = sorted(values)
    n = len(values)
    if n == 0:
        return 0

    index = math.ceil(0.95 * n) - 1
    return values[index]

@app.get("/")
def home():
    return {"message": "Analytics API running"}

@app.post("/")
async def analytics_root(request: Request):
    return await calculate(request)

@app.post("/analytics")
async def analytics(request: Request):
    return await calculate(request)

async def calculate(request: Request):
    body = await request.json()

    regions = body.get("regions", [])
    threshold = float(body.get("threshold_ms", 180))

    results = []

    for region in regions:
        rows = [
            r for r in telemetry
            if str(r.get("region", "")).lower() == region.lower()
        ]

        latencies = [float(r["latency_ms"]) for r in rows]
        uptimes = [float(r["uptime_pct"]) for r in rows]

        if len(rows) == 0:
            results.append({
                "region": region,
                "avg_latency": 0,
                "p95_latency": 0,
                "avg_uptime": 0,
                "breaches": 0
            })
            continue

        results.append({
            "region": region,
            "avg_latency": round(sum(latencies) / len(latencies), 2),
            "p95_latency": round(percentile_95(latencies), 2),
            "avg_uptime": round(sum(uptimes) / len(uptimes), 3),
            "breaches": sum(1 for x in latencies if x > threshold)
        })

    return results
