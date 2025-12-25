/**
 * Zustand Store for VRP State
 */
import { create } from 'zustand';
import type { Site, Vehicle, Shipment, MatrixData, OptimizeResult } from '@/types/vrp';

interface VRPState {
    // Data
    sites: Site[];
    vehicles: Vehicle[];
    shipments: Shipment[];
    matrix: MatrixData | null;
    result: OptimizeResult | null;

    // UI State
    selectedSiteId: string | null;
    selectedVehicleId: string | null;
    selectedShipmentId: string | null;
    isOptimizing: boolean;

    // Actions
    addSite: (site: Site) => void;
    updateSite: (id: string, updates: Partial<Site>) => void;
    removeSite: (id: string) => void;

    addVehicle: (vehicle: Vehicle) => void;
    updateVehicle: (id: string, updates: Partial<Vehicle>) => void;
    removeVehicle: (id: string) => void;

    addShipment: (shipment: Shipment) => void;
    updateShipment: (id: string, updates: Partial<Shipment>) => void;
    removeShipment: (id: string) => void;

    setMatrix: (matrix: MatrixData) => void;
    setResult: (result: OptimizeResult | null) => void;

    setSelectedSite: (id: string | null) => void;
    setSelectedVehicle: (id: string | null) => void;
    setSelectedShipment: (id: string | null) => void;
    setIsOptimizing: (val: boolean) => void;

    reset: () => void;
}

const initialState = {
    sites: [],
    vehicles: [],
    shipments: [],
    matrix: null,
    result: null,
    selectedSiteId: null,
    selectedVehicleId: null,
    selectedShipmentId: null,
    isOptimizing: false,
};

export const useVRPStore = create<VRPState>((set) => ({
    ...initialState,

    addSite: (site) => set((state) => ({ sites: [...state.sites, site] })),
    updateSite: (id, updates) => set((state) => ({
        sites: state.sites.map((s) => s.id === id ? { ...s, ...updates } : s)
    })),
    removeSite: (id) => set((state) => ({
        sites: state.sites.filter((s) => s.id !== id),
        // Also remove related vehicles and shipments
        vehicles: state.vehicles.filter((v) => v.start_site_id !== id && v.end_site_id !== id),
        shipments: state.shipments.filter((sh) => sh.pickup_site_id !== id && sh.delivery_site_id !== id),
    })),

    addVehicle: (vehicle) => set((state) => ({ vehicles: [...state.vehicles, vehicle] })),
    updateVehicle: (id, updates) => set((state) => ({
        vehicles: state.vehicles.map((v) => v.id === id ? { ...v, ...updates } : v)
    })),
    removeVehicle: (id) => set((state) => ({
        vehicles: state.vehicles.filter((v) => v.id !== id)
    })),

    addShipment: (shipment) => set((state) => ({ shipments: [...state.shipments, shipment] })),
    updateShipment: (id, updates) => set((state) => ({
        shipments: state.shipments.map((s) => s.id === id ? { ...s, ...updates } : s)
    })),
    removeShipment: (id) => set((state) => ({
        shipments: state.shipments.filter((s) => s.id !== id)
    })),

    setMatrix: (matrix) => set({ matrix }),
    setResult: (result) => set({ result }),

    setSelectedSite: (id) => set({ selectedSiteId: id }),
    setSelectedVehicle: (id) => set({ selectedVehicleId: id }),
    setSelectedShipment: (id) => set({ selectedShipmentId: id }),
    setIsOptimizing: (val) => set({ isOptimizing: val }),

    reset: () => set(initialState),
}));
