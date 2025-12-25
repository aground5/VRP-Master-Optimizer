from vrp_solver.ortools_solver.wrapper import VRPSolver

class FlowConstraints:
    @staticmethod
    def apply(solver: VRPSolver):
        m = solver.model
        data = solver.data
        cars = solver.variables
        
        visit_step = cars['visit_step']
        visit_vehicle = cars['visit_vehicle']
        is_served = cars['is_served']
        route = cars['route']
        
        # Helper: Map P -> D
        # In Domain, we have list of shipments.
        
        for ship in data.shipments:
            p = ship.pickup_id
            d = ship.delivery_id
            
            # 1. Sync Service State
            m.Add(is_served[p] == is_served[d])
            
            # 2. Precedence (Pickup < Delivery)
            m.Add(visit_step[p] < visit_step[d]).OnlyEnforceIf(is_served[p])
            
            # 3. Same Vehicle
            m.Add(visit_vehicle[p] == visit_vehicle[d]).OnlyEnforceIf(is_served[p])
            
            # 4. Inventory Continuity (No Depot while carrying Packet)
            # Iterate all vehicles
            for v in range(solver.num_vehicles):
                # Is this vehicle carrying this pair?
                carrying = m.NewBoolVar(f'cry_{v}_{p}')
                # Check if this vehicle is the one serving p
                # visit_vehicle values are 1-based (v+1)
                m.Add(visit_vehicle[p] == v + 1).OnlyEnforceIf(carrying)
                m.Add(visit_vehicle[p] != v + 1).OnlyEnforceIf(carrying.Not())
                
                # DEPOT Location ID.
                # Assuming StartLoc == EndLoc == Depot for all? 
                # Original code assumes 0 is Depot.
                DEPOT = 0 
                
                for s in range(solver.max_steps):
                    is_intermediate = m.NewBoolVar(f'inter_{v}_{p}_{s}')
                    
                    # s > visit_step[p]
                    after_pick = m.NewBoolVar(f'ap_{v}_{p}_{s}')
                    m.Add(s > visit_step[p]).OnlyEnforceIf(after_pick)
                    m.Add(s <= visit_step[p]).OnlyEnforceIf(after_pick.Not())
                    
                    # s < visit_step[d]
                    before_drop = m.NewBoolVar(f'bd_{v}_{p}_{s}')
                    m.Add(s < visit_step[d]).OnlyEnforceIf(before_drop)
                    m.Add(s >= visit_step[d]).OnlyEnforceIf(before_drop.Not())
                    
                    m.AddBoolAnd([carrying, after_pick, before_drop]).OnlyEnforceIf(is_intermediate)
                    m.AddBoolOr([carrying.Not(), after_pick.Not(), before_drop.Not()]).OnlyEnforceIf(is_intermediate.Not())
                    
                    # Constraint: Intermediate steps cannot be Depot
                    m.Add(route[v, s] != DEPOT).OnlyEnforceIf(is_intermediate)
