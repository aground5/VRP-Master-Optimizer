from dataclasses import dataclass

@dataclass
class VRPConfig:
    """Central configuration for VRP solver."""
    
    # Scale
    scale_factor: int = 10
    capacity_scale_factor: int = 100  # For handling float weights/volumes (e.g. 0.01 precision)
    
    # Labor/Operations
    standard_work_time: int = 480    # 8 hours
    max_work_time: int = 720         # 12 hours
    break_interval: int = 240        # Break after 4 hours
    break_duration: int = 30         # 30 min break
    overtime_multiplier: float = 1.5
    
    # Anti-Cheat Defenses
    depot_min_service_time: int = 30 # Min time at depot
    min_intra_transit: int = 5       # Min transit between same-site stops
    
    # Costs
    cost_per_kg_km: int = 1
    cost_per_wait_min: int = 5       # Idling penalty
    
    # Penalties
    unserved_penalty: int = 500000
    late_penalty: int = 50000
    zone_penalty: int = 2000

    # Solver
    max_solver_time: float = 30.0
    num_solver_workers: int = 8
