import os
from typing import List
import numpy as np
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

# 1. Enable CORS for all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (including POST, OPTIONS)
    allow_headers=["*"],  # Allows all headers
)

# 2. Define the expected request schema
class TelemetryRequest(BaseModel):
    regions: List[str]
    threshold_ms: float

# Mock Telemetry Data (Replace this with your downloaded sample data if needed)
# In a real scenario, this would load from a JSON file or database.
MOCK_TELEMETRY = {
    "apac": [
        {"latency": 150, "up": 1},
        {"latency": 190, "up": 1},
        {"latency": 120, "up": 0},
        {"latency": 210, "up": 1},
    ],
    "amer": [
        {"latency": 80, "up": 1},
        {"latency": 95, "up": 1},
        {"latency": 185, "up": 1},
        {"latency": 70, "up": 1},
    ]
}

@app.post("/analytics")
def get_analytics(payload: TelemetryRequest):
    response_data = {}
    
    for region in payload.regions:
        # Fallback to empty list if region doesn't exist in data
        records = MOCK_TELEMETRY.get(region.lower(), [])
        
        if not records:
            response_data[region] = {
                "avg_latency": 0.0,
                "p95_latency": 0.0,
                "avg_uptime": 0.0,
                "breaches": 0
            }
            continue
            
        latencies = [r["latency"] for r in records]
        uptimes = [r["up"] for r in records]
        
        # Calculate Metrics
        avg_latency = float(np.mean(latencies))
        p95_latency = float(np.percentile(latencies, 95))
        avg_uptime = float(np.mean(uptimes))
        breaches = int(sum(1 for l in latencies if l > payload.threshold_ms))
        
        response_data[region] = {
            "avg_latency": round(avg_latency, 2),
            "p95_latency": round(p95_latency, 2),
            "avg_uptime": round(avg_uptime, 4), # e.g. 0.95 for 95% uptime
            "breaches": breaches
        }
        
    return response_data
