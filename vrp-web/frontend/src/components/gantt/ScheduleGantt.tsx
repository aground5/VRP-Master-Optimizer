'use client';

/**
 * Custom Gantt Chart - No External Dependencies
 * Shows shipment time windows BEFORE optimization
 * Shows vehicle schedules AFTER optimization
 */
import { useMemo, useState, useRef, useEffect, useCallback } from 'react';
import { useVRPStore } from '@/lib/store/vrp-store';

const COLORS = ['#3b82f6', '#22c55e', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#14b8a6', '#f97316'];

interface GanttRow {
    id: string;
    name: string;
    bars: { start: number; end: number; label: string; color: string; isLate?: boolean }[];
}

interface GanttChartProps {
    rows: GanttRow[];
    maxTime: number;
    emptyMessage: string;
    rowLabel: string;
    legend: string;
    onBarChange?: (rowId: string, barIndex: number, newStart: number, newEnd: number) => void;
}

function GanttChart({ rows, maxTime, emptyMessage, rowLabel, legend, onBarChange }: GanttChartProps) {
    // Viewport State
    const [viewStart, setViewStart] = useState(0); // Minutes
    const [viewDuration, setViewDuration] = useState(maxTime); // Minutes visible (Zoom level)

    // Drag state for bars
    const [draggingBar, setDraggingBar] = useState<{
        rowId: string;
        barIndex: number;
        startX: number;
        originalStart: number;
        originalEnd: number;
    } | null>(null);

    // Pan state for navigating time
    const [isPanning, setIsPanning] = useState(false);
    const [panStartX, setPanStartX] = useState(0);
    const [panStartView, setPanStartView] = useState(0);

    // To show immediate feedback while dragging bars
    const [tempBarMove, setTempBarMove] = useState<{ delta: number } | null>(null);

    const containerRef = useRef<HTMLDivElement>(null); // Time Axis / Width measurer
    const headerRef = useRef<HTMLDivElement>(null); // Top Header
    const rowsContainerRef = useRef<HTMLDivElement>(null); // Main Content

    const [containerWidth, setContainerWidth] = useState(800);

    // Update container width on resize
    useEffect(() => {
        if (!containerRef.current) return;
        const observer = new ResizeObserver(entries => {
            for (const entry of entries) {
                setContainerWidth(entry.contentRect.width);
            }
        });
        observer.observe(containerRef.current);
        return () => observer.disconnect();
    }, []);

    // Derived values
    const pxPerMin = containerWidth / viewDuration;

    const minutesToPixels = useCallback((minutes: number) => minutes * pxPerMin, [pxPerMin]);
    const pixelsToMinutes = useCallback((pixels: number) => pixels / pxPerMin, [pxPerMin]);

    // Zoom Logic
    const handleZoom = useCallback((factor: number) => { // factor < 1 zoom in, > 1 zoom out
        setViewDuration(prevDur => {
            const newDur = Math.max(60, Math.min(maxTime, prevDur * factor)); // Min 60 mins

            // Adjust start to keep view within bounds
            setViewStart(prevStart => {
                const maxStart = maxTime - newDur;
                return Math.max(0, Math.min(maxStart, prevStart));
            });

            return newDur;
        });
    }, [maxTime]);

    // Ensure start is clamped when maxTime/duration changes
    useEffect(() => {
        setViewStart(s => Math.max(0, Math.min(maxTime - viewDuration, s)));
    }, [maxTime, viewDuration]);


    // Dynamic Time Ticks
    const ticks = useMemo(() => {
        let interval = 60; // default 1 hour
        const minPx = 60; // Min pixels between ticks

        if (pxPerMin * 60 < minPx) interval = 120; // 2 hours
        if (pxPerMin * 30 > minPx) interval = 30;
        if (pxPerMin * 15 > minPx) interval = 15;
        if (pxPerMin * 10 > minPx) interval = 10;
        if (pxPerMin * 5 > minPx) interval = 5;

        // Generate ticks covering visible area
        const startTick = Math.floor(viewStart / interval) * interval;
        const endTick = Math.ceil((viewStart + viewDuration) / interval) * interval;

        const t = [];
        for (let m = startTick; m <= endTick; m += interval) {
            if (m >= 0 && m <= maxTime) t.push(m);
        }
        return { values: t, interval };
    }, [viewStart, viewDuration, maxTime, pxPerMin]);


    // --- Interactions ---

    // 1. Native Wheel Listener for Robust PreventDefault (Prevent Back Gesture)
    useEffect(() => {
        const targets = [headerRef.current, containerRef.current, rowsContainerRef.current];

        const handleWheel = (e: WheelEvent) => {
            // Logic:
            // Horizontal (any target) -> Pan & Prevent Default (Stop Back Gesture)
            // Vertical (Header/Axis) -> Zoom & Prevent Default
            // Vertical (Rows) -> Scroll (Native Behavior) - Do NOT Prevent Default

            if (Math.abs(e.deltaX) > Math.abs(e.deltaY)) {
                // Horizontal Pan
                e.preventDefault();
                e.stopPropagation();

                const deltaMin = pixelsToMinutes(e.deltaX);
                setViewStart(s => Math.max(0, Math.min(maxTime - viewDuration, s + deltaMin)));
            } else if (e.deltaY !== 0) {
                // Vertical
                if (e.currentTarget === rowsContainerRef.current) {
                    // Let row container scroll vertically
                    return;
                }

                // Header or Axis -> Zoom
                e.preventDefault();
                e.stopPropagation();
                handleZoom(e.deltaY > 0 ? 1.1 : 0.9);
            }
        };

        // Passive: false is crucial for preventDefault to work on wheel/touch
        targets.forEach(t => t?.addEventListener('wheel', handleWheel, { passive: false }));

        return () => {
            targets.forEach(t => t?.removeEventListener('wheel', handleWheel));
        };
    }, [viewDuration, maxTime, pixelsToMinutes, handleZoom]); // Dependencies that might change logic


    // 2. Bar Dragging
    useEffect(() => {
        const handleMouseMove = (e: MouseEvent) => {
            if (!draggingBar) return;
            const deltaPx = e.clientX - draggingBar.startX;
            const deltaMin = pixelsToMinutes(deltaPx);
            setTempBarMove({ delta: deltaMin });
        };

        const handleMouseUp = () => {
            if (draggingBar && tempBarMove && onBarChange) {
                const roundedDelta = Math.round(tempBarMove.delta);
                if (roundedDelta !== 0) {
                    onBarChange(
                        draggingBar.rowId,
                        draggingBar.barIndex,
                        Math.max(0, draggingBar.originalStart + roundedDelta),
                        Math.max(0, draggingBar.originalEnd + roundedDelta)
                    );
                }
            }
            setDraggingBar(null);
            setTempBarMove(null);
            document.body.style.cursor = '';
            document.body.style.userSelect = '';
        };

        if (draggingBar) {
            window.addEventListener('mousemove', handleMouseMove);
            window.addEventListener('mouseup', handleMouseUp);
            document.body.style.cursor = 'grabbing';
            document.body.style.userSelect = 'none';
        }
        return () => {
            window.removeEventListener('mousemove', handleMouseMove);
            window.removeEventListener('mouseup', handleMouseUp);
            document.body.style.cursor = '';
            document.body.style.userSelect = '';
        };
    }, [draggingBar, tempBarMove, onBarChange, pixelsToMinutes]);

    // 3. Pan (Drag Background)
    useEffect(() => {
        const handleMouseMove = (e: MouseEvent) => {
            if (!isPanning) return;
            const deltaPx = e.clientX - panStartX;
            const deltaMin = pixelsToMinutes(deltaPx);

            // Dragging right (positive delta) -> View moves left (decrease start)
            const newStart = panStartView - deltaMin;
            setViewStart(Math.max(0, Math.min(maxTime - viewDuration, newStart)));
        };

        const handleMouseUp = () => {
            setIsPanning(false);
            document.body.style.cursor = '';
            document.body.style.userSelect = '';
        };

        if (isPanning) {
            window.addEventListener('mousemove', handleMouseMove);
            window.addEventListener('mouseup', handleMouseUp);
            document.body.style.cursor = 'grab';
            document.body.style.userSelect = 'none';
        }
        return () => {
            window.removeEventListener('mousemove', handleMouseMove);
            window.removeEventListener('mouseup', handleMouseUp);
            document.body.style.cursor = '';
            document.body.style.userSelect = '';
        };
    }, [isPanning, panStartX, panStartView, pixelsToMinutes, maxTime, viewDuration]);


    if (rows.length === 0) {
        return (
            <div className="flex items-center justify-center h-full text-gray-500">
                {emptyMessage}
            </div>
        );
    }

    return (
        <div className="h-full flex flex-col bg-white rounded-lg border overflow-hidden select-none">
            {/* Header */}
            <div className="flex border-b bg-gray-50 items-center justify-between pr-2">
                <div
                    className="flex items-center flex-1 overflow-hidden overscroll-x-none"
                    ref={headerRef}
                // No onWheel here, handled by native listener
                >
                    <div className="w-36 shrink-0 p-2 font-medium text-sm border-r bg-gray-100 z-10 select-none">
                        {rowLabel}
                    </div>

                    <div className="flex-1 px-4 text-xs text-gray-400 italic flex items-center justify-between cursor-zoom-in">
                        <div>
                            Zoom: {Math.round((maxTime / viewDuration) * 100)}% | Tick: {ticks.interval}m
                        </div>
                        <div className="text-gray-300 hidden md:block">
                            Wheel horizontally to Pan | Wheel vertically to Zoom
                        </div>
                    </div>
                </div>

                {/* Controls */}
                <div className="flex items-center gap-2 p-1 border-l pl-2 bg-white">
                    <button
                        onClick={() => handleZoom(1.2)}
                        className="p-1 hover:bg-gray-100 rounded border text-gray-600 w-8 text-center bg-white shadow-sm"
                        title="Zoom Out"
                    >
                        -
                    </button>
                    <button
                        onClick={() => handleZoom(0.8)}
                        className="p-1 hover:bg-gray-100 rounded border text-gray-600 w-8 text-center bg-white shadow-sm"
                        title="Zoom In"
                    >
                        +
                    </button>
                </div>
            </div>

            {/* Content Area */}
            <div className="flex-1 overflow-hidden relative flex flex-col">
                {/* Time Axis (Sticky Top) */}
                <div
                    className="flex border-b bg-gray-50 h-8 relative shrink-0 cursor-ew-resize hover:bg-gray-100 transition-colors"
                >
                    <div className="w-36 shrink-0 border-r bg-gray-50 z-20"></div>
                    {/* Time Scale Area with Pan Handlers */}
                    <div
                        className="flex-1 relative overflow-hidden overscroll-x-none"
                        ref={containerRef}
                        onMouseDown={(e) => {
                            // Start Pan on Time Header - keep react handler for mouse events
                            e.preventDefault();
                            setIsPanning(true);
                            setPanStartX(e.clientX);
                            setPanStartView(viewStart);
                        }}
                    // No onWheel here
                    >
                        {ticks.values.map(m => {
                            const left = minutesToPixels(m - viewStart);
                            // Skip if excessively out of view
                            if (left < -50 || left > containerWidth + 50) return null;

                            const isMajor = m % 60 === 0;
                            return (
                                <div
                                    key={m}
                                    className={`absolute top-0 text-xs ${isMajor ? 'text-gray-600 font-medium' : 'text-gray-400'} pt-2 border-l ${isMajor ? 'border-gray-400' : 'border-gray-300'} pl-1 select-none pointer-events-none`}
                                    style={{ left: `${left}px` }}
                                >
                                    {Math.floor(m / 60).toString().padStart(2, '0')}:{String(m % 60).padStart(2, '0')}
                                </div>
                            );
                        })}
                    </div>
                </div>

                {/* Rows Container - Scrollable Vertical Only */}
                <div
                    className="flex-1 overflow-y-auto overflow-x-hidden relative overscroll-x-none"
                    ref={rowsContainerRef}
                    // No onWheel here
                    // Add listeners here to capture dragging on empty space
                    onMouseDown={(e) => {
                        // Drag Body -> Pan
                        if (e.button === 0) { // Left click only
                            // Note: Bars stopPropagation, so this only runs on background
                            setIsPanning(true);
                            setPanStartX(e.clientX);
                            setPanStartView(viewStart);
                        }
                    }}
                >
                    {rows.map((row, idx) => (
                        <div key={row.id} className={`flex border-b ${idx % 2 === 0 ? 'bg-white' : 'bg-gray-50'} relative h-12`}>
                            {/* Sticky Sidebar Name (Left Fixed) */}
                            <div className="w-36 shrink-0 p-2 text-sm border-r truncate sticky left-0 z-10 bg-inherit shadow-sm" title={row.name}>
                                {row.name}
                            </div>

                            {/* Bars Channel */}
                            <div className="flex-1 relative overflow-hidden pointer-events-none">
                                {/* Grid lines */}
                                {ticks.values.map(m => {
                                    const left = minutesToPixels(m - viewStart);
                                    if (left < -2 || left > containerWidth) return null;
                                    return (
                                        <div
                                            key={m}
                                            className={`absolute top-0 bottom-0 border-r ${m % 60 === 0 ? 'border-gray-200' : 'border-gray-50 dash'}`}
                                            style={{ left: `${left}px` }}
                                        />
                                    );
                                })}

                                {/* Bars */}
                                {row.bars.map((bar, bIdx) => {
                                    let start = bar.start;
                                    let end = bar.end;
                                    const isDraggingThis = draggingBar?.rowId === row.id && draggingBar?.barIndex === bIdx;

                                    if (isDraggingThis && tempBarMove) {
                                        start += tempBarMove.delta;
                                        end += tempBarMove.delta;
                                    }

                                    const left = minutesToPixels(start - viewStart);
                                    const width = minutesToPixels(end - start);

                                    // Skip rendering if completely out of view
                                    if (left + width < 0 || left > containerWidth) return null;

                                    return (
                                        <div
                                            key={bIdx}
                                            onMouseDown={(e) => {
                                                if (!onBarChange) return;
                                                e.preventDefault();
                                                e.stopPropagation(); // Stop Pan interaction
                                                setDraggingBar({
                                                    rowId: row.id,
                                                    barIndex: bIdx,
                                                    startX: e.clientX,
                                                    originalStart: bar.start,
                                                    originalEnd: bar.end,
                                                });
                                            }}
                                            className={`absolute top-2 h-8 rounded text-xs text-white flex items-center px-1 overflow-hidden whitespace-nowrap pointer-events-auto 
                                                ${bar.isLate ? 'ring-2 ring-red-300' : ''} 
                                                ${onBarChange ? 'cursor-move hover:brightness-90 shadow-sm' : ''}
                                                ${isDraggingThis ? 'opacity-80 ring-2 ring-blue-400 z-20' : ''}
                                            `}
                                            style={{
                                                left: `${left}px`,
                                                width: `${Math.max(width, 2)}px`,
                                                backgroundColor: bar.color,
                                                transition: isDraggingThis ? 'none' : 'background-color 0.1s',
                                            }}
                                            title={`${bar.label} (${Math.round(start)}-${Math.round(end)}분)`}
                                        >
                                            {bar.label}
                                        </div>
                                    );
                                })}
                            </div>
                        </div>
                    ))}
                </div>
            </div>

            {/* Legend / Status */}
            <div className="border-t p-2 bg-gray-50 text-xs text-gray-600 flex justify-between items-center">
                <div className="flex gap-4">
                    <span>{legend}</span>
                    <span>View: {Math.round(viewStart)} - {Math.round(viewStart + viewDuration)} min</span>
                </div>

                <span className="text-gray-400 hidden sm:inline">
                    {onBarChange && '💡 Drag bars: Edit | Drag Bkg: Pan | Shift+Wheel: Pan | Header Wheel: Zoom'}
                </span>
            </div>
        </div>
    );
}

export function OrderGantt() {
    const { shipments, sites, updateShipment } = useVRPStore();

    const { rows, maxTime } = useMemo(() => {
        const rows: GanttRow[] = [];
        let maxTime = 720; // 12 hours minimum

        shipments.forEach((ship, idx) => {
            const pickupSite = sites.find(s => s.id === ship.pickup_site_id);
            const deliverySite = sites.find(s => s.id === ship.delivery_site_id);
            const color = COLORS[idx % COLORS.length];

            const bars = [];

            // Bar 0: Pickup
            bars.push({
                start: ship.pickup_window.start,
                end: ship.pickup_window.end,
                label: `📤 ${pickupSite?.name?.slice(0, 6) || 'Pickup'}`,
                color: color,
            });
            maxTime = Math.max(maxTime, ship.pickup_window.end);

            // Bar 1: Delivery
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

        maxTime = Math.ceil(maxTime / 60) * 60;
        return { rows, maxTime };
    }, [shipments, sites]);

    const handleBarChange = useCallback((rowId: string, barIndex: number, newStart: number, newEnd: number) => {
        const shipment = shipments.find(s => s.id === rowId);
        if (!shipment) return;

        // barIndex 0 is Pickup, 1 is Delivery
        if (barIndex === 0) {
            updateShipment(rowId, {
                pickup_window: { start: Math.round(newStart), end: Math.round(newEnd) }
            });
        } else if (barIndex === 1) {
            updateShipment(rowId, {
                delivery_window: { start: Math.round(newStart), end: Math.round(newEnd) }
            });
        }
    }, [shipments, updateShipment]);

    return (
        <GanttChart
            rows={rows}
            maxTime={maxTime}
            emptyMessage="주문을 추가하면 시간대가 표시됩니다"
            rowLabel="📦 주문"
            legend="⏰ 주문 시간대 (픽업/배송 가능 시간)"
            onBarChange={handleBarChange}
        />
    );
}

export function DeliveryGantt() {
    const { result, vehicles, sites } = useVRPStore();

    const { rows, maxTime } = useMemo(() => {
        if (!result) return { rows: [], maxTime: 720 };

        const rows: GanttRow[] = [];
        let maxTime = 720;

        result.routes.forEach((route, vIdx) => {
            const vehicle = vehicles.find(v => v.id === route.vehicle_id);
            const color = COLORS[vIdx % COLORS.length];

            const bars = route.stops.map((stop, sIdx) => {
                const site = sites.find(s => s.id === stop.site_id);
                const serviceDuration = site?.service_duration || 10;
                const endTime = stop.arrival_time + serviceDuration;
                maxTime = Math.max(maxTime, endTime);

                let prefix = '';
                if (stop.stop_type === 'pickup') prefix = '📤 ';
                else if (stop.stop_type === 'delivery') prefix = '📥 ';
                else if (stop.stop_type?.startsWith('depot')) prefix = '🏠 ';

                return {
                    start: stop.arrival_time,
                    end: endTime,
                    label: `${prefix}${site?.name?.slice(0, 6) || `Stop ${sIdx}`}`,
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

        maxTime = Math.ceil(maxTime / 60) * 60;
        return { rows, maxTime };
    }, [result, vehicles, sites]);

    return (
        <GanttChart
            rows={rows}
            maxTime={maxTime}
            emptyMessage="최적화 결과가 없습니다"
            rowLabel="🚛 차량"
            legend="✅ 최적화 완료 - 차량별 경로"
        // Read-only, no onBarChange
        />
    );
}

// Deprecated: Keeping for backward compatibility if needed, but redirects to OrderGantt
export function ScheduleGantt() {
    return <OrderGantt />;
}
