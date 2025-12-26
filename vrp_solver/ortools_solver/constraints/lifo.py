"""
LIFO Constraints for Stop-based VRP.

Handles:
- LIFO (Last-In-First-Out) rehandling penalty
- Crowded vehicle penalty (load > 70% capacity)
"""
from vrp_solver.ortools_solver.wrapper import VRPSolver


class LifoConstraints:
    @staticmethod
    def apply(solver: VRPSolver):
        m = solver.model
        data = solver.data
        cars = solver.variables
        
        visit_step = cars['visit_step']
        visit_vehicle = cars['visit_vehicle']
        load_v = cars['load_v']
        is_served = cars['is_served']
        
        num_ships = solver.num_shipments
        rehand_terms = []
        
        for v in range(solver.num_vehicles):
            veh_data = data.vehicles[v]
            
            # Threshold: 70% of capacity volume
            # SCALE for float support
            scale = solver.config.capacity_scale_factor
            thresh_val = int(veh_data.profile.capacity.volume * scale * 0.7)
            
            for curr_idx in range(num_ships):
                p_curr_stop = solver.shipment_pickup_stop[curr_idx]
                d_curr_stop = solver.shipment_delivery_stop[curr_idx]
                
                # ...
                
                # 1. Check if shipment is served by this vehicle
                served_by_v = m.NewBoolVar(f'sbv_{v}_{curr_idx}')
                m.Add(visit_vehicle[p_curr_stop] == v + 1).OnlyEnforceIf(served_by_v)
                m.Add(visit_vehicle[p_curr_stop] != v + 1).OnlyEnforceIf(served_by_v.Not())
                
                # 2. Load at delivery moment
                load_at_drop = m.NewIntVar(0, 2000, f'lad_{v}_{curr_idx}')
                
                for s in range(solver.max_steps):
                    is_drop_step = m.NewBoolVar(f'ids_{v}_{curr_idx}_{s}')
                    m.Add(visit_step[d_curr_stop] == s).OnlyEnforceIf(is_drop_step)
                    m.Add(visit_step[d_curr_stop] != s).OnlyEnforceIf(is_drop_step.Not())
                    
                    m.Add(load_at_drop == load_v[v, s]).OnlyEnforceIf([served_by_v, is_drop_step])
                
                # 3. Crowded check
                is_crowded = m.NewBoolVar(f'iic_{v}_{curr_idx}')
                m.Add(load_at_drop >= thresh_val).OnlyEnforceIf(is_crowded)
                m.Add(load_at_drop < thresh_val).OnlyEnforceIf(is_crowded.Not())
                
                # 4. Check blockers (other shipments loaded after, unloaded after)
                for other_idx in range(num_ships):
                    if curr_idx == other_idx:
                        continue
                    
                    p_other_stop = solver.shipment_pickup_stop[other_idx]
                    d_other_stop = solver.shipment_delivery_stop[other_idx]
                    vol_other = data.shipments[other_idx].cargo.volume
                    
                    # SCALE volume for penalty calculation to maintain magnitude
                    vol_other_scaled = int(vol_other * scale)
                    
                    other_by_v = m.NewBoolVar(f'obv_{v}_{other_idx}')
                    m.Add(visit_vehicle[p_other_stop] == v + 1).OnlyEnforceIf(other_by_v)
                    m.Add(visit_vehicle[p_other_stop] != v + 1).OnlyEnforceIf(other_by_v.Not())
                    
                    # Loaded after current
                    la = m.NewBoolVar(f'la_{v}_{curr_idx}_{other_idx}')
                    m.Add(visit_step[p_other_stop] > visit_step[p_curr_stop]).OnlyEnforceIf(la)
                    m.Add(visit_step[p_other_stop] <= visit_step[p_curr_stop]).OnlyEnforceIf(la.Not())
                    
                    # Unloaded after current
                    ua = m.NewBoolVar(f'ua_{v}_{curr_idx}_{other_idx}')
                    m.Add(visit_step[d_other_stop] > visit_step[d_curr_stop]).OnlyEnforceIf(ua)
                    m.Add(visit_step[d_other_stop] <= visit_step[d_curr_stop]).OnlyEnforceIf(ua.Not())
                    
                    # Picked up before current delivery
                    pr = m.NewBoolVar(f'pr_{v}_{curr_idx}_{other_idx}')
                    m.Add(visit_step[p_other_stop] < visit_step[d_curr_stop]).OnlyEnforceIf(pr)
                    m.Add(visit_step[p_other_stop] >= visit_step[d_curr_stop]).OnlyEnforceIf(pr.Not())
                    
                    # Blocking conditions
                    blk_crowded = m.NewBoolVar(f'blkc_{v}_{curr_idx}_{other_idx}')
                    m.AddBoolAnd([served_by_v, other_by_v, la, ua, pr, is_crowded]).OnlyEnforceIf(blk_crowded)
                    m.AddBoolOr([served_by_v.Not(), other_by_v.Not(), la.Not(), ua.Not(), pr.Not(), is_crowded.Not()]).OnlyEnforceIf(blk_crowded.Not())
                    
                    blk_basic = m.NewBoolVar(f'blkb_{v}_{curr_idx}_{other_idx}')
                    m.AddBoolAnd([served_by_v, other_by_v, la, ua, pr, is_crowded.Not()]).OnlyEnforceIf(blk_basic)
                    m.AddBoolOr([served_by_v.Not(), other_by_v.Not(), la.Not(), ua.Not(), pr.Not(), is_crowded]).OnlyEnforceIf(blk_basic.Not())
                    
                    cost_crowded = vol_other_scaled * 50
                    cost_basic = vol_other_scaled * 10
                    
                    term = m.NewIntVar(0, 100000, f'rhT_{v}_{curr_idx}_{other_idx}')
                    m.Add(term == cost_crowded).OnlyEnforceIf(blk_crowded)
                    m.Add(term == cost_basic).OnlyEnforceIf(blk_basic)
                    m.Add(term == 0).OnlyEnforceIf([blk_crowded.Not(), blk_basic.Not()])
                    
                    rehand_terms.append(term)
        
        c_rehandling = m.NewIntVar(0, 1000000, 'c_rehandling')
        m.Add(c_rehandling == sum(rehand_terms))
        cars['c_rehandling'] = c_rehandling
