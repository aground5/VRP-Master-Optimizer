"""
VRP Domain Package.

Exports all domain entities and the VRPData container.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional

# Core Entities
from .location import Location, SiteProfile
from .vehicle import Vehicle, VehicleProfile, VehicleCapacity, VehicleCostProfile, VehicleCost
from .shipment import Shipment, Cargo, TimeWindow
from .labor import LaborPolicy, WorkShift, BreakRule, LaborCost
from .cost import PenaltyConfig, OperationalCost

@dataclass
class VRPData:
    """
    Container for all VRP problem data (the Ontology).
    
    This is the single source of truth passed to the solver.
    """
    # Entities
    locations: List[Location] = field(default_factory=list)
    vehicles: List[Vehicle] = field(default_factory=list)
    shipments: List[Shipment] = field(default_factory=list)
    
    # Matrices [from_id][to_id]
    travel_time_matrix: List[List[int]] = field(default_factory=list)
    travel_dist_matrix: List[List[int]] = field(default_factory=list)
    setup_time_matrix: List[List[int]] = field(default_factory=list)
    
    # Global Policies
    penalties: PenaltyConfig = field(default_factory=PenaltyConfig)
    operations: OperationalCost = field(default_factory=OperationalCost)
    
    # --- Helper Methods ---
    
    def get_shipment_by_pickup(self, loc_id: int) -> Optional[Shipment]:
        for s in self.shipments:
            if s.pickup_id == loc_id:
                return s
        return None

    def get_shipment_by_delivery(self, loc_id: int) -> Optional[Shipment]:
        for s in self.shipments:
            if s.delivery_id == loc_id:
                return s
        return None
    
    def get_location(self, loc_id: int) -> Optional[Location]:
        for loc in self.locations:
            if loc.id == loc_id:
                return loc
        return None
    
    def get_vehicle(self, veh_id: int) -> Optional[Vehicle]:
        for v in self.vehicles:
            if v.id == veh_id:
                return v
        return None
