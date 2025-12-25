# VRP-Master-Optimizer

> **"MiniZinc을 활용한 종합 VRP(차량 경로 문제) 최적화 모델: 다차원 용량, 시간대, 페널티 기반 서비스 로직 포함"**
> ("A comprehensive VRP (Vehicle Routing Problem) optimization model using MiniZinc, featuring multi-dimensional capacity, time windows, and penalty-based service logic.")

## 📖 개요 (Overview)

이 프로젝트는 **MiniZinc**를 사용하여 개발된 고급 **차량 경로 문제(VRP)** 해결 모델입니다. 단순한 경로 탐색을 넘어, 복잡한 현실 세계의 물류 과제들을 해결하기 위해 비용, 효율성, 그리고 서비스 품질을 최적화하도록 설계되었습니다.

## ✨ 주요 기능 (Features)

이 모델은 다음과 같은 다양한 현실적 제약 조건들을 포함하고 있습니다:

*   **차량 제약 (Vehicle Constraints)**
    *   **다차원 용량 (Multi-dimensional Capacity):** 중량(kg)과 부피(m³) 제약을 동시에 처리합니다.
    *   **근무 시간 제한 (Work Hour Limits):** 의무 휴식 시간을 포함한 최대 근무 시간을 준수합니다.
    *   **연비 효율 (Fuel Efficiency):** 적재 중량에 따른 비용(무거운 화물 = 높은 연료 소모)을 계산합니다.

*   **배송 제약 (Shipment Constraints)**
    *   **시간대 (Time Windows):** 각 고객의 `ready_time`(준비 시간) 및 `due_time`(마감 시간)을 준수합니다.
    *   **픽업 및 배송 (Pickup & Delivery):** 연계된 픽업 및 배송 위치를 지원합니다(배송 전 픽업 필수).
    *   **서비스 시간 (Service Durations):** 각 정차 지점에서의 상하차 시간을 고려합니다.

*   **호환성 (Compatibility)**
    *   **특수 차량 배차 (Specialized Assignments):** 특정 화물에 대한 차량 유형 요구사항(예: 냉동/냉장 탑차)을 강제합니다.

*   **운영 로직 (Operational Logic)**
    *   **전이 속성 (Transition Attributes):** 특정 위치 간의 준비/청소(Setup/Cleaning) 시간을 포함합니다.
    *   **페널티 기반 로직 (Penalty-based Logic):** 불가능한 해(UNSAT)를 방지하기 위해 높은 페널티 비용을 감수하고 일부 위치를 건너뛰는 것을 허용합니다.
    *   **조기 도착 대기 (Earliest Arrival):** 차량이 `ready_time` 이전에 도착할 경우 대기합니다.

## 🎯 최적화 목표 (Optimization Objective)

이 솔버는 다음 항목들의 가중 합인 **총 비용(Total Cost)**을 최소화합니다:

1.  **고정 비용 (Fixed Costs):** 차량 운행에 따른 기본 비용.
2.  **거리 비용 (Distance Costs):** 이동 거리 $\times$ (km당 기본 비용 + 중량 페널티).
3.  **시간 비용 (Time Costs):** 총 운영 시간(운전, 서비스, 대기 포함) $\times$ 분당 비용.
4.  **페널티 비용 (Penalty Costs):** 서비스되지 않은 고객에 대해 부과되는 높은 페널티.

$$ \text{Minimize } (C_{fixed} + C_{dist} + C_{time} + C_{penalty}) $$

## 🛠️ 기술 스택 (Technology)

*   **Language:** [MiniZinc](https://www.minizinc.org/)
*   **Solver:** 표준 CP/MIP 솔버(예: Gecode, COIN-BC)와 호환되도록 설계되었습니다.

## 🏷️ 태그 (Tags)

`optimization` `vrp` `minizinc` `logistics` `constraint-programming` `operations-research`

## 📄 라이선스 (License)

이 프로젝트는 **MIT License** 하에 배포됩니다.
