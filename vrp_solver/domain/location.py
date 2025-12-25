"""
Location & Site Domain Models.

Encapsulates nodes in the network, their properties, and access constraints.
"""
from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class SiteProfile:
    """Static characteristics of a site type."""
    service_time_factor: float = 1.0  # Multiplier for default service time
    access_tags: List[str] = field(default_factory=list)  # e.g., ["no_truck", "lift_gate_required"]
    
@dataclass
class Location:
    """A node in the VRP graph (Depot, Customer, Hub)."""
    id: int
    name: str = ""
    
    # Time Window
    start_window: int = 0        # Ready time (earliest arrival)
    end_window: int = 10000      # Due time (latest arrival)
    
    # Service
    service_duration: int = 0    # Default service time at this location
    
    # Zone/Region
    zone_id: int = 0             # Zone identifier for clustering penalties
    
    # Site Constraints
    profile: SiteProfile = field(default_factory=SiteProfile)
    
    # Optional Coordinates (for visualization/distance calc if not matrix-based)
    x: float = 0.0
    y: float = 0.0
