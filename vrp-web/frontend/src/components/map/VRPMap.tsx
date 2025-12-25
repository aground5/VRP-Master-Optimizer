'use client';

/**
 * VRP Map Component
 * Allows users to place sites on the map
 */
import { useCallback, useState } from 'react';
import Map, { Marker, NavigationControl, Source, Layer } from 'react-map-gl/maplibre';
import type { MapLayerMouseEvent } from 'react-map-gl/maplibre';
import { useVRPStore } from '@/lib/store/vrp-store';
import type { Site, SiteType } from '@/types/vrp';
import 'maplibre-gl/dist/maplibre-gl.css';

const INITIAL_VIEW = {
    latitude: 37.5665,
    longitude: 126.9780,
    zoom: 11,
};

// MapTiler free style
const MAP_STYLE = 'https://api.maptiler.com/maps/streets/style.json?key=Wq8lhCKnogtzu1SfzcJE';

// Fallback to OSM style if no key
const OSM_STYLE = {
    version: 8,
    sources: {
        osm: {
            type: 'raster',
            tiles: ['https://tile.openstreetmap.org/{z}/{x}/{y}.png'],
            tileSize: 256,
            attribution: '© OpenStreetMap contributors',
        },
    },
    layers: [{ id: 'osm', type: 'raster', source: 'osm' }],
};

interface VRPMapProps {
    onSiteClick?: (siteId: string) => void;
}

export function VRPMap({ onSiteClick }: VRPMapProps) {
    const { sites, addSite, selectedSiteId, setSelectedSite, result } = useVRPStore();
    const [addMode, setAddMode] = useState<SiteType | null>(null);

    const handleMapClick = useCallback((e: MapLayerMouseEvent) => {
        if (!addMode) return;

        const newSite: Site = {
            id: `site_${Date.now()}`,
            name: `${addMode === 'depot' ? 'Depot' : 'Customer'} ${sites.length + 1}`,
            type: addMode,
            coords: { lat: e.lngLat.lat, lng: e.lngLat.lng },
            service_duration: 10,
            zone_id: 0,
        };

        addSite(newSite);
        setAddMode(null);
    }, [addMode, sites.length, addSite]);

    const handleMarkerClick = (siteId: string) => {
        setSelectedSite(siteId);
        onSiteClick?.(siteId);
    };

    // Route lines from result
    const routeLines = result?.routes.map((route, idx) => {
        const coords = route.stops
            .map((stop) => {
                const site = sites.find((s) => s.id === stop.site_id);
                return site ? [site.coords.lng, site.coords.lat] as [number, number] : null;
            })
            .filter((c): c is [number, number] => c !== null);

        return {
            type: 'Feature' as const,
            properties: { vehicleIdx: idx },
            geometry: { type: 'LineString' as const, coordinates: coords },
        };
    }) || [];

    const routeGeoJSON: GeoJSON.FeatureCollection = {
        type: 'FeatureCollection',
        features: routeLines,
    };

    return (
        <div className="relative w-full h-full">
            {/* Add Site Buttons */}
            <div className="absolute top-4 left-4 z-10 flex gap-2">
                <button
                    className={`px-3 py-2 rounded-md text-sm font-medium ${addMode === 'depot' ? 'bg-blue-600 text-white' : 'bg-white shadow'
                        }`}
                    onClick={() => setAddMode(addMode === 'depot' ? null : 'depot')}
                >
                    🏭 Add Depot
                </button>
                <button
                    className={`px-3 py-2 rounded-md text-sm font-medium ${addMode === 'customer' ? 'bg-green-600 text-white' : 'bg-white shadow'
                        }`}
                    onClick={() => setAddMode(addMode === 'customer' ? null : 'customer')}
                >
                    📍 Add Customer
                </button>
            </div>

            {addMode && (
                <div className="absolute top-16 left-4 z-10 bg-yellow-100 px-3 py-2 rounded text-sm">
                    Click on map to place {addMode}
                </div>
            )}

            <Map
                initialViewState={INITIAL_VIEW}
                style={{ width: '100%', height: '100%' }}
                mapStyle={OSM_STYLE as any}
                onClick={handleMapClick}
                cursor={addMode ? 'crosshair' : 'grab'}
            >
                <NavigationControl position="top-right" />

                {/* Route Lines */}
                {result && (
                    <Source id="routes" type="geojson" data={routeGeoJSON}>
                        <Layer
                            id="route-lines"
                            type="line"
                            paint={{
                                'line-color': ['match', ['get', 'vehicleIdx'],
                                    0, '#3b82f6',
                                    1, '#22c55e',
                                    2, '#f59e0b',
                                    3, '#ef4444',
                                    '#6b7280'
                                ],
                                'line-width': 4,
                                'line-opacity': 0.8,
                            }}
                        />
                    </Source>
                )}

                {/* Site Markers */}
                {sites.map((site) => (
                    <Marker
                        key={site.id}
                        latitude={site.coords.lat}
                        longitude={site.coords.lng}
                        onClick={(e) => {
                            e.originalEvent.stopPropagation();
                            handleMarkerClick(site.id);
                        }}
                    >
                        <div
                            className={`w-8 h-8 flex items-center justify-center rounded-full cursor-pointer text-lg
                ${site.type === 'depot' ? 'bg-blue-500' : 'bg-green-500'}
                ${selectedSiteId === site.id ? 'ring-4 ring-yellow-400' : ''}
              `}
                        >
                            {site.type === 'depot' ? '🏭' : '📍'}
                        </div>
                    </Marker>
                ))}
            </Map>
        </div>
    );
}
