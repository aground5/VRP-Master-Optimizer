"""
Routing Constraints for Stop-based VRP.

Handles:
- Route structure (start depot → stops → end depot)
- Stop visit tracking
- Vehicle usage detection
"""
from vrp_solver.ortools_solver.wrapper import VRPSolver
from vrp_solver.domain import StopType


class RoutingConstraints:
    @staticmethod
    def apply(solver: VRPSolver):
        m = solver.model
        data = solver.data
        cars = solver.variables
        
        num_v = solver.num_vehicles
        max_s = solver.max_steps
        num_stops = solver.num_stops
        
        route = cars['route']
        is_done = cars['is_done']
        visit_step = cars['visit_step']
        visit_vehicle = cars['visit_vehicle']
        is_stop_active = cars['is_stop_active']
        is_served = cars['is_served']
        
        # ====================================================
        # 1. Route Structure: Start/End with correct depots
        # ====================================================
        for v in range(num_v):
            start_depot_stop = solver.vehicle_start_stop[v]
            end_depot_stop = solver.vehicle_end_stop[v]
            
            # Step 0: Must be this vehicle's start depot
            m.Add(route[v, 0] == start_depot_stop)
            m.Add(is_done[v, 0] == False)
            
            # Forbid re-visiting Start Depot at any later step
            for s in range(1, max_s):
                m.Add(route[v, s] != start_depot_stop)
            
            # Route continuity: once done, stay at end depot
            for s in range(max_s - 1):
                # If done[s], then done[s+1]
                m.AddImplication(is_done[v, s], is_done[v, s+1])
                
                # If done[s], route must be at end depot
                m.Add(route[v, s] == end_depot_stop).OnlyEnforceIf(is_done[v, s])
                
                # [Optimization] Forbid self-loops (consecutive same stops) while active
                # This prevents "Waiting at Node" from appearing as separate steps in the output
                m.Add(route[v, s] != route[v, s+1]).OnlyEnforceIf(is_done[v, s+1].Not())
            
            # Last step must be done
            m.Add(is_done[v, max_s - 1] == True)
        
        # ====================================================
        # 2. End depot detection: done[s+1] when reaching end depot
        # ====================================================
        for v in range(num_v):
            end_depot_stop = solver.vehicle_end_stop[v]
            
            for s in range(max_s - 1):
                # Create indicator: is current step at end depot?
                at_end = m.NewBoolVar(f'at_end_{v}_{s}')
                m.Add(route[v, s] == end_depot_stop).OnlyEnforceIf(at_end)
                m.Add(route[v, s] != end_depot_stop).OnlyEnforceIf(at_end.Not())
                
                # If at end depot and NOT already done, become done
                m.AddImplication(at_end, is_done[v, s])
        
        # ====================================================
        # 3. Restrict which stops each vehicle can visit
        # ====================================================
        # Each vehicle can only visit:
        # - Its own start/end depots
        # - Any shipment stop (pickup/delivery)
        for v in range(num_v):
            other_depot_stops = []
            for v2 in range(num_v):
                if v2 != v:
                    other_depot_stops.append(solver.vehicle_start_stop[v2])
                    other_depot_stops.append(solver.vehicle_end_stop[v2])
            
            # Forbid visiting other vehicles' depots
            for s in range(max_s):
                for forbidden_stop in other_depot_stops:
                    m.Add(route[v, s] != forbidden_stop)
        
        # ====================================================
        # 4. Link Stop visits to route
        # ====================================================
        # For each shipment stop, track which vehicle visits it and when
        shipment_stops = data.shipment_stops  # excludes depots
        
        for stop in shipment_stops:
            stop_id = stop.id
            visits_bools = []
            
            for v in range(num_v):
                for s in range(max_s):
                    # Is route[v,s] == stop_id AND not done yet?
                    is_this_stop = m.NewBoolVar(f'is_stop_{v}_{s}_{stop_id}')
                    not_done = is_done[v, s].Not()
                    
                    m.Add(route[v, s] == stop_id).OnlyEnforceIf(is_this_stop)
                    m.Add(route[v, s] != stop_id).OnlyEnforceIf(is_this_stop.Not())
                    
                    # Track this as a valid visit
                    is_valid_visit = m.NewBoolVar(f'valid_{v}_{s}_{stop_id}')
                    m.AddBoolAnd([is_this_stop, not_done]).OnlyEnforceIf(is_valid_visit)
                    m.AddBoolOr([is_this_stop.Not(), not_done.Not()]).OnlyEnforceIf(is_valid_visit.Not())
                    
                    visits_bools.append(is_valid_visit)
                    
                    # If this is a valid visit, record step and vehicle
                    m.Add(visit_step[stop_id] == s).OnlyEnforceIf(is_valid_visit)
                    m.Add(visit_vehicle[stop_id] == v + 1).OnlyEnforceIf(is_valid_visit)
            
            # Each shipment stop is visited at most once
            m.Add(sum(visits_bools) <= 1)
            
            # is_stop_active[stop_id] = sum(visits_bools) == 1
            m.Add(sum(visits_bools) == 1).OnlyEnforceIf(is_stop_active[stop_id])
            m.Add(sum(visits_bools) == 0).OnlyEnforceIf(is_stop_active[stop_id].Not())
            
            # Default values when not visited
            m.Add(visit_step[stop_id] == 0).OnlyEnforceIf(is_stop_active[stop_id].Not())
            m.Add(visit_vehicle[stop_id] == 0).OnlyEnforceIf(is_stop_active[stop_id].Not())
        
        # ====================================================
        # 5. Link shipment service to stop activity
        # ====================================================
        # A shipment is served if BOTH pickup AND delivery are active
        for ship_idx in range(solver.num_shipments):
            p_stop = solver.shipment_pickup_stop[ship_idx]
            d_stop = solver.shipment_delivery_stop[ship_idx]
            
            # is_served[ship] == is_stop_active[pickup] AND is_stop_active[delivery]
            m.AddBoolAnd([is_stop_active[p_stop], is_stop_active[d_stop]]).OnlyEnforceIf(is_served[ship_idx])
            m.AddBoolOr([is_stop_active[p_stop].Not(), is_stop_active[d_stop].Not()]).OnlyEnforceIf(is_served[ship_idx].Not())
            
            # Sync: if pickup active, delivery must be active (and vice versa)
            m.Add(is_stop_active[p_stop] == is_stop_active[d_stop])
        
        # ====================================================
        # 6. Vehicle usage detection
        # ====================================================
        is_used = cars['is_used']
        for v in range(num_v):
            # Vehicle is used if it's NOT done at step 1
            # (meaning it visits at least one non-depot stop)
            m.Add(is_used[v] == 0).OnlyEnforceIf(is_done[v, 1])
            m.Add(is_used[v] == 1).OnlyEnforceIf(is_done[v, 1].Not())
