"""
Debug which constraint causes infeasibility.
"""
import sys
import os
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

# Minimal test data - just 2 shipments
TEST_DATA = {
    "sites": [
        {"id": "depot_gunpo", "name": "CJ 군포센터", "type": "depot", "coords": {"lat": 37.3616, "lng": 126.9352}, "time_window": {"start": 0, "end": 720}, "service_duration": 0, "zone_id": 0},
        {"id": "depot_icheon", "name": "CJ 이천센터", "type": "depot", "coords": {"lat": 37.272, "lng": 127.435}, "time_window": {"start": 0, "end": 720}, "service_duration": 0, "zone_id": 0},
        {"id": "site_gangnam", "name": "강남역", "type": "customer", "coords": {"lat": 37.4979, "lng": 127.0276}, "time_window": {"start": 60, "end": 180}, "service_duration": 10, "zone_id": 1},
        {"id": "site_seocho", "name": "서초동", "type": "customer", "coords": {"lat": 37.4837, "lng": 127.0324}, "time_window": {"start": 90, "end": 210}, "service_duration": 10, "zone_id": 1},
        {"id": "site_yangjae", "name": "양재역", "type": "customer", "coords": {"lat": 37.4846, "lng": 127.0344}, "time_window": {"start": 60, "end": 240}, "service_duration": 10, "zone_id": 1},
        {"id": "site_jamsil", "name": "잠실역", "type": "customer", "coords": {"lat": 37.5133, "lng": 127.1001}, "time_window": {"start": 120, "end": 300}, "service_duration": 15, "zone_id": 2},
        {"id": "site_olympic", "name": "올림픽공원", "type": "customer", "coords": {"lat": 37.5209, "lng": 127.1215}, "time_window": {"start": 90, "end": 270}, "service_duration": 10, "zone_id": 2},
        {"id": "site_garak", "name": "가락시장", "type": "customer", "coords": {"lat": 37.4925, "lng": 127.118}, "time_window": {"start": 60, "end": 180}, "service_duration": 20, "zone_id": 2},
        {"id": "site_yeouido", "name": "여의도", "type": "customer", "coords": {"lat": 37.5219, "lng": 126.9245}, "time_window": {"start": 90, "end": 240}, "service_duration": 10, "zone_id": 3},
        {"id": "site_hongdae", "name": "홍대입구", "type": "customer", "coords": {"lat": 37.5563, "lng": 126.9237}, "time_window": {"start": 120, "end": 360}, "service_duration": 15, "zone_id": 3},
        {"id": "site_mapo", "name": "마포구청", "type": "customer", "coords": {"lat": 37.5663, "lng": 126.9014}, "time_window": {"start": 60, "end": 300}, "service_duration": 10, "zone_id": 3},
        {"id": "site_jongno", "name": "종로3가", "type": "customer", "coords": {"lat": 37.5714, "lng": 126.992}, "time_window": {"start": 90, "end": 270}, "service_duration": 10, "zone_id": 4},
        {"id": "site_myeongdong", "name": "명동", "type": "customer", "coords": {"lat": 37.5636, "lng": 126.9869}, "time_window": {"start": 120, "end": 300}, "service_duration": 15, "zone_id": 4},
        {"id": "site_seoul_st", "name": "서울역", "type": "customer", "coords": {"lat": 37.5547, "lng": 126.9707}, "time_window": {"start": 60, "end": 360}, "service_duration": 10, "zone_id": 4},
        {"id": "site_nowon", "name": "노원역", "type": "customer", "coords": {"lat": 37.6554, "lng": 127.0614}, "time_window": {"start": 90, "end": 240}, "service_duration": 10, "zone_id": 5},
        {"id": "site_suyu", "name": "수유역", "type": "customer", "coords": {"lat": 37.6377, "lng": 127.0252}, "time_window": {"start": 60, "end": 210}, "service_duration": 10, "zone_id": 5}
    ],
    "vehicles": [
        {"id": "truck_1", "name": "1호차 (소형)", "start_site_id": "depot_gunpo", "end_site_id": "depot_gunpo", "capacity": {"weight": 30, "volume": 30}, "cost": {"fixed": 300, "per_km": 8, "per_minute": 8}, "shift": {"start_time": 0, "max_duration": 600, "standard_duration": 480}, "break_rule": {"interval_minutes": 240, "duration_minutes": 30}, "tags": []},
        {"id": "truck_2", "name": "2호차 (소형)", "start_site_id": "depot_gunpo", "end_site_id": "depot_gunpo", "capacity": {"weight": 30, "volume": 30}, "cost": {"fixed": 300, "per_km": 8, "per_minute": 8}, "shift": {"start_time": 0, "max_duration": 600, "standard_duration": 480}, "break_rule": {"interval_minutes": 240, "duration_minutes": 30}, "tags": []},
        {"id": "truck_3", "name": "3호차 (대형)", "start_site_id": "depot_icheon", "end_site_id": "depot_icheon", "capacity": {"weight": 80, "volume": 80}, "cost": {"fixed": 800, "per_km": 15, "per_minute": 12}, "shift": {"start_time": 0, "max_duration": 720, "standard_duration": 480}, "break_rule": {"interval_minutes": 240, "duration_minutes": 30}, "tags": ["heavy"]},
        {"id": "truck_4", "name": "4호차 (대형)", "start_site_id": "depot_icheon", "end_site_id": "depot_icheon", "capacity": {"weight": 80, "volume": 80}, "cost": {"fixed": 800, "per_km": 15, "per_minute": 12}, "shift": {"start_time": 0, "max_duration": 720, "standard_duration": 480}, "break_rule": {"interval_minutes": 240, "duration_minutes": 30}, "tags": ["heavy"]}
    ],
    "shipments": [
        {"id": "ship_1", "name": "주문 1 (강남→잠실)", "pickup_site_id": "site_gangnam", "delivery_site_id": "site_jamsil", "cargo": {"weight": 10, "volume": 10}, "required_tags": [], "priority": 1},
        {"id": "ship_2", "name": "주문 2 (서초→올림픽)", "pickup_site_id": "site_seocho", "delivery_site_id": "site_olympic", "cargo": {"weight": 15, "volume": 12}, "required_tags": [], "priority": 1},
        {"id": "ship_3", "name": "주문 3 (양재→가락)", "pickup_site_id": "site_yangjae", "delivery_site_id": "site_garak", "cargo": {"weight": 8, "volume": 8}, "required_tags": [], "priority": 2},
        {"id": "ship_4", "name": "주문 4 (여의도→홍대)", "pickup_site_id": "site_yeouido", "delivery_site_id": "site_hongdae", "cargo": {"weight": 5, "volume": 5}, "required_tags": [], "priority": 1},
        {"id": "ship_5", "name": "주문 5 (마포→종로)", "pickup_site_id": "site_mapo", "delivery_site_id": "site_jongno", "cargo": {"weight": 12, "volume": 10}, "required_tags": [], "priority": 1},
        {"id": "ship_6", "name": "주문 6 (명동→서울역)", "pickup_site_id": "site_myeongdong", "delivery_site_id": "site_seoul_st", "cargo": {"weight": 6, "volume": 6}, "required_tags": [], "priority": 1},
        {"id": "ship_7", "name": "주문 7 (노원→수유)", "pickup_site_id": "site_nowon", "delivery_site_id": "site_suyu", "cargo": {"weight": 20, "volume": 18}, "required_tags": ["heavy"], "priority": 1},
        {"id": "ship_8", "name": "주문 8 (잠실→강남)", "pickup_site_id": "site_jamsil", "delivery_site_id": "site_gangnam", "cargo": {"weight": 7, "volume": 7}, "required_tags": [], "priority": 2}
    ],
    "durations": [
        [0, 55, 21, 21, 21, 26, 29, 25, 27, 31, 31, 30, 29, 28, 40, 38],
        [56, 0, 53, 52, 51, 48, 50, 45, 64, 67, 69, 61, 62, 63, 60, 63],
        [21, 50, 0, 4, 4, 7, 11, 10, 13, 16, 18, 10, 10, 12, 21, 18],
        [20, 50, 4, 0, 3, 9, 13, 10, 16, 19, 21, 13, 13, 15, 23, 20],
        [20, 49, 4, 2, 0, 9, 13, 10, 14, 17, 19, 13, 13, 13, 23, 20],
        [25, 46, 7, 9, 7, 0, 5, 4, 17, 20, 22, 14, 15, 16, 19, 19],
        [29, 48, 11, 13, 12, 5, 0, 7, 21, 24, 26, 18, 19, 20, 22, 22],
        [25, 43, 10, 10, 9, 4, 6, 0, 20, 23, 25, 17, 18, 19, 22, 22],
        [26, 63, 14, 16, 17, 20, 24, 22, 0, 7, 9, 10, 10, 7, 24, 20],
        [31, 64, 15, 18, 18, 22, 26, 24, 7, 0, 5, 9, 9, 7, 22, 18],
        [30, 66, 18, 20, 21, 24, 28, 27, 8, 4, 0, 11, 12, 10, 23, 19],
        [30, 57, 10, 13, 13, 16, 20, 18, 11, 9, 11, 0, 3, 6, 14, 10],
        [29, 57, 9, 13, 12, 16, 20, 19, 10, 9, 11, 3, 0, 5, 16, 12],
        [28, 60, 12, 14, 15, 18, 22, 21, 7, 7, 9, 5, 5, 0, 18, 14],
        [39, 56, 21, 23, 22, 18, 22, 21, 24, 22, 23, 15, 16, 19, 0, 5],
        [37, 58, 18, 20, 19, 18, 22, 21, 19, 18, 18, 10, 12, 15, 6, 0]
    ],
    "distances": [
        [0, 56451, 20690, 20102, 20418, 25782, 27705, 25308, 25707, 29715, 28304, 29086, 27815, 27391, 40947, 37654],
        [57715, 0, 52744, 53162, 51031, 47982, 54812, 45207, 66277, 67468, 70164, 61190, 61438, 63066, 67053, 69197],
        [20668, 50271, 0, 2268, 3259, 6756, 9441, 9554, 12406, 13169, 15596, 9509, 9024, 9847, 20658, 17002],
        [20069, 49111, 2139, 0, 1778, 7570, 10255, 8888, 14092, 15611, 18038, 11581, 11096, 12288, 22734, 19014],
        [20408, 49436, 2306, 794, 0, 7894, 10579, 9213, 13739, 15257, 17684, 11748, 11263, 11935, 23059, 19339],
        [25760, 46403, 6739, 7789, 6994, 0, 2787, 2900, 18972, 20163, 22859, 13885, 14133, 15761, 17364, 18912],
        [28419, 54269, 9397, 10447, 9653, 2658, 0, 4428, 21630, 22821, 25518, 16543, 16791, 18420, 19721, 20132],
        [25422, 43598, 9656, 9193, 8398, 2916, 3875, 0, 21889, 23080, 25776, 16802, 17050, 18678, 20178, 21263],
        [26951, 63573, 13907, 14239, 15548, 19648, 22333, 22445, 0, 6031, 7492, 9155, 8569, 6387, 22189, 18731],
        [29457, 72286, 13038, 15175, 16303, 19654, 22339, 22452, 5943, 0, 2957, 7175, 6927, 5182, 20164, 16706],
        [28181, 74603, 15541, 18743, 18807, 24152, 26837, 26950, 7424, 2955, 0, 10027, 9654, 7909, 22033, 17069],
        [30465, 64967, 9496, 12138, 12162, 13588, 16273, 16386, 9497, 7605, 10019, 0, 1428, 4514, 13346, 9888],
        [29542, 65631, 8574, 11216, 11839, 15190, 17875, 17988, 9376, 6764, 9461, 1373, 0, 3759, 14442, 10983],
        [27061, 68264, 10680, 12116, 13945, 17296, 19981, 20094, 5942, 5245, 7941, 4006, 2809, 0, 17075, 13617],
        [40952, 64778, 20641, 22961, 22166, 17356, 19804, 20154, 23135, 21243, 21143, 13838, 15066, 18152, 0, 4235],
        [37801, 67227, 17057, 19180, 18385, 17669, 20118, 20467, 18900, 17008, 16908, 9603, 10831, 13917, 4413, 0]
    ],
    "penalties": {"unserved": 500000, "late_delivery": 50000, "zone_crossing": 2000},
    "max_solver_time": 30
}


def convert_to_vrp_data(data: dict) -> VRPData:
    """Convert raw dict to VRPData domain object."""
    sites = data["sites"]
    vehicles = data["vehicles"]
    shipments = data["shipments"]
    
    site_id_to_idx = {site["id"]: i for i, site in enumerate(sites)}
    
    locations = []
    for i, site in enumerate(sites):
        loc = Location(
            id=i,
            name=site["name"],
            service_duration=site["service_duration"],
            zone_id=site["zone_id"],
            profile=SiteProfile(),
            x=site["coords"]["lng"],
            y=site["coords"]["lat"]
        )
        locations.append(loc)
    
    domain_vehicles = []
    for i, veh in enumerate(vehicles):
        start_idx = site_id_to_idx.get(veh["start_site_id"], 0)
        end_idx = site_id_to_idx.get(veh["end_site_id"], 0)
        
        domain_veh = DomainVehicle(
            id=i,
            name=veh["name"],
            start_loc=start_idx,
            end_loc=end_idx,
            profile=VehicleProfile(
                type_id=1,
                capacity=VehicleCapacity(
                    weight=veh["capacity"]["weight"],
                    volume=veh["capacity"]["volume"]
                ),
                tags=veh.get("tags", [])
            ),
            cost=VehicleCostProfile(
                fixed=veh["cost"]["fixed"],
                per_km=veh["cost"]["per_km"],
                per_minute=veh["cost"]["per_minute"],
                per_kg_km=1,
                per_wait_minute=5
            ),
            labor=LaborPolicy(
                shift=WorkShift(
                    start_time=veh["shift"]["start_time"],
                    max_duration=veh["shift"]["max_duration"],
                    standard_duration=veh["shift"]["standard_duration"]
                ),
                break_rule=BreakRule(
                    interval_minutes=veh["break_rule"]["interval_minutes"],
                    duration_minutes=veh["break_rule"]["duration_minutes"]
                ),
                cost=LaborCost(regular_rate=veh["cost"]["per_minute"], overtime_multiplier=1.5)
            )
        )
        domain_vehicles.append(domain_veh)
    
    domain_shipments = []
    for i, ship in enumerate(shipments):
        pickup_idx = site_id_to_idx.get(ship["pickup_site_id"])
        delivery_idx = site_id_to_idx.get(ship["delivery_site_id"])
        
        pickup_site = sites[pickup_idx]
        delivery_site = sites[delivery_idx]
        
        domain_ship = DomainShipment(
            id=i,
            name=ship["name"],
            pickup_id=pickup_idx,
            delivery_id=delivery_idx,
            cargo=DomainCargo(
                weight=ship["cargo"]["weight"],
                volume=ship["cargo"]["volume"]
            ),
            pickup_window=TimeWindow(
                start=0,
                end=24*60
            ),
            delivery_window=TimeWindow(
                start=0,
                end=24*60
            ),
            required_tags=ship.get("required_tags", []),
            priority=ship["priority"],
            unserved_penalty=data["penalties"]["unserved"]
        )
        domain_shipments.append(domain_ship)
    
    travel_time = data["durations"]
    travel_dist = [[d // 1000 for d in row] for row in data["distances"]]
    setup_time = [[0] * len(locations) for _ in range(len(locations))]
    
    penalties = DomainPenaltyConfig(
        unserved=data["penalties"]["unserved"],
        late_delivery=data["penalties"]["late_delivery"],
        zone_crossing=data["penalties"]["zone_crossing"]
    )
    
    operations = OperationalCost(depot_service_time=30, min_intra_transit=5)

    # NEW: Build stops
    from vrp_solver.logic.data_loader import build_stops
    stops = build_stops(domain_vehicles, domain_shipments)
    
    return VRPData(
        locations=locations,
        vehicles=domain_vehicles,
        shipments=domain_shipments,
        stops=stops,
        travel_time_matrix=travel_time,
        travel_dist_matrix=travel_dist,
        setup_time_matrix=setup_time,
        penalties=penalties,
        operations=operations
    )


def test_with_constraints(vrp_data, config, constraint_set: list, label: str):
    """Test solver with specific constraints enabled."""
    solver = VRPSolver(vrp_data, config)
    solver.create_variables()
    
    constraint_map = {
        "Routing": RoutingConstraints,
        "Time": TimeConstraints,
        "Capacity": CapacityConstraints,
        "Flow": FlowConstraints,
        "LIFO": LifoConstraints,
        "Objective": ObjectiveConstraints
    }
    
    for name in constraint_set:
        constraint_map[name].apply(solver)
    
    cp_solver, status = solver.solve()
    
    status_names = {
        cp_model.OPTIMAL: "OPTIMAL",
        cp_model.FEASIBLE: "FEASIBLE",
        cp_model.INFEASIBLE: "INFEASIBLE",
        cp_model.MODEL_INVALID: "MODEL_INVALID",
        cp_model.UNKNOWN: "UNKNOWN"
    }
    
    result = status_names.get(status, str(status))
    is_ok = status in (cp_model.OPTIMAL, cp_model.FEASIBLE)
    symbol = "✅" if is_ok else "❌"
    
    print(f"{symbol} {label}: {result}")
    return is_ok


def main():
    print("="*60)
    print("CONSTRAINT ISOLATION TEST")
    print("="*60)
    
    vrp_data = convert_to_vrp_data(TEST_DATA)
    config = VRPConfig()
    config.max_solver_time = 10  # shorter timeout for testing
    
    print("\nTesting constraints incrementally:\n")
    
    # Test 1: Routing only
    test_with_constraints(vrp_data, config, 
        ["Routing", "Objective"], 
        "Routing + Objective only")
    
    # Test 2: + Time
    test_with_constraints(vrp_data, config, 
        ["Routing", "Time", "Objective"], 
        "Routing + Time + Objective")
    
    # Test 3: + Capacity
    test_with_constraints(vrp_data, config, 
        ["Routing", "Time", "Capacity", "Objective"], 
        "Routing + Time + Capacity + Objective")
    
    # Test 4: + Flow
    test_with_constraints(vrp_data, config, 
        ["Routing", "Time", "Capacity", "Flow", "Objective"], 
        "Routing + Time + Capacity + Flow + Objective")
    
    # Test 5: + LIFO
    test_with_constraints(vrp_data, config, 
        ["Routing", "Time", "Capacity", "Flow", "LIFO", "Objective"], 
        "ALL constraints")
    
    print("\n" + "="*60)
    print("INDIVIDUAL CONSTRAINT REMOVAL TEST")
    print("="*60)
    print("\nRemoving one constraint at a time from full set:\n")
    
    # Remove each constraint one at a time
    all_constraints = ["Routing", "Time", "Capacity", "Flow", "LIFO", "Objective"]
    
    for skip in ["Time", "Capacity", "Flow", "LIFO"]:
        subset = [c for c in all_constraints if c != skip]
        test_with_constraints(vrp_data, config, 
            subset, 
            f"WITHOUT {skip}")


if __name__ == "__main__":
    main()
