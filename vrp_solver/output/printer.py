"""
VRP Solution Printer for Stop-based model.
"""
from ortools.sat.python import cp_model
from vrp_solver.ortools_solver.wrapper import VRPSolver


def print_solution(wrapper: VRPSolver, cp_solver: cp_model.CpSolver, status):
    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        print("No solution found.")
        return

    cars = wrapper.variables
    data = wrapper.data
    
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
    print("🚚 VRP FINAL SIMULATION REPORT (Stop-Based Model)")
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
    
    # Shipment Service Summary
    print("============================================================")
    print("📦 SHIPMENT SERVICE STATUS")
    print("============================================================")
    
    is_served = cars['is_served']
    visit_step = cars['visit_step']
    visit_vehicle = cars['visit_vehicle']
    
    served_count = 0
    for ship_idx, ship in enumerate(data.shipments):
        if val(is_served[ship_idx]):
            served_count += 1
            p_stop = wrapper.shipment_pickup_stop[ship_idx]
            d_stop = wrapper.shipment_delivery_stop[ship_idx]
            
            p_step = val(visit_step[p_stop])
            d_step = val(visit_step[d_stop])
            veh = val(visit_vehicle[p_stop])
            
            print(f"  ✅ {ship.name}: Pickup@step{p_step} -> Delivery@step{d_step} (Vehicle {veh})")
        else:
            print(f"  ❌ {ship.name}: NOT SERVED")
    
    print(f"\nTotal: {served_count}/{len(data.shipments)} shipments served")
    print("============================================================\n")
    
    # Vehicle Routes
    route = cars['route']
    arrival_time = cars['arrival_time']
    load_w = cars['load_w']
    is_done = cars['is_done']
    is_used = cars['is_used']
    
    print("============================================================")
    print("🚛 VEHICLE ROUTES")
    print("============================================================")
    
    for v in range(wrapper.num_vehicles):
        if val(is_used[v]):
            print(f"\n🚛 Vehicle {v + 1}")
            
            for s in range(wrapper.max_steps):
                if val(is_done[v, s]) and (s > 0 and val(is_done[v, s-1])):
                    continue  # Skip tail
                
                vd = val(is_done[v, s])
                vpd = val(is_done[v, s-1]) if s > 0 else False
                
                if not vd or (vd and not vpd):
                    stop_idx = val(route[v, s])
                    stop = data.stops[stop_idx]
                    loc = data.locations[stop.location_idx]
                    w = val(load_w[v, s])
                    arr = val(arrival_time[v, s])
                    
                    stop_info = f"{stop.stop_type.value}"
                    if stop.shipment_idx >= 0:
                        stop_info += f" (Ship_{stop.shipment_idx})"
                    
                    print(f"   Step {s:02d} | {loc.name} | {stop_info} | Time: {arr:04d} | Load {w}")
    
    print("\n============================================================")
