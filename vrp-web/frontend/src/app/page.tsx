'use client';

import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { VRPMap } from '@/components/map/VRPMap';
import { OntologyFlow } from '@/components/flow/OntologyFlow';
import { ScheduleGantt } from '@/components/gantt/ScheduleGantt';
import { PropertyPanel } from '@/components/panel/PropertyPanel';
import { DetailPanel } from '@/components/panel/DetailPanel';
import { ControlBar } from '@/components/panel/ControlBar';
import { ResultPanel } from '@/components/panel/ResultPanel';
import { useVRPStore } from '@/lib/store/vrp-store';

export default function Home() {
  const { selectedSiteId, selectedVehicleId, selectedShipmentId } = useVRPStore();
  const hasSelection = selectedSiteId || selectedVehicleId || selectedShipmentId;

  return (
    <div className="flex flex-col h-screen bg-gray-100">
      {/* Header */}
      <header className="bg-white border-b px-4 py-3 flex items-center gap-4">
        <h1 className="text-xl font-bold text-gray-800">🚛 VRP Optimizer</h1>
        <span className="text-sm text-gray-500">Vehicle Routing Problem - Ontology-based Solver</span>
      </header>

      {/* Control Bar */}
      <ControlBar />

      {/* Main Content */}
      <div className="flex flex-1 overflow-hidden">
        {/* Left Panel - Quick Add */}
        <aside className="w-64 bg-white border-r overflow-y-auto">
          <PropertyPanel />
        </aside>

        {/* Center - Map/Flow/Gantt View */}
        <main className="flex-1 relative">
          <Tabs defaultValue="map" className="h-full flex flex-col">
            <TabsList className="mx-2 mt-2 w-fit">
              <TabsTrigger value="map">🗺️ Map</TabsTrigger>
              <TabsTrigger value="flow">🔗 Ontology</TabsTrigger>
              <TabsTrigger value="gantt">📊 Gantt</TabsTrigger>
            </TabsList>

            <TabsContent value="map" className="flex-1 m-0 relative">
              <VRPMap />
            </TabsContent>

            <TabsContent value="flow" className="flex-1 m-0">
              <OntologyFlow />
            </TabsContent>

            <TabsContent value="gantt" className="flex-1 m-0 p-2">
              <ScheduleGantt />
            </TabsContent>
          </Tabs>
        </main>

        {/* Right Panel - Detail Editor or Results */}
        <aside className="w-80 bg-white border-l overflow-y-auto">
          {hasSelection ? (
            <>
              <div className="p-3 border-b font-medium text-sm bg-blue-50">✏️ 상세 편집</div>
              <DetailPanel />
            </>
          ) : (
            <>
              <div className="p-3 border-b font-medium text-sm">📊 Results</div>
              <ResultPanel />
            </>
          )}
        </aside>
      </div>
    </div>
  );
}
