from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
import json
from pathlib import Path
import math

app = FastAPI()

CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "POST, GET, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type, Authorization",
}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.options("/{path:path}")
async def options_handler(path: str):
    return Response(headers=CORS_HEADERS)

def add_cors(data):
    return Response(
        content=json.dumps(data),
        media_type="application/json",
        headers=CORS_HEADERS
    )

def load_data():
    path = Path(__file__).parent / "telemetry.json"
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, dict):
        for key in ["data", "records", "telemetry"]:
            if key in data:
                return data[key]
    return data

telemetry = load_data()

def p95(values):
    values = sorted(values)
    if not values:
        return 0
    return values[math.ceil(0.95 * len(values)) - 1]

@app.get("/")
def home():
    return add_cors({"message": "Analytics API running"})

@app.post("/analytics")
async def analytics(request: Request):
    body = await request.json()
    regions = body.get("regions", [])
    threshold = body.get("threshold_ms", 180)

    response = {}

    for region in regions:
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

        response[region] = {
            "avg_latency": round(sum(latencies) / len(latencies), 2) if latencies else 0,
            "p95_latency": round(p95(latencies), 2) if latencies else 0,
            "avg_uptime": round(sum(uptimes) / len(uptimes), 2) if uptimes else 0,
            "breaches": sum(1 for x in latencies if x > threshold),
        }

    return add_cors(response)
