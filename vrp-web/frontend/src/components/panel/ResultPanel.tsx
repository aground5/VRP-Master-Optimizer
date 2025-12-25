'use client';

/**
 * Result Panel - Display optimization results
 */
import { useVRPStore } from '@/lib/store/vrp-store';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

export function ResultPanel() {
    const { result, sites } = useVRPStore();

    if (!result) {
        return (
            <div className="p-4 text-center text-gray-500">
                Run optimization to see results
            </div>
        );
    }

    const getSiteName = (siteId: string) => {
        const site = sites.find((s) => s.id === siteId);
        return site?.name || siteId;
    };

    const formatTime = (minutes: number) => {
        const h = Math.floor(minutes / 60);
        const m = minutes % 60;
        return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}`;
    };

    return (
        <div className="p-4 space-y-4 overflow-y-auto h-full">
            {/* Status */}
            <Card>
                <CardHeader className="pb-2">
                    <CardTitle className="text-sm flex items-center gap-2">
                        {result.status === 'optimal' ? '✅' : result.status === 'feasible' ? '⚠️' : '❌'}
                        Status: {result.status.toUpperCase()}
                    </CardTitle>
                </CardHeader>
            </Card>

            {/* Cost Breakdown */}
            <Card>
                <CardHeader className="pb-2">
                    <CardTitle className="text-sm">💰 Cost Breakdown</CardTitle>
                </CardHeader>
                <CardContent className="text-sm space-y-1">
                    <div className="flex justify-between">
                        <span>Fixed</span>
                        <span>{result.costs.fixed.toLocaleString()}</span>
                    </div>
                    <div className="flex justify-between">
                        <span>Distance</span>
                        <span>{result.costs.distance.toLocaleString()}</span>
                    </div>
                    <div className="flex justify-between">
                        <span>Labor</span>
                        <span>{result.costs.labor.toLocaleString()}</span>
                    </div>
                    <div className="flex justify-between">
                        <span>Zone Penalty</span>
                        <span>{result.costs.zone_penalty.toLocaleString()}</span>
                    </div>
                    <div className="flex justify-between">
                        <span>Waiting</span>
                        <span>{result.costs.waiting.toLocaleString()}</span>
                    </div>
                    <div className="flex justify-between">
                        <span>Late Penalty</span>
                        <span>{result.costs.late_penalty.toLocaleString()}</span>
                    </div>
                    <hr className="my-2" />
                    <div className="flex justify-between font-bold">
                        <span>Total</span>
                        <span>{result.costs.total.toLocaleString()}</span>
                    </div>
                </CardContent>
            </Card>

            {/* Routes */}
            {result.routes.map((route, idx) => (
                <Card key={route.vehicle_id}>
                    <CardHeader className="pb-2">
                        <CardTitle className="text-sm">🚛 Vehicle {idx + 1}</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="space-y-1 text-xs">
                            {route.stops.map((stop, sIdx) => (
                                <div
                                    key={sIdx}
                                    className={`flex items-center gap-2 p-1 rounded ${stop.is_late ? 'bg-red-100' : ''}`}
                                >
                                    <span className="w-16 text-gray-500">{formatTime(stop.arrival_time)}</span>
                                    <span>{getSiteName(stop.site_id)}</span>
                                    <span className="text-gray-400">{stop.load_weight}kg</span>
                                    {stop.is_late && <span className="text-red-500">LATE</span>}
                                </div>
                            ))}
                        </div>
                    </CardContent>
                </Card>
            ))}

            {/* Unserved */}
            {result.unserved_shipments.length > 0 && (
                <Card className="border-red-300">
                    <CardHeader className="pb-2">
                        <CardTitle className="text-sm text-red-600">⚠️ Unserved Shipments</CardTitle>
                    </CardHeader>
                    <CardContent>
                        {result.unserved_shipments.map((id) => (
                            <div key={id} className="text-sm">{id}</div>
                        ))}
                    </CardContent>
                </Card>
            )}
        </div>
    );
}
