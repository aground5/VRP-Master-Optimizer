import sys
import os

# Ensure current dir is in path
sys.path.append(os.getcwd())

from vrp_solver.config import VRPConfig
from vrp_solver.logic.data_loader import load_dummy_data
from vrp_solver.ortools_solver.wrapper import VRPSolver
from vrp_solver.ortools_solver.constraints.routing import RoutingConstraints
from vrp_solver.ortools_solver.constraints.time import TimeConstraints
from vrp_solver.ortools_solver.constraints.capacity import CapacityConstraints
from vrp_solver.ortools_solver.constraints.flow import FlowConstraints
from vrp_solver.ortools_solver.constraints.lifo import LifoConstraints
from vrp_solver.ortools_solver.constraints.objectives import ObjectiveConstraints
from vrp_solver.output.printer import print_solution

def main():
    # 1. Config & Data
    config = VRPConfig()
    data = load_dummy_data(config)
    
    # 2. Init Solver
    solver = VRPSolver(data, config)
    solver.create_variables()
    
    # 3. Apply Constraints
    print("Applying Routing Constraints...")
    RoutingConstraints.apply(solver)
    
    print("Applying Time Constraints...")
    TimeConstraints.apply(solver)
    
    print("Applying Capacity Constraints...")
    CapacityConstraints.apply(solver)
    
    print("Applying Flow Constraints...")
    FlowConstraints.apply(solver)
    
    print("Applying LIFO Constraints...")
    LifoConstraints.apply(solver)
    
    print("Applying Objective Constraints...")
    ObjectiveConstraints.apply(solver)
    
    # 4. Solve
    print("Solving...")
    cp_solver, status = solver.solve()
    
    # 5. Output
    print_solution(solver, cp_solver, status)

if __name__ == "__main__":
    main()
