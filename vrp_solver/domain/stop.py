"""
Stop Domain Model.

A Stop is a logical node in the routing graph.
It represents a visitable point (pickup, delivery, or depot) separate from the physical Location.
This allows multiple visits to the same physical location for different shipments.
"""
from dataclasses import dataclass
from enum import Enum


class StopType(Enum):
    """Type of stop in the route."""
    DEPOT_START = "depot_start"  # Vehicle departure point
    DEPOT_END = "depot_end"      # Vehicle return point
    PICKUP = "pickup"            # Pickup for a shipment
    DELIVERY = "delivery"        # Delivery for a shipment


@dataclass
class Stop:
    """
    A logical stop/node in the VRP graph.
    
    Note: TimeWindow is NOT stored here!
    - For PICKUP/DELIVERY: Use Shipment.pickup_window/delivery_window
    - For DEPOT: Use Location.start_window/end_window
    
    This design avoids data duplication and keeps Shipment as the source of truth.
    """
    id: int                     # Unique stop index (0, 1, 2, ...)
    stop_type: StopType         # What kind of stop
    location_idx: int           # Physical location index
    
    # For PICKUP/DELIVERY only (-1 for depots)
    shipment_idx: int = -1
    
    # For DEPOT only (-1 for shipment stops)
    vehicle_idx: int = -1
    
    # Pre-computed load deltas (for capacity constraints)
    # PICKUP: +weight/+volume, DELIVERY: -weight/-volume, DEPOT: 0
    weight_delta: int = 0
    volume_delta: int = 0
    
    @property
    def is_depot(self) -> bool:
        return self.stop_type in (StopType.DEPOT_START, StopType.DEPOT_END)
    
    @property
    def is_pickup(self) -> bool:
        return self.stop_type == StopType.PICKUP
    
    @property
    def is_delivery(self) -> bool:
        return self.stop_type == StopType.DELIVERY
