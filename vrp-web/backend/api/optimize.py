"""
VRP Optimization Endpoint

Converts API request to VRP domain ontology and runs OR-Tools solver.
"""
from fastapi import APIRouter, HTTPException
import sys
import os

# Add parent path to import vrp_solver
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from schemas.models import (
    OptimizeRequest, OptimizeResponse, 
    VehicleRoute, RouteStop, CostBreakdown
)

router = APIRouter(prefix="/api/optimize", tags=["optimize"])


def convert_request_to_vrp_data(request: OptimizeRequest):
    """Convert API request to VRPData domain object."""
    from vrp_solver.domain import (
        VRPData, Location, SiteProfile,
        Vehicle as DomainVehicle, VehicleProfile, VehicleCapacity, VehicleCostProfile,
        Shipment as DomainShipment, Cargo as DomainCargo,
        LaborPolicy, WorkShift, BreakRule, LaborCost,
        PenaltyConfig as DomainPenaltyConfig, OperationalCost,
        Stop, StopType
    )
    from vrp_solver.domain.shipment import TimeWindow as DomainTimeWindow
    
    # Build site_id -> index mapping
    site_id_to_idx = {site.id: i for i, site in enumerate(request.sites)}
    
    # Locations
    locations = []
    for i, site in enumerate(request.sites):
        loc = Location(
            id=i,
            name=site.name or site.id,
            service_duration=site.service_duration,
            zone_id=site.zone_id,
            profile=SiteProfile(),
            x=site.coords.lng,
            y=site.coords.lat
        )
        locations.append(loc)
    
    # Vehicles
    vehicles = []
    for i, veh in enumerate(request.vehicles):
        start_idx = site_id_to_idx.get(veh.start_site_id, 0)
        end_idx = site_id_to_idx.get(veh.end_site_id, 0)
        
        domain_veh = DomainVehicle(
            id=i,
            name=veh.name or veh.id,
            start_loc=start_idx,
            end_loc=end_idx,
            profile=VehicleProfile(
                type_id=1,
                capacity=VehicleCapacity(
                    weight=veh.capacity.weight,
                    volume=veh.capacity.volume
                ),
                tags=veh.tags
            ),
            cost=VehicleCostProfile(
                fixed=veh.cost.fixed,
                per_km=veh.cost.per_km,
                per_minute=veh.cost.per_minute,
                per_kg_km=1,
                per_wait_minute=5
            ),
            labor=LaborPolicy(
                shift=WorkShift(
                    start_time=veh.shift.start_time,
                    max_duration=veh.shift.max_duration,
                    standard_duration=veh.shift.standard_duration
                ),
                break_rule=BreakRule(
                    interval_minutes=veh.break_rule.interval_minutes,
                    duration_minutes=veh.break_rule.duration_minutes
                ),
                cost=LaborCost(regular_rate=veh.cost.per_minute, overtime_multiplier=1.5)
            )
        )
        vehicles.append(domain_veh)
    
    # Matrices (needed for Time Paradox safety check)
    travel_time = request.durations
    travel_dist = [[d // 1000 for d in row] for row in request.distances]  # m -> km
    setup_time = [[0] * len(locations) for _ in range(len(locations))]
    
    # Shipments (with Time Paradox safety logic)
    shipments = []
    for i, ship in enumerate(request.shipments):
        pickup_idx = site_id_to_idx.get(ship.pickup_site_id)
        delivery_idx = site_id_to_idx.get(ship.delivery_site_id)
        
        if pickup_idx is None or delivery_idx is None:
            raise HTTPException(status_code=400, detail=f"Invalid site reference in shipment {ship.id}")
        
        # Get time windows
        p_start = ship.pickup_window.start
        p_end = ship.pickup_window.end
        d_start = ship.delivery_window.start
        d_end = ship.delivery_window.end
        
        # [Safety Logic] Fix Time Paradox
        min_travel = travel_time[pickup_idx][delivery_idx] if travel_time else 20
        service_time = locations[pickup_idx].service_duration
        min_delivery_start = p_start + service_time + min_travel
        
        if d_end < min_delivery_start:
            d_start = max(d_start, min_delivery_start)
            d_end = d_start + 100
        
        domain_ship = DomainShipment(
            id=i,
            name=ship.name or ship.id,
            pickup_id=pickup_idx,
            delivery_id=delivery_idx,
            cargo=DomainCargo(
                weight=ship.cargo.weight,
                volume=ship.cargo.volume
            ),
            pickup_window=DomainTimeWindow(start=p_start, end=p_end),
            delivery_window=DomainTimeWindow(start=d_start, end=d_end),
            required_tags=ship.required_tags,
            priority=ship.priority,
            unserved_penalty=request.penalties.unserved
        )
        shipments.append(domain_ship)
    
    # Build Stops (Stop-based architecture)
    stops = []
    stop_id = 0
    
    # Start depots (one per vehicle)
    for v_idx, veh in enumerate(vehicles):
        stops.append(Stop(
            id=stop_id,
            stop_type=StopType.DEPOT_START,
            location_idx=veh.start_loc,
            vehicle_idx=v_idx,
            shipment_idx=-1,
            weight_delta=0,
            volume_delta=0
        ))
        stop_id += 1
    
    # Shipment stops (pickup + delivery)
    for s_idx, ship in enumerate(shipments):
        stops.append(Stop(
            id=stop_id,
            stop_type=StopType.PICKUP,
            location_idx=ship.pickup_id,
            shipment_idx=s_idx,
            vehicle_idx=-1,
            weight_delta=+ship.cargo.weight,
            volume_delta=+ship.cargo.volume
        ))
        stop_id += 1
        
        stops.append(Stop(
            id=stop_id,
            stop_type=StopType.DELIVERY,
            location_idx=ship.delivery_id,
            shipment_idx=s_idx,
            vehicle_idx=-1,
            weight_delta=-ship.cargo.weight,
            volume_delta=-ship.cargo.volume
        ))
        stop_id += 1
    
    # End depots (one per vehicle)
    for v_idx, veh in enumerate(vehicles):
        stops.append(Stop(
            id=stop_id,
            stop_type=StopType.DEPOT_END,
            location_idx=veh.end_loc,
            vehicle_idx=v_idx,
            shipment_idx=-1,
            weight_delta=0,
            volume_delta=0
        ))
        stop_id += 1
    
    penalties = DomainPenaltyConfig(
        unserved=request.penalties.unserved,
        late_delivery=request.penalties.late_delivery,
        zone_crossing=request.penalties.zone_crossing
    )
    
    operations = OperationalCost(depot_service_time=30, min_intra_transit=5)
    
    return VRPData(
        locations=locations,
        vehicles=vehicles,
        shipments=shipments,
        stops=stops,
        travel_time_matrix=travel_time,
        travel_dist_matrix=travel_dist,
        setup_time_matrix=setup_time,
        penalties=penalties,
        operations=operations
    ), site_id_to_idx


@router.post("", response_model=OptimizeResponse)
async def optimize(request: OptimizeRequest):
    """Run VRP optimization."""
    from vrp_solver.config import VRPConfig
    from vrp_solver.ortools_solver.wrapper import VRPSolver
    from vrp_solver.ortools_solver.constraints.routing import RoutingConstraints
    from vrp_solver.ortools_solver.constraints.time import TimeConstraints
    from vrp_solver.ortools_solver.constraints.capacity import CapacityConstraints
    from vrp_solver.ortools_solver.constraints.flow import FlowConstraints
    from vrp_solver.ortools_solver.constraints.lifo import LifoConstraints
    from vrp_solver.ortools_solver.constraints.objectives import ObjectiveConstraints
    from ortools.sat.python import cp_model
    
    # Convert request to domain
    vrp_data, site_id_map = convert_request_to_vrp_data(request)
    idx_to_site_id = {v: k for k, v in site_id_map.items()}
    
    # Config
    # Config
    if request.config:
        # Use provided config
        config = VRPConfig()
        config.capacity_scale_factor = request.config.capacity_scale_factor
        
        config.standard_work_time = request.config.standard_work_time
        config.max_work_time = request.config.max_work_time
        config.overtime_multiplier = request.config.overtime_multiplier
        config.break_interval = request.config.break_interval
        config.break_duration = request.config.break_duration
        
        config.depot_min_service_time = request.config.depot_min_service_time
        config.min_intra_transit = request.config.min_intra_transit
        
        config.cost_per_kg_km = request.config.cost_per_kg_km
        config.cost_per_wait_min = request.config.cost_per_wait_min
        
        config.unserved_penalty = request.config.unserved_penalty
        config.late_penalty = request.config.late_penalty
        config.zone_penalty = request.config.zone_penalty
        
        config.max_solver_time = request.config.max_solver_time
        config.num_solver_workers = request.config.num_solver_workers
    else:
        # Fallback to defaults + top-level legacy overrides
        config = VRPConfig()
        config.max_solver_time = request.max_solver_time
        # Legacy penalties override if needed, but we'll assume new frontend uses config

    
    # Create solver
    solver = VRPSolver(vrp_data, config)
    solver.create_variables()
    
    # Apply constraints
    RoutingConstraints.apply(solver)
    TimeConstraints.apply(solver)
    CapacityConstraints.apply(solver)
    FlowConstraints.apply(solver)
    LifoConstraints.apply(solver)
    ObjectiveConstraints.apply(solver)
    
    # Solve
    cp_solver, status = solver.solve()
    
    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return OptimizeResponse(
            status="infeasible",
            routes=[],
            costs=CostBreakdown(
                fixed=0, distance=0, labor=0, zone_penalty=0,
                rehandling=0, waiting=0, late_penalty=0, unserved_penalty=0, total=0
            ),
            unserved_shipments=[s.id for s in request.shipments]
        )
    
    # Extract results (Stop-based)
    cars = solver.variables
    routes = []
    
    for v in range(solver.num_vehicles):
        if not cp_solver.Value(cars['is_used'][v]):
            continue
        
        stops = []
        
        for s in range(solver.max_steps):
            is_d = cp_solver.Value(cars['is_done'][v, s])
            prev_d = cp_solver.Value(cars['is_done'][v, s-1]) if s > 0 else False
            
            if not is_d or (is_d and not prev_d):
                stop_idx = cp_solver.Value(cars['route'][v, s])
                stop = vrp_data.stops[stop_idx]
                loc_idx = stop.location_idx
                site_id = idx_to_site_id.get(loc_idx, f"site_{loc_idx}")
                
                route_stop = RouteStop(
                    site_id=site_id,
                    arrival_time=cp_solver.Value(cars['arrival_time'][v, s]),
                    load_weight=cp_solver.Value(cars['load_w'][v, s]) / config.capacity_scale_factor,
                    load_volume=cp_solver.Value(cars['load_v'][v, s]) / config.capacity_scale_factor,
                    is_late=bool(cp_solver.Value(cars['debug_is_late'].get((v, s), 0))),
                    stop_type=stop.stop_type.value,
                    shipment_id=request.shipments[stop.shipment_idx].id if stop.shipment_idx >= 0 else None
                )
                stops.append(route_stop)
        
        veh_route = VehicleRoute(
            vehicle_id=request.vehicles[v].id,
            stops=stops,
            total_distance=0,
            total_time=stops[-1].arrival_time if stops else 0
        )
        routes.append(veh_route)
    
    # Costs
    costs = CostBreakdown(
        fixed=cp_solver.Value(cars['c_fixed']),
        distance=cp_solver.Value(cars['c_dist']),
        labor=cp_solver.Value(cars['c_time']),
        zone_penalty=cp_solver.Value(cars['c_zone']),
        rehandling=cp_solver.Value(cars.get('c_rehandling', 0)),
        waiting=cp_solver.Value(cars['c_waiting']),
        late_penalty=cp_solver.Value(cars['c_late']),
        unserved_penalty=cp_solver.Value(cars['c_penalty']),
        total=cp_solver.Value(cars['total_cost'])
    )
    
    # Unserved (now uses shipment index, not location index!)
    unserved = []
    for i, ship in enumerate(request.shipments):
        if not cp_solver.Value(cars['is_served'][i]):
            unserved.append(ship.id)
    
    return OptimizeResponse(
        status="optimal" if status == cp_model.OPTIMAL else "feasible",
        routes=routes,
        costs=costs,
        unserved_shipments=unserved
    )
