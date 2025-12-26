from dataclasses import dataclass, field
from typing import List
from .stop import Stop

@dataclass
class Route:
    """
    A planned sequence of stops for a single vehicle.
    Output of the VRP Solver.
    """
    vehicle_id: int
    stops: List[Stop] = field(default_factory=list)
    
    # Route Summary
    total_cost: float = 0.0
    total_distance: float = 0.0
    total_time: int = 0
    total_waiting: int = 0
    
    # Validation
    is_feasible: bool = True
    violation_msg: str = ""
