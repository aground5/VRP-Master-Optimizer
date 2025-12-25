"""
Vehicle Domain Models.

Encapsulates fleet assets, their profiles, and operational capabilities.
"""
from dataclasses import dataclass, field
from typing import List, Optional
from .cost import VehicleCostProfile
from .labor import LaborPolicy

@dataclass
class VehicleCapacity:
    """Physical capacity limits of a vehicle."""
    weight: int = 50             # Max weight (kg)
    volume: int = 50             # Max volume (m³ or units)
    # Could add: pallets, linear_meters, etc.

@dataclass
class VehicleProfile:
    """Static characteristics of a vehicle type."""
    type_id: int = 1
    capacity: VehicleCapacity = field(default_factory=VehicleCapacity)
    tags: List[str] = field(default_factory=list)  # Compatibility tags: ["frozen", "lift_gate", "hazmat"]
    speed_factor: float = 1.0    # Multiplier for travel times (slower trucks = > 1.0)

@dataclass
class Vehicle:
    """A specific vehicle instance in the fleet."""
    id: int
    name: str = ""
    start_loc: int = 0           # Starting depot/location
    end_loc: int = 0             # Ending depot/location
    profile: VehicleProfile = field(default_factory=VehicleProfile)
    cost: VehicleCostProfile = field(default_factory=VehicleCostProfile)
    labor: LaborPolicy = field(default_factory=LaborPolicy)

# Legacy compatibility alias
VehicleCost = VehicleCostProfile
