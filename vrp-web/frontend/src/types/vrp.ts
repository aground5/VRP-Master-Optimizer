/**
 * VRP Types - Matching Backend Schemas
 */

export type SiteType = 'depot' | 'customer' | 'hub';

export interface Coordinates {
    lat: number;
    lng: number;
}

export interface TimeWindow {
    start: number;
    end: number;
}

export interface Site {
    id: string;
    name: string;
    type: SiteType;
    coords: Coordinates;
    service_duration: number;
    zone_id: number;
}

export interface VehicleCapacity {
    weight: number;
    volume: number;
}

export interface VehicleCost {
    fixed: number;
    per_km: number;
    per_minute: number;
}

export interface LaborShift {
    start_time: number;
    max_duration: number;
    standard_duration: number;
}

export interface BreakRule {
    interval_minutes: number;
    duration_minutes: number;
}

export interface Vehicle {
    id: string;
    name: string;
    start_site_id: string;
    end_site_id: string;
    capacity: VehicleCapacity;
    cost: VehicleCost;
    shift: LaborShift;
    break_rule: BreakRule;
    tags: string[];
}

export interface Cargo {
    weight: number;
    volume: number;
}

export interface Shipment {
    id: string;
    name: string;
    pickup_site_id: string;
    delivery_site_id: string;
    pickup_window: TimeWindow;     // Order-specific pickup time window
    delivery_window: TimeWindow;   // Order-specific delivery time window
    cargo: Cargo;
    required_tags: string[];
    priority: number;
}

export interface RouteStop {
    site_id: string;
    arrival_time: number;
    load_weight: number;
    load_volume: number;
    is_late: boolean;
}

export interface VehicleRoute {
    vehicle_id: string;
    stops: RouteStop[];
    total_distance: number;
    total_time: number;
}

export interface CostBreakdown {
    fixed: number;
    distance: number;
    labor: number;
    zone_penalty: number;
    rehandling: number;
    waiting: number;
    late_penalty: number;
    unserved_penalty: number;
    total: number;
}

export interface OptimizeResult {
    status: 'optimal' | 'feasible' | 'infeasible';
    routes: VehicleRoute[];
    costs: CostBreakdown;
    unserved_shipments: string[];
}

export interface MatrixData {
    durations: number[][];
    distances: number[][];
}
