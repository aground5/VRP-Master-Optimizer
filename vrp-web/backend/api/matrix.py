"""
OSRM Matrix API Proxy

Fetches distance/time matrix from OSRM public API.
"""
from fastapi import APIRouter, HTTPException
import httpx
from typing import List

from schemas.models import MatrixRequest, MatrixResponse, Site

router = APIRouter(prefix="/api/matrix", tags=["matrix"])

OSRM_BASE_URL = "https://router.project-osrm.org"


def build_osrm_coords(sites: List[Site]) -> str:
    """Convert sites to OSRM coordinate string: lng,lat;lng,lat;..."""
    return ";".join(f"{s.coords.lng},{s.coords.lat}" for s in sites)


@router.post("", response_model=MatrixResponse)
async def generate_matrix(request: MatrixRequest):
    """
    Generate distance/time matrix from OSRM for all sites.
    """
    if len(request.sites) < 2:
        raise HTTPException(status_code=400, detail="Need at least 2 sites")
    
    if len(request.sites) > 100:
        raise HTTPException(status_code=400, detail="Max 100 sites supported")
    
    coords = build_osrm_coords(request.sites)
    url = f"{OSRM_BASE_URL}/table/v1/driving/{coords}?annotations=duration,distance"
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPError as e:
            raise HTTPException(status_code=502, detail=f"OSRM API error: {str(e)}")
    
    if data.get("code") != "Ok":
        raise HTTPException(status_code=502, detail=f"OSRM error: {data.get('message', 'Unknown')}")
    
    # Convert: seconds -> minutes, meters -> meters
    durations_sec = data.get("durations", [])
    distances_m = data.get("distances", [])
    
    # Convert seconds to minutes (round up)
    durations_min = [
        [int((d + 59) // 60) if d is not None else 9999 for d in row]
        for row in durations_sec
    ]
    
    # Keep distances in meters (or convert to km if needed)
    distances = [
        [int(d) if d is not None else 999999 for d in row]
        for row in distances_m
    ]
    
    return MatrixResponse(durations=durations_min, distances=distances)
