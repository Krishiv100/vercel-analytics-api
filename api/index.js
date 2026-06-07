from fastapi import FastAPI, Response, status
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Keep this middleware as a secondary layer of safety
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Explicitly catch preflight requests just in case
@app.options("/{path:path}")
def preflight_handler(path: str):
    return Response(
        status_code=status.HTTP_200_OK, 
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, GET, OPTIONS",
            "Access-Control-Allow-Headers": "*",
        }
    )
