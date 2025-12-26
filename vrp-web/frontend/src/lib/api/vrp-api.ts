/**
 * API Client for VRP Backend
 */
import type { Site, MatrixData, Vehicle, Shipment, OptimizeResult, SolverConfig } from '@/types/vrp';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function generateMatrix(sites: Site[]): Promise<MatrixData> {
    const response = await fetch(`${API_BASE}/api/matrix`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sites }),
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to generate matrix');
    }

    return response.json();
}

interface OptimizeParams {
    sites: Site[];
    vehicles: Vehicle[];
    shipments: Shipment[];
    durations: number[][];
    distances: number[][];
    penalties?: {
        unserved: number;
        late_delivery: number;
        zone_crossing: number;
    };
    max_solver_time?: number;
    config?: SolverConfig;
}

export async function optimize(params: OptimizeParams): Promise<OptimizeResult> {
    const response = await fetch(`${API_BASE}/api/optimize`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            ...params,
            config: params.config,
            penalties: params.penalties || {
                unserved: 500000,
                late_delivery: 50000,
                zone_crossing: 2000,
            },
            max_solver_time: params.max_solver_time || 30.0,
        }),
    });


    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Optimization failed');
    }

    return response.json();
}
