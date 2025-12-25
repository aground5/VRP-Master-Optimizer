from vrp_solver.ortools_solver.wrapper import VRPSolver

class CapacityConstraints:
    @staticmethod
    def apply(solver: VRPSolver):
        m = solver.model
        data = solver.data
        cars = solver.variables
        
        num_v = solver.num_vehicles
        max_s = solver.max_steps
        
        route = cars['route']
        load_w = cars['load_w']
        load_v = cars['load_v']
        
        # Build demand maps from Shipments
        demand_weight = [0] * solver.num_locations
        demand_volume = [0] * solver.num_locations
        
        for ship in data.shipments:
            demand_weight[ship.pickup_id] = ship.cargo.weight
            demand_volume[ship.pickup_id] = ship.cargo.volume
            demand_weight[ship.delivery_id] = -ship.cargo.weight
            demand_volume[ship.delivery_id] = -ship.cargo.volume
            
        for v in range(num_v):
            veh = data.vehicles[v]
            
            # Init
            m.Add(load_w[v, 0] == 0)
            m.Add(load_v[v, 0] == 0)
            
            for s in range(max_s - 1):
                next_n = route[v, s+1]
                
                next_is_depot = m.NewBoolVar(f'nid_{v}_{s}')
                m.Add(next_n == veh.end_loc).OnlyEnforceIf(next_is_depot)
                m.Add(next_n != veh.end_loc).OnlyEnforceIf(next_is_depot.Not())
                
                dem_w = m.NewIntVar(-100, 100, f'dw_{v}_{s}')
                m.AddElement(next_n, demand_weight, dem_w)
                dem_v = m.NewIntVar(-100, 100, f'dv_{v}_{s}')
                m.AddElement(next_n, demand_volume, dem_v)
                
                m.Add(load_w[v, s+1] == 0).OnlyEnforceIf(next_is_depot)
                m.Add(load_v[v, s+1] == 0).OnlyEnforceIf(next_is_depot)
                
                m.Add(load_w[v, s+1] == load_w[v, s] + dem_w).OnlyEnforceIf(next_is_depot.Not())
                m.Add(load_v[v, s+1] == load_v[v, s] + dem_v).OnlyEnforceIf(next_is_depot.Not())
                
            # Max Capacity Check - Using new ontology
            for s in range(max_s):
                m.Add(load_w[v, s] <= veh.profile.capacity.weight)
                m.Add(load_v[v, s] <= veh.profile.capacity.volume)
