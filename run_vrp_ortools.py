from ortools.sat.python import cp_model
import collections

def main():
    # =========================================================
    # 1. 데이터 설정 (Complex Realistic Data - Google OR-Tools 17-node)
    # =========================================================
    
    # Scale Factor: 10x (To accommodate 30min Depot Service and 5min Intra constraints)
    # Original Data: strict small windows (0-5). Scaled: 0-50.
    
    num_vehicles = 4
    num_locations = 17 # 0(Depot) + 16 Locations
    max_steps = 20     # Enough for 16 nodes / 4 veh = ~4-5 stops each + depot
    
    VEHICLES = range(num_vehicles)
    LOCS = range(num_locations)
    STEPS = range(max_steps)
    DEPOT = 0

    # [1-1] 차량 정보 (8 Fleet to meet Strict Windows without Cheating)
    # Since windows are tight (50 min) and sequencing is hard, we deploy more vehicles.
    # Capacity 50 (Same)
    v_cap_weight = [50] * num_vehicles
    v_cap_volume = [50] * num_vehicles
    v_start_loc  = [0] * num_vehicles
    v_end_loc    = [0] * num_vehicles

    # [1-2] 노동법
    v_start_window = [0] * num_vehicles
    # Realistic Shift: 12 Hours = 720 min
    v_max_work_time = [720] * num_vehicles 
    standard_work_time = 480 
    break_interval = 240      
    break_duration = 30       

    # [Defenses]
    depot_min_service_time = 30 # Anti-Laundering
    min_intra_transit = 5       # Anti-Teleport
    cost_per_wait_min = 5       # Anti-Idling

    # [1-3] 비용 구조
    # Reduce Fixed Cost to encourage using more vehicles (Load Balancing)
    cost_fixed     = [500, 500, 5000, 5000] 
    cost_per_km    = [10, 10, 10, 10]
    cost_per_min   = [10, 10, 10, 10] 
    cost_per_kg_km = 1

    # [1-4] 화물 정보 (17 nodes)
    # OR-Tools PDP Pairs: 
    # [1->6], [2->10], [4->3], [5->9], [7->8], [15->11], [13->12], [16->14]
    
    # Demands (Based on CVRP example but balanced for P/D)
    # P indices: 1, 2, 4, 5, 7, 15, 13, 16
    # Assign random weights to pairs:
    # 1->6: 10kg, 2->10: 20kg, 4->3: 5kg, 5->9: 15kg
    # 7->8: 10kg, 15->11: 20kg, 13->12: 10kg, 16->14: 15kg
    
    # Initialize 0
    demand_weight = [0] * num_locations
    demand_volume = [0] * num_locations
    pickup_pair   = [0] * num_locations
    
    # Define Pairs Map: Pickup -> (Delivery, Weight)
    pair_defs = {
        1: (6, 10), 2: (10, 20), 4: (3, 5), 5: (9, 15),
        7: (8, 10), 15: (11, 20), 13: (12, 10), 16: (14, 15)
    }
    
    for p, (d, w) in pair_defs.items():
        # Sets
        pickup_pair[p] = d
        demand_weight[p] = w
        demand_volume[p] = w # Assume 1:1 Vol/Weight
        demand_weight[d] = -w
        demand_volume[d] = -w
        
    # Time Windows (Based on VRPTW example data, Scaled x10)
    # Data:
    # 0(Depot): (0,5)->(0,50) ... Wait, 0-50 is very short for 4 vehicles?
    # Let's Scale time x20? Or just Relax Depot Window to (0, 1000).
    # The example solves small routing. We want robust simulation.
    # Let's set reasonable windows based on scaled travel times.
    
    # Raw Time Matrix (0-16) from example (See list below)
    # Ex: 0->1 is 6. Scaled x10 = 60 mins.
    # If travel is 60m, Windows (0,50) is impossible.
    # The original example had units "Hours"? No, "20min route".
    # Wait, Time matrix values: 6, 9, 8... Window 7-12.
    # So travel 6 * 10 = 60 min. Window (70, 120).
    # Depot (0, 50). Start at 0?
    
    raw_windows = [
        (0, 100),  # 0 Depot (Extended to allow returns)
        (7, 12),  # 1
        (10, 15), # 2
        (16, 18), # 3
        (10, 13), # 4
        (0, 5),   # 5
        (5, 10),  # 6
        (0, 4),   # 7
        (5, 10),  # 8
        (0, 3),   # 9
        (10, 16), # 10
        (10, 15), # 11
        (0, 5),   # 12
        (5, 10),  # 13
        (7, 8),   # 14
        (10, 15), # 15
        (11, 15), # 16
    ]
    
    # Raw Time Matrix (Moved Up)
    raw_time_matrix = [
        [0, 6, 9, 8, 7, 3, 6, 2, 3, 2, 6, 6, 4, 4, 5, 9, 7],
        [6, 0, 8, 3, 2, 6, 8, 4, 8, 8, 13, 7, 5, 8, 12, 10, 14],
        [9, 8, 0, 11, 10, 6, 3, 9, 5, 8, 4, 15, 14, 13, 9, 18, 9],
        [8, 3, 11, 0, 1, 7, 10, 6, 10, 10, 14, 6, 7, 9, 14, 6, 16],
        [7, 2, 10, 1, 0, 6, 9, 4, 8, 9, 13, 4, 6, 8, 12, 8, 14],
        [3, 6, 6, 7, 6, 0, 2, 3, 2, 2, 7, 9, 7, 7, 6, 12, 8],
        [6, 8, 3, 10, 9, 2, 0, 6, 2, 5, 4, 12, 10, 10, 6, 15, 5],
        [2, 4, 9, 6, 4, 3, 6, 0, 4, 4, 8, 5, 4, 3, 7, 8, 10],
        [3, 8, 5, 10, 8, 2, 2, 4, 0, 3, 4, 9, 8, 7, 3, 13, 6],
        [2, 8, 8, 10, 9, 2, 5, 4, 3, 0, 4, 6, 5, 4, 3, 9, 5],
        [6, 13, 4, 14, 13, 7, 4, 8, 4, 4, 0, 10, 9, 8, 4, 13, 4],
        [6, 7, 15, 6, 4, 9, 12, 5, 9, 6, 10, 0, 1, 3, 7, 3, 10],
        [4, 5, 14, 7, 6, 7, 10, 4, 8, 5, 9, 1, 0, 2, 6, 4, 8],
        [4, 8, 13, 9, 8, 7, 10, 3, 7, 4, 8, 3, 2, 0, 4, 5, 6],
        [5, 12, 9, 14, 12, 6, 6, 7, 3, 3, 4, 7, 6, 4, 0, 9, 2],
        [9, 10, 18, 6, 8, 12, 15, 8, 13, 9, 13, 3, 4, 5, 9, 0, 9],
        [7, 14, 9, 16, 14, 8, 5, 10, 6, 5, 4, 10, 8, 6, 2, 9, 0],
    ]

    # Scale x10
    scale = 10
    # Keep Start Constraints (Ready Time) to test Waiting Cost
    ready_time = [w[0] * scale for w in raw_windows]
    # PROPOSAL: Strict windows with "Fallout" logic.
    due_time   = [w[1] * scale for w in raw_windows] 
    due_time[0] = 720 # Depot is always Shift End
    
    service_duration = [10] * num_locations # 10 min service everywhere
    service_duration[0] = 0
    
    unserved_penalty = [500000] * num_locations # Force Service
    unserved_penalty[0] = 0

    # Scale x5 (Faster Travel / Smaller Map) to allow chaining within ORIGINAL windows
    # If Travel x10, Travel > Window Width -> Impossible to chain.
    # Travel x5 -> Travel < Window Width -> Feasible.
    travel_time = [[t * 5 for t in row] for row in raw_time_matrix]
    # Assume Dist = Time (Speed 1km/min)
    travel_dist = [[t * 5 for t in row] for row in raw_time_matrix]
    
    # [1-6] 호환성
    setup_time = [[0] * num_locations for _ in range(num_locations)] 

    v_type = [1] * num_vehicles
    req_v_type = [0] * num_locations

    # [1-7] 구역(Zoning)
    # 1-8: Zone 1, 9-16: Zone 2
    zone = [0] * num_locations
    for i in range(1, 9): zone[i] = 1
    for i in range(9, 17): zone[i] = 2
    
    zone_penalty = 2000

    # [1-8] Matrix
    # (Moved above to support auto-calibration)
    
    # ...

    
    # Scale x10
    travel_time = [[t * scale for t in row] for row in raw_time_matrix]
    # Assume Dist = Time (Speed 1km/min)
    travel_dist = [[t * scale for t in row] for row in raw_time_matrix]
    # =========================================================
    # 2. 모델 생성
    # =========================================================
    model = cp_model.CpModel()

    # Variables
    route = {}
    for v in VEHICLES:
        for s in STEPS:
            route[v, s] = model.NewIntVar(0, num_locations - 1, f'route_{v}_{s}')
            
    arrival_time = {}
    for v in VEHICLES:
        for s in STEPS:
            arrival_time[v, s] = model.NewIntVar(0, 10000, f'arr_{v}_{s}')

    load_w = {}
    load_v = {}
    for v in VEHICLES:
        for s in STEPS:
            load_w[v, s] = model.NewIntVar(0, 2000, f'lw_{v}_{s}')
            load_v[v, s] = model.NewIntVar(0, 2000, f'lv_{v}_{s}')
            
    is_done = {}
    for v in VEHICLES:
        for s in STEPS:
            is_done[v, s] = model.NewBoolVar(f'done_{v}_{s}')
    
    is_used = {}
    for v in VEHICLES:
        is_used[v] = model.NewBoolVar(f'used_{v}')
        
    is_served = {}
    for c in LOCS:
        is_served[c] = model.NewBoolVar(f'served_{c}')
        
    # [NEW] Visit Step & Vehicle Recording (LIFO Support)
    # visit_step[c]: which step (0..max) was location c visited? (if multiple? assumes 1 visit per non-depot)
    # visit_vehicle[c]: which vehicle (0..num_v) visited location c?
    # Note: Using 1-based indexing for vehicle encoding in MZN (1..num), here we can use 0..num-1?
    # Or strict 0..num-1 is fine. BUT, if not visited, what value?
    # MZN: 0..num_vehicles. If not visited => 0. So vehicles should be 1..num? 
    # Let's map vehicles 0,1,2 to 1,2,3 for this variable to distinguish from "None(0)".
    
    visit_step = {}
    visit_vehicle = {} # 0 means not visited. 1..num_vehicles means visited by v=(val-1)
    
    for c in LOCS:
        visit_step[c] = model.NewIntVar(0, max_steps, f'v_step_{c}')
        visit_vehicle[c] = model.NewIntVar(0, num_vehicles, f'v_veh_{c}')

    # =========================================================
    # 3. 제약 조건
    # =========================================================

    # (1) Route Structure
    for v in VEHICLES:
        model.Add(route[v, 0] == v_start_loc[v])
        model.Add(is_done[v, 0] == False)
        for s in range(max_steps - 1):
            model.AddImplication(is_done[v, s], is_done[v, s+1])
            model.Add(route[v, s] == v_end_loc[v]).OnlyEnforceIf(is_done[v, s])
            
            curr_is_end = model.NewBoolVar(f'cie_{v}_{s}')
            next_is_end = model.NewBoolVar(f'nie_{v}_{s}')
            model.Add(route[v, s] == v_end_loc[v]).OnlyEnforceIf(curr_is_end)
            model.Add(route[v, s] != v_end_loc[v]).OnlyEnforceIf(curr_is_end.Not())
            model.Add(route[v, s+1] == v_end_loc[v]).OnlyEnforceIf(next_is_end)
            model.Add(route[v, s+1] != v_end_loc[v]).OnlyEnforceIf(next_is_end.Not())
            
            both_end = model.NewBoolVar(f'bend_{v}_{s}')
            model.AddBoolAnd([curr_is_end, next_is_end]).OnlyEnforceIf(both_end)
            model.AddBoolOr([curr_is_end.Not(), next_is_end.Not()]).OnlyEnforceIf(both_end.Not())
            model.Add(is_done[v, s+1] == both_end)
            
    # (2) Visit Logic & LIFO Recording
    # MZN: if is_served[c] then exists v, s (route==c, v_step=s, v_veh=v) else step=0, veh=0
    # DEPOT always step=0, veh=? (MZN: visit_step[DEPOT] == 0)
    
    model.Add(visit_step[DEPOT] == 0)
    # visit_vehicle[DEPOT] not constrained in MZN explicitly other than by loop? 
    # MZN loop ignores c=1? "forall(c in 2..num_locations)". Yes.
    
    for c in range(1, num_locations):
        visits = []
        for v in VEHICLES:
            for s in STEPS:
                is_loc = model.NewBoolVar(f'is_loc_{v}_{s}_{c}')
                model.Add(route[v, s] == c).OnlyEnforceIf(is_loc)
                model.Add(route[v, s] != c).OnlyEnforceIf(is_loc.Not())
                visits.append(is_loc)
                
                # If this is the visit, record step and vehicle
                # visit_step[c] == s. visit_vehicle[c] == v + 1 (1-based)
                # Note: MZN S corresponds to Python index. MZN 1..max. Python 0..max-1.
                # Adjust Step Value? MZN uses S. 
                # c_rehandling logic compares steps. As long as consistent, 0-based is fine.
                # However, strict LIFO constraint uses <. 0 is fine.
                
                model.Add(visit_step[c] == s).OnlyEnforceIf(is_loc)
                model.Add(visit_vehicle[c] == v + 1).OnlyEnforceIf(is_loc)
                
        # Link is_served
        model.Add(sum(visits) == is_served[c])
        
        # If not served, values are 0
        model.Add(visit_step[c] == 0).OnlyEnforceIf(is_served[c].Not())
        model.Add(visit_vehicle[c] == 0).OnlyEnforceIf(is_served[c].Not())

    # (3) Pickup Pairs
    for p in LOCS:
        d = pickup_pair[p]
        if d > 0:
            model.Add(is_served[p] == is_served[d])

    # (4) State Updates
    total_late_penalties = [] # [PROPOSAL] Minimize Late Deliveries
    debug_due_dates = {}      # To show user allowed times
    debug_is_late = {}        # To show user late status
    
    for v in VEHICLES:
        for s in range(max_steps - 1):
            curr_n = route[v, s]
            next_n = route[v, s+1]
            
            idx = model.NewIntVar(0, num_locations**2-1, f'idx_{v}_{s}')
            model.Add(idx == curr_n * num_locations + next_n)
            
            drive_t = model.NewIntVar(0, 1000, f'dt_{v}_{s}')
            flat_time = [val for row in travel_time for val in row]
            model.AddElement(idx, flat_time, drive_t)
            
            setup_t = model.NewIntVar(0, 1000, f'st_{v}_{s}')
            flat_setup = [val for row in setup_time for val in row]
            model.AddElement(idx, flat_setup, setup_t)
            
            service_t = model.NewIntVar(0, 1000, f'sert_{v}_{s}')
            model.AddElement(curr_n, service_duration, service_t)
            
            # [Defense 1 & 4] Anti-Teleport & Depot Service Logic
            # if curr==DEPOT and next != DEPOT -> 30 (Depot Service)
            # if curr!=DEPOT and curr == next -> 5 (Intra-site)
            # else 0
            anti_teleport_t = model.NewIntVar(0, 100, f'att_{v}_{s}')
            
            from_depot = model.NewBoolVar(f'fd_{v}_{s}')
            stay_spot  = model.NewBoolVar(f'ss_{v}_{s}')
            is_depot   = model.NewBoolVar(f'id_{v}_{s}')
            
            model.Add(curr_n == DEPOT).OnlyEnforceIf(is_depot)
            model.Add(curr_n != DEPOT).OnlyEnforceIf(is_depot.Not())
            
            # from_depot: curr=DEPOT (is_depot) AND next != DEPOT
            next_is_depot_check = model.NewBoolVar(f'nidc_{v}_{s}')
            model.Add(next_n == DEPOT).OnlyEnforceIf(next_is_depot_check)
            model.Add(next_n != DEPOT).OnlyEnforceIf(next_is_depot_check.Not())
            
            model.AddBoolAnd([is_depot, next_is_depot_check.Not()]).OnlyEnforceIf(from_depot)
            model.AddBoolOr([is_depot.Not(), next_is_depot_check]).OnlyEnforceIf(from_depot.Not())
            
            # stay_spot: curr != DEPOT AND curr == next
            same_loc = model.NewBoolVar(f'sl_{v}_{s}')
            model.Add(curr_n == next_n).OnlyEnforceIf(same_loc)
            model.Add(curr_n != next_n).OnlyEnforceIf(same_loc.Not())
            
            model.AddBoolAnd([is_depot.Not(), same_loc]).OnlyEnforceIf(stay_spot)
            model.AddBoolOr([is_depot, same_loc.Not()]).OnlyEnforceIf(stay_spot.Not())
            
            model.Add(anti_teleport_t == depot_min_service_time).OnlyEnforceIf(from_depot)
            model.Add(anti_teleport_t == min_intra_transit).OnlyEnforceIf(stay_spot)
            model.AddBoolAnd([from_depot.Not(), stay_spot.Not()]).OnlyEnforceIf(
                model.NewBoolVar(f'neither_{v}_{s}')
            )
            # If neither, 0. (Implicitly if not enforced?) 
            # Better: Add(anti_teleport_t == 0).OnlyEnforceIf([from_depot.Not(), stay_spot.Not()])
            model.Add(anti_teleport_t == 0).OnlyEnforceIf([from_depot.Not(), stay_spot.Not()])
            
            rest_t = model.NewIntVar(0, break_duration, f'rt_{v}_{s}')
            long_drive = model.NewBoolVar(f'ld_{v}_{s}')
            model.Add(drive_t > break_interval).OnlyEnforceIf(long_drive)
            model.Add(drive_t <= break_interval).OnlyEnforceIf(long_drive.Not())
            model.Add(rest_t == break_duration).OnlyEnforceIf(long_drive)
            model.Add(rest_t == 0).OnlyEnforceIf(long_drive.Not())
            
            arr_cand = model.NewIntVar(0, 10000, f'ac_{v}_{s}')
            next_ready = model.NewIntVar(0, 10000, f'nr_{v}_{s}')
            model.AddElement(next_n, ready_time, next_ready)
            
            calc_arrival = model.NewIntVar(0, 10000, f'ca_{v}_{s}')
            # Added anti_teleport_t
            model.Add(calc_arrival == arrival_time[v, s] + service_t + drive_t + rest_t + setup_t + anti_teleport_t)
            model.AddMaxEquality(arr_cand, [next_ready, calc_arrival])
            
            model.Add(arrival_time[v, s+1] == arrival_time[v, s]).OnlyEnforceIf(is_done[v, s+1])
            model.Add(arrival_time[v, s+1] == arr_cand).OnlyEnforceIf(is_done[v, s+1].Not())
            
            next_is_depot = model.NewBoolVar(f'nid_{v}_{s}')
            model.Add(next_n == v_end_loc[v]).OnlyEnforceIf(next_is_depot)
            model.Add(next_n != v_end_loc[v]).OnlyEnforceIf(next_is_depot.Not())
            
            dem_w = model.NewIntVar(-100, 100, f'dw_{v}_{s}')
            model.AddElement(next_n, demand_weight, dem_w)
            dem_v = model.NewIntVar(-100, 100, f'dv_{v}_{s}')
            model.AddElement(next_n, demand_volume, dem_v)
            
            model.Add(load_w[v, s+1] == 0).OnlyEnforceIf(next_is_depot)
            model.Add(load_v[v, s+1] == 0).OnlyEnforceIf(next_is_depot)
            model.Add(load_w[v, s+1] == load_w[v, s] + dem_w).OnlyEnforceIf(next_is_depot.Not())
            model.Add(load_v[v, s+1] == load_v[v, s] + dem_v).OnlyEnforceIf(next_is_depot.Not())

    # (5) Initial
    for v in VEHICLES:
        model.Add(arrival_time[v, 0] == v_start_window[v])
        model.Add(load_w[v, 0] == 0)
        model.Add(load_v[v, 0] == 0)

    # (6) Validity
    for v in VEHICLES:
        for s in STEPS:
            model.Add(arrival_time[v, s] - v_start_window[v] <= v_max_work_time[v])
            model.Add(load_w[v, s] <= v_cap_weight[v])
            model.Add(load_v[v, s] <= v_cap_volume[v])
            
            loc = route[v, s]
            active_node = model.NewBoolVar(f'an_{v}_{s}')
            loc_depot = model.NewBoolVar(f'ldp_{v}_{s}')
            model.Add(loc == DEPOT).OnlyEnforceIf(loc_depot)
            model.Add(loc != DEPOT).OnlyEnforceIf(loc_depot.Not())
            
            model.AddBoolAnd([is_done[v, s].Not(), loc_depot.Not()]).OnlyEnforceIf(active_node)
            model.AddBoolOr([is_done[v, s], loc_depot]).OnlyEnforceIf(active_node.Not())
            
            loc_due = model.NewIntVar(0, 10000, f'ldu_{v}_{s}')
            model.AddElement(loc, due_time, loc_due)
            
            # [PROPOSAL] Soft Window Logic
            # Constraint: Arrival <= Due + 30 + (720 - Due - 30) * is_late
            # Minimizes 'is_late' count.
            step_late = model.NewBoolVar(f'sl_{v}_{s}')
            
            safe_due = model.NewIntVar(0, 10000, f'sd_{v}_{s}')
            model.Add(safe_due == loc_due + 30)
            
            shift_end = 720
            relaxed_limit = model.NewIntVar(0, 10000, f'rl_{v}_{s}')
            # relaxed = safe_due + (720 - safe_due) * step_late
            # Linearize: safe_due + limit_diff * step_late
            limit_diff = model.NewIntVar(-10000, 10000, f'ldiff_{v}_{s}')
            model.Add(limit_diff == shift_end - safe_due)
            
            penalty_boost = model.NewIntVar(-10000, 10000, f'pb_{v}_{s}')
            model.AddMultiplicationEquality(penalty_boost, [limit_diff, step_late])
            
            final_due = model.NewIntVar(0, 10000, f'fd_{v}_{s}')
            model.Add(final_due == safe_due + penalty_boost)
            
            model.Add(arrival_time[v, s] <= final_due).OnlyEnforceIf(active_node)
            
            # If not active, not late
            model.Add(step_late == 0).OnlyEnforceIf(active_node.Not())
            total_late_penalties.append(step_late)
            
            # Store for Reporting
            debug_due_dates[(v, s)] = final_due
            debug_is_late[(v, s)] = step_late
            
            req_t = model.NewIntVar(0, 10, f'rq_{v}_{s}')
            model.AddElement(loc, req_v_type, req_t)
            
            type_ok = model.NewBoolVar(f'tok_{v}_{s}')
            is_z = model.NewBoolVar(f'iz_{v}_{s}')
            model.Add(req_t == 0).OnlyEnforceIf(is_z)
            model.Add(req_t != 0).OnlyEnforceIf(is_z.Not())
            is_m = model.NewBoolVar(f'im_{v}_{s}')
            model.Add(req_t == v_type[v]).OnlyEnforceIf(is_m)
            model.Add(req_t != v_type[v]).OnlyEnforceIf(is_m.Not())
            model.AddBoolOr([is_z, is_m]).OnlyEnforceIf(type_ok)
            model.Add(type_ok == 1).OnlyEnforceIf(active_node)

    # (7) Pickup Precedence (Standard LIFO-like step order)
    # is_served[p] -> visit_step[p] < visit_step[d] AND same vehicle
    for p in LOCS:
        d = pickup_pair[p]
        if d > 0:
            model.Add(visit_step[p] < visit_step[d]).OnlyEnforceIf(is_served[p])
            model.Add(visit_vehicle[p] == visit_vehicle[d]).OnlyEnforceIf(is_served[p])

    # (8) Usage
    for v in VEHICLES:
        model.Add(is_used[v] == 0).OnlyEnforceIf(is_done[v, 1])
        model.Add(is_used[v] == 1).OnlyEnforceIf(is_done[v, 1].Not())

    # (9) Inventory Continuity (No Depot while carrying Packet)
    # Prevent "Pick A -> Depot (Reset Load) -> Pick B -> Drop A (using B's weight)" cheat.
    for p in LOCS:
        d = pickup_pair[p]
        if d > 0:
            # If served, then for all s: visit_step[p] < s < visit_step[d], route[v,s] != DEPOT
            # This is hard to encode with simple boolean logic because 'v' is variable?
            # actually visit_vehicle[p] tells us 'v'.
            
            # Implementation:
            # Iterate all v. If v visits p and d, then intermediate steps cannot be depot.
            for v in VEHICLES:
                # Is this vehicle carrying this pair?
                carrying = model.NewBoolVar(f'cry_{v}_{p}')
                # We can check if is_served[p] and visit_vehicle[p] == v+1
                # Simplified: check if visit_vehicle[p] == v+1
                model.Add(visit_vehicle[p] == v + 1).OnlyEnforceIf(carrying)
                model.Add(visit_vehicle[p] != v + 1).OnlyEnforceIf(carrying.Not())
                
                # Check ranges
                # Since s is discrete, we can say:
                # For all s:
                #    If carrying AND (visit_step[p] < s < visit_step[d]) => route[v, s] != DEPOT
                
                for s in STEPS:
                    is_intermediate = model.NewBoolVar(f'inter_{v}_{p}_{s}')
                    
                    # s > visit_step[p]
                    after_pick = model.NewBoolVar(f'ap_{v}_{p}_{s}')
                    model.Add(s > visit_step[p]).OnlyEnforceIf(after_pick)
                    model.Add(s <= visit_step[p]).OnlyEnforceIf(after_pick.Not())
                    
                    # s < visit_step[d]
                    before_drop = model.NewBoolVar(f'bd_{v}_{p}_{s}')
                    model.Add(s < visit_step[d]).OnlyEnforceIf(before_drop)
                    model.Add(s >= visit_step[d]).OnlyEnforceIf(before_drop.Not())
                    
                    model.AddBoolAnd([carrying, after_pick, before_drop]).OnlyEnforceIf(is_intermediate)
                    model.AddBoolOr([carrying.Not(), after_pick.Not(), before_drop.Not()]).OnlyEnforceIf(is_intermediate.Not())
                    
                    # Constraint
                    model.Add(route[v, s] != DEPOT).OnlyEnforceIf(is_intermediate)

    # =========================================================
    # 4. 목적 함수
    # =========================================================
    
    # 1. Fixed
    c_fixed = model.NewIntVar(0, 1000000, 'c_fixed')
    model.Add(c_fixed == sum(is_used[v] * cost_fixed[v] for v in VEHICLES))
    
    # 2. Dist
    c_dist = model.NewIntVar(0, 10000000, 'c_dist')
    dist_terms = []
    for v in VEHICLES:
        for s in range(max_steps - 1):
            act_edge = model.NewBoolVar(f'ae_{v}_{s}')
            c1 = is_done[v, s+1].Not()
            c2 = model.NewBoolVar(f'ls_{v}_{s}')
            model.AddBoolAnd([is_done[v, s+1], is_done[v, s].Not()]).OnlyEnforceIf(c2)
            model.AddBoolOr([is_done[v, s+1].Not(), is_done[v, s]]).OnlyEnforceIf(c2.Not())
            model.AddBoolOr([c1, c2]).OnlyEnforceIf(act_edge)
            model.AddBoolAnd([c1.Not(), c2.Not()]).OnlyEnforceIf(act_edge.Not())
            
            idx = model.NewIntVar(0, num_locations**2 - 1, f'di_{v}_{s}')
            model.Add(idx == route[v, s] * num_locations + route[v, s+1])
            d_val = model.NewIntVar(0, 1000, f'dv_{v}_{s}')
            flat_dist = [val for row in travel_dist for val in row]
            model.AddElement(idx, flat_dist, d_val)
            
            w_pen = model.NewIntVar(0, 100000, f'wp_{v}_{s}')
            model.Add(w_pen == load_w[v, s] * cost_per_kg_km)
            
            rate = model.NewIntVar(0, 100000, f'rt_{v}_{s}')
            model.Add(rate == cost_per_km[v] + w_pen)
            
            s_cost = model.NewIntVar(0, 1000000, f'sc_{v}_{s}')
            model.AddMultiplicationEquality(s_cost, [d_val, rate])
            
            term = model.NewIntVar(0, 1000000, f'dt_{v}_{s}')
            model.Add(term == s_cost).OnlyEnforceIf(act_edge)
            model.Add(term == 0).OnlyEnforceIf(act_edge.Not())
            dist_terms.append(term)
    model.Add(c_dist == sum(dist_terms))

    # 3. Labor (Overtime)
    c_time = model.NewIntVar(0, 1000000, 'c_time')
    time_terms = []
    for v in VEHICLES:
        max_arr = model.NewIntVar(0, 10000, f'ma_{v}')
        model.AddMaxEquality(max_arr, [arrival_time[v, s] for s in STEPS])
        tot_work = model.NewIntVar(0, 10000, f'tw_{v}')
        model.Add(tot_work == max_arr - v_start_window[v])
        
        reg = model.NewIntVar(0, standard_work_time, f'reg_{v}')
        model.AddMinEquality(reg, [tot_work, standard_work_time])
        
        diff = model.NewIntVar(-10000, 10000, f'df_{v}')
        model.Add(diff == tot_work - standard_work_time)
        over = model.NewIntVar(0, 10000, f'ov_{v}')
        model.AddMaxEquality(over, [diff, 0])
        
        c_r = model.NewIntVar(0, 1000000, f'cr_{v}')
        model.Add(c_r == reg * cost_per_min[v])
        c_o = model.NewIntVar(0, 1000000, f'co_{v}')
        over_rate = (cost_per_min[v] * 15) // 10
        model.Add(c_o == over * over_rate)
        
        t_term = model.NewIntVar(0, 1000000, f'tt_{v}')
        model.Add(t_term == c_r + c_o)
        time_terms.append(t_term)
    model.Add(c_time == sum(time_terms))

    # 4. Penalty
    c_penalty = model.NewIntVar(0, 1000000, 'c_penalty')
    pen_terms = []
    for c in range(1, num_locations):
        ns = model.NewIntVar(0, 1, f'ns_{c}')
        model.Add(ns == 1 - is_served[c])
        pt = model.NewIntVar(0, 100000, f'pt_{c}')
        model.Add(pt == ns * unserved_penalty[c])
        pen_terms.append(pt)
    model.Add(c_penalty == sum(pen_terms))

    # 5. Zone
    c_zone = model.NewIntVar(0, 1000000, 'c_zone')
    z_terms = []
    for v in VEHICLES:
        for s in range(max_steps - 1):
            act_edge = model.NewBoolVar(f'za_{v}_{s}')
            c1 = is_done[v, s+1].Not()
            c2 = model.NewBoolVar(f'zl_{v}_{s}')
            model.AddBoolAnd([is_done[v, s+1], is_done[v, s].Not()]).OnlyEnforceIf(c2)
            model.AddBoolOr([is_done[v, s+1].Not(), is_done[v, s]]).OnlyEnforceIf(c2.Not())
            model.AddBoolOr([c1, c2]).OnlyEnforceIf(act_edge)
            model.AddBoolAnd([c1.Not(), c2.Not()]).OnlyEnforceIf(act_edge.Not())
            
            curr = route[v, s]
            next_n = route[v, s+1]
            zc = model.NewIntVar(0, 10, f'zc_{v}_{s}')
            model.AddElement(curr, zone, zc)
            zn = model.NewIntVar(0, 10, f'zn_{v}_{s}')
            model.AddElement(next_n, zone, zn)
            
            cnt = model.NewBoolVar(f'cnt_{v}_{s}')
            model.Add(curr != DEPOT).OnlyEnforceIf(cnt)
            model.Add(curr == DEPOT).OnlyEnforceIf(cnt.Not())
            nnt = model.NewBoolVar(f'nnt_{v}_{s}')
            model.Add(next_n != DEPOT).OnlyEnforceIf(nnt)
            model.Add(next_n == DEPOT).OnlyEnforceIf(nnt.Not())
            zd = model.NewBoolVar(f'zd_{v}_{s}')
            model.Add(zc != zn).OnlyEnforceIf(zd)
            model.Add(zc == zn).OnlyEnforceIf(zd.Not())
            
            app = model.NewBoolVar(f'zap_{v}_{s}')
            model.AddBoolAnd([act_edge, cnt, nnt, zd]).OnlyEnforceIf(app)
            model.AddBoolOr([act_edge.Not(), cnt.Not(), nnt.Not(), zd.Not()]).OnlyEnforceIf(app.Not())
            
            zt = model.NewIntVar(0, zone_penalty, f'zt_{v}_{s}')
            model.Add(zt == zone_penalty).OnlyEnforceIf(app)
            model.Add(zt == 0).OnlyEnforceIf(app.Not())
            z_terms.append(zt)
    model.Add(c_zone == sum(z_terms))
    
    # [Defense 2] Waiting Cost (Anti-Idling)
    # Penalize "Arriving Early and Waiting at the Curb"
    # Wait = max(0, ReadyTime - EarliestArrival)
    c_waiting = model.NewIntVar(0, 1000000, 'c_waiting')
    wait_terms = []
    
    for v in VEHICLES:
        for s in range(max_steps - 1):
            # Recalculate 'Earliest Arrival' components (duplicate logic from constraints but needed for cost)
            curr = route[v, s]
            next_n = route[v, s+1]
            idx = model.NewIntVar(0, num_locations**2 - 1, f'widx_{v}_{s}')
            model.Add(idx == curr * num_locations + next_n)
            
            drive_t = model.NewIntVar(0, 1000, f'wdt_{v}_{s}')
            flat_time = [val for row in travel_time for val in row]
            model.AddElement(idx, flat_time, drive_t)
            
            # Re-calc anti-teleport for cost? 
            # We can approximate or just use the simplest 'Earliest' = Arr + Serv + Drive.
            # Anti-teleport affects arrival time, so it reduces waiting!
            # If Earliest = Arr[s] + Serv + Drive + AT.
            # If AT is implemented, it pushes Earliest later, reducing Wait.
            # So we should include AT logic if we want accurate 'Wait'.
            
            # To avoid exploding logic, let's reuse 'arrival_time[v, s+1]'?
            # Arrival[s+1] == max(Ready, Earliest).
            # Wait = Arrival[s+1] - Earliest.
            # This captures strictly the time spent waiting.
            
            # Earliest (Physical) = Arr[s] + Serv + Drive + Rest + Setup + AT
            # We defined this as 'calc_arrival' in the constraint loop.
            # BUT we can't easily access 'calc_arrival' here defined inside a distinct loop scope?
            # Actually we can't.
            
            # Simplified approach:
            # Wait 'gap' = ReadyTime[next] - (Arrival[s] + Service[curr] + Drive).
            # If this is positive, we pay.
            # Ignoring Rest/Setup/AT for the *cost check* makes it strict/conservative.
            # Let's try to include Setup/AT if possible, but Service/Drive is the bulk.
            
            service_t = model.NewIntVar(0, 1000, f'wst_{v}_{s}')
            model.AddElement(curr, service_duration, service_t)
            
            ready_next = model.NewIntVar(0, 10000, f'wrn_{v}_{s}')
            model.AddElement(next_n, ready_time, ready_next)
            
            earliest_simple = model.NewIntVar(0, 10000, f'es_{v}_{s}')
            model.Add(earliest_simple == arrival_time[v, s] + service_t + drive_t)
            
            wait_gap = model.NewIntVar(-10000, 10000, f'wg_{v}_{s}')
            model.Add(wait_gap == ready_next - earliest_simple)
            
            wait_val = model.NewIntVar(0, 10000, f'wv_{v}_{s}')
            model.AddMaxEquality(wait_val, [wait_gap, 0])
            
            term = model.NewIntVar(0, 100000, f'wc_{v}_{s}')
            model.Add(term == wait_val * cost_per_wait_min).OnlyEnforceIf(is_done[v, s+1].Not())
            model.Add(term == 0).OnlyEnforceIf(is_done[v, s+1])
            wait_terms.append(term)
            
    model.Add(c_waiting == sum(wait_terms))

    # =========================================================
    # [FIXED] 6. Re-handling Cost (Dynamic Instant Load Logic)
    # =========================================================
    c_rehandling = model.NewIntVar(0, 1000000, 'c_rehandling')
    rehand_terms = []
    
    # Pairs list caching
    pairs_list = []
    for p in LOCS:
        d = pickup_pair[p]
        if d > 0:
            pairs_list.append((p, d))

    for v in VEHICLES:
        # Load Threshold (70% of Capacity)
        thresh_val = (v_cap_volume[v] * 70) // 100
        
        for (p_curr, d_curr) in pairs_list:
            # 1. Check if Pair is served by Vehicle V
            served_by_v = model.NewBoolVar(f'sbv_{v}_{p_curr}')
            model.Add(visit_vehicle[p_curr] == v + 1).OnlyEnforceIf(served_by_v)
            model.Add(visit_vehicle[p_curr] != v + 1).OnlyEnforceIf(served_by_v.Not())
            
            # 2. Calculate Load at the Moment of Delivery (d_curr)
            # Find load_v[v, s] where s == visit_step[d_curr]
            load_at_drop = model.NewIntVar(0, 2000, f'lad_{v}_{p_curr}')
            
            # Optimization: Only calculate if served by v
            for s in STEPS:
                is_drop_step = model.NewBoolVar(f'ids_{v}_{p_curr}_{s}')
                # Is s the delivery step?
                model.Add(visit_step[d_curr] == s).OnlyEnforceIf(is_drop_step)
                model.Add(visit_step[d_curr] != s).OnlyEnforceIf(is_drop_step.Not())
                
                # Bind load (Only if served_by_v AND is_drop_step)
                # But we need load_at_drop to be defined. 
                # If served_by_v is false, load_at_drop is 0 (default).
                # Logic: load_at_drop == load_v[v, s] IF [served, drop_step].
                model.Add(load_at_drop == load_v[v, s]).OnlyEnforceIf([served_by_v, is_drop_step])
            
            # 3. Check "Instant" Crowding
            is_instantly_crowded = model.NewBoolVar(f'iic_{v}_{p_curr}')
            model.Add(load_at_drop >= thresh_val).OnlyEnforceIf(is_instantly_crowded)
            model.Add(load_at_drop < thresh_val).OnlyEnforceIf(is_instantly_crowded.Not())

            # 4. Check Blockers
            for (p_other, d_other) in pairs_list:
                if p_curr == p_other: continue
                
                # Other served by same vehicle
                other_by_v = model.NewBoolVar(f'obv_{v}_{p_other}')
                model.Add(visit_vehicle[p_other] == v + 1).OnlyEnforceIf(other_by_v)
                model.Add(visit_vehicle[p_other] != v + 1).OnlyEnforceIf(other_by_v.Not())
                
                # LIFO Violation Logic
                # Loaded After (p_other > p_curr)
                la = model.NewBoolVar(f'la_{v}_{p_curr}_{p_other}')
                model.Add(visit_step[p_other] > visit_step[p_curr]).OnlyEnforceIf(la)
                model.Add(visit_step[p_other] <= visit_step[p_curr]).OnlyEnforceIf(la.Not())
                
                # Unloaded After (d_other > d_curr) -> Still on truck
                ua = model.NewBoolVar(f'ua_{v}_{p_curr}_{p_other}')
                model.Add(visit_step[d_other] > visit_step[d_curr]).OnlyEnforceIf(ua)
                model.Add(visit_step[d_other] <= visit_step[d_curr]).OnlyEnforceIf(ua.Not())
                
                # Physically Present (p_other < d_curr) -> Already picked up
                pr = model.NewBoolVar(f'pr_{v}_{p_curr}_{p_other}')
                model.Add(visit_step[p_other] < visit_step[d_curr]).OnlyEnforceIf(pr)
                model.Add(visit_step[p_other] >= visit_step[d_curr]).OnlyEnforceIf(pr.Not())
                
                # [Condition A] Crowded Penalty (High Cost)
                blk_crowded = model.NewBoolVar(f'blkc_{v}_{p_curr}_{p_other}')
                model.AddBoolAnd([
                    served_by_v, other_by_v, la, ua, pr, is_instantly_crowded
                ]).OnlyEnforceIf(blk_crowded)
                model.AddBoolOr([
                    served_by_v.Not(), other_by_v.Not(), la.Not(), ua.Not(), pr.Not(), is_instantly_crowded.Not()
                ]).OnlyEnforceIf(blk_crowded.Not())
                
                # [Condition B] Basic Rehandling (Low Cost)
                blk_basic = model.NewBoolVar(f'blkb_{v}_{p_curr}_{p_other}')
                model.AddBoolAnd([
                    served_by_v, other_by_v, la, ua, pr, is_instantly_crowded.Not()
                ]).OnlyEnforceIf(blk_basic)
                model.AddBoolOr([
                    served_by_v.Not(), other_by_v.Not(), la.Not(), ua.Not(), pr.Not(), is_instantly_crowded
                ]).OnlyEnforceIf(blk_basic.Not())

                vol = demand_volume[p_other]
                
                # Cost Calculation
                term = model.NewIntVar(0, 100000, f'rhT_{v}_{p_curr}_{p_other}')
                
                # Crowded -> Vol * 50
                # Basic -> Vol * 10
                cost_crowded = vol * 50
                cost_basic   = vol * 10 
                
                model.Add(term == cost_crowded).OnlyEnforceIf(blk_crowded)
                model.Add(term == cost_basic).OnlyEnforceIf(blk_basic)
                model.Add(term == 0).OnlyEnforceIf([blk_crowded.Not(), blk_basic.Not()])
                
                rehand_terms.append(term)
            
    model.Add(c_rehandling == sum(rehand_terms))

    total_cost = model.NewIntVar(0, 10000000, 'total_cost')
    # Update total cost with c_waiting
    # [PROPOSAL] Late Cost
    c_late = model.NewIntVar(0, 10000000, 'c_late')
    model.Add(c_late == sum(total_late_penalties) * 50000) # High cost to minimize COUNT
    
    model.Add(total_cost == c_fixed + c_dist + c_time + c_penalty + c_zone + c_rehandling + c_waiting + c_late)
    model.Minimize(total_cost)

    # Solve
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 30.0
    status = solver.Solve(model)

    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        t_cost = solver.Value(total_cost)
        fv = solver.Value(c_fixed)
        dv = solver.Value(c_dist)
        tv = solver.Value(c_time)
        zv = solver.Value(c_zone)
        rh = solver.Value(c_rehandling)
        pv = solver.Value(c_penalty)
        
        print("============================================================")
        print("🚚 VRP FINAL SIMULATION REPORT (LIFO & Overtime) [OR-Tools]")
        print("============================================================")
        print("💰 Total Cost breakdown:")
        print(f"   Total Objective : {t_cost}")
        print("   ----------------------------------------")
        print(f"   1. Fixed Cost   : {fv}")
        print(f"   2. Dist Cost    : {dv}")
        print(f"   3. Labor Cost   : {tv} (OT 1.5x Applied)")
        print(f"   4. Zone Penalty : {zv}")
        print(f"   5. Re-handling  : {rh} (Volumetric LIFO)")
        print(f"   6. Waiting Cost : {solver.Value(c_waiting)} (Anti-Idling)")
        print(f"   7. Miss Penalty : {pv}")
        print(f"   8. Late Penalty : {solver.Value(c_late)} (Count: {solver.Value(c_late)//50000})")
        print("============================================================\n")
        
        print("============================================================")
        print("🔎 LIFO INTERFERENCE DEBUG (Why did I pay?)")
        print("============================================================")
        
        # Re-construct logic to show users
        total_rehand_check = 0
        pairs = []
        for p in LOCS:
            d = pickup_pair[p]
            if d > 0:
                pairs.append((p, d))
                
        for (p_curr, d_curr) in pairs:
            if not solver.Value(is_served[p_curr]): continue
            
            p_step = solver.Value(visit_step[p_curr])
            d_step = solver.Value(visit_step[d_curr])
            veh_curr = solver.Value(visit_vehicle[p_curr])
            
            # Check who blocked me
            blockers = []
            for (p_other, d_other) in pairs:
                if p_curr == p_other: continue
                if not solver.Value(is_served[p_other]): continue
                
                veh_other = solver.Value(visit_vehicle[p_other])
                po_step = solver.Value(visit_step[p_other])
                do_step = solver.Value(visit_step[d_other])
                
                # Logic: Same Vehicle + Loaded After + Unloaded After + Physically Present
                if (veh_curr == veh_other and
                    po_step > p_step and    # Loaded AFTER me (on top)
                    do_step > d_step and    # Unloaded AFTER me (still there)
                    po_step < d_step):      # Picked up BEFORE I was dropped (present)
                    
                    vol = demand_volume[p_other]
                    cost = vol * 50
                    blockers.append(f"   - 📦 Blocked by Pair {p_other}->{d_other} (Vol {vol})")
                    blockers.append(f"     [Timing] Me: {p_step}~{d_step} vs Blocker: {po_step}~{do_step}")
                    blockers.append(f"     [Cost] {vol} * 50 = {cost}")
                    total_rehand_check += cost

            if blockers:
                print(f"🚨 Pair {p_curr}->{d_curr} (Delivering at Step {d_step}) was blocked:")
                for b in blockers:
                    print(b)
        
        print(f"👉 Calculated Total Re-handling: {total_rehand_check}")
        print("============================================================\n")
        
        for v in VEHICLES:
            if solver.Value(is_used[v]):
                print(f"🚛 Vehicle {v + 1} [Type {v_type[v]}]")
                
                final_time = 0
                for s in STEPS:
                    val = solver.Value(arrival_time[v, s])
                    if val > final_time: final_time = val
                work_t = final_time - v_start_window[v]
                over_t = max(0, work_t - standard_work_time)
                
                print(f"   Work Time: {final_time} min (Overtime: {over_t} min)")
                print("   ------------------------------------------------------------")
                
                for s in STEPS:
                    is_d = solver.Value(is_done[v, s])
                    prev_d = solver.Value(is_done[v, s-1]) if s > 0 else False
                    
                    if not is_d or (is_d and not prev_d):
                        loc_idx = solver.Value(route[v, s])
                        w = solver.Value(load_w[v, s])
                        arr = solver.Value(arrival_time[v, s])
                        
                        if loc_idx == DEPOT:
                            if s == 0: loc_str = "🏭 DEPOT (Start)       "
                            else:      loc_str = "🏭 DEPOT (Reload/End)  "
                            time_str = f"Time: {arr:04d}"
                        else:
                            z_val = zone[loc_idx]
                            loc_str = f"📍 Loc {loc_idx + 1:02d} (Zone {z_val})     "
                            
                            # Retrieve Debug Info
                            d_val = solver.Value(debug_due_dates[(v, s)])
                            l_val = solver.Value(debug_is_late[(v, s)])
                            
                            if l_val == 1:
                                time_str = f"Time: {arr:04d} / Due: {d_val:04d} [LATE!]"
                            else:
                                time_str = f"Time: {arr:04d} / Due: {d_val:04d} [OK]"
                        
                        print(f"   Step {s:02d} | {loc_str} | {time_str} | Load: {w:03d}kg")
                print("")
                
        skipped = []
        for c in range(1, num_locations):
            if not solver.Value(is_served[c]):
                skipped.append(c + 1)
        if skipped:
            print(f"⚠️ Skipped: {skipped}")
    else:
        print("No solution found.")

if __name__ == '__main__':
    main()
