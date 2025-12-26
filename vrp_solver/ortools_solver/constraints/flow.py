"""
Flow Constraints for Stop-based VRP.

Handles:
- Pickup-Delivery precedence (pickup before delivery)
- Same vehicle for pickup and delivery
- No depot visits while carrying cargo
"""
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
        is_stop_active = cars['is_stop_active']
        route = cars['route']
        
        num_v = solver.num_vehicles
        
        for ship_idx, ship in enumerate(data.shipments):
            p_stop = solver.shipment_pickup_stop[ship_idx]
            d_stop = solver.shipment_delivery_stop[ship_idx]
            
            # 1. Precedence: Pickup before Delivery
            m.Add(visit_step[p_stop] < visit_step[d_stop]).OnlyEnforceIf(is_served[ship_idx])
            
            # 2. Same Vehicle
            m.Add(visit_vehicle[p_stop] == visit_vehicle[d_stop]).OnlyEnforceIf(is_served[ship_idx])
            
            # 3. No depot visits between pickup and delivery
            for v in range(num_v):
                # Is this vehicle handling this shipment?
                carrying = m.NewBoolVar(f'cry_{v}_{ship_idx}')
                # visit_vehicle values are 1-based (v+1)
                m.Add(visit_vehicle[p_stop] == v + 1).OnlyEnforceIf(carrying)
                m.Add(visit_vehicle[p_stop] != v + 1).OnlyEnforceIf(carrying.Not())
                
                # Get depot stops for this vehicle
                start_depot = solver.vehicle_start_stop[v]
                end_depot = solver.vehicle_end_stop[v]
                
                for s in range(solver.max_steps):
                    is_intermediate = m.NewBoolVar(f'inter_{v}_{ship_idx}_{s}')
                    
                    # s > visit_step[p_stop]
                    after_pick = m.NewBoolVar(f'ap_{v}_{ship_idx}_{s}')
                    m.Add(s > visit_step[p_stop]).OnlyEnforceIf(after_pick)
                    m.Add(s <= visit_step[p_stop]).OnlyEnforceIf(after_pick.Not())
                    
                    # s < visit_step[d_stop]
                    before_drop = m.NewBoolVar(f'bd_{v}_{ship_idx}_{s}')
                    m.Add(s < visit_step[d_stop]).OnlyEnforceIf(before_drop)
                    m.Add(s >= visit_step[d_stop]).OnlyEnforceIf(before_drop.Not())
                    
                    m.AddBoolAnd([carrying, after_pick, before_drop]).OnlyEnforceIf(is_intermediate)
                    m.AddBoolOr([carrying.Not(), after_pick.Not(), before_drop.Not()]).OnlyEnforceIf(is_intermediate.Not())
                    
                    # Constraint: Intermediate steps cannot be end depot
                    # (Going back to depot while carrying would unload prematurely)
                    m.Add(route[v, s] != end_depot).OnlyEnforceIf(is_intermediate)
