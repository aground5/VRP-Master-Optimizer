from vrp_solver.ortools_solver.wrapper import VRPSolver

class RoutingConstraints:
    @staticmethod
    def apply(solver: VRPSolver):
        m = solver.model
        data = solver.data
        cars = solver.variables
        
        num_v = solver.num_vehicles
        max_s = solver.max_steps
        num_loc = solver.num_locations
        
        route = cars['route']
        is_done = cars['is_done']
        visit_step = cars['visit_step']
        visit_vehicle = cars['visit_vehicle']
        is_served = cars['is_served']
        
        DEPOT = 0 # Assumed
        
        # (1) Route Structure (Start/End continuity)
        for v in range(num_v):
            veh_data = data.vehicles[v]
            
            # Start at StartLoc
            m.Add(route[v, 0] == veh_data.start_loc)
            m.Add(is_done[v, 0] == False)
            
            for s in range(max_s - 1):
                # if done[s], then done[s+1]
                m.AddImplication(is_done[v, s], is_done[v, s+1])
                
                # If done, stay at EndLoc
                m.Add(route[v, s] == veh_data.end_loc).OnlyEnforceIf(is_done[v, s])
                
                # Transition to End (Logic from original: 'curr_is_end', 'next_is_end')
                # Simplifying: 
                # If NOT done[s], but done[s+1], this is the last step.
                # Actually, the original logic is specific to forcing 'route' value to be 'EndLoc' 
                # exactly when 'is_done' becomes true.
                
                # Re-implementing exact original logic for safety
                curr_is_end = m.NewBoolVar(f'cie_{v}_{s}')
                next_is_end = m.NewBoolVar(f'nie_{v}_{s}')
                
                m.Add(route[v, s] == veh_data.end_loc).OnlyEnforceIf(curr_is_end)
                m.Add(route[v, s] != veh_data.end_loc).OnlyEnforceIf(curr_is_end.Not())
                m.Add(route[v, s+1] == veh_data.end_loc).OnlyEnforceIf(next_is_end)
                m.Add(route[v, s+1] != veh_data.end_loc).OnlyEnforceIf(next_is_end.Not())
                
                both_end = m.NewBoolVar(f'bend_{v}_{s}')
                m.AddBoolAnd([curr_is_end, next_is_end]).OnlyEnforceIf(both_end)
                m.AddBoolOr([curr_is_end.Not(), next_is_end.Not()]).OnlyEnforceIf(both_end.Not())
                
                m.Add(is_done[v, s+1] == both_end)
                
        # (2) Link Visits
        m.Add(visit_step[DEPOT] == 0)
        
        for c in range(1, num_loc):
            visits_bools = []
            for v in range(num_v):
                for s in range(max_s):
                    is_loc = m.NewBoolVar(f'is_loc_{v}_{s}_{c}')
                    m.Add(route[v, s] == c).OnlyEnforceIf(is_loc)
                    m.Add(route[v, s] != c).OnlyEnforceIf(is_loc.Not())
                    visits_bools.append(is_loc)
                    
                    # If this is the visit, record step & vehicle
                    m.Add(visit_step[c] == s).OnlyEnforceIf(is_loc)
                    m.Add(visit_vehicle[c] == v + 1).OnlyEnforceIf(is_loc)
            
            # Check sum of visits
            m.Add(sum(visits_bools) == is_served[c])
            
            # Unserved defaults
            m.Add(visit_step[c] == 0).OnlyEnforceIf(is_served[c].Not())
            m.Add(visit_vehicle[c] == 0).OnlyEnforceIf(is_served[c].Not())

        # (3) Usage
        is_used = cars['is_used']
        for v in range(num_v):
            # If done at step 1, not used (start->end immediately)
            m.Add(is_used[v] == 0).OnlyEnforceIf(is_done[v, 1])
            m.Add(is_used[v] == 1).OnlyEnforceIf(is_done[v, 1].Not())
