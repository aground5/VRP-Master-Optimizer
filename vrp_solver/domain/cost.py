"""
Cost Domain Models.

Encapsulates all cost structures: fixed, variable, penalties.
"""
from dataclasses import dataclass

@dataclass
class VehicleCostProfile:
    """Cost parameters for a vehicle type."""
    fixed: int = 0               # Per-use fixed cost
    per_km: int = 0              # Distance-based cost
    per_minute: int = 0          # Time-based cost (labor)
    per_kg_km: int = 0           # Weight-distance cost (fuel efficiency)
    per_wait_minute: int = 0     # Idling/waiting cost (anti-idle)

@dataclass
class PenaltyConfig:
    """Penalty costs for violations."""
    unserved: int = 500000       # Penalty for not serving a location
    late_delivery: int = 50000   # Penalty per late delivery event
    zone_crossing: int = 2000    # Penalty for crossing zones
    
@dataclass
class OperationalCost:
    """Operational parameters affecting cost calculations."""
    depot_service_time: int = 30 # Min time at depot (anti-laundering)
    min_intra_transit: int = 5   # Min transit between stops at same site (anti-teleport)
