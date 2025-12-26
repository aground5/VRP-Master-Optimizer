'use client';

/**
 * Result Panel - Display optimization results
 */
import { useVRPStore } from '@/lib/store/vrp-store';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
    Clock,
    Truck,
    MapPin,
    DollarSign,
    AlertCircle,
    CheckCircle,
    ChevronRight,
    ChevronDown,
    Package
} from 'lucide-react';
import { useState } from 'react';
import type { VehicleRoute } from '@/types/vrp';

export function ResultPanel() {
    const { result, sites, setSelectedVehicle } = useVRPStore();
    const [expandedRoutes, setExpandedRoutes] = useState<Record<string, boolean>>({});

    const toggleRoute = (vehicleId: string) => {
        setExpandedRoutes(prev => ({
            ...prev,
            [vehicleId]: !prev[vehicleId]
        }));
    };

    if (!result) {
        return (
            <div className="flex flex-col items-center justify-center h-full text-gray-400 p-8 text-center">
                <Truck className="w-12 h-12 mb-4 opacity-20" />
                <p>Run optimization to see analysis results</p>
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

    const totalShipments = result.routes.reduce((acc, r) =>
        acc + r.stops.filter(s => s.stop_type === 'pickup').length, 0);

    const unservedCount = result.unserved_shipments.length;
    const totalPossible = totalShipments + unservedCount;
    const serviceLevel = totalPossible > 0 ? ((totalShipments / totalPossible) * 100).toFixed(1) : '0';

    return (
        <div className="flex flex-col h-full bg-gray-50/50">
            {/* Header / Summary */}
            <div className="grid grid-cols-2 gap-2 p-2">
                <Card className="shadow-sm">
                    <CardContent className="p-3 flex flex-col items-center justify-center">
                        <span className="text-[10px] uppercase text-gray-500 font-bold mb-1">Total Cost</span>
                        <div className="text-lg font-bold text-gray-800">
                            {result.costs.total.toLocaleString()}
                        </div>
                    </CardContent>
                </Card>
                <Card className="shadow-sm">
                    <CardContent className="p-3 flex flex-col items-center justify-center">
                        <span className="text-[10px] uppercase text-gray-500 font-bold mb-1">Service Level</span>
                        <div className={`text-lg font-bold ${Number(serviceLevel) === 100 ? 'text-green-600' : 'text-amber-600'}`}>
                            {serviceLevel}%
                        </div>
                    </CardContent>
                </Card>
            </div>

            <div className="flex-1 overflow-y-auto px-2 pb-4 space-y-3">
                {/* Key Metrics */}
                <div className="grid grid-cols-3 gap-2">
                    <div className="bg-white p-2 rounded border flex flex-col items-center">
                        <MapPin className="w-4 h-4 text-blue-500 mb-1" />
                        <span className="text-[10px] text-gray-400">Distance</span>
                        <span className="font-semibold text-sm">{(result.costs.distance / 1000).toFixed(1)}km</span>
                    </div>
                    <div className="bg-white p-2 rounded border flex flex-col items-center">
                        <Clock className="w-4 h-4 text-purple-500 mb-1" />
                        <span className="text-[10px] text-gray-400">Time</span>
                        <span className="font-semibold text-sm">{Math.round(result.routes.reduce((acc, r) => acc + r.total_time, 0) / 60)}h</span>
                    </div>
                    <div className="bg-white p-2 rounded border flex flex-col items-center">
                        <Truck className="w-4 h-4 text-slate-500 mb-1" />
                        <span className="text-[10px] text-gray-400">Routes</span>
                        <span className="font-semibold text-sm">{result.routes.length}</span>
                    </div>
                </div>

                {/* Unserved Alert */}
                {unservedCount > 0 && (
                    <div className="bg-red-50 border border-red-200 rounded-md p-3 flex items-start gap-3">
                        <AlertCircle className="w-5 h-5 text-red-600 shrink-0 mt-0.5" />
                        <div>
                            <h4 className="text-sm font-bold text-red-700">Unserved Shipments ({unservedCount})</h4>
                            <p className="text-xs text-red-600 mt-1">
                                {result.unserved_shipments.map(id => id).join(', ')}
                            </p>
                        </div>
                    </div>
                )}

                {/* Cost Detail Accordion */}
                <Card>
                    <CardHeader className="py-2 px-3 bg-gray-50/50 border-b">
                        <CardTitle className="text-xs font-semibold uppercase text-gray-500 flex items-center gap-2">
                            <DollarSign className="w-3 h-3" /> Cost Breakdown
                        </CardTitle>
                    </CardHeader>
                    <CardContent className="p-0">
                        <table className="w-full text-xs">
                            <tbody>
                                <CostRow label="Fixed Costs" value={result.costs.fixed} />
                                <CostRow label="Distance" value={result.costs.distance} />
                                <CostRow label="Labor Driven" value={result.costs.labor} />
                                <CostRow label="Zone & Penalties" value={result.costs.zone_penalty + result.costs.late_penalty} />
                                <CostRow label="Wait Time" value={result.costs.waiting} />
                            </tbody>
                        </table>
                    </CardContent>
                </Card>

                {/* Route List */}
                <div className="space-y-2">
                    <h3 className="text-xs font-bold uppercase text-gray-400 ml-1">Vehicle Routes</h3>
                    {result.routes.map((route, idx) => {
                        const isExpanded = expandedRoutes[route.vehicle_id];
                        const stopCount = route.stops.filter(s => s.stop_type !== 'depot_start' && s.stop_type !== 'depot_end').length;

                        return (
                            <div key={route.vehicle_id} className="bg-white border rounded-md overflow-hidden shadow-sm transition-all hover:shadow-md">
                                <div
                                    className="p-3 flex items-center cursor-pointer hover:bg-gray-50"
                                    onClick={() => {
                                        toggleRoute(route.vehicle_id);
                                        setSelectedVehicle(route.vehicle_id);
                                    }}
                                >
                                    <div className={`mr-2 transition-transform ${isExpanded ? 'rotate-90' : ''}`}>
                                        <ChevronRight className="w-4 h-4 text-gray-400" />
                                    </div>
                                    <div className="flex-1">
                                        <div className="flex items-center gap-2">
                                            <span className="font-bold text-sm text-gray-800">Vehicle {idx + 1}</span>
                                            <span className="text-[10px] bg-slate-100 px-1.5 py-0.5 rounded text-slate-600 font-mono">
                                                {formatTime(route.total_time)} min
                                            </span>
                                        </div>
                                        <div className="text-xs text-gray-500 mt-0.5 flex gap-2">
                                            <span>{stopCount} stops</span>
                                            <span>•</span>
                                            <span>{Math.round(route.total_distance / 1000)}km</span>
                                        </div>
                                    </div>
                                </div>

                                {isExpanded && (
                                    <div className="border-t bg-gray-50 p-2 space-y-2">
                                        {/* Timeline */}
                                        <div className="relative pl-4 space-y-4 before:absolute before:left-[19px] before:top-2 before:bottom-2 before:w-0.5 before:bg-gray-200">
                                            {route.stops.map((stop, sIdx) => {
                                                const isDepot = stop.stop_type.includes('depot');
                                                const isPickup = stop.stop_type === 'pickup';

                                                return (
                                                    <div key={sIdx} className="relative flex items-start gap-3 group">
                                                        {/* Dot / Icon */}
                                                        <div className={`
                                                            z-10 w-2.5 h-2.5 rounded-full mt-1.5 shrink-0 border-2 border-white shadow-sm
                                                            ${isDepot ? 'bg-gray-400' : isPickup ? 'bg-green-500' : 'bg-blue-500'}
                                                         `} />

                                                        <div className="flex-1 min-w-0 bg-white p-2 rounded border shadow-sm group-hover:border-blue-200 transition-colors">
                                                            <div className="flex justify-between items-start mb-1">
                                                                <span className="font-mono text-xs font-bold text-gray-600">
                                                                    {formatTime(stop.arrival_time)}
                                                                </span>
                                                                <span className={`
                                                                    text-[9px] uppercase font-bold px-1 rounded
                                                                    ${isDepot ? 'bg-gray-100 text-gray-600' :
                                                                        isPickup ? 'bg-green-50 text-green-700' :
                                                                            'bg-blue-50 text-blue-700'}
                                                                `}>
                                                                    {stop.stop_type.replace('_', ' ')}
                                                                </span>
                                                            </div>

                                                            <div className="text-sm font-medium truncate" title={getSiteName(stop.site_id)}>
                                                                {getSiteName(stop.site_id)}
                                                            </div>

                                                            {!isDepot && (
                                                                <div className="flex items-center gap-2 mt-1.5 text-xs text-gray-500">
                                                                    <Package className="w-3 h-3" />
                                                                    <span>{stop.load_weight}kg</span>
                                                                    {stop.is_late && (
                                                                        <span className="text-red-600 font-bold ml-auto flex items-center gap-1">
                                                                            <AlertCircle className="w-3 h-3" /> Late
                                                                        </span>
                                                                    )}
                                                                </div>
                                                            )}
                                                        </div>
                                                    </div>
                                                );
                                            })}
                                        </div>
                                    </div>
                                )}
                            </div>
                        );
                    })}
                </div>
            </div>
        </div>
    );
}

function CostRow({ label, value }: { label: string; value: number }) {
    if (value === 0) return null;
    return (
        <tr className="border-b last:border-0 border-gray-100 hover:bg-gray-50/50">
            <td className="py-2 px-3 text-gray-600">{label}</td>
            <td className="py-2 px-3 text-right font-mono font-medium">{value.toLocaleString()}</td>
        </tr>
    );
}
