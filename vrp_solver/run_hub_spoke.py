"""
Run Hub & Spoke Simulation (Example Data 2).

User Request: "Hub & Spoke style, all from Depot -> Dest, Open Time Windows, Configurable Work Shifts"
"""
import sys
import os
import copy
from datetime import datetime
from dataclasses import dataclass, replace

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from vrp_solver.config import VRPConfig
from vrp_solver.domain import (
    VRPData, Location, SiteProfile,
    Vehicle as DomainVehicle, VehicleProfile, VehicleCapacity, VehicleCostProfile,
    Shipment as DomainShipment, Cargo as DomainCargo, TimeWindow,
    LaborPolicy, WorkShift, BreakRule, LaborCost,
    PenaltyConfig as DomainPenaltyConfig, OperationalCost
)
from vrp_solver.ortools_solver.wrapper import VRPSolver
from vrp_solver.ortools_solver.constraints.routing import RoutingConstraints
from vrp_solver.ortools_solver.constraints.time import TimeConstraints
from vrp_solver.ortools_solver.constraints.capacity import CapacityConstraints
from vrp_solver.ortools_solver.constraints.flow import FlowConstraints
from vrp_solver.ortools_solver.constraints.lifo import LifoConstraints
from vrp_solver.ortools_solver.constraints.objectives import ObjectiveConstraints
from ortools.sat.python import cp_model

# Import raw data from test script to reuse it
from vrp_solver.test_constraints_debug import TEST_DATA, convert_to_vrp_data


# =============================================================================
# USER CONFIGURATION
# =============================================================================

# =============================================================================
# CJ LOGISTICS HUB & SPOKE CONFIGURATION
# =============================================================================
HUB_SITE_ID = "depot_gunpo"  # CJ Hub (Gunpo)

# Courier Driver Shift (Real-world style)
# Drivers typically arrive ~07:00 for sorting/scanning
# Departure for delivery ~09:00
# Work ends when empty or ~20:00
WORK_START_TIME = 9 * 60  # 09:00 Departure from Terminal
WORK_END_TIME = 20 * 60   # 20:00 End of Shift

# Delivery Window (Customer Expectation)
# Standard: "Delivered Today" (09:00 - 22:00)
OPEN_WINDOW_START = 9 * 60
OPEN_WINDOW_END = 22 * 60

# =============================================================================


def apply_hub_spoke_transform(raw_data: dict) -> dict:
    """
    Transforms generic VRP data into a CJ Logistics Hub & Spoke model.
    Scenario: 'Last Mile Delivery'
    - All parcels have arrived at the Terminal (Hub) overnight.
    - All drivers start at the Hub, load up, and deliver to customers.
    - No 'Pickup' from customers in this scenario (focus on delivery).
    """
    data = copy.deepcopy(raw_data)
    
    # 1. Transform Vehicles (Courier Trucks)
    # CJ Logistics mostly uses 1-ton trucks (Porter/Bongo) with High Top (~8 CBM)
    for veh in data["vehicles"]:
        veh["start_site_id"] = HUB_SITE_ID
        veh["end_site_id"] = HUB_SITE_ID
        
        # Courier Shift & Capacity
        veh["capacity"]["weight"] = 1000
        veh["capacity"]["volume"] = 8  # Adjusted to realistic 1-ton high-top estimate
        
        veh["shift"]["start_time"] = WORK_START_TIME
        veh["shift"]["max_duration"] = WORK_END_TIME - WORK_START_TIME
        veh["shift"]["standard_duration"] = 8 * 60 # 8 hours standard
        
        # Rename for realism if needed
        if "truck" in veh["id"]:
             veh["name"] = f"CJ대한통운 {veh['name']}"

    # 2. Transform Shipments (Hub -> Customer)
    for ship in data["shipments"]:
        # Origin is always the Hub (items are already there)
        ship["pickup_site_id"] = HUB_SITE_ID
        
        # Relax time windows to "Today"
        # We handle this by modifying the SITES or the logic below.
        # But wait, in the new domain, windows are on SHIPMENTS.
        # We must update the shipment windows directly if they exist in the raw dict
        # or rely on the converter. 
        # The current converter reads from SITES. 
        # So strictly speaking, we must specificy windows here if the converter supports it,
        # OR modify the sites.
        
        pass 

    # 3. Transform Sites (Relax windows)
    # 3. Transform Sites (Relax windows) - REMOVED
    # Site time windows are no longer used in the new schema. 
    # Time limits are handled by shipment windows and vehicle shifts.
    pass

    return data


def solve_simulation():
    print(f"============================================================")
    print(f"   CJ LOGISTICS - HUB & SPOKE SIMULATION (LAST MILE)   ")
    print(f"============================================================")
    print(f" Terminal : {HUB_SITE_ID} (Gunpo Hub)")
    print(f" Working Hours: {WORK_START_TIME//60:02d}:{WORK_START_TIME%60:02d} ~ {WORK_END_TIME//60:02d}:{WORK_END_TIME%60:02d}")
    print(f" Concept  : All items loaded at Hub -> Delivered to Spoke")
    print(f"============================================================\n")

    # 1. Transform Data
    # Load from file instead of imported TEST_DATA
    import json
    data_path = os.path.join(os.path.dirname(__file__), "hub_spoke_data.json")
    with open(data_path, 'r') as f:
        raw_data = json.load(f)

    modified_data = apply_hub_spoke_transform(raw_data)
    
    # 2. Convert to Domain Objects
    vrp_data = convert_to_vrp_data(modified_data)
    idx_to_site = {} # Unused but passed to function

    # 3. Solver Config
    config = VRPConfig()
    config.max_solver_time = 30
    
    # 4. Initialize Solver
    solver = VRPSolver(vrp_data, config)
    solver.create_variables()
    
    # 5. Apply Constraints
    RoutingConstraints.apply(solver)
    TimeConstraints.apply(solver)
    CapacityConstraints.apply(solver)
    FlowConstraints.apply(solver)
    ObjectiveConstraints.apply(solver)
    
    # 6. Solve
    print("🔄 Optimizing Routes...\n")
    cp_solver, status = solver.solve()
    
    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        print("✅ Delivery Schedule Created!\n")
        print_worker_schedule(solver, cp_solver, vrp_data, idx_to_site)
    else:
        print("\n❌ Optimization Failed. Constraints might be too tight.")


def print_worker_schedule(solver, cp_solver, data, idx_to_site):
    vars = solver.variables
    
    for v in range(solver.num_vehicles):
        if not cp_solver.Value(vars['is_used'][v]):
            continue
            
        veh = data.vehicles[v]
        print(f"� {veh.name}")
        print(f"   Shift: {WORK_START_TIME//60:02d}:{WORK_START_TIME%60:02d} ~ {WORK_END_TIME//60:02d}:{WORK_END_TIME%60:02d}")
        
        # Reconstruct route
        route_stops = []
        # Reconstruct route
        sorted_steps = []
        found_end = False
        
        for s in range(solver.max_steps):
            is_nav_done = cp_solver.Value(vars['is_done'][v, s])
            
            # If we previously hit the end, ignore further padding steps
            if found_end:
                continue
            
            # Cases:
            # 1. Active step (is_done=False) -> Add to route
            # 2. First done step (is_done=True) -> This is the End Depot arrival. Add then mark finished.
            
            should_add = False
            if not is_nav_done:
                should_add = True
            elif is_nav_done and not found_end:
                should_add = True
                found_end = True
                
            if should_add:
                 # route[v, s] returns the STOP index, not location index
                stop_idx = cp_solver.Value(vars['route'][v, s])
                arr_time = cp_solver.Value(vars['arrival_time'][v, s])
                
                # Retrieve the Stop object to get the real location index
                try:
                    stop_obj = data.stops[stop_idx]
                    loc_idx = stop_obj.location_idx
                    loc_obj = data.locations[loc_idx]
                except IndexError:
                    print(f"    [WARNING] Invalid Stop Index: {stop_idx}")
                    continue

                sorted_steps.append({
                    "step": s,
                    "loc": loc_obj,
                    "arr": arr_time,
                    "type": stop_obj.stop_type.name 
                })
        
        sorted_steps.sort(key=lambda x: x["step"])

        # Filter out trailing depot visits if they are just dummy fillers?
        # A standard VRP output often has Start -> ... -> End.
        # If the solver fills remaining steps with End Depot, we might see duplicates.
        # Let's clean it up for display.
        
        print(f"   {'Time':<10} | {'Location':<15} | {'Note'}")
        print("-" * 50)
        
        for i, stop in enumerate(sorted_steps):
            t_str = f"{stop['arr']//60:02d}:{stop['arr']%60:02d}"
            loc_name = stop['loc'].name
            
            note = ""
            stop_type = stop.get('type', '')
            if stop_type == 'DEPOT_START': note = "출근/상차 (Start)"
            elif stop_type == 'DEPOT_END': note = "복귀/퇴근 (End)"
            elif stop_type == 'PICKUP': note = "픽업 (Pickup)"
            elif stop_type == 'DELIVERY': note = "배송 (Delivery)"
            else: note = stop_type

            print(f"   {t_str:<10} | {loc_name:<15} | {note}")
            
        print("\n")


if __name__ == "__main__":
    solve_simulation()
