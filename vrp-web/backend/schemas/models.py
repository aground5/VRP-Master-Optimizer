"""
VRP Web API - Pydantic Schemas

These schemas define the API contract and map to the VRP domain ontology.
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum

# ============================================================
# Location / Site
# ============================================================

class SiteType(str, Enum):
    DEPOT = "depot"
    CUSTOMER = "customer"
    HUB = "hub"

class Coordinates(BaseModel):
    lat: float
    lng: float

class TimeWindow(BaseModel):
    start: int = Field(0, description="Ready time in minutes from midnight")
    end: int = Field(1440, description="Due time in minutes from midnight")

class Site(BaseModel):
    id: str
    name: str = ""
    type: SiteType = SiteType.CUSTOMER
    coords: Coordinates
    service_duration: int = Field(10, description="Service time in minutes")
    zone_id: int = 0

# ============================================================
# Vehicle
# ============================================================

class VehicleCapacity(BaseModel):
    weight: int = 50
    volume: int = 50

class VehicleCost(BaseModel):
    fixed: int = 0
    per_km: int = 10
    per_minute: int = 10

class LaborShift(BaseModel):
    start_time: int = 0
    max_duration: int = 720
    standard_duration: int = 480

class BreakRule(BaseModel):
    interval_minutes: int = 240
    duration_minutes: int = 30

class Vehicle(BaseModel):
    id: str
    name: str = ""
    start_site_id: str  # Reference to Site ID
    end_site_id: str    # Reference to Site ID
    capacity: VehicleCapacity = Field(default_factory=VehicleCapacity)
    cost: VehicleCost = Field(default_factory=VehicleCost)
    shift: LaborShift = Field(default_factory=LaborShift)
    break_rule: BreakRule = Field(default_factory=BreakRule)
    tags: List[str] = Field(default_factory=list)

# ============================================================
# Shipment / Cargo
# ============================================================

class Cargo(BaseModel):
    weight: int = 0
    volume: int = 0

class Shipment(BaseModel):
    id: str
    name: str = ""
    pickup_site_id: str    # Reference to Site ID
    delivery_site_id: str  # Reference to Site ID
    pickup_window: TimeWindow = Field(default_factory=TimeWindow)     # Order-specific pickup time window
    delivery_window: TimeWindow = Field(default_factory=TimeWindow)   # Order-specific delivery time window
    cargo: Cargo = Field(default_factory=Cargo)
    required_tags: List[str] = Field(default_factory=list)
    priority: int = 1

# ============================================================
# Matrix Request/Response
# ============================================================

class MatrixRequest(BaseModel):
    sites: List[Site]

class MatrixResponse(BaseModel):
    durations: List[List[int]]  # in minutes
    distances: List[List[int]]  # in meters

# ============================================================
# Optimize Request/Response
# ============================================================

class PenaltyConfig(BaseModel):
    unserved: int = 500000
    late_delivery: int = 50000
    zone_crossing: int = 2000

class OptimizeRequest(BaseModel):
    sites: List[Site]
    vehicles: List[Vehicle]
    shipments: List[Shipment]
    durations: List[List[int]]
    distances: List[List[int]]
    penalties: PenaltyConfig = Field(default_factory=PenaltyConfig)
    max_solver_time: float = 30.0

class RouteStop(BaseModel):
    site_id: str
    arrival_time: int
    load_weight: int
    load_volume: int
    is_late: bool = False

class VehicleRoute(BaseModel):
    vehicle_id: str
    stops: List[RouteStop]
    total_distance: int
    total_time: int

class CostBreakdown(BaseModel):
    fixed: int
    distance: int
    labor: int
    zone_penalty: int
    rehandling: int
    waiting: int
    late_penalty: int
    unserved_penalty: int
    total: int

class OptimizeResponse(BaseModel):
    status: str  # "optimal", "feasible", "infeasible"
    routes: List[VehicleRoute]
    costs: CostBreakdown
    unserved_shipments: List[str] = Field(default_factory=list)
