"""
Objective Constraints for Stop-based VRP.

Handles all cost components:
- Fixed cost (vehicle usage)
- Distance cost (with load penalty)
- Labor cost (regular + overtime)
- Unserved penalty (per shipment)
- Zone crossing penalty
- Waiting cost
- Late penalty
- Rehandling cost (from LIFO)
"""
from vrp_solver.ortools_solver.wrapper import VRPSolver


class ObjectiveConstraints:
    @staticmethod
    def apply(solver: VRPSolver):
        m = solver.model
        data = solver.data
        cars = solver.variables
        
        num_v = solver.num_vehicles
        max_s = solver.max_steps
        num_loc = solver.num_locations
        num_ships = solver.num_shipments
        
        route = cars['route']
        route_location = cars['route_location']  # Pre-linked via Element in wrapper
        is_used = cars['is_used']
        is_done = cars['is_done']
        arrival_time = cars['arrival_time']
        load_w = cars['load_w']
        is_served = cars['is_served']
        
        # Matrix Helpers
        flat_dist = [d for row in data.travel_dist_matrix for d in row]
        flat_time = [t for row in data.travel_time_matrix for t in row]
        
        penalties = data.penalties
        
        # =====================
        # 1. Fixed Cost
        # =====================
        c_fixed = m.NewIntVar(0, 1000000, 'c_fixed')
        m.Add(c_fixed == sum(is_used[v] * data.vehicles[v].cost.fixed for v in range(num_v)))
        cars['c_fixed'] = c_fixed
        
        # =====================
        # 2. Distance Cost
        # =====================
        c_dist = m.NewIntVar(0, 10000000, 'c_dist')
        dist_terms = []
        
        for v in range(num_v):
            veh_cost = data.vehicles[v].cost
            
            for s in range(max_s - 1):
                # Active edge check
                act_edge = m.NewBoolVar(f'ae_{v}_{s}')
                c1 = is_done[v, s+1].Not()
                c2 = m.NewBoolVar(f'ls_{v}_{s}')
                m.AddBoolAnd([is_done[v, s+1], is_done[v, s].Not()]).OnlyEnforceIf(c2)
                m.AddBoolOr([is_done[v, s+1].Not(), is_done[v, s]]).OnlyEnforceIf(c2.Not())
                m.AddBoolOr([c1, c2]).OnlyEnforceIf(act_edge)
                m.AddBoolAnd([c1.Not(), c2.Not()]).OnlyEnforceIf(act_edge.Not())
                
                # Use route_location for distance lookup
                curr_loc = route_location[v, s]
                next_loc = route_location[v, s+1]
                
                idx = m.NewIntVar(0, num_loc**2 - 1, f'di_{v}_{s}')
                m.Add(idx == curr_loc * num_loc + next_loc)
                
                d_val = m.NewIntVar(0, 1000, f'dist_{v}_{s}')
                m.AddElement(idx, flat_dist, d_val)
                
                w_pen = m.NewIntVar(0, 100000, f'wp_{v}_{s}')
                m.Add(w_pen == load_w[v, s] * veh_cost.per_kg_km)
                
                rate = m.NewIntVar(0, 100000, f'rate_{v}_{s}')
                m.Add(rate == veh_cost.per_km + w_pen)
                
                s_cost = m.NewIntVar(0, 1000000, f'sc_{v}_{s}')
                m.AddMultiplicationEquality(s_cost, [d_val, rate])
                
                term = m.NewIntVar(0, 1000000, f'dterm_{v}_{s}')
                m.Add(term == s_cost).OnlyEnforceIf(act_edge)
                m.Add(term == 0).OnlyEnforceIf(act_edge.Not())
                dist_terms.append(term)
                
        m.Add(c_dist == sum(dist_terms))
        cars['c_dist'] = c_dist
        
        # =====================
        # 3. Labor Cost (Overtime)
        # =====================
        c_time = m.NewIntVar(0, 1000000, 'c_time')
        time_terms = []
        
        for v in range(num_v):
            veh = data.vehicles[v]
            labor = veh.labor
            shift = labor.shift
            labor_cost = labor.cost
            
            max_arr = m.NewIntVar(0, 10000, f'ma_{v}')
            m.AddMaxEquality(max_arr, [arrival_time[v, s] for s in range(max_s)])
            
            tot_work = m.NewIntVar(0, 10000, f'tw_{v}')
            m.Add(tot_work == max_arr - shift.start_time)
            
            reg = m.NewIntVar(0, shift.standard_duration, f'reg_{v}')
            m.AddMinEquality(reg, [tot_work, shift.standard_duration])
            
            diff = m.NewIntVar(-10000, 10000, f'df_{v}')
            m.Add(diff == tot_work - shift.standard_duration)
            over = m.NewIntVar(0, 10000, f'ov_{v}')
            m.AddMaxEquality(over, [diff, 0])
            
            c_r = m.NewIntVar(0, 1000000, f'calc_r_{v}')
            m.Add(c_r == reg * labor_cost.regular_rate)
            
            c_o = m.NewIntVar(0, 1000000, f'calc_o_{v}')
            over_rate = int(labor_cost.regular_rate * labor_cost.overtime_multiplier)
            m.Add(c_o == over * over_rate)
            
            t_term = m.NewIntVar(0, 1000000, f'tt_{v}')
            m.Add(t_term == c_r + c_o)
            time_terms.append(t_term)
            
        m.Add(c_time == sum(time_terms))
        cars['c_time'] = c_time

        # =====================
        # 4. Unserved Penalty (per Shipment!)
        # =====================
        c_penalty = m.NewIntVar(0, 10000000, 'c_penalty')
        pen_terms = []
        
        for ship_idx in range(num_ships):
            ship = data.shipments[ship_idx]
            ns = m.NewIntVar(0, 1, f'ns_{ship_idx}')
            m.Add(ns == 1 - is_served[ship_idx])
            pt = m.NewIntVar(0, ship.unserved_penalty, f'pt_{ship_idx}')
            m.Add(pt == ns * ship.unserved_penalty)
            pen_terms.append(pt)
            
        m.Add(c_penalty == sum(pen_terms))
        cars['c_penalty'] = c_penalty
        
        # =====================
        # 5. Zone Crossing Penalty
        # =====================
        c_zone = m.NewIntVar(0, 1000000, 'c_zone')
        z_terms = []
        stop_zones = solver.stop_zone  # Pre-computed: stop_id -> zone_id
        
        for v in range(num_v):
            for s in range(max_s - 1):
                act_edge = m.NewBoolVar(f'za_{v}_{s}')
                c1 = is_done[v, s+1].Not()
                c2 = m.NewBoolVar(f'zl_{v}_{s}')
                m.AddBoolAnd([is_done[v, s+1], is_done[v, s].Not()]).OnlyEnforceIf(c2)
                m.AddBoolOr([is_done[v, s+1].Not(), is_done[v, s]]).OnlyEnforceIf(c2.Not())
                m.AddBoolOr([c1, c2]).OnlyEnforceIf(act_edge)
                m.AddBoolAnd([c1.Not(), c2.Not()]).OnlyEnforceIf(act_edge.Not())
                
                curr_stop = route[v, s]
                next_stop = route[v, s+1]
                
                zc = m.NewIntVar(0, 10, f'zc_{v}_{s}')
                m.AddElement(curr_stop, stop_zones, zc)
                zn = m.NewIntVar(0, 10, f'zn_{v}_{s}')
                m.AddElement(next_stop, stop_zones, zn)
                
                # Check not at depot (zone 0)
                cnt = m.NewBoolVar(f'cnt_{v}_{s}')
                m.Add(zc != 0).OnlyEnforceIf(cnt)
                m.Add(zc == 0).OnlyEnforceIf(cnt.Not())
                nnt = m.NewBoolVar(f'nnt_{v}_{s}')
                m.Add(zn != 0).OnlyEnforceIf(nnt)
                m.Add(zn == 0).OnlyEnforceIf(nnt.Not())
                
                zd = m.NewBoolVar(f'zd_{v}_{s}')
                m.Add(zc != zn).OnlyEnforceIf(zd)
                m.Add(zc == zn).OnlyEnforceIf(zd.Not())
                
                app = m.NewBoolVar(f'zap_{v}_{s}')
                m.AddBoolAnd([act_edge, cnt, nnt, zd]).OnlyEnforceIf(app)
                m.AddBoolOr([act_edge.Not(), cnt.Not(), nnt.Not(), zd.Not()]).OnlyEnforceIf(app.Not())
                
                zt = m.NewIntVar(0, penalties.zone_crossing, f'zt_{v}_{s}')
                m.Add(zt == penalties.zone_crossing).OnlyEnforceIf(app)
                m.Add(zt == 0).OnlyEnforceIf(app.Not())
                z_terms.append(zt)
                
        m.Add(c_zone == sum(z_terms))
        cars['c_zone'] = c_zone
        
        # =====================
        # 6. Waiting Cost
        # =====================
        c_waiting = m.NewIntVar(0, 1000000, 'c_waiting')
        wait_terms = []
        
        # Build stop_ready from Shipment TimeWindows
        stop_ready = []
        for stop in data.stops:
            if stop.is_depot:
                stop_ready.append(0)  # Depot has no waiting constraint
            elif stop.is_pickup:
                ship = data.shipments[stop.shipment_idx]
                stop_ready.append(ship.pickup_window.start if ship.pickup_window else 0)
            elif stop.is_delivery:
                ship = data.shipments[stop.shipment_idx]
                stop_ready.append(ship.delivery_window.start if ship.delivery_window else 0)
            else:
                stop_ready.append(0)
        
        stop_service = solver.stop_service_duration
        
        for v in range(num_v):
            veh_cost = data.vehicles[v].cost
            
            for s in range(max_s - 1):
                curr_loc = route_location[v, s]
                next_loc = route_location[v, s+1]
                
                idx = m.NewIntVar(0, num_loc**2 - 1, f'widx_{v}_{s}')
                m.Add(idx == curr_loc * num_loc + next_loc)
                
                drive_t = m.NewIntVar(0, 1000, f'wdt_{v}_{s}')
                m.AddElement(idx, flat_time, drive_t)
                
                curr_stop = route[v, s]
                service_t = m.NewIntVar(0, 1000, f'wst_{v}_{s}')
                m.AddElement(curr_stop, stop_service, service_t)
                
                next_stop = route[v, s+1]
                ready_next = m.NewIntVar(0, 10000, f'wrn_{v}_{s}')
                m.AddElement(next_stop, stop_ready, ready_next)
                
                earliest_simple = m.NewIntVar(0, 10000, f'es_{v}_{s}')
                m.Add(earliest_simple == arrival_time[v, s] + service_t + drive_t)
                
                wait_gap = m.NewIntVar(-10000, 10000, f'wg_{v}_{s}')
                m.Add(wait_gap == ready_next - earliest_simple)
                
                wait_val = m.NewIntVar(0, 10000, f'wv_{v}_{s}')
                m.AddMaxEquality(wait_val, [wait_gap, 0])
                
                term = m.NewIntVar(0, 100000, f'wc_{v}_{s}')
                m.Add(term == wait_val * veh_cost.per_wait_minute).OnlyEnforceIf(is_done[v, s+1].Not())
                m.Add(term == 0).OnlyEnforceIf(is_done[v, s+1])
                wait_terms.append(term)
                
        m.Add(c_waiting == sum(wait_terms))
        cars['c_waiting'] = c_waiting
        
        # =====================
        # 7. Late Penalty
        # =====================
        c_late = m.NewIntVar(0, 10000000, 'c_late')
        if 'late_flags' in cars:
            m.Add(c_late == sum(cars['late_flags']) * penalties.late_delivery)
        else:
            m.Add(c_late == 0)
        cars['c_late'] = c_late
        
        # =====================
        # 8. Total Cost & Minimize
        # =====================
        total_cost = m.NewIntVar(0, 100000000, 'total_cost')
        c_rehand = cars.get('c_rehandling', 0)
        
        m.Add(total_cost == c_fixed + c_dist + c_time + c_penalty + c_zone + c_waiting + c_late + c_rehand)
        m.Minimize(total_cost)
        cars['total_cost'] = total_cost
