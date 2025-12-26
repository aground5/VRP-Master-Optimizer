"""
Data Loader.

Converts raw input data into Domain Ontology objects.
"""
from typing import List
from vrp_solver.domain import (
    VRPData, Location, SiteProfile,
    Vehicle, VehicleProfile, VehicleCapacity, VehicleCostProfile,
    Shipment, Cargo, TimeWindow,
    LaborPolicy, WorkShift, BreakRule, LaborCost,
    PenaltyConfig, OperationalCost,
    Stop, StopType
)
from vrp_solver.config import VRPConfig


def build_stops(vehicles: List[Vehicle], shipments: List[Shipment]) -> List[Stop]:
    """
    Build the Stop list from vehicles and shipments.
    
    Stop structure:
      - First: Start depot for each vehicle
      - Middle: Pickup & Delivery stops for each shipment
      - Last: End depot for each vehicle
    
    This allows multiple stops to reference the same physical location.
    """
    stops = []
    stop_id = 0
    
    # --- 1. Start Depots (one per vehicle) ---
    for v_idx, veh in enumerate(vehicles):
        stops.append(Stop(
            id=stop_id,
            stop_type=StopType.DEPOT_START,
            location_idx=veh.start_loc,
            vehicle_idx=v_idx,
            shipment_idx=-1
        ))
        stop_id += 1
    
    # --- 2. Shipment Stops (pickup + delivery for each) ---
    for s_idx, ship in enumerate(shipments):
        # Pickup stop
        stops.append(Stop(
            id=stop_id,
            stop_type=StopType.PICKUP,
            location_idx=ship.pickup_id,
            shipment_idx=s_idx,
            vehicle_idx=-1
        ))
        stop_id += 1
        
        # Delivery stop
        stops.append(Stop(
            id=stop_id,
            stop_type=StopType.DELIVERY,
            location_idx=ship.delivery_id,
            shipment_idx=s_idx,
            vehicle_idx=-1
        ))
        stop_id += 1
    
    # --- 3. End Depots (one per vehicle) ---
    for v_idx, veh in enumerate(vehicles):
        stops.append(Stop(
            id=stop_id,
            stop_type=StopType.DEPOT_END,
            location_idx=veh.end_loc,
            vehicle_idx=v_idx,
            shipment_idx=-1
        ))
        stop_id += 1
    
    return stops


def load_dummy_data(config: VRPConfig) -> VRPData:
    """
    Loads the hardcoded 17-node example data,
    transforming it into the Domain Ontology.
    """
    scale = config.scale_factor
    
    # --- 1. Raw Data (Same as original) ---
    num_vehicles = 4
    num_locations = 17 
    
    # Raw Time Matrix (0-16)
    raw_time_matrix = [
        [0, 6, 9, 8, 7, 3, 6, 2, 3, 2, 6, 6, 4, 4, 5, 9, 7],
        [6, 0, 8, 3, 2, 6, 8, 4, 8, 8, 13, 7, 5, 8, 12, 10, 14],
        [9, 8, 0, 11, 10, 6, 3, 9, 5, 8, 4, 15, 14, 13, 9, 18, 9],
        [8, 3, 11, 0, 1, 7, 10, 6, 10, 10, 14, 6, 7, 9, 14, 6, 16],
        [7, 2, 10, 1, 0, 6, 9, 4, 8, 9, 13, 4, 6, 8, 12, 8, 14],
        [3, 6, 6, 7, 6, 0, 2, 3, 2, 2, 7, 9, 7, 7, 6, 12, 8],
        [6, 8, 3, 10, 9, 2, 0, 6, 2, 5, 4, 12, 10, 10, 6, 15, 5],
        [2, 4, 9, 6, 4, 3, 6, 0, 4, 4, 8, 5, 4, 3, 7, 8, 10],
        [3, 8, 5, 10, 8, 2, 2, 4, 0, 3, 4, 9, 8, 7, 3, 13, 6],
        [2, 8, 8, 10, 9, 2, 5, 4, 3, 0, 4, 6, 5, 4, 3, 9, 5],
        [6, 13, 4, 14, 13, 7, 4, 8, 4, 4, 0, 10, 9, 8, 4, 13, 4],
        [6, 7, 15, 6, 4, 9, 12, 5, 9, 6, 10, 0, 1, 3, 7, 3, 10],
        [4, 5, 14, 7, 6, 7, 10, 4, 8, 5, 9, 1, 0, 2, 6, 4, 8],
        [4, 8, 13, 9, 8, 7, 10, 3, 7, 4, 8, 3, 2, 0, 4, 5, 6],
        [5, 12, 9, 14, 12, 6, 6, 7, 3, 3, 4, 7, 6, 4, 0, 9, 2],
        [9, 10, 18, 6, 8, 12, 15, 8, 13, 9, 13, 3, 4, 5, 9, 0, 9],
        [7, 14, 9, 16, 14, 8, 5, 10, 6, 5, 4, 10, 8, 6, 2, 9, 0],
    ]
    
    raw_windows = [
        (0, 100), (7, 12), (10, 15), (16, 18), (10, 13), (0, 5),
        (5, 10), (0, 4), (5, 10), (0, 3), (10, 16), (10, 15),
        (0, 5), (5, 10), (7, 8), (10, 15), (11, 15),
    ]

    # --- 2. Build Locations ---
    locations = []
    ready_time = [w[0] * scale for w in raw_windows]
    due_time   = [w[1] * scale for w in raw_windows]
    due_time[0] = 720  # Depot end shift
    
    service_duration = [10] * num_locations
    service_duration[0] = 0
    
    # Zones: 1-8: Zone 1, 9-16: Zone 2
    zones = [0] * num_locations
    for i in range(1, 9): zones[i] = 1
    for i in range(9, 17): zones[i] = 2
    
    for i in range(num_locations):
        loc = Location(
            id=i,
            name=f"Loc_{i}",
            service_duration=service_duration[i],
            zone_id=zones[i],
            profile=SiteProfile()
        )
        locations.append(loc)
        
    # --- 3. Build Vehicles ---
    cost_fixed = [500, 500, 5000, 5000] 
    cost_per_km = [10, 10, 10, 10]
    cost_per_min = [10, 10, 10, 10]
    
    vehicles = []
    for i in range(num_vehicles):
        veh = Vehicle(
            id=i,
            name=f"Truck_{i+1}",
            start_loc=0,
            end_loc=0,
            profile=VehicleProfile(
                type_id=1,
                capacity=VehicleCapacity(weight=50, volume=50),
                tags=[]  # No special tags for now
            ),
            cost=VehicleCostProfile(
                fixed=cost_fixed[i],
                per_km=cost_per_km[i],
                per_minute=cost_per_min[i],
                per_kg_km=config.cost_per_kg_km,
                per_wait_minute=config.cost_per_wait_min
            ),
            labor=LaborPolicy(
                shift=WorkShift(
                    start_time=0,
                    max_duration=config.max_work_time,
                    standard_duration=config.standard_work_time
                ),
                break_rule=BreakRule(
                    interval_minutes=config.break_interval,
                    duration_minutes=config.break_duration
                ),
                cost=LaborCost(
                    regular_rate=cost_per_min[i],
                    overtime_multiplier=config.overtime_multiplier
                )
            )
        )
        vehicles.append(veh)
        
    # --- 4. Build Shipments ---
    pair_defs = {
        1: (6, 10), 2: (10, 20), 4: (3, 5), 5: (9, 15),
        7: (8, 10), 15: (11, 20), 13: (12, 10), 16: (14, 15)
    }
    
    shipments = []
    pid_counter = 0
    for p, (d, w) in pair_defs.items():
        # Get time windows from raw data
        p_start = ready_time[p]
        p_end = due_time[p]
        d_start = ready_time[d]
        d_end = due_time[d]
        
        # [Safety Logic] Fix Time Paradox: Delivery must be reachable after Pickup
        # Min required: pickup_start + service(10) + travel_time
        min_travel = raw_time_matrix[p][d] * 5  # raw * 5 = actual travel time
        min_delivery_start = p_start + 10 + min_travel
        
        if d_end < min_delivery_start:
            # Delivery window ends before we can possibly arrive - fix it
            d_start = max(d_start, min_delivery_start)
            d_end = d_start + 100  # Give a wide window
        
        shipment = Shipment(
            id=pid_counter,
            name=f"Ship_{pid_counter}",
            pickup_id=p,
            delivery_id=d,
            cargo=Cargo(weight=w, volume=w),
            pickup_window=TimeWindow(start=p_start, end=p_end),
            delivery_window=TimeWindow(start=d_start, end=d_end),
            required_tags=[],
            priority=1,
            unserved_penalty=config.unserved_penalty
        )
        shipments.append(shipment)
        pid_counter += 1
    
    # --- 5. Build Stops ---
    stops = build_stops(vehicles, shipments)
        
    # --- 6. Matrices ---
    calc_travel_time = [[t * 5 for t in row] for row in raw_time_matrix]
    calc_travel_dist = [[t * 5 for t in row] for row in raw_time_matrix]
    setup_time = [[0] * num_locations for _ in range(num_locations)]
    
    # --- 7. Global Policies ---
    penalties = PenaltyConfig(
        unserved=config.unserved_penalty,
        late_delivery=config.late_penalty,
        zone_crossing=config.zone_penalty
    )
    
    operations = OperationalCost(
        depot_service_time=config.depot_min_service_time,
        min_intra_transit=config.min_intra_transit
    )
    
    return VRPData(
        locations=locations,
        vehicles=vehicles,
        shipments=shipments,
        stops=stops,
        travel_time_matrix=calc_travel_time,
        travel_dist_matrix=calc_travel_dist,
        setup_time_matrix=setup_time,
        penalties=penalties,
        operations=operations
    )
