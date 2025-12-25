from ortools.sat.python import cp_model
from vrp_solver.ortools_solver.wrapper import VRPSolver

def print_solution(wrapper: VRPSolver, cp_solver: cp_model.CpSolver, status):
    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        print("No solution found.")
        return

    cars = wrapper.variables
    data = wrapper.data
    m = wrapper.model
    
    # helper for getValue
    def val(var):
        if isinstance(var, int): return var
        return cp_solver.Value(var)
    
    t_cost = val(cars['total_cost'])
    fv     = val(cars['c_fixed'])
    dv     = val(cars['c_dist'])
    tv     = val(cars['c_time'])
    zv     = val(cars['c_zone'])
    rh     = val(cars.get('c_rehandling', 0))
    wv     = val(cars['c_waiting'])
    pv     = val(cars['c_penalty'])
    lv     = val(cars['c_late'])
    
    print("============================================================")
    print("🚚 VRP FINAL SIMULATION REPORT (Modular Ontology)")
    print("============================================================")
    print("💰 Total Cost breakdown:")
    print(f"   Total Objective : {t_cost}")
    print("   ----------------------------------------")
    print(f"   1. Fixed Cost   : {fv}")
    print(f"   2. Dist Cost    : {dv}")
    print(f"   3. Labor Cost   : {tv}")
    print(f"   4. Zone Penalty : {zv}")
    print(f"   5. Re-handling  : {rh}")
    print(f"   6. Waiting Cost : {wv}")
    print(f"   7. Miss Penalty : {pv}")
    print(f"   8. Late Penalty : {lv}")
    print("============================================================\n")
    
    # LIFO Debug
    print("============================================================")
    print("🔎 LIFO INTERFERENCE DEBUG")
    print("============================================================")
    
    total_rehand_check = 0
    # Reconstruct pairs list
    pairs = []
    for s in data.shipments:
        pairs.append((s.pickup_id, s.delivery_id, s.volume))
        
    is_served = cars['is_served']
    visit_step = cars['visit_step']
    visit_vehicle = cars['visit_vehicle']
    
    for (p_curr, d_curr, vol_curr) in pairs:
        if not val(is_served[p_curr]): continue
        
        p_step = val(visit_step[p_curr])
        d_step = val(visit_step[d_curr])
        veh_curr = val(visit_vehicle[p_curr])
        
        blockers = []
        for (p_other, d_other, vol_other) in pairs:
            if p_curr == p_other: continue
            if not val(is_served[p_other]): continue
            
            veh_other = val(visit_vehicle[p_other])
            po_step = val(visit_step[p_other])
            do_step = val(visit_step[d_other])
            
            if (veh_curr == veh_other and
                po_step > p_step and
                do_step > d_step and
                po_step < d_step):
                
                cost = vol_other * 50 # Assuming crowded for debug print (simplification)
                # Ideally we check checked variable, but re-calculation is fine for text
                blockers.append(f"   - 📦 Blocked by Pair {p_other}->{d_other} (Vol {vol_other})")
        
        if blockers:
            print(f"🚨 Set {p_curr}->{d_curr} blocked at step {d_step}:")
            for b in blockers: print(b)
            
    print("============================================================\n")
    
    # Schedules
    route = cars['route']
    arrival_time = cars['arrival_time']
    load_w = cars['load_w']
    is_done = cars['is_done']
    is_used = cars['is_used']
    
    debug_due = cars.get('debug_due_dates', {})
    debug_late = cars.get('debug_is_late', {})
    
    for v in range(wrapper.num_vehicles):
        if val(is_used[v]):
            print(f"🚛 Vehicle {v + 1}")
            
            for s in range(wrapper.max_steps):
                if val(is_done[v, s]) and (s > 0 and val(is_done[v, s-1])):
                    continue # Skip tail
                
                # Check for "Just Finished" step for display?
                # Logic: show if not done OR (done and prev not done)
                vd = val(is_done[v, s])
                vpd = val(is_done[v, s-1]) if s > 0 else False
                
                if not vd or (vd and not vpd):
                    loc_idx = val(route[v, s])
                    w = val(load_w[v, s])
                    arr = val(arrival_time[v, s])
                    
                    loc_name = data.locations[loc_idx].name
                    
                    time_str = f"Time: {arr:04d}"
                    if (v,s) in debug_late:
                        l = val(debug_late[v,s])
                        d = val(debug_due[v,s])
                        if l: time_str += f" / Due {d} [LATE]"
                    
                    print(f"   Step {s:02d} | {loc_name} | {time_str} | Load {w}")
            print("")
