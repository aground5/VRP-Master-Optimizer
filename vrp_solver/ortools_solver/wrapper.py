"""
VRP Solver Wrapper.

Creates CP-SAT model variables for Stop-based VRP.
"""
from ortools.sat.python import cp_model
from typing import Dict, Any, List
from vrp_solver.domain import VRPData, StopType
from vrp_solver.config import VRPConfig


class VRPSolver:
    def __init__(self, data: VRPData, config: VRPConfig):
        self.data = data
        self.config = config
        self.model = cp_model.CpModel()
        self.variables: Dict[str, Any] = {}
        
        # Dimensions
        self.num_vehicles = len(data.vehicles)
        self.num_locations = len(data.locations)
        self.num_stops = data.num_stops
        self.num_shipments = len(data.shipments)
        
        # Max steps: enough for all stops + buffer (no artificial limit)
        self.max_steps = (2 * self.num_shipments) + (2 * self.num_vehicles) + 5
        
        # Pre-compute lookup arrays for Element constraints
        self._build_lookup_arrays()
    
    def _build_lookup_arrays(self):
        """Build arrays for efficient Element constraint lookups."""
        data = self.data
        
        # stop_id -> location_idx
        self.stop_to_location = [s.location_idx for s in data.stops]
        
        # stop_id -> weight_delta
        # Apply scaling for float support (e.g. 0.1 -> 10)
        scale = self.config.capacity_scale_factor
        self.stop_weight_delta = [int(s.weight_delta * scale) for s in data.stops]
        
        # stop_id -> volume_delta
        self.stop_volume_delta = [int(s.volume_delta * scale) for s in data.stops]
        
        # stop_id -> service_duration (from location)
        self.stop_service_duration = [
            data.locations[s.location_idx].service_duration for s in data.stops
        ]
        
        # stop_id -> zone_id (from location)
        self.stop_zone = [
            data.locations[s.location_idx].zone_id for s in data.stops
        ]
        
        # Identify depot stops per vehicle
        self.vehicle_start_stop = {}
        self.vehicle_end_stop = {}
        for stop in data.stops:
            if stop.stop_type == StopType.DEPOT_START:
                self.vehicle_start_stop[stop.vehicle_idx] = stop.id
            elif stop.stop_type == StopType.DEPOT_END:
                self.vehicle_end_stop[stop.vehicle_idx] = stop.id
        
        # Identify shipment stops
        self.shipment_pickup_stop = {}
        self.shipment_delivery_stop = {}
        for stop in data.stops:
            if stop.stop_type == StopType.PICKUP:
                self.shipment_pickup_stop[stop.shipment_idx] = stop.id
            elif stop.stop_type == StopType.DELIVERY:
                self.shipment_delivery_stop[stop.shipment_idx] = stop.id

    def create_variables(self):
        """Initializes all CP variables for Stop-based routing."""
        m = self.model
        num_v = self.num_vehicles
        num_stops = self.num_stops
        num_ships = self.num_shipments
        max_s = self.max_steps
        
        # ======================
        # 1. Routing Variables (Stop-based)
        # ======================
        route = {}          # route[v, s] = Stop index at step s for vehicle v
        arrival_time = {}   # arrival_time[v, s] = time when vehicle arrives at step s
        load_w = {}         # load_w[v, s] = weight load after step s
        load_v = {}         # load_v[v, s] = volume load after step s
        is_done = {}        # is_done[v, s] = True if route is finished at step s
        
        for v in range(num_v):
            for s in range(max_s):
                # Domain: any stop index (0 to num_stops-1)
                route[v, s] = m.NewIntVar(0, num_stops - 1, f'route_{v}_{s}')
                arrival_time[v, s] = m.NewIntVar(0, 10000, f'arr_{v}_{s}')
                load_w[v, s] = m.NewIntVar(0, 2000, f'lw_{v}_{s}')
                load_v[v, s] = m.NewIntVar(0, 2000, f'lv_{v}_{s}')
                is_done[v, s] = m.NewBoolVar(f'done_{v}_{s}')
        
        self.variables['route'] = route
        self.variables['arrival_time'] = arrival_time
        self.variables['load_w'] = load_w
        self.variables['load_v'] = load_v
        self.variables['is_done'] = is_done
        
        # ======================
        # 2. Vehicle Usage
        # ======================
        is_used = {}
        for v in range(num_v):
            is_used[v] = m.NewBoolVar(f'used_{v}')
        self.variables['is_used'] = is_used
        
        # ======================
        # 3. Stop Visit State (per Stop, not per Location!)
        # ======================
        visit_step = {}     # visit_step[stop_id] = step when visited (0 if not)
        visit_vehicle = {}  # visit_vehicle[stop_id] = vehicle (1-indexed, 0 if not)
        is_stop_active = {} # is_stop_active[stop_id] = True if this stop is visited
        
        for stop_id in range(num_stops):
            visit_step[stop_id] = m.NewIntVar(0, max_s, f'vstep_{stop_id}')
            visit_vehicle[stop_id] = m.NewIntVar(0, num_v, f'vveh_{stop_id}')
            is_stop_active[stop_id] = m.NewBoolVar(f'active_{stop_id}')
        
        self.variables['visit_step'] = visit_step
        self.variables['visit_vehicle'] = visit_vehicle
        self.variables['is_stop_active'] = is_stop_active
        
        # ======================
        # 4. Shipment Service State (per Shipment)
        # ======================
        is_served = {}  # is_served[ship_idx] = True if shipment is served
        for ship_idx in range(num_ships):
            is_served[ship_idx] = m.NewBoolVar(f'served_{ship_idx}')
        self.variables['is_served'] = is_served
        
        # ======================
        # 5. Helper variables for location lookup (Element constraints)
        # ======================
        # These will store the location index at each route step
        route_location = {}
        for v in range(num_v):
            for s in range(max_s):
                route_location[v, s] = m.NewIntVar(0, self.num_locations - 1, f'rloc_{v}_{s}')
                # Link via Element constraint
                m.AddElement(route[v, s], self.stop_to_location, route_location[v, s])
        self.variables['route_location'] = route_location
        
        # ======================
        # 6. Objective Components
        # ======================
        self.variables['cost_terms'] = []
        
        return self.variables

    def solve(self):
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = self.config.max_solver_time
        status = solver.Solve(self.model)
        return solver, status
