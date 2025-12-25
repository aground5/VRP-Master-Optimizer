include "globals.mzn";

% =========================================================
% 1. 데이터 설정 ("Trap V3 - Checkmate" Scenario)
% =========================================================

int: num_vehicles = 3;
int: num_locations = 8;  % 1:Depot
int: max_steps = 16;     

set of int: VEHICLES = 1..num_vehicles;
set of int: LOCS = 1..num_locations;
set of int: STEPS = 1..max_steps;
int: DEPOT = 1;

% [1-1] 차량 스펙
array[VEHICLES] of int: v_cap_weight = [30, 100, 120];
array[VEHICLES] of int: v_cap_volume = [30, 100, 100];
array[VEHICLES] of int: v_start_loc  = [1, 1, 1];
array[VEHICLES] of int: v_end_loc    = [1, 1, 1];

% [1-2] 노동법 (Overtime Calculation)
array[VEHICLES] of int: v_start_window = [0, 0, 0];
array[VEHICLES] of int: v_max_work_time = [600, 600, 660];
int: standard_work_time = 480;  
int: break_interval = 240;      
int: break_duration = 30;       

% [1-3] 비용 구조
array[VEHICLES] of int: cost_fixed     = [3000, 8000, 12000];
array[VEHICLES] of int: cost_per_km    = [5, 15, 20];
array[VEHICLES] of int: cost_per_min   = [10, 10, 15]; 
int: cost_per_kg_km = 1; 

% [1-4] 화물 정보 (1:Depot)
% Scenario Update: Trap V3
% Pair A (1->5), Pair B (2->6), Pair C (3->4), task 7
array[LOCS] of int: demand_weight = [0, 20, 30, 10, -10, -20, -30, 20]; 
array[LOCS] of int: demand_volume = [0, 20, 50, 10, -10, -20, -50, 20];

% Time Windows (Trap V3)
% Pick A(1): Due 25, Pick B(2): Due 60, Drop A(5): Due 200, Drop B(6): Ready 500
array[LOCS] of int: ready_time = [0, 0, 0, 0, 0, 60, 500, 0];
array[LOCS] of int: due_time   = [1000, 25, 60, 1000, 1000, 200, 1000, 1000];
array[LOCS] of int: service_duration = [0, 10, 10, 10, 10, 20, 20, 10];

% [1-5] 픽업 & 배송 / 페널티
% Pair A: 1->5, Pair B: 2->6, Pair C: 3->4
array[LOCS] of int: pickup_pair = [0, 5, 6, 4, 0, 0, 0, 0];
% Boost A penalty to 1,000,000 to force LIFO check
array[LOCS] of int: unserved_penalty = [0, 1000000, 100000, 50000, 50000, 1000000, 100000, 50000];

% [1-6] 호환성
array[VEHICLES] of int: v_type = [1, 1, 1];
array[LOCS] of int: req_v_type = [0, 0, 0, 0, 0, 0, 0, 0];

% [1-7] 구역(Zoning)
array[LOCS] of int: zone = [0, 1, 1, 1, 1, 1, 1, 1]; 
int: zone_penalty = 500;

% [1-8] 거리/시간/전이 (Updated Travel Dist for Trap)
array[LOCS, LOCS] of int: travel_dist = 
[| 0, 10, 15, 20, 20, 20, 25, 30
 |10,  0,  2, 20, 20, 20, 25, 30
 |15,  2,  0, 20, 20, 10, 10, 30
 |20, 20, 20,  0,  5, 20, 20, 20
 |20, 20, 20,  5,  0, 20, 20, 20
 |20, 20, 10, 20, 20,  0,  5, 20
 |25, 25, 10, 20, 20,  5,  0, 20
 |30, 30, 30, 20, 20, 20, 20,  0 |];
array[LOCS, LOCS] of int: travel_time = array2d(LOCS, LOCS, [d * 2 | d in travel_dist]);
array[LOCS, LOCS] of int: setup_time = array2d(LOCS, LOCS, [0 | i,j in LOCS]); 

% =========================================================
% 2. 결정 변수
% =========================================================
array[VEHICLES, STEPS] of var LOCS: route;
array[VEHICLES, STEPS] of var 0..10000: arrival_time;
array[VEHICLES, STEPS] of var 0..2000: load_w; 
array[VEHICLES, STEPS] of var 0..2000: load_v;

array[VEHICLES, STEPS] of var bool: is_done; 
array[VEHICLES] of var 0..1: is_used;
array[LOCS] of var 0..1: is_served;

% LIFO 시뮬레이션을 위한 방문 순서 기록
array[LOCS] of var 0..max_steps: visit_step;
array[LOCS] of var 0..num_vehicles: visit_vehicle;

% =========================================================
% 3. 제약 조건
% =========================================================

% (1) 경로 구조 & 업무 종료
constraint forall(v in VEHICLES) (
    route[v, 1] == v_start_loc[v] /\
    is_done[v, 1] == false /\
    forall(s in 1..max_steps-1) (
        (is_done[v, s] -> is_done[v, s+1]) /\
        (is_done[v, s] -> route[v, s] == v_end_loc[v]) /\
        ((route[v, s] == v_end_loc[v] /\ route[v, s+1] == v_end_loc[v]) <-> is_done[v, s+1])
    )
);

% (2) 방문 여부 및 Step 기록 (LIFO 핵심)
constraint forall(c in 2..num_locations) (
    if is_served[c] == 1 then
        exists(v in VEHICLES, s in STEPS) (
            route[v, s] == c /\ 
            visit_step[c] == s /\ 
            visit_vehicle[c] == v
        )
    else
        visit_step[c] == 0 /\ visit_vehicle[c] == 0
    endif
);
constraint visit_step[DEPOT] == 0;

% (3) 픽업 & 배송 쌍
constraint forall(p in LOCS where pickup_pair[p] > 0) (
    is_served[p] == is_served[pickup_pair[p]]
);

% (4) 상태 업데이트
constraint forall(v in VEHICLES, s in 1..max_steps-1) (
    let {
        var LOCS: curr = route[v, s];
        var LOCS: next = route[v, s+1];
        var int: drive_t = travel_time[curr, next];
        var int: setup_t = setup_time[curr, next];
        var int: rest_t = if drive_t > break_interval then break_duration else 0 endif;
    } in (
        if is_done[v, s+1] then
            arrival_time[v, s+1] == arrival_time[v, s]
        else
            arrival_time[v, s+1] == max(ready_time[next], arrival_time[v, s] + service_duration[curr] + drive_t + rest_t + setup_t)
        endif /\
        
        if next == v_end_loc[v] then
             load_w[v, s+1] == 0 /\ load_v[v, s+1] == 0
        else
             load_w[v, s+1] == load_w[v, s] + demand_weight[next] /\
             load_v[v, s+1] == load_v[v, s] + demand_volume[next]
        endif
    )
);

% (5) 초기값
constraint forall(v in VEHICLES) (
    arrival_time[v, 1] == v_start_window[v] /\ load_w[v, 1] == 0 /\ load_v[v, 1] == 0
);

% (6) 유효성 검사
constraint forall(v in VEHICLES, s in STEPS) (
    let { var LOCS: loc = route[v, s] } in 
    load_w[v, s] >= 0 /\ load_w[v, s] <= v_cap_weight[v] /\
    load_v[v, s] >= 0 /\ load_v[v, s] <= v_cap_volume[v] /\
    arrival_time[v, s] - v_start_window[v] <= v_max_work_time[v] /\
    
    if is_done[v, s] == false /\ loc != v_start_loc[v] /\ loc != v_end_loc[v] then
        arrival_time[v, s] >= ready_time[loc] /\
        arrival_time[v, s] <= due_time[loc] /\
        (req_v_type[loc] == 0 \/ req_v_type[loc] == v_type[v])
    else true endif
);

% (7) 픽업 순서
constraint forall(p in LOCS where pickup_pair[p] > 0) (
    let { int: d = pickup_pair[p] } in
    (is_served[p] == 1) -> (
        visit_step[p] < visit_step[d] /\ 
        visit_vehicle[p] == visit_vehicle[d]
    )
);

% (8) 차량 사용 여부
constraint forall(v in VEHICLES) (
    is_used[v] = (if is_done[v, 2] then 0 else 1 endif)
);

% (9) Inventory Continuity (꼼수 방지: 짐 실은 채로 Depot 금지)
% 적재(Step P) ~ 하차(Step D) 사이 구간은 Depot 방문 불가
constraint forall(p in LOCS where pickup_pair[p] > 0) (
    forall(v in VEHICLES) (
        if visit_vehicle[p] == v then
             let { 
                var int: p_s = visit_step[p];
                int: d = pickup_pair[p];
                var int: d_s = visit_step[d];
             } in
             forall(s in STEPS) (
                 if s > p_s /\ s < d_s then
                     route[v, s] != DEPOT
                 else true endif
             )
        else true endif
    )
);

% =========================================================
% 4. 목적 함수 (Objective Function)
% =========================================================

% 1. 고정 비용
var int: c_fixed = sum(v in VEHICLES) (is_used[v] * cost_fixed[v]);

% 2. 거리 비용
var int: c_dist = sum(v in VEHICLES, s in 1..max_steps-1) (
    let {
        var int: dist = travel_dist[route[v, s], route[v, s+1]];
        var int: w_penalty = load_w[v, s] * cost_per_kg_km;
    } in
    if is_done[v, s+1] == false \/ (is_done[v, s+1] /\ is_done[v, s] == false) then
        dist * (cost_per_km[v] + w_penalty)
    else 0 endif
);

% 3. 인건비 (연장 근무 1.5배)
var int: c_time = sum(v in VEHICLES) (
    let {
        var int: total_work_t = max([arrival_time[v, s] | s in STEPS]) - v_start_window[v];
        var int: regular_t = min(total_work_t, standard_work_time);
        var int: overtime_t = max(0, total_work_t - standard_work_time);
    } in
    (regular_t * cost_per_min[v]) + 
    (overtime_t * (cost_per_min[v] * 15 div 10)) 
);

% 4. 누락 페널티
var int: c_penalty = sum(c in 2..num_locations) ( (1 - is_served[c]) * unserved_penalty[c] );

% 5. 구역 위반 페널티
var int: c_zone = sum(v in VEHICLES, s in 1..max_steps-1) (
    let { var LOCS: curr = route[v, s]; var LOCS: next = route[v, s+1]; } in
    if is_done[v, s+1] == false /\ curr != DEPOT /\ next != DEPOT /\ zone[curr] != zone[next] 
    then zone_penalty else 0 endif
);

% 6. 물리적 부피 결합 (Re-handling Cost) - [FIXED Logic]
var int: c_rehandling = sum(v in VEHICLES, s in 1..max_steps-1) (
    let {
        var LOCS: curr_loc = route[v, s];
        var bool: is_delivery = (demand_weight[curr_loc] < 0);
        var LOCS: my_pickup = sum(p in LOCS) (if pickup_pair[p] == curr_loc then p else 0 endif);
    } in
    if is_delivery /\ my_pickup > 0 then
        sum(other_p in LOCS where pickup_pair[other_p] > 0 /\ other_p != my_pickup) (
            let {
                var LOCS: other_d = pickup_pair[other_p];
            } in
            % 조건: 같은 차량 + 다른 짐이 나중에 실림(위에 있음) + 다른 짐이 아직 안 내림(블로킹)
            % + [FIX] 다른 짐이 내 픽업보다 나중에 실렸더라도, 내 하차 시점에 "이미 실려 있어야" 함 (s > visit_step[other_p])
            if visit_vehicle[other_p] == v /\
               visit_step[other_p] > visit_step[my_pickup] /\
               visit_step[other_d] > s /\
               visit_step[other_p] < s  % [FIX] Physically Present Check
            then
                demand_volume[other_p] * 50 
            else 0 endif
        )
    else 0 endif
);

var int: total_cost = c_fixed + c_dist + c_time + c_penalty + c_zone + c_rehandling;

solve minimize total_cost;

% =========================================================
% 5. 상세 결과 출력
% =========================================================
output [
    "============================================================\n",
    "🚚 VRP FINAL SIMULATION REPORT (Trap V3 & Inventory Check)\n",
    "============================================================\n",
    "💰 Total Cost breakdown:\n",
    "   Total Objective : " ++ show(total_cost) ++ "\n",
    "   ----------------------------------------\n",
    "   1. Fixed Cost   : " ++ show(c_fixed) ++ "\n",
    "   2. Dist Cost    : " ++ show(c_dist) ++ "\n",
    "   3. Labor Cost   : " ++ show(c_time) ++ " (OT 1.5x Applied)\n",
    "   4. Zone Penalty : " ++ show(c_zone) ++ "\n",
    "   5. Re-handling  : " ++ show(c_rehandling) ++ " (Volumetric LIFO)\n",
    "   6. Miss Penalty : " ++ show(c_penalty) ++ "\n",
    "============================================================\n\n"
] ++
[
    if fix(is_used[v]) == 1 then
        "🚛 Vehicle " ++ show(v) ++ " [Type " ++ show(v_type[v]) ++ "]\n" ++
        "   Work Time: " ++ show(max([fix(arrival_time[v,s]) | s in STEPS])) ++ " min " ++
        "(Overtime: " ++ show(max(0, max([fix(arrival_time[v,s]) | s in STEPS]) - standard_work_time)) ++ " min)\n" ++
        "   ------------------------------------------------------------\n" ++
        concat([
            if fix(is_done[v,s]) == false \/ (s>1 /\ fix(is_done[v,s])==true /\ fix(is_done[v,s-1])==false) then
                let { int: loc = fix(route[v,s]); int: w = fix(load_w[v,s]); int: cap = v_cap_weight[v]; } in
                "   Step " ++ show_int(2, s) ++ " | " ++
                (if loc == DEPOT then 
                    if s == 1 then "🏭 DEPOT (Start)       " else "🏭 DEPOT (Reload/End)  " endif
                 else 
                    "📍 Loc " ++ show_int(2, loc) ++ " (Zone " ++ show(zone[loc]) ++ ")     "
                 endif) ++
                " | Time: " ++ show_int(4, arrival_time[v,s]) ++ " " ++
                " | Load: " ++ show_int(3, w) ++ "kg\n"
            else "" endif
            | s in STEPS
        ]) ++ "\n"
    else "" endif
    | v in VEHICLES
];