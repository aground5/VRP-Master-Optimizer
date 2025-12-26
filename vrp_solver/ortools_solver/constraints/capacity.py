"""
Capacity Constraints for Stop-based VRP.

Handles:
- Load tracking (weight/volume) using pre-computed stop deltas
- Capacity limits per vehicle
"""
from vrp_solver.ortools_solver.wrapper import VRPSolver


class CapacityConstraints:
    @staticmethod
    def apply(solver: VRPSolver):
        m = solver.model
        data = solver.data
        cars = solver.variables
        
        num_v = solver.num_vehicles
        max_s = solver.max_steps
        
        route = cars['route']  # Stop index
        load_w = cars['load_w']
        load_v = cars['load_v']
        is_done = cars['is_done']
        
        # Pre-computed deltas from wrapper
        stop_weight_delta = solver.stop_weight_delta
        stop_volume_delta = solver.stop_volume_delta
        
        for v in range(num_v):
            veh = data.vehicles[v]
            end_depot_stop = solver.vehicle_end_stop[v]
            
            # Initial load = 0
            m.Add(load_w[v, 0] == 0)
            m.Add(load_v[v, 0] == 0)
            
            for s in range(max_s - 1):
                curr_stop = route[v, s]
                
                # Get delta from current stop
                delta_w = m.NewIntVar(-500, 500, f'dw_{v}_{s}')
                m.AddElement(curr_stop, stop_weight_delta, delta_w)
                delta_vol = m.NewIntVar(-500, 500, f'dv_{v}_{s}')
                m.AddElement(curr_stop, stop_volume_delta, delta_vol)
                
                # Check if at end depot
                at_end_depot = m.NewBoolVar(f'aed_{v}_{s}')
                m.Add(curr_stop == end_depot_stop).OnlyEnforceIf(at_end_depot)
                m.Add(curr_stop != end_depot_stop).OnlyEnforceIf(at_end_depot.Not())
                
                # If at end depot or done, reset to 0
                # Otherwise, apply delta
                reset_cond = m.NewBoolVar(f'reset_{v}_{s}')
                m.AddBoolOr([at_end_depot, is_done[v, s]]).OnlyEnforceIf(reset_cond)
                m.AddBoolAnd([at_end_depot.Not(), is_done[v, s].Not()]).OnlyEnforceIf(reset_cond.Not())
                
                m.Add(load_w[v, s+1] == 0).OnlyEnforceIf(reset_cond)
                m.Add(load_v[v, s+1] == 0).OnlyEnforceIf(reset_cond)
                
                m.Add(load_w[v, s+1] == load_w[v, s] + delta_w).OnlyEnforceIf(reset_cond.Not())
                m.Add(load_v[v, s+1] == load_v[v, s] + delta_vol).OnlyEnforceIf(reset_cond.Not())
            
            # Capacity limits
            scale = solver.config.capacity_scale_factor
            for s in range(max_s):
                m.Add(load_w[v, s] <= int(veh.profile.capacity.weight * scale))
                m.Add(load_v[v, s] <= int(veh.profile.capacity.volume * scale))
                # Non-negative load
                m.Add(load_w[v, s] >= 0)
                m.Add(load_v[v, s] >= 0)
