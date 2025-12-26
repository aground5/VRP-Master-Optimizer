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
from .stop import Stop, StopType
from .route import Route

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
    stops: List[Stop] = field(default_factory=list)  # NEW: Stop-based routing
    
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
    
    # --- NEW: Stop-based helpers ---
    
    def get_stop(self, stop_id: int) -> Optional[Stop]:
        """Get stop by ID."""
        if 0 <= stop_id < len(self.stops):
            return self.stops[stop_id]
        return None
    
    def get_stop_location(self, stop_id: int) -> int:
        """Get the physical location index for a stop."""
        stop = self.get_stop(stop_id)
        return stop.location_idx if stop else 0
    
    def get_pickup_stop(self, shipment_idx: int) -> Optional[Stop]:
        """Get the pickup stop for a shipment."""
        for stop in self.stops:
            if stop.shipment_idx == shipment_idx and stop.is_pickup:
                return stop
        return None
    
    def get_delivery_stop(self, shipment_idx: int) -> Optional[Stop]:
        """Get the delivery stop for a shipment."""
        for stop in self.stops:
            if stop.shipment_idx == shipment_idx and stop.is_delivery:
                return stop
        return None
    
    def get_start_depot_stop(self, vehicle_idx: int) -> Optional[Stop]:
        """Get the start depot stop for a vehicle."""
        for stop in self.stops:
            if stop.vehicle_idx == vehicle_idx and stop.stop_type == StopType.DEPOT_START:
                return stop
        return None
    
    def get_end_depot_stop(self, vehicle_idx: int) -> Optional[Stop]:
        """Get the end depot stop for a vehicle."""
        for stop in self.stops:
            if stop.vehicle_idx == vehicle_idx and stop.stop_type == StopType.DEPOT_END:
                return stop
        return None
    
    @property
    def num_stops(self) -> int:
        """Total number of stops."""
        return len(self.stops)
    
    @property
    def shipment_stops(self) -> List[Stop]:
        """All pickup and delivery stops (excludes depots)."""
        return [s for s in self.stops if not s.is_depot]
