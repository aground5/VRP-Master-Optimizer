from ortools.sat.python import cp_model
from typing import Dict, Any, List
from vrp_solver.domain import VRPData
from vrp_solver.config import VRPConfig

class VRPSolver:
    def __init__(self, data: VRPData, config: VRPConfig):
        self.data = data
        self.config = config
        self.model = cp_model.CpModel()
        self.variables: Dict[str, Any] = {}
        
        # Dimensions
        self.num_vehicles = len(data.vehicles)
        self.num_locations = len(data.locations)
        # Heuristic for max steps: Enough for all nodes + buffer
        self.max_steps = 20 

    def create_variables(self):
        """Initializes all CP variables."""
        m = self.model
        num_v = self.num_vehicles
        num_loc = self.num_locations
        max_s = self.max_steps
        
        # 1. Routing Variables
        route = {}
        arrival_time = {}
        load_w = {}
        load_v = {}
        is_done = {}
        
        for v in range(num_v):
            for s in range(max_s):
                route[v, s] = m.NewIntVar(0, num_loc - 1, f'route_{v}_{s}')
                arrival_time[v, s] = m.NewIntVar(0, 10000, f'arr_{v}_{s}')
                load_w[v, s] = m.NewIntVar(0, 2000, f'lw_{v}_{s}')
                load_v[v, s] = m.NewIntVar(0, 2000, f'lv_{v}_{s}')
                is_done[v, s] = m.NewBoolVar(f'done_{v}_{s}')
        
        self.variables['route'] = route
        self.variables['arrival_time'] = arrival_time
        self.variables['load_w'] = load_w
        self.variables['load_v'] = load_v
        self.variables['is_done'] = is_done
        
        # 2. Vehicle Usage
        is_used = {}
        for v in range(num_v):
            is_used[v] = m.NewBoolVar(f'used_{v}')
        self.variables['is_used'] = is_used
        
        # 3. Location Visit State
        is_served = {}
        visit_step = {}
        visit_vehicle = {} 
        
        for c in range(num_loc):
            is_served[c] = m.NewBoolVar(f'served_{c}')
            visit_step[c] = m.NewIntVar(0, max_s, f'v_step_{c}')
            # 0 means not visited, 1..num_v means visited by (v-1)
            visit_vehicle[c] = m.NewIntVar(0, num_v, f'v_veh_{c}')
            
        self.variables['is_served'] = is_served
        self.variables['visit_step'] = visit_step
        self.variables['visit_vehicle'] = visit_vehicle
        
        # 4. Objective Components (to be populated by constraints)
        self.variables['cost_terms'] = []
        
        return self.variables

    def solve(self):
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = self.config.max_solver_time
        status = solver.Solve(self.model)
        return solver, status
