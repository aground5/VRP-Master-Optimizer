'use client';

/**
 * Simplified Ontology Flow
 * Nodes trigger selection -> DetailPanel shows editor
 */
import { useMemo, useEffect } from 'react';
import {
    ReactFlow,
    Background,
    Controls,
    MiniMap,
    Node,
    Edge,
    useNodesState,
    useEdgesState,
    NodeTypes,
    Handle,
    Position,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';

import { useVRPStore } from '@/lib/store/vrp-store';
import type { Vehicle, Shipment, Site } from '@/types/vrp';

// Node data types
interface VehicleNodeData {
    label: string;
    vehicle: Vehicle;
}

interface ShipmentNodeData {
    label: string;
    shipment: Shipment;
}

interface SiteNodeData {
    label: string;
    site: Site;
}

// Custom Node: Vehicle (Clickable)
function VehicleNode({ data, selected }: { data: VehicleNodeData; selected?: boolean }) {
    const { sites } = useVRPStore();
    const depot = sites.find(s => s.id === data.vehicle.start_site_id);

    return (
        <div className={`bg-blue-100 border-2 rounded-lg p-3 min-w-[160px] cursor-pointer transition-all ${selected ? 'border-blue-600 ring-2 ring-blue-300 scale-105' : 'border-blue-400 hover:border-blue-500'}`}>
            <Handle type="source" position={Position.Right} />
            <div className="text-sm font-bold text-blue-800">🚛 {data.vehicle.name}</div>
            <div className="text-xs text-gray-600 mt-1">
                용량: {data.vehicle.capacity.weight}kg
            </div>
            <div className="text-xs text-gray-500">
                Depot: {depot?.name || '-'}
            </div>
        </div>
    );
}

// Custom Node: Shipment (Clickable)
function ShipmentNode({ data, selected }: { data: ShipmentNodeData; selected?: boolean }) {
    const { sites } = useVRPStore();
    const pickup = sites.find(s => s.id === data.shipment.pickup_site_id);
    const delivery = sites.find(s => s.id === data.shipment.delivery_site_id);

    return (
        <div className={`bg-green-100 border-2 rounded-lg p-3 min-w-[160px] cursor-pointer transition-all ${selected ? 'border-green-600 ring-2 ring-green-300 scale-105' : 'border-green-400 hover:border-green-500'}`}>
            <Handle type="target" position={Position.Left} />
            <Handle type="source" position={Position.Right} />
            <div className="text-sm font-bold text-green-800">📦 {data.shipment.name}</div>
            <div className="text-xs text-gray-600 mt-1">
                {data.shipment.cargo.weight}kg
            </div>
            <div className="text-xs text-gray-500">
                {pickup?.name?.slice(0, 6)} → {delivery?.name?.slice(0, 6)}
            </div>
        </div>
    );
}

// Custom Node: Site (Clickable)
function SiteNode({ data, selected }: { data: SiteNodeData; selected?: boolean }) {
    const isDepot = data.site.type === 'depot';
    return (
        <div className={`${isDepot ? 'bg-purple-100 border-purple-500' : 'bg-gray-100 border-gray-400'} border-2 rounded-lg p-3 min-w-[100px] cursor-pointer transition-all ${selected ? 'ring-2 ring-purple-300 scale-105' : 'hover:border-purple-400'}`}>
            <Handle type="target" position={Position.Left} />
            <div className="text-sm font-bold">
                {isDepot ? '🏭' : '📍'} {data.site.name?.slice(0, 8)}
            </div>
            <div className="text-xs text-gray-500">Zone {data.site.zone_id}</div>
        </div>
    );
}

const nodeTypes: NodeTypes = {
    vehicle: VehicleNode as any,
    shipment: ShipmentNode as any,
    site: SiteNode as any,
};

export function OntologyFlow() {
    const {
        vehicles, shipments, sites, result,
        setSelectedVehicle, setSelectedShipment, setSelectedSite,
        selectedVehicleId, selectedShipmentId, selectedSiteId
    } = useVRPStore();

    const { initialNodes, initialEdges } = useMemo(() => {
        const nodes: Node[] = [];
        const edges: Edge[] = [];

        // Vehicle nodes (left)
        vehicles.forEach((v, i) => {
            nodes.push({
                id: `v_${v.id}`,
                type: 'vehicle',
                position: { x: 50, y: 50 + i * 130 },
                data: { label: v.name || v.id, vehicle: v },
                selected: selectedVehicleId === v.id,
            });
        });

        // Shipment nodes (center)
        shipments.forEach((s, i) => {
            nodes.push({
                id: `s_${s.id}`,
                type: 'shipment',
                position: { x: 300, y: 50 + i * 120 },
                data: { label: s.name || s.id, shipment: s },
                selected: selectedShipmentId === s.id,
            });
        });

        // Site nodes (right) - depots + referenced customers
        const depotSites = sites.filter(s => s.type === 'depot');
        const referencedIds = new Set([
            ...shipments.map(s => s.pickup_site_id),
            ...shipments.map(s => s.delivery_site_id),
        ]);
        const customerSites = sites.filter(s => referencedIds.has(s.id) && s.type !== 'depot');

        depotSites.forEach((site, i) => {
            nodes.push({
                id: `loc_${site.id}`,
                type: 'site',
                position: { x: 550, y: 30 + i * 80 },
                data: { label: site.name, site },
                selected: selectedSiteId === site.id,
            });
        });

        customerSites.forEach((site, i) => {
            nodes.push({
                id: `loc_${site.id}`,
                type: 'site',
                position: { x: 550, y: 200 + i * 70 },
                data: { label: site.name, site },
                selected: selectedSiteId === site.id,
            });
        });

        // Edges: Vehicle -> Depot
        vehicles.forEach(v => {
            edges.push({
                id: `e_${v.id}_depot`,
                source: `v_${v.id}`,
                target: `loc_${v.start_site_id}`,
                style: { stroke: '#8b5cf6', strokeDasharray: '5 5' },
            });
        });

        // Edges: Shipment -> Sites
        shipments.forEach(s => {
            edges.push({
                id: `e_${s.id}_pickup`,
                source: `s_${s.id}`,
                target: `loc_${s.pickup_site_id}`,
                style: { stroke: '#22c55e' },
            });
            edges.push({
                id: `e_${s.id}_delivery`,
                source: `s_${s.id}`,
                target: `loc_${s.delivery_site_id}`,
                style: { stroke: '#f59e0b' },
            });
        });

        // Result edges
        if (result) {
            result.routes.forEach(route => {
                const visitedSiteIds = route.stops.map(s => s.site_id);
                shipments.forEach(ship => {
                    if (visitedSiteIds.includes(ship.pickup_site_id) && visitedSiteIds.includes(ship.delivery_site_id)) {
                        edges.push({
                            id: `e_result_${route.vehicle_id}_${ship.id}`,
                            source: `v_${route.vehicle_id}`,
                            target: `s_${ship.id}`,
                            animated: true,
                            style: { stroke: '#3b82f6', strokeWidth: 2 },
                        });
                    }
                });
            });
        }

        return { initialNodes: nodes, initialEdges: edges };
    }, [vehicles, shipments, sites, result, selectedVehicleId, selectedShipmentId, selectedSiteId]);

    const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
    const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

    useEffect(() => {
        setNodes(initialNodes);
        setEdges(initialEdges);
    }, [initialNodes, initialEdges, setNodes, setEdges]);

    // Handle node click -> set selection
    const handleNodeClick = (_: any, node: Node) => {
        // Clear all selections first
        setSelectedVehicle(null);
        setSelectedShipment(null);
        setSelectedSite(null);

        if (node.id.startsWith('v_')) {
            const vehicleId = node.id.replace('v_', '');
            setSelectedVehicle(vehicleId);
        } else if (node.id.startsWith('s_')) {
            const shipmentId = node.id.replace('s_', '');
            setSelectedShipment(shipmentId);
        } else if (node.id.startsWith('loc_')) {
            const siteId = node.id.replace('loc_', '');
            setSelectedSite(siteId);
        }
    };

    return (
        <div className="w-full h-full">
            <ReactFlow
                nodes={nodes}
                edges={edges}
                onNodesChange={onNodesChange}
                onEdgesChange={onEdgesChange}
                nodeTypes={nodeTypes}
                onNodeClick={handleNodeClick}
                fitView
            >
                <Background />
                <Controls />
                <MiniMap />
            </ReactFlow>
        </div>
    );
}
