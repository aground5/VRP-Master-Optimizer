from dataclasses import dataclass, field
from typing import Optional
from enum import Enum

class StopType(Enum):
    DEPOT_START = "depot_start"
    DEPOT_END = "depot_end"
    PICKUP = "pickup"
    DELIVERY = "delivery"

@dataclass
class Stop:
    """
    Resolved Node in a Route.
    Contains optimization RESULTS (Timestamps, Metrics).
    """
    id: int
    stop_type: StopType
    location_idx: int
    shipment_idx: int = -1
    vehicle_idx: int = -1

    # --- Results (Planned) ---
    arrival_time: int = 0        # ToA (Time of Arrival)
    departure_time: int = 0      # ToD (Time of Departure)
    service_time: int = 0        # Duration of service at this stop
    waiting_time: int = 0        # Wait time if arrived early
    
    # --- Cumulative Metrics (Validation) ---
    cum_dist: float = 0.0        # Cumulative distance from start
    cum_weight: float = 0.0      # Current load (weight) after this stop
    cum_volume: float = 0.0      # Current load (volume) after this stop
    
    # --- Violations (Soft Constraints) ---
    late_arrival_min: int = 0    # Minutes late beyond time window

    @property
    def total_duration(self) -> int:
        return self.departure_time - self.arrival_time

    @property
    def is_depot(self) -> bool:
        return self.stop_type in (StopType.DEPOT_START, StopType.DEPOT_END)
    
    @property
    def is_pickup(self) -> bool:
        return self.stop_type == StopType.PICKUP
    
    @property
    def is_delivery(self) -> bool:
        return self.stop_type == StopType.DELIVERY
