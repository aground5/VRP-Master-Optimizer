'use client';

/**
 * Control Bar - Matrix generation and optimization
 */
import { useState } from 'react';
import { useVRPStore } from '@/lib/store/vrp-store';
import { generateMatrix, optimize } from '@/lib/api/vrp-api';
import { exampleSites, exampleVehicles, exampleShipments } from '@/lib/data/example-data';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';

export function ControlBar() {
    const {
        sites, vehicles, shipments, matrix,
        setMatrix, setResult, isOptimizing, setIsOptimizing,
        addSite, addVehicle, addShipment, reset
    } = useVRPStore();
    const [error, setError] = useState<string | null>(null);
    const [loading, setLoading] = useState(false);

    const handleLoadExample = () => {
        // Reset current data
        reset();

        // Load example data
        exampleSites.forEach(site => addSite(site));
        exampleVehicles.forEach(veh => addVehicle(veh));
        exampleShipments.forEach(ship => addShipment(ship));

        setError(null);
    };

    const handleGenerateMatrix = async () => {
        if (sites.length < 2) {
            setError('Need at least 2 sites');
            return;
        }

        setError(null);
        setLoading(true);
        try {
            const result = await generateMatrix(sites);
            setMatrix(result);
        } catch (e: any) {
            setError(e.message);
        } finally {
            setLoading(false);
        }
    };

    const handleOptimize = async () => {
        if (!matrix) {
            setError('Generate matrix first');
            return;
        }
        if (vehicles.length === 0) {
            setError('Add at least one vehicle');
            return;
        }
        if (shipments.length === 0) {
            setError('Add at least one shipment');
            return;
        }

        setError(null);
        setIsOptimizing(true);

        try {
            const result = await optimize({
                sites,
                vehicles,
                shipments,
                durations: matrix.durations,
                distances: matrix.distances,
            });
            setResult(result);
        } catch (e: any) {
            setError(e.message);
        } finally {
            setIsOptimizing(false);
        }
    };

    return (
        <Card className="m-2">
            <CardContent className="flex items-center gap-4 p-3">
                <Button
                    onClick={handleLoadExample}
                    variant="secondary"
                    size="sm"
                >
                    📥 Load Example
                </Button>

                <div className="flex items-center gap-2 text-sm text-gray-600">
                    <span>📍 {sites.length} Sites</span>
                    <span>🚛 {vehicles.length} Vehicles</span>
                    <span>📦 {shipments.length} Shipments</span>
                </div>

                <div className="flex-1" />

                <Button
                    onClick={handleGenerateMatrix}
                    disabled={sites.length < 2 || loading}
                    variant="outline"
                    size="sm"
                >
                    {loading ? '⏳ Loading...' : matrix ? '✅ Matrix Ready' : '📐 Generate Matrix'}
                </Button>

                <Button
                    onClick={handleOptimize}
                    disabled={!matrix || vehicles.length === 0 || shipments.length === 0 || isOptimizing}
                    size="sm"
                >
                    {isOptimizing ? '⏳ Optimizing...' : '🚀 Optimize'}
                </Button>

                {error && (
                    <span className="text-red-500 text-sm">{error}</span>
                )}
            </CardContent>
        </Card>
    );
}
