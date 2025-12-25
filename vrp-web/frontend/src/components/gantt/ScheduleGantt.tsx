'use client';

/**
 * Custom Gantt Chart - No External Dependencies
 * Shows shipment time windows BEFORE optimization
 * Shows vehicle schedules AFTER optimization
 */
import { useMemo } from 'react';
import { useVRPStore } from '@/lib/store/vrp-store';

const COLORS = ['#3b82f6', '#22c55e', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#14b8a6', '#f97316'];

interface GanttRow {
    id: string;
    name: string;
    bars: { start: number; end: number; label: string; color: string; isLate?: boolean }[];
}

export function ScheduleGantt() {
    const { result, vehicles, shipments, sites } = useVRPStore();

    const { rows, maxTime } = useMemo(() => {
        const rows: GanttRow[] = [];
        let maxTime = 720; // 12 hours default

        if (!result) {
            // Before optimization: Show ORDER-SPECIFIC time windows
            shipments.forEach((ship, idx) => {
                const pickupSite = sites.find(s => s.id === ship.pickup_site_id);
                const deliverySite = sites.find(s => s.id === ship.delivery_site_id);
                const color = COLORS[idx % COLORS.length];

                const bars = [];

                // Use shipment's own pickup_window (order-specific)
                bars.push({
                    start: ship.pickup_window.start,
                    end: ship.pickup_window.end,
                    label: `📤 ${pickupSite?.name?.slice(0, 6) || 'Pickup'}`,
                    color: color,
                });
                maxTime = Math.max(maxTime, ship.pickup_window.end);

                // Use shipment's own delivery_window (order-specific)
                bars.push({
                    start: ship.delivery_window.start,
                    end: ship.delivery_window.end,
                    label: `📥 ${deliverySite?.name?.slice(0, 6) || 'Delivery'}`,
                    color: color + '80', // Semi-transparent
                });
                maxTime = Math.max(maxTime, ship.delivery_window.end);

                rows.push({
                    id: ship.id,
                    name: ship.name || `주문 ${idx + 1}`,
                    bars,
                });
            });
        } else {
            // After optimization: Show vehicle schedules
            result.routes.forEach((route, vIdx) => {
                const vehicle = vehicles.find(v => v.id === route.vehicle_id);
                const color = COLORS[vIdx % COLORS.length];

                const bars = route.stops.map((stop, sIdx) => {
                    const site = sites.find(s => s.id === stop.site_id);
                    const serviceDuration = site?.service_duration || 10;
                    const endTime = stop.arrival_time + serviceDuration;
                    maxTime = Math.max(maxTime, endTime);

                    return {
                        start: stop.arrival_time,
                        end: endTime,
                        label: site?.name?.slice(0, 6) || `Stop ${sIdx + 1}`,
                        color: stop.is_late ? '#ef4444' : color,
                        isLate: stop.is_late,
                    };
                });

                rows.push({
                    id: route.vehicle_id,
                    name: vehicle?.name || `차량 ${vIdx + 1}`,
                    bars,
                });
            });
        }

        return { rows, maxTime };
    }, [result, vehicles, shipments, sites]);

    // Time scale
    const hours = useMemo(() => {
        const h = [];
        for (let i = 0; i <= Math.ceil(maxTime / 60); i++) {
            h.push(i);
        }
        return h;
    }, [maxTime]);

    if (rows.length === 0) {
        return (
            <div className="flex items-center justify-center h-full text-gray-500">
                {result ? '경로 데이터가 없습니다' : '주문을 추가하면 시간대가 표시됩니다'}
            </div>
        );
    }

    const barWidth = (start: number, end: number) => ((end - start) / maxTime) * 100;
    const barLeft = (start: number) => (start / maxTime) * 100;

    return (
        <div className="h-full flex flex-col bg-white rounded-lg border overflow-hidden">
            {/* Header */}
            <div className="flex border-b bg-gray-50">
                <div className="w-36 shrink-0 p-2 font-medium text-sm border-r">
                    {result ? '🚛 차량' : '📦 주문'}
                </div>
                <div className="flex-1 flex">
                    {hours.map(h => (
                        <div
                            key={h}
                            className="flex-1 text-center text-xs text-gray-500 py-2 border-r last:border-r-0"
                            style={{ minWidth: 60 }}
                        >
                            {String(h).padStart(2, '0')}:00
                        </div>
                    ))}
                </div>
            </div>

            {/* Rows */}
            <div className="flex-1 overflow-y-auto">
                {rows.map((row, idx) => (
                    <div key={row.id} className={`flex border-b ${idx % 2 === 0 ? 'bg-white' : 'bg-gray-50'}`}>
                        <div className="w-36 shrink-0 p-2 text-sm border-r truncate" title={row.name}>
                            {row.name}
                        </div>
                        <div className="flex-1 relative h-12">
                            {/* Grid lines */}
                            {hours.map(h => (
                                <div
                                    key={h}
                                    className="absolute top-0 bottom-0 border-r border-gray-200"
                                    style={{ left: `${(h * 60 / maxTime) * 100}%` }}
                                />
                            ))}

                            {/* Bars */}
                            {row.bars.map((bar, bIdx) => (
                                <div
                                    key={bIdx}
                                    className={`absolute top-2 h-8 rounded text-xs text-white flex items-center px-1 overflow-hidden whitespace-nowrap ${bar.isLate ? 'ring-2 ring-red-300' : ''}`}
                                    style={{
                                        left: `${barLeft(bar.start)}%`,
                                        width: `${Math.max(barWidth(bar.start, bar.end), 2)}%`,
                                        backgroundColor: bar.color,
                                    }}
                                    title={`${bar.label} (${bar.start}-${bar.end}분)`}
                                >
                                    {bar.label}
                                </div>
                            ))}
                        </div>
                    </div>
                ))}
            </div>

            {/* Legend */}
            <div className="border-t p-2 bg-gray-50 text-xs text-gray-600">
                {result ? '✅ 최적화 완료 - 차량별 경로' : '⏰ 주문 시간대 (픽업/배송 가능 시간)'}
            </div>
        </div>
    );
}
