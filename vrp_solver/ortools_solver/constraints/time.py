from vrp_solver.ortools_solver.wrapper import VRPSolver

class TimeConstraints:
    @staticmethod
    def apply(solver: VRPSolver):
        m = solver.model
        data = solver.data
        cars = solver.variables
        
        num_v = solver.num_vehicles
        max_s = solver.max_steps
        num_loc = solver.num_locations
        
        route = cars['route']
        arrival_time = cars['arrival_time']
        is_done = cars['is_done']
        
        # Data flattening for AddElement
        flat_time = [t for row in data.travel_time_matrix for t in row]
        flat_setup = [t for row in data.setup_time_matrix for t in row]
        serv_dur = [loc.service_duration for loc in data.locations]
        ready_t = [loc.start_window for loc in data.locations]
        due_t = [loc.end_window for loc in data.locations]
        
        cars['late_flags'] = []
        cars['debug_due_dates'] = {}
        cars['debug_is_late'] = {}
        
        DEPOT = 0
        
        # Global operational costs from data.operations
        depot_min_service = data.operations.depot_service_time
        min_intra = data.operations.min_intra_transit
        
        for v in range(num_v):
            veh = data.vehicles[v]
            
            # Labor policy from vehicle
            labor = veh.labor
            break_rule = labor.break_rule
            shift = labor.shift
            
            # Initial Arrival
            m.Add(arrival_time[v, 0] == shift.start_time)
            
            for s in range(max_s - 1):
                curr_n = route[v, s]
                next_n = route[v, s+1]
                
                # Index for Matrix
                idx = m.NewIntVar(0, num_loc**2-1, f'idx_{v}_{s}')
                m.Add(idx == curr_n * num_loc + next_n)
                
                # Components
                drive_val = m.NewIntVar(0, 1000, f'dt_{v}_{s}')
                m.AddElement(idx, flat_time, drive_val)
                
                setup_val = m.NewIntVar(0, 1000, f'st_{v}_{s}')
                m.AddElement(idx, flat_setup, setup_val)
                
                service_val = m.NewIntVar(0, 1000, f'sert_{v}_{s}')
                m.AddElement(curr_n, serv_dur, service_val)
                
                # --- Anti-Teleport & Depot Service ---
                anti_teleport_t = m.NewIntVar(0, 100, f'att_{v}_{s}')
                
                from_depot = m.NewBoolVar(f'fd_{v}_{s}')
                stay_spot  = m.NewBoolVar(f'ss_{v}_{s}')
                is_curr_depot = m.NewBoolVar(f'id_{v}_{s}')
                
                m.Add(curr_n == DEPOT).OnlyEnforceIf(is_curr_depot)
                m.Add(curr_n != DEPOT).OnlyEnforceIf(is_curr_depot.Not())
                
                next_is_depot_check = m.NewBoolVar(f'nidc_{v}_{s}')
                m.Add(next_n == DEPOT).OnlyEnforceIf(next_is_depot_check)
                m.Add(next_n != DEPOT).OnlyEnforceIf(next_is_depot_check.Not())
                
                m.AddBoolAnd([is_curr_depot, next_is_depot_check.Not()]).OnlyEnforceIf(from_depot)
                m.AddBoolOr([is_curr_depot.Not(), next_is_depot_check]).OnlyEnforceIf(from_depot.Not())
                
                same_loc = m.NewBoolVar(f'sl_{v}_{s}')
                m.Add(curr_n == next_n).OnlyEnforceIf(same_loc)
                m.Add(curr_n != next_n).OnlyEnforceIf(same_loc.Not())
                
                m.AddBoolAnd([is_curr_depot.Not(), same_loc]).OnlyEnforceIf(stay_spot)
                m.AddBoolOr([is_curr_depot, same_loc.Not()]).OnlyEnforceIf(stay_spot.Not())
                
                m.Add(anti_teleport_t == depot_min_service).OnlyEnforceIf(from_depot)
                m.Add(anti_teleport_t == min_intra).OnlyEnforceIf(stay_spot)
                m.Add(anti_teleport_t == 0).OnlyEnforceIf([from_depot.Not(), stay_spot.Not()])
                
                # --- Rest (Break) ---
                rest_t = m.NewIntVar(0, break_rule.duration_minutes, f'rt_{v}_{s}')
                long_drive = m.NewBoolVar(f'ld_{v}_{s}')
                m.Add(drive_val > break_rule.interval_minutes).OnlyEnforceIf(long_drive)
                m.Add(drive_val <= break_rule.interval_minutes).OnlyEnforceIf(long_drive.Not())
                m.Add(rest_t == break_rule.duration_minutes).OnlyEnforceIf(long_drive)
                m.Add(rest_t == 0).OnlyEnforceIf(long_drive.Not())
                
                # --- Calc Arrival ---
                arr_cand = m.NewIntVar(0, 10000, f'ac_{v}_{s}')
                next_ready_val = m.NewIntVar(0, 10000, f'nr_{v}_{s}')
                m.AddElement(next_n, ready_t, next_ready_val)
                
                calc_arrival = m.NewIntVar(0, 10000, f'ca_{v}_{s}')
                m.Add(calc_arrival == arrival_time[v, s] + service_val + drive_val + rest_t + setup_val + anti_teleport_t)
                
                m.AddMaxEquality(arr_cand, [next_ready_val, calc_arrival])
                
                m.Add(arrival_time[v, s+1] == arrival_time[v, s]).OnlyEnforceIf(is_done[v, s+1])
                m.Add(arrival_time[v, s+1] == arr_cand).OnlyEnforceIf(is_done[v, s+1].Not())
            
            # Validity Check Loop
            for s in range(max_s):
                # Max Work Time from labor shift
                m.Add(arrival_time[v, s] - shift.start_time <= shift.max_duration)
                
                # Late Logic
                loc = route[v, s]
                active_node = m.NewBoolVar(f'an_{v}_{s}')
                loc_depot = m.NewBoolVar(f'ldp_{v}_{s}')
                m.Add(loc == DEPOT).OnlyEnforceIf(loc_depot)
                m.Add(loc != DEPOT).OnlyEnforceIf(loc_depot.Not())
                
                m.AddBoolAnd([is_done[v, s].Not(), loc_depot.Not()]).OnlyEnforceIf(active_node)
                m.AddBoolOr([is_done[v, s], loc_depot]).OnlyEnforceIf(active_node.Not())
                
                loc_due = m.NewIntVar(0, 10000, f'ldu_{v}_{s}')
                m.AddElement(loc, due_t, loc_due)
                
                step_late = m.NewBoolVar(f'sl_{v}_{s}')
                safe_due = m.NewIntVar(0, 10000, f'sd_{v}_{s}')
                m.Add(safe_due == loc_due + 30)
                
                shift_end = shift.max_duration
                limit_diff = m.NewIntVar(-10000, 10000, f'ldiff_{v}_{s}')
                m.Add(limit_diff == shift_end - safe_due)
                
                penalty_boost = m.NewIntVar(-10000, 10000, f'pb_{v}_{s}')
                m.AddMultiplicationEquality(penalty_boost, [limit_diff, step_late])
                
                final_due = m.NewIntVar(0, 10000, f'fd_{v}_{s}')
                m.Add(final_due == safe_due + penalty_boost)
                
                m.Add(arrival_time[v, s] <= final_due).OnlyEnforceIf(active_node)
                
                m.Add(step_late == 0).OnlyEnforceIf(active_node.Not())
                
                cars['late_flags'].append(step_late)
                cars['debug_due_dates'][(v, s)] = final_due
                cars['debug_is_late'][(v, s)] = step_late
