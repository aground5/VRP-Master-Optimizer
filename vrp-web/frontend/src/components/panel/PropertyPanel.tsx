'use client';

/**
 * Property Panel - Edit selected entities
 */
import { useVRPStore } from '@/lib/store/vrp-store';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import type { Vehicle, Shipment } from '@/types/vrp';

export function PropertyPanel() {
    const {
        sites, vehicles, shipments,
        selectedSiteId, selectedVehicleId,
        updateSite, updateVehicle, addVehicle, addShipment,
        removeSite, removeVehicle
    } = useVRPStore();

    const selectedSite = sites.find((s) => s.id === selectedSiteId);

    // Add Vehicle Form
    const handleAddVehicle = () => {
        const depots = sites.filter((s) => s.type === 'depot');
        if (depots.length === 0) {
            alert('Add a depot first!');
            return;
        }

        const newVehicle: Vehicle = {
            id: `veh_${Date.now()}`,
            name: `Truck ${vehicles.length + 1}`,
            start_site_id: depots[0].id,
            end_site_id: depots[0].id,
            capacity: { weight: 50, volume: 50 },
            cost: { fixed: 500, per_km: 10, per_minute: 10 },
            shift: { start_time: 0, max_duration: 720, standard_duration: 480 },
            break_rule: { interval_minutes: 240, duration_minutes: 30 },
            tags: [],
        };
        addVehicle(newVehicle);
    };

    // Add Shipment (simple modal would be better, but for now quick add)
    const handleAddShipment = () => {
        const customers = sites.filter((s) => s.type === 'customer');
        if (customers.length < 2) {
            alert('Add at least 2 customer sites first!');
            return;
        }

        const newShipment: Shipment = {
            id: `ship_${Date.now()}`,
            name: `Order ${shipments.length + 1}`,
            pickup_site_id: customers[0].id,
            delivery_site_id: customers[1].id,
            pickup_window: { start: 60, end: 180 },     // Default pickup window
            delivery_window: { start: 180, end: 360 },  // Default delivery window
            cargo: { weight: 10, volume: 10 },
            required_tags: [],
            priority: 1,
        };
        addShipment(newShipment);
    };

    return (
        <div className="p-4 space-y-4 overflow-y-auto h-full">
            {/* Site Editor */}
            {selectedSite && (
                <Card>
                    <CardHeader className="pb-2">
                        <CardTitle className="text-sm">
                            {selectedSite.type === 'depot' ? '🏭' : '📍'} {selectedSite.name}
                        </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-3">
                        <div>
                            <Label className="text-xs">Name</Label>
                            <Input
                                value={selectedSite.name}
                                onChange={(e) => updateSite(selectedSite.id, { name: e.target.value })}
                                className="h-8 text-sm"
                            />
                        </div>
                        <div>
                            <Label className="text-xs">Service Duration (min)</Label>
                            <Input
                                type="number"
                                value={selectedSite.service_duration}
                                onChange={(e) => updateSite(selectedSite.id, { service_duration: Number(e.target.value) })}
                                className="h-8 text-sm"
                            />
                        </div>
                        <div>
                            <Label className="text-xs">Zone ID</Label>
                            <Input
                                type="number"
                                value={selectedSite.zone_id}
                                onChange={(e) => updateSite(selectedSite.id, { zone_id: Number(e.target.value) })}
                                className="h-8 text-sm"
                            />
                        </div>
                        <Button
                            variant="destructive"
                            size="sm"
                            className="w-full"
                            onClick={() => removeSite(selectedSite.id)}
                        >
                            Delete Site
                        </Button>
                    </CardContent>
                </Card>
            )}

            {/* Quick Actions */}
            <Card>
                <CardHeader className="pb-2">
                    <CardTitle className="text-sm">Quick Actions</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2">
                    <Button onClick={handleAddVehicle} className="w-full" size="sm">
                        🚛 Add Vehicle
                    </Button>
                    <Button onClick={handleAddShipment} className="w-full" size="sm" variant="outline">
                        📦 Add Shipment
                    </Button>
                </CardContent>
            </Card>

            {/* Vehicles List */}
            <Card>
                <CardHeader className="pb-2">
                    <CardTitle className="text-sm">Vehicles ({vehicles.length})</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2">
                    {vehicles.map((v) => (
                        <div key={v.id} className="flex items-center justify-between p-2 bg-gray-50 rounded text-sm">
                            <span>🚛 {v.name}</span>
                            <Button variant="ghost" size="sm" onClick={() => removeVehicle(v.id)}>×</Button>
                        </div>
                    ))}
                </CardContent>
            </Card>

            {/* Shipments List */}
            <Card>
                <CardHeader className="pb-2">
                    <CardTitle className="text-sm">Shipments ({shipments.length})</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2">
                    {shipments.map((s) => (
                        <div key={s.id} className="p-2 bg-gray-50 rounded text-xs">
                            📦 {s.name}: {s.cargo.weight}kg
                        </div>
                    ))}
                </CardContent>
            </Card>
        </div>
    );
}
