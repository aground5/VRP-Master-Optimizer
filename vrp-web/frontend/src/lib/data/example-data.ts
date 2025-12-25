/**
 * Example Data - Seoul Area with CJ-inspired logistics sites
 */
import type { Site, Vehicle, Shipment } from '@/types/vrp';

// 17 sites around Seoul metropolitan area (time windows are on SHIPMENTS, not sites)
export const exampleSites: Site[] = [
    // Depots (CJ-inspired logistics centers)
    { id: 'depot_gunpo', name: 'CJ 군포센터', type: 'depot', coords: { lat: 37.3616, lng: 126.9352 }, service_duration: 0, zone_id: 0 },
    { id: 'depot_icheon', name: 'CJ 이천센터', type: 'depot', coords: { lat: 37.2720, lng: 127.4350 }, service_duration: 0, zone_id: 0 },

    // Zone 1: Gangnam/Seocho
    { id: 'site_gangnam', name: '강남역', type: 'customer', coords: { lat: 37.4979, lng: 127.0276 }, service_duration: 10, zone_id: 1 },
    { id: 'site_seocho', name: '서초동', type: 'customer', coords: { lat: 37.4837, lng: 127.0324 }, service_duration: 10, zone_id: 1 },
    { id: 'site_yangjae', name: '양재역', type: 'customer', coords: { lat: 37.4846, lng: 127.0344 }, service_duration: 10, zone_id: 1 },

    // Zone 2: Songpa/Jamsil
    { id: 'site_jamsil', name: '잠실역', type: 'customer', coords: { lat: 37.5133, lng: 127.1001 }, service_duration: 15, zone_id: 2 },
    { id: 'site_olympic', name: '올림픽공원', type: 'customer', coords: { lat: 37.5209, lng: 127.1215 }, service_duration: 10, zone_id: 2 },
    { id: 'site_garak', name: '가락시장', type: 'customer', coords: { lat: 37.4925, lng: 127.1180 }, service_duration: 20, zone_id: 2 },

    // Zone 3: Mapo/Yeouido
    { id: 'site_yeouido', name: '여의도', type: 'customer', coords: { lat: 37.5219, lng: 126.9245 }, service_duration: 10, zone_id: 3 },
    { id: 'site_hongdae', name: '홍대입구', type: 'customer', coords: { lat: 37.5563, lng: 126.9237 }, service_duration: 15, zone_id: 3 },
    { id: 'site_mapo', name: '마포구청', type: 'customer', coords: { lat: 37.5663, lng: 126.9014 }, service_duration: 10, zone_id: 3 },

    // Zone 4: Jongno/Jung-gu
    { id: 'site_jongno', name: '종로3가', type: 'customer', coords: { lat: 37.5714, lng: 126.9920 }, service_duration: 10, zone_id: 4 },
    { id: 'site_myeongdong', name: '명동', type: 'customer', coords: { lat: 37.5636, lng: 126.9869 }, service_duration: 15, zone_id: 4 },
    { id: 'site_seoul_st', name: '서울역', type: 'customer', coords: { lat: 37.5547, lng: 126.9707 }, service_duration: 10, zone_id: 4 },

    // Zone 5: Nowon/Dobong
    { id: 'site_nowon', name: '노원역', type: 'customer', coords: { lat: 37.6554, lng: 127.0614 }, service_duration: 10, zone_id: 5 },
    { id: 'site_suyu', name: '수유역', type: 'customer', coords: { lat: 37.6377, lng: 127.0252 }, service_duration: 10, zone_id: 5 },
];

export const exampleVehicles: Vehicle[] = [
    {
        id: 'truck_1',
        name: '1호차 (소형)',
        start_site_id: 'depot_gunpo',
        end_site_id: 'depot_gunpo',
        capacity: { weight: 30, volume: 30 },
        cost: { fixed: 300, per_km: 8, per_minute: 8 },
        shift: { start_time: 0, max_duration: 600, standard_duration: 480 },
        break_rule: { interval_minutes: 240, duration_minutes: 30 },
        tags: [],
    },
    {
        id: 'truck_2',
        name: '2호차 (소형)',
        start_site_id: 'depot_gunpo',
        end_site_id: 'depot_gunpo',
        capacity: { weight: 30, volume: 30 },
        cost: { fixed: 300, per_km: 8, per_minute: 8 },
        shift: { start_time: 0, max_duration: 600, standard_duration: 480 },
        break_rule: { interval_minutes: 240, duration_minutes: 30 },
        tags: [],
    },
    {
        id: 'truck_3',
        name: '3호차 (대형)',
        start_site_id: 'depot_icheon',
        end_site_id: 'depot_icheon',
        capacity: { weight: 80, volume: 80 },
        cost: { fixed: 800, per_km: 15, per_minute: 12 },
        shift: { start_time: 0, max_duration: 720, standard_duration: 480 },
        break_rule: { interval_minutes: 240, duration_minutes: 30 },
        tags: ['heavy'],
    },
    {
        id: 'truck_4',
        name: '4호차 (대형)',
        start_site_id: 'depot_icheon',
        end_site_id: 'depot_icheon',
        capacity: { weight: 80, volume: 80 },
        cost: { fixed: 800, per_km: 15, per_minute: 12 },
        shift: { start_time: 0, max_duration: 720, standard_duration: 480 },
        break_rule: { interval_minutes: 240, duration_minutes: 30 },
        tags: ['heavy'],
    },
];

// 8 Pickup-Delivery pairs with ORDER-SPECIFIC time windows
export const exampleShipments: Shipment[] = [
    { id: 'ship_1', name: '주문 1 (강남→잠실)', pickup_site_id: 'site_gangnam', delivery_site_id: 'site_jamsil', pickup_window: { start: 60, end: 120 }, delivery_window: { start: 150, end: 240 }, cargo: { weight: 10, volume: 10 }, required_tags: [], priority: 1 },
    { id: 'ship_2', name: '주문 2 (서초→올림픽)', pickup_site_id: 'site_seocho', delivery_site_id: 'site_olympic', pickup_window: { start: 90, end: 150 }, delivery_window: { start: 180, end: 270 }, cargo: { weight: 15, volume: 12 }, required_tags: [], priority: 1 },
    { id: 'ship_3', name: '주문 3 (양재→가락)', pickup_site_id: 'site_yangjae', delivery_site_id: 'site_garak', pickup_window: { start: 60, end: 120 }, delivery_window: { start: 120, end: 180 }, cargo: { weight: 8, volume: 8 }, required_tags: [], priority: 2 },
    { id: 'ship_4', name: '주문 4 (여의도→홍대)', pickup_site_id: 'site_yeouido', delivery_site_id: 'site_hongdae', pickup_window: { start: 120, end: 180 }, delivery_window: { start: 200, end: 300 }, cargo: { weight: 5, volume: 5 }, required_tags: [], priority: 1 },
    { id: 'ship_5', name: '주문 5 (마포→종로)', pickup_site_id: 'site_mapo', delivery_site_id: 'site_jongno', pickup_window: { start: 80, end: 140 }, delivery_window: { start: 160, end: 240 }, cargo: { weight: 12, volume: 10 }, required_tags: [], priority: 1 },
    { id: 'ship_6', name: '주문 6 (명동→서울역)', pickup_site_id: 'site_myeongdong', delivery_site_id: 'site_seoul_st', pickup_window: { start: 150, end: 210 }, delivery_window: { start: 240, end: 330 }, cargo: { weight: 6, volume: 6 }, required_tags: [], priority: 1 },
    { id: 'ship_7', name: '주문 7 (노원→수유)', pickup_site_id: 'site_nowon', delivery_site_id: 'site_suyu', pickup_window: { start: 100, end: 160 }, delivery_window: { start: 180, end: 250 }, cargo: { weight: 20, volume: 18 }, required_tags: ['heavy'], priority: 1 },
    { id: 'ship_8', name: '주문 8 (잠실→강남)', pickup_site_id: 'site_jamsil', delivery_site_id: 'site_gangnam', pickup_window: { start: 200, end: 280 }, delivery_window: { start: 300, end: 400 }, cargo: { weight: 7, volume: 7 }, required_tags: [], priority: 2 },
];
