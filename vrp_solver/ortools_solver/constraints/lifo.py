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
        
        # Helper list of pairs
        pairs_list = []
        for s in data.shipments:
            pairs_list.append((s.pickup_id, s.delivery_id, s.cargo.volume))

        rehand_terms = []
        
        for v in range(solver.num_vehicles):
            veh_data = data.vehicles[v]
            
            # Threshold 70% of capacity volume
            thresh_val = (veh_data.profile.capacity.volume * 70) // 100
            
            for (p_curr, d_curr, vol_curr) in pairs_list:
                # 1. Check if Pair is served by Vehicle V
                served_by_v = m.NewBoolVar(f'sbv_{v}_{p_curr}')
                m.Add(visit_vehicle[p_curr] == v + 1).OnlyEnforceIf(served_by_v)
                m.Add(visit_vehicle[p_curr] != v + 1).OnlyEnforceIf(served_by_v.Not())
                
                # 2. Load at drop moment
                load_at_drop = m.NewIntVar(0, 2000, f'lad_{v}_{p_curr}')
                
                for s in range(solver.max_steps):
                    is_drop_step = m.NewBoolVar(f'ids_{v}_{p_curr}_{s}')
                    m.Add(visit_step[d_curr] == s).OnlyEnforceIf(is_drop_step)
                    m.Add(visit_step[d_curr] != s).OnlyEnforceIf(is_drop_step.Not())
                    
                    m.Add(load_at_drop == load_v[v, s]).OnlyEnforceIf([served_by_v, is_drop_step])
                
                # 3. Crowd Check
                is_instantly_crowded = m.NewBoolVar(f'iic_{v}_{p_curr}')
                m.Add(load_at_drop >= thresh_val).OnlyEnforceIf(is_instantly_crowded)
                m.Add(load_at_drop < thresh_val).OnlyEnforceIf(is_instantly_crowded.Not())
                
                # 4. Blockers
                for (p_other, d_other, vol_other) in pairs_list:
                    if p_curr == p_other: continue
                    
                    other_by_v = m.NewBoolVar(f'obv_{v}_{p_other}')
                    m.Add(visit_vehicle[p_other] == v + 1).OnlyEnforceIf(other_by_v)
                    m.Add(visit_vehicle[p_other] != v + 1).OnlyEnforceIf(other_by_v.Not())
                    
                    la = m.NewBoolVar(f'la_{v}_{p_curr}_{p_other}')
                    m.Add(visit_step[p_other] > visit_step[p_curr]).OnlyEnforceIf(la)
                    m.Add(visit_step[p_other] <= visit_step[p_curr]).OnlyEnforceIf(la.Not())
                    
                    ua = m.NewBoolVar(f'ua_{v}_{p_curr}_{p_other}')
                    m.Add(visit_step[d_other] > visit_step[d_curr]).OnlyEnforceIf(ua)
                    m.Add(visit_step[d_other] <= visit_step[d_curr]).OnlyEnforceIf(ua.Not())
                    
                    pr = m.NewBoolVar(f'pr_{v}_{p_curr}_{p_other}')
                    m.Add(visit_step[p_other] < visit_step[d_curr]).OnlyEnforceIf(pr)
                    m.Add(visit_step[p_other] >= visit_step[d_curr]).OnlyEnforceIf(pr.Not())
                    
                    blk_crowded = m.NewBoolVar(f'blkc_{v}_{p_curr}_{p_other}')
                    m.AddBoolAnd([served_by_v, other_by_v, la, ua, pr, is_instantly_crowded]).OnlyEnforceIf(blk_crowded)
                    m.AddBoolOr([served_by_v.Not(), other_by_v.Not(), la.Not(), ua.Not(), pr.Not(), is_instantly_crowded.Not()]).OnlyEnforceIf(blk_crowded.Not())
                    
                    blk_basic = m.NewBoolVar(f'blkb_{v}_{p_curr}_{p_other}')
                    m.AddBoolAnd([served_by_v, other_by_v, la, ua, pr, is_instantly_crowded.Not()]).OnlyEnforceIf(blk_basic)
                    m.AddBoolOr([served_by_v.Not(), other_by_v.Not(), la.Not(), ua.Not(), pr.Not(), is_instantly_crowded]).OnlyEnforceIf(blk_basic.Not())
                    
                    cost_crowded = vol_other * 50
                    cost_basic   = vol_other * 10
                    
                    term = m.NewIntVar(0, 100000, f'rhT_{v}_{p_curr}_{p_other}')
                    m.Add(term == cost_crowded).OnlyEnforceIf(blk_crowded)
                    m.Add(term == cost_basic).OnlyEnforceIf(blk_basic)
                    m.Add(term == 0).OnlyEnforceIf([blk_crowded.Not(), blk_basic.Not()])
                    
                    rehand_terms.append(term)
                    
        c_rehandling = m.NewIntVar(0, 1000000, 'c_rehandling')
        m.Add(c_rehandling == sum(rehand_terms))
        cars['c_rehandling'] = c_rehandling
