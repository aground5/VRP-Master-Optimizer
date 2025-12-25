"""
VRP Web API - FastAPI Main Application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.matrix import router as matrix_router
from api.optimize import router as optimize_router

app = FastAPI(
    title="VRP Optimizer API",
    description="Vehicle Routing Problem optimization service with OSRM integration",
    version="1.0.0"
)

# CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(matrix_router)
app.include_router(optimize_router)


@app.get("/")
async def root():
    return {
        "name": "VRP Optimizer API",
        "version": "1.0.0",
        "endpoints": ["/api/matrix", "/api/optimize"]
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}
