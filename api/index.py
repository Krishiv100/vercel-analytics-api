from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
import json
import math
from pathlib import Path

app = FastAPI()

CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    "Access-Control-Allow-Headers": "*",
}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

def load_telemetry():
    folder = Path(__file__).parent
    for name in ["telemetry.json", "telemetary.json", "telementary.json"]:
        path = folder / name
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    return []

telemetry = load_telemetry()

def p95(values):
    values = sorted(values)
    if not values:
        return 0
    return values[math.ceil(0.95 * len(values)) - 1]

def json_response(data):
    return Response(
        content=json.dumps(data),
        media_type="application/json",
        headers=CORS_HEADERS
    )

@app.options("/{path:path}")
async def options_handler(path: str):
    return Response(headers=CORS_HEADERS)

@app.get("/")
def home():
    return json_response({
        "message": "Analytics API running",
        "records_loaded": len(telemetry)
    })

async def calculate(request: Request):
    body = await request.json()
    regions = body.get("regions", [])
    threshold = float(body.get("threshold_ms", 180))

    result = {}

    for region in regions:
        rows = [
            r for r in telemetry
            if str(r.get("region", "")).lower() == region.lower()
        ]

        latencies = [float(r.get("latency_ms", 0)) for r in rows]
        uptimes = [float(r.get("uptime_pct", 0)) for r in rows]

        result[region] = {
            "avg_latency": round(sum(latencies) / len(latencies), 2) if latencies else 0,
            "p95_latency": round(p95(latencies), 2) if latencies else 0,
            "avg_uptime": round(sum(uptimes) / len(uptimes), 3) if uptimes else 0,
            "breaches": sum(1 for x in latencies if x > threshold)
        }

    return json_response(result)

@app.post("/analytics")
async def analytics(request: Request):
    return await calculate(request)

@app.post("/analytics/")
async def analytics_slash(request: Request):
    return await calculate(request)
