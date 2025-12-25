"""
Shipment & Cargo Domain Models.

Encapsulates transport requests, cargo properties, and compatibility requirements.
"""
from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class Cargo:
    """Physical properties of the cargo."""
    weight: int = 0              # Weight in kg
    volume: int = 0              # Volume in m³ or units
    pallets: int = 0             # Optional pallet count
    temp_class: Optional[str] = None  # e.g., "frozen", "chilled", "ambient"
    
@dataclass
class TimeWindow:
    """A time window constraint."""
    start: int = 0               # Earliest time (ready time)
    end: int = 10000             # Latest time (due time)
    
@dataclass
class Shipment:
    """A transport request (Pickup & Delivery pair)."""
    id: int
    name: str = ""
    
    # Locations
    pickup_id: int = 0
    delivery_id: int = 0
    
    # Cargo
    cargo: Cargo = field(default_factory=Cargo)
    
    # Time Windows (optional, can override location windows)
    pickup_window: Optional[TimeWindow] = None
    delivery_window: Optional[TimeWindow] = None
    
    # Compatibility Requirements
    required_tags: List[str] = field(default_factory=list)  # e.g., ["frozen", "lift_gate"]
    
    # Priority/SLA
    priority: int = 1            # 1 = normal, higher = more urgent
    unserved_penalty: int = 500000  # Custom penalty for this shipment
    
    # Shortcut properties for backward compatibility
    @property
    def weight(self) -> int:
        return self.cargo.weight
    
    @property
    def volume(self) -> int:
        return self.cargo.volume
