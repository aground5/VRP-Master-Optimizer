"""
Time Constraints for Stop-based VRP.

Handles:
- Travel time between stops (via location lookup)
- Shipment-level time windows (pickup/delivery)
- Service duration at stops
- Waiting time handling
- Work shift limits
"""
from vrp_solver.ortools_solver.wrapper import VRPSolver
from vrp_solver.domain import StopType


class TimeConstraints:
    @staticmethod
    def apply(solver: VRPSolver):
        m = solver.model
        data = solver.data
        cars = solver.variables
        
        num_v = solver.num_vehicles
        max_s = solver.max_steps
        num_loc = solver.num_locations
        
        route = cars['route']
        route_location = cars['route_location']  # Pre-linked via Element in wrapper
        arrival_time = cars['arrival_time']
        is_done = cars['is_done']
        is_served = cars['is_served']
        
        # Data flattening for AddElement
        flat_time = [t for row in data.travel_time_matrix for t in row]
        flat_setup = [t for row in data.setup_time_matrix for t in row]
        serv_dur = solver.stop_service_duration  # Per-stop service duration
        
        cars['late_flags'] = []
        cars['debug_due_dates'] = {}
        cars['debug_is_late'] = {}
        
        # Global operational costs
        depot_min_service = data.operations.depot_service_time
        min_intra = data.operations.min_intra_transit
        
        for v in range(num_v):
            veh = data.vehicles[v]
            labor = veh.labor
            break_rule = labor.break_rule
            shift = labor.shift
            
            # Initial Arrival at shift start
            m.Add(arrival_time[v, 0] == shift.start_time)
            
            for s in range(max_s - 1):
                # Use route_location (already linked via Element in wrapper)
                curr_loc = route_location[v, s]
                next_loc = route_location[v, s+1]
                
                # Index for flat matrix: curr_loc * num_loc + next_loc
                idx = m.NewIntVar(0, num_loc**2-1, f'idx_{v}_{s}')
                m.Add(idx == curr_loc * num_loc + next_loc)
                
                # Drive time
                drive_val = m.NewIntVar(0, 1000, f'dt_{v}_{s}')
                m.AddElement(idx, flat_time, drive_val)
                
                # Setup time
                setup_val = m.NewIntVar(0, 1000, f'st_{v}_{s}')
                m.AddElement(idx, flat_setup, setup_val)
                
                # Service duration (from stop lookup array)
                curr_stop = route[v, s]
                service_val = m.NewIntVar(0, 1000, f'sert_{v}_{s}')
                m.AddElement(curr_stop, serv_dur, service_val)
                
                # --- Anti-teleport logic ---
                anti_teleport_t = m.NewIntVar(0, 100, f'att_{v}_{s}')
                
                # Check if transitioning from depot
                start_depot_stop = solver.vehicle_start_stop[v]
                from_depot = m.NewBoolVar(f'fd_{v}_{s}')
                m.Add(route[v, s] == start_depot_stop).OnlyEnforceIf(from_depot)
                m.Add(route[v, s] != start_depot_stop).OnlyEnforceIf(from_depot.Not())
                
                # Check if staying at same location
                same_loc = m.NewBoolVar(f'sl_{v}_{s}')
                m.Add(curr_loc == next_loc).OnlyEnforceIf(same_loc)
                m.Add(curr_loc != next_loc).OnlyEnforceIf(same_loc.Not())
                
                stay_spot = m.NewBoolVar(f'ss_{v}_{s}')
                m.AddBoolAnd([from_depot.Not(), same_loc]).OnlyEnforceIf(stay_spot)
                m.AddBoolOr([from_depot, same_loc.Not()]).OnlyEnforceIf(stay_spot.Not())
                
                m.Add(anti_teleport_t == depot_min_service).OnlyEnforceIf(from_depot)
                m.Add(anti_teleport_t == min_intra).OnlyEnforceIf(stay_spot)
                m.Add(anti_teleport_t == 0).OnlyEnforceIf([from_depot.Not(), stay_spot.Not()])
                
                # --- Rest (Break) ---
                rest_t = m.NewIntVar(0, break_rule.duration_minutes, f'rt_{v}_{s}')
                long_drive = m.NewBoolVar(f'ld_{v}_{s}')
                m.Add(drive_val > break_rule.interval_minutes).OnlyEnforceIf(long_drive)
                m.Add(drive_val <= break_rule.interval_minutes).OnlyEnforceIf(long_drive.Not())
                m.Add(rest_t == break_rule.duration_minutes).OnlyEnforceIf(long_drive)
                m.Add(rest_t == 0).OnlyEnforceIf(long_drive.Not())
                
                # --- Calculate arrival time ---
                calc_arrival = m.NewIntVar(0, 10000, f'ca_{v}_{s}')
                m.Add(calc_arrival == arrival_time[v, s] + service_val + drive_val + rest_t + setup_val + anti_teleport_t)
                
                # No waiting logic here - handled via time window constraints below
                # FIX: Only freeze time if we were ALREADY done at step s.
                # If s was active (False), but s+1 is done (True) -> Transition -> Travel time applies.
                m.Add(arrival_time[v, s+1] == arrival_time[v, s]).OnlyEnforceIf(is_done[v, s])
                # CRITICAL: Use >= to allow waiting (vehicle can arrive early and wait)
                # FIX: Apply travel constraint whenever we are moving FROM a valid step (is_done[v, s] is False)
                # Even if we move TO the end depot (is_done[v, s+1] becomes True), we must travel there.
                m.Add(arrival_time[v, s+1] >= calc_arrival).OnlyEnforceIf(is_done[v, s].Not())
            
            # --- Work shift limit ---
            for s in range(max_s):
                m.Add(arrival_time[v, s] - shift.start_time <= shift.max_duration)
        
        # ==============================================
        # Time Window Constraints (Shipment-based)
        # ==============================================
        visit_step = cars['visit_step']
        
        for ship_idx, ship in enumerate(data.shipments):
            p_stop_id = solver.shipment_pickup_stop[ship_idx]
            d_stop_id = solver.shipment_delivery_stop[ship_idx]
            
            # Get time windows from Shipment (Source of Truth!)
            if ship.pickup_window:
                p_tw_start = ship.pickup_window.start
                p_tw_end = ship.pickup_window.end
            else:
                # Fallback to location window
                p_loc = data.locations[data.stops[p_stop_id].location_idx]
                p_tw_start = p_loc.start_window
                p_tw_end = p_loc.end_window
            
            if ship.delivery_window:
                d_tw_start = ship.delivery_window.start
                d_tw_end = ship.delivery_window.end
            else:
                d_loc = data.locations[data.stops[d_stop_id].location_idx]
                d_tw_start = d_loc.start_window
                d_tw_end = d_loc.end_window
            
            # For each vehicle×step, if this is the pickup stop, enforce TW
            for v in range(num_v):
                for s in range(max_s):
                    # Pickup time window
                    is_pickup_visit = m.NewBoolVar(f'ipv_{ship_idx}_{v}_{s}')
                    m.Add(route[v, s] == p_stop_id).OnlyEnforceIf(is_pickup_visit)
                    m.Add(route[v, s] != p_stop_id).OnlyEnforceIf(is_pickup_visit.Not())
                    
                    valid_pickup = m.NewBoolVar(f'vp_{ship_idx}_{v}_{s}')
                    m.AddBoolAnd([is_pickup_visit, is_done[v, s].Not()]).OnlyEnforceIf(valid_pickup)
                    m.AddBoolOr([is_pickup_visit.Not(), is_done[v, s]]).OnlyEnforceIf(valid_pickup.Not())
                    
                    # arrival >= pickup_tw_start (wait if early)
                    # arrival <= pickup_tw_end (hard constraint)
                    m.Add(arrival_time[v, s] >= p_tw_start).OnlyEnforceIf(valid_pickup)
                    m.Add(arrival_time[v, s] <= p_tw_end).OnlyEnforceIf(valid_pickup)
                    
                    # Delivery time window
                    is_delivery_visit = m.NewBoolVar(f'idv_{ship_idx}_{v}_{s}')
                    m.Add(route[v, s] == d_stop_id).OnlyEnforceIf(is_delivery_visit)
                    m.Add(route[v, s] != d_stop_id).OnlyEnforceIf(is_delivery_visit.Not())
                    
                    valid_delivery = m.NewBoolVar(f'vd_{ship_idx}_{v}_{s}')
                    m.AddBoolAnd([is_delivery_visit, is_done[v, s].Not()]).OnlyEnforceIf(valid_delivery)
                    m.AddBoolOr([is_delivery_visit.Not(), is_done[v, s]]).OnlyEnforceIf(valid_delivery.Not())
                    
                    m.Add(arrival_time[v, s] >= d_tw_start).OnlyEnforceIf(valid_delivery)
                    m.Add(arrival_time[v, s] <= d_tw_end).OnlyEnforceIf(valid_delivery)
        
        # Late penalty tracking (simplified for now)
        for v in range(num_v):
            for s in range(max_s):
                step_late = m.NewBoolVar(f'late_{v}_{s}')
                m.Add(step_late == 0)  # Placeholder - all within TW or infeasible
                cars['late_flags'].append(step_late)
                cars['debug_is_late'][(v, s)] = step_late
