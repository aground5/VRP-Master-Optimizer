import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger } from '@/components/ui/sheet';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useVRPStore } from '@/lib/store/vrp-store';
import { Settings, RefreshCw } from 'lucide-react';
import { useState } from 'react';

export function ConfigPanel() {
    const { config, updateConfig, reset } = useVRPStore();
    const [isOpen, setIsOpen] = useState(false);

    const handleChange = (key: keyof typeof config, value: string) => {
        const num = parseFloat(value);
        if (!isNaN(num)) {
            updateConfig({ [key]: num });
        }
    };

    return (
        <Sheet open={isOpen} onOpenChange={setIsOpen}>
            <SheetTrigger asChild>
                <Button variant="outline" size="sm" className="gap-2">
                    <Settings className="h-4 w-4" />
                    Settings
                </Button>
            </SheetTrigger>
            <SheetContent className="w-[400px] sm:w-[540px] overflow-y-auto">
                <SheetHeader>
                    <SheetTitle className="flex items-center justify-between">
                        <span>Solver Configuration</span>
                        <Button variant="ghost" size="sm" onClick={() => updateConfig(config)} title="Reset defaults (Todo)">
                            <RefreshCw className="h-4 w-4" />
                        </Button>
                    </SheetTitle>
                </SheetHeader>

                <Tabs defaultValue="costs" className="mt-6">
                    <TabsList className="grid w-full grid-cols-4">
                        <TabsTrigger value="costs">Costs</TabsTrigger>
                        <TabsTrigger value="penalties">Penalties</TabsTrigger>
                        <TabsTrigger value="labor">Labor</TabsTrigger>
                        <TabsTrigger value="ops">Ops</TabsTrigger>
                    </TabsList>

                    <TabsContent value="costs" className="space-y-4 py-4">
                        <div className="space-y-2">
                            <Label>Cost per kg/km</Label>
                            <Input
                                type="number"
                                value={config.cost_per_kg_km}
                                onChange={(e) => handleChange('cost_per_kg_km', e.target.value)}
                            />
                            <p className="text-xs text-muted-foreground">Monetary cost per kg per km traveled.</p>
                        </div>
                        <div className="space-y-2">
                            <Label>Cost per Wait Minute</Label>
                            <Input
                                type="number"
                                value={config.cost_per_wait_min}
                                onChange={(e) => handleChange('cost_per_wait_min', e.target.value)}
                            />
                            <p className="text-xs text-muted-foreground">Penalty cost for vehicle idling/waiting.</p>
                        </div>
                    </TabsContent>

                    <TabsContent value="penalties" className="space-y-4 py-4">
                        <div className="space-y-2">
                            <Label>Unserved Penalty</Label>
                            <Input
                                type="number"
                                value={config.unserved_penalty}
                                onChange={(e) => handleChange('unserved_penalty', e.target.value)}
                            />
                            <p className="text-xs text-muted-foreground">Cost for failing to serve a shipment.</p>
                        </div>
                        <div className="space-y-2">
                            <Label>Late Penalty</Label>
                            <Input
                                type="number"
                                value={config.late_penalty}
                                onChange={(e) => handleChange('late_penalty', e.target.value)}
                            />
                            <p className="text-xs text-muted-foreground">Cost for delivering after the deadline (soft constraint).</p>
                        </div>
                        <div className="space-y-2">
                            <Label>Zone Crossing Penalty</Label>
                            <Input
                                type="number"
                                value={config.zone_penalty}
                                onChange={(e) => handleChange('zone_penalty', e.target.value)}
                            />
                        </div>
                    </TabsContent>

                    <TabsContent value="labor" className="space-y-4 py-4">
                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <Label>Standard Work Time (min)</Label>
                                <Input
                                    type="number"
                                    value={config.standard_work_time}
                                    onChange={(e) => handleChange('standard_work_time', e.target.value)}
                                />
                            </div>
                            <div className="space-y-2">
                                <Label>Max Work Time (min)</Label>
                                <Input
                                    type="number"
                                    value={config.max_work_time}
                                    onChange={(e) => handleChange('max_work_time', e.target.value)}
                                />
                            </div>
                        </div>
                        <div className="space-y-2">
                            <Label>Overtime Multiplier</Label>
                            <Input
                                type="number" step="0.1"
                                value={config.overtime_multiplier}
                                onChange={(e) => handleChange('overtime_multiplier', e.target.value)}
                            />
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <Label>Break Interval (min)</Label>
                                <Input
                                    type="number"
                                    value={config.break_interval}
                                    onChange={(e) => handleChange('break_interval', e.target.value)}
                                />
                            </div>
                            <div className="space-y-2">
                                <Label>Break Duration (min)</Label>
                                <Input
                                    type="number"
                                    value={config.break_duration}
                                    onChange={(e) => handleChange('break_duration', e.target.value)}
                                />
                            </div>
                        </div>
                    </TabsContent>

                    <TabsContent value="ops" className="space-y-4 py-4">
                        <div className="space-y-2">
                            <Label>Scale Factor (for floats)</Label>
                            <Input
                                type="number"
                                value={config.capacity_scale_factor}
                                onChange={(e) => handleChange('capacity_scale_factor', e.target.value)}
                            />
                            <p className="text-xs text-muted-foreground">Multiplier to handle float precision (e.g. 100 for 2 decimals).</p>
                        </div>
                        <div className="space-y-2">
                            <Label>Solver Time Limit (sec)</Label>
                            <Input
                                type="number"
                                value={config.max_solver_time}
                                onChange={(e) => handleChange('max_solver_time', e.target.value)}
                            />
                        </div>
                        <div className="space-y-2">
                            <Label>Min Depot Service Time (min)</Label>
                            <Input
                                type="number"
                                value={config.depot_min_service_time}
                                onChange={(e) => handleChange('depot_min_service_time', e.target.value)}
                            />
                        </div>
                    </TabsContent>
                </Tabs>
            </SheetContent>
        </Sheet>
    );
}
