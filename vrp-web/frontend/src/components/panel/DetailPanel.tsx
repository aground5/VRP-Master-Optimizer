'use client';

/**
 * Detail Panel - Dynamic editor for selected entity
 */
import { useVRPStore } from '@/lib/store/vrp-store';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

export function DetailPanel() {
    const {
        sites, vehicles, shipments,
        selectedSiteId, selectedVehicleId, selectedShipmentId,
        updateSite, updateVehicle, updateShipment,
        removeSite, removeVehicle, removeShipment,
        setSelectedSite, setSelectedVehicle, setSelectedShipment
    } = useVRPStore();

    const selectedSite = sites.find((s) => s.id === selectedSiteId);
    const selectedVehicle = vehicles.find((v) => v.id === selectedVehicleId);
    const selectedShipment = shipments.find((s) => s.id === selectedShipmentId);

    const depots = sites.filter(s => s.type === 'depot');
    const customers = sites.filter(s => s.type === 'customer');

    // Clear selections
    const clearSelection = () => {
        setSelectedSite(null);
        setSelectedVehicle(null);
        setSelectedShipment(null);
    };

    // No selection
    if (!selectedSite && !selectedVehicle && !selectedShipment) {
        return (
            <div className="p-4 text-center text-gray-500 text-sm">
                <p>📍 지도/Flow에서 항목을 클릭하여</p>
                <p>상세 편집하세요</p>
            </div>
        );
    }

    // Site Detail
    if (selectedSite) {
        return (
            <div className="p-4 space-y-4">
                <div className="flex items-center justify-between">
                    <h3 className="font-bold text-lg">
                        {selectedSite.type === 'depot' ? '🏭' : '📍'} Site 상세
                    </h3>
                    <Button variant="ghost" size="sm" onClick={clearSelection}>×</Button>
                </div>

                <Card>
                    <CardContent className="pt-4 space-y-3">
                        <div>
                            <Label className="text-xs">이름</Label>
                            <Input
                                value={selectedSite.name}
                                onChange={(e) => updateSite(selectedSite.id, { name: e.target.value })}
                            />
                        </div>
                        <div>
                            <Label className="text-xs">서비스 시간 (분)</Label>
                            <Input
                                type="number"
                                value={selectedSite.service_duration}
                                onChange={(e) => updateSite(selectedSite.id, { service_duration: Number(e.target.value) })}
                            />
                        </div>
                        <div>
                            <Label className="text-xs">Zone ID</Label>
                            <Input
                                type="number"
                                value={selectedSite.zone_id}
                                onChange={(e) => updateSite(selectedSite.id, { zone_id: Number(e.target.value) })}
                            />
                        </div>
                        <Button variant="destructive" className="w-full" onClick={() => { removeSite(selectedSite.id); clearSelection(); }}>
                            삭제
                        </Button>
                    </CardContent>
                </Card>
            </div>
        );
    }

    // Vehicle Detail
    if (selectedVehicle) {
        return (
            <div className="p-4 space-y-4">
                <div className="flex items-center justify-between">
                    <h3 className="font-bold text-lg">🚛 차량 상세</h3>
                    <Button variant="ghost" size="sm" onClick={clearSelection}>×</Button>
                </div>

                <Card>
                    <CardContent className="pt-4 space-y-3">
                        <div>
                            <Label className="text-xs">이름</Label>
                            <Input
                                value={selectedVehicle.name}
                                onChange={(e) => updateVehicle(selectedVehicle.id, { name: e.target.value })}
                            />
                        </div>
                        <div className="grid grid-cols-2 gap-2">
                            <div>
                                <Label className="text-xs">적재 무게 (kg)</Label>
                                <Input
                                    type="number"
                                    value={selectedVehicle.capacity.weight}
                                    onChange={(e) => updateVehicle(selectedVehicle.id, {
                                        capacity: { ...selectedVehicle.capacity, weight: Number(e.target.value) }
                                    })}
                                />
                            </div>
                            <div>
                                <Label className="text-xs">적재 부피 (m³)</Label>
                                <Input
                                    type="number"
                                    value={selectedVehicle.capacity.volume}
                                    onChange={(e) => updateVehicle(selectedVehicle.id, {
                                        capacity: { ...selectedVehicle.capacity, volume: Number(e.target.value) }
                                    })}
                                />
                            </div>
                        </div>
                        <div>
                            <Label className="text-xs">출발 Depot</Label>
                            <select
                                className="w-full h-9 px-3 border rounded text-sm"
                                value={selectedVehicle.start_site_id}
                                onChange={(e) => updateVehicle(selectedVehicle.id, {
                                    start_site_id: e.target.value,
                                    end_site_id: e.target.value
                                })}
                            >
                                {depots.map(d => (
                                    <option key={d.id} value={d.id}>{d.name}</option>
                                ))}
                            </select>
                        </div>
                        <div className="grid grid-cols-2 gap-2">
                            <div>
                                <Label className="text-xs">고정 비용</Label>
                                <Input
                                    type="number"
                                    value={selectedVehicle.cost.fixed}
                                    onChange={(e) => updateVehicle(selectedVehicle.id, {
                                        cost: { ...selectedVehicle.cost, fixed: Number(e.target.value) }
                                    })}
                                />
                            </div>
                            <div>
                                <Label className="text-xs">km당 비용</Label>
                                <Input
                                    type="number"
                                    value={selectedVehicle.cost.per_km}
                                    onChange={(e) => updateVehicle(selectedVehicle.id, {
                                        cost: { ...selectedVehicle.cost, per_km: Number(e.target.value) }
                                    })}
                                />
                            </div>
                        </div>
                        <div>
                            <Label className="text-xs">최대 근무 시간 (분)</Label>
                            <Input
                                type="number"
                                value={selectedVehicle.shift.max_duration}
                                onChange={(e) => updateVehicle(selectedVehicle.id, {
                                    shift: { ...selectedVehicle.shift, max_duration: Number(e.target.value) }
                                })}
                            />
                        </div>
                        <Button variant="destructive" className="w-full" onClick={() => { removeVehicle(selectedVehicle.id); clearSelection(); }}>
                            삭제
                        </Button>
                    </CardContent>
                </Card>
            </div>
        );
    }

    // Shipment Detail
    if (selectedShipment) {
        return (
            <div className="p-4 space-y-4">
                <div className="flex items-center justify-between">
                    <h3 className="font-bold text-lg">📦 주문 상세</h3>
                    <Button variant="ghost" size="sm" onClick={clearSelection}>×</Button>
                </div>

                <Card>
                    <CardContent className="pt-4 space-y-3">
                        <div>
                            <Label className="text-xs">이름</Label>
                            <Input
                                value={selectedShipment.name}
                                onChange={(e) => updateShipment(selectedShipment.id, { name: e.target.value })}
                            />
                        </div>
                        <div className="grid grid-cols-2 gap-2">
                            <div>
                                <Label className="text-xs">무게 (kg)</Label>
                                <Input
                                    type="number"
                                    value={selectedShipment.cargo.weight}
                                    onChange={(e) => updateShipment(selectedShipment.id, {
                                        cargo: { ...selectedShipment.cargo, weight: Number(e.target.value) }
                                    })}
                                />
                            </div>
                            <div>
                                <Label className="text-xs">부피 (m³)</Label>
                                <Input
                                    type="number"
                                    value={selectedShipment.cargo.volume}
                                    onChange={(e) => updateShipment(selectedShipment.id, {
                                        cargo: { ...selectedShipment.cargo, volume: Number(e.target.value) }
                                    })}
                                />
                            </div>
                        </div>
                        <div>
                            <Label className="text-xs">픽업 위치</Label>
                            <select
                                className="w-full h-9 px-3 border rounded text-sm"
                                value={selectedShipment.pickup_site_id}
                                onChange={(e) => updateShipment(selectedShipment.id, { pickup_site_id: e.target.value })}
                            >
                                {customers.map(c => (
                                    <option key={c.id} value={c.id}>{c.name}</option>
                                ))}
                            </select>
                        </div>
                        <div className="grid grid-cols-2 gap-2">
                            <div>
                                <Label className="text-xs">픽업 시작 (분)</Label>
                                <Input
                                    type="number"
                                    value={selectedShipment.pickup_window.start}
                                    onChange={(e) => updateShipment(selectedShipment.id, {
                                        pickup_window: { ...selectedShipment.pickup_window, start: Number(e.target.value) }
                                    })}
                                />
                            </div>
                            <div>
                                <Label className="text-xs">픽업 종료 (분)</Label>
                                <Input
                                    type="number"
                                    value={selectedShipment.pickup_window.end}
                                    onChange={(e) => updateShipment(selectedShipment.id, {
                                        pickup_window: { ...selectedShipment.pickup_window, end: Number(e.target.value) }
                                    })}
                                />
                            </div>
                        </div>
                        <div>
                            <Label className="text-xs">배송 위치</Label>
                            <select
                                className="w-full h-9 px-3 border rounded text-sm"
                                value={selectedShipment.delivery_site_id}
                                onChange={(e) => updateShipment(selectedShipment.id, { delivery_site_id: e.target.value })}
                            >
                                {customers.map(c => (
                                    <option key={c.id} value={c.id}>{c.name}</option>
                                ))}
                            </select>
                        </div>
                        <div className="grid grid-cols-2 gap-2">
                            <div>
                                <Label className="text-xs">배송 시작 (분)</Label>
                                <Input
                                    type="number"
                                    value={selectedShipment.delivery_window.start}
                                    onChange={(e) => updateShipment(selectedShipment.id, {
                                        delivery_window: { ...selectedShipment.delivery_window, start: Number(e.target.value) }
                                    })}
                                />
                            </div>
                            <div>
                                <Label className="text-xs">배송 종료 (분)</Label>
                                <Input
                                    type="number"
                                    value={selectedShipment.delivery_window.end}
                                    onChange={(e) => updateShipment(selectedShipment.id, {
                                        delivery_window: { ...selectedShipment.delivery_window, end: Number(e.target.value) }
                                    })}
                                />
                            </div>
                        </div>
                        <div>
                            <Label className="text-xs">우선순위</Label>
                            <Input
                                type="number"
                                value={selectedShipment.priority}
                                onChange={(e) => updateShipment(selectedShipment.id, { priority: Number(e.target.value) })}
                            />
                        </div>
                        <Button variant="destructive" className="w-full" onClick={() => { removeShipment(selectedShipment.id); clearSelection(); }}>
                            삭제
                        </Button>
                    </CardContent>
                </Card>
            </div>
        );
    }

    return null;
}
