/**
 * Example Data - Seoul Area with CJ-inspired logistics sites
 */
import type { Site, Vehicle, Shipment, MatrixData } from '@/types/vrp';

// 17 sites around Seoul metropolitan area (time windows are on SHIPMENTS, not sites)
export const exampleSites: Site[] = [
    // Depots (CJ Logistics Hubs & Sub-terminals)
    { id: 'depot_gunpo', name: 'CJ 군포허브', type: 'depot', coords: { lat: 37.3616, lng: 126.9352 }, service_duration: 0, zone_id: 0 },
    { id: 'depot_icheon', name: 'CJ 이천허브', type: 'depot', coords: { lat: 37.2720, lng: 127.4350 }, service_duration: 0, zone_id: 0 },
    { id: 'depot_gimpo', name: 'CJ 김포서브', type: 'depot', coords: { lat: 37.6152, lng: 126.7157 }, service_duration: 0, zone_id: 0 },
    { id: 'depot_yongin', name: 'CJ 용인허브', type: 'depot', coords: { lat: 37.2410, lng: 127.1775 }, service_duration: 0, zone_id: 0 },

    // Zone 1: Gangnam/Seocho
    { id: 'site_gangnam', name: '강남역', type: 'customer', coords: { lat: 37.4979, lng: 127.0276 }, service_duration: 15, zone_id: 1 },
    { id: 'site_seocho', name: '서초동', type: 'customer', coords: { lat: 37.4837, lng: 127.0324 }, service_duration: 15, zone_id: 1 },
    { id: 'site_yangjae', name: '양재역', type: 'customer', coords: { lat: 37.4846, lng: 127.0344 }, service_duration: 15, zone_id: 1 },

    // Zone 2: Songpa/Jamsil
    { id: 'site_jamsil', name: '잠실역', type: 'customer', coords: { lat: 37.5133, lng: 127.1001 }, service_duration: 20, zone_id: 2 },
    { id: 'site_olympic', name: '올림픽공원', type: 'customer', coords: { lat: 37.5209, lng: 127.1215 }, service_duration: 15, zone_id: 2 },
    { id: 'site_garak', name: '가락시장', type: 'customer', coords: { lat: 37.4925, lng: 127.1180 }, service_duration: 25, zone_id: 2 },

    // Zone 3: Mapo/Yeouido
    { id: 'site_yeouido', name: '여의도', type: 'customer', coords: { lat: 37.5219, lng: 126.9245 }, service_duration: 15, zone_id: 3 },
    { id: 'site_hongdae', name: '홍대입구', type: 'customer', coords: { lat: 37.5563, lng: 126.9237 }, service_duration: 20, zone_id: 3 },
    { id: 'site_mapo', name: '마포구청', type: 'customer', coords: { lat: 37.5663, lng: 126.9014 }, service_duration: 15, zone_id: 3 },

    // Zone 4: Jongno/Jung-gu
    { id: 'site_jongno', name: '종로3가', type: 'customer', coords: { lat: 37.5714, lng: 126.9920 }, service_duration: 15, zone_id: 4 },
    { id: 'site_myeongdong', name: '명동', type: 'customer', coords: { lat: 37.5636, lng: 126.9869 }, service_duration: 20, zone_id: 4 },
    { id: 'site_seoul_st', name: '서울역', type: 'customer', coords: { lat: 37.5547, lng: 126.9707 }, service_duration: 15, zone_id: 4 },

    // Zone 5: Nowon/Dobong
    { id: 'site_nowon', name: '노원역', type: 'customer', coords: { lat: 37.6554, lng: 127.0614 }, service_duration: 15, zone_id: 5 },
    { id: 'site_suyu', name: '수유역', type: 'customer', coords: { lat: 37.6377, lng: 127.0252 }, service_duration: 15, zone_id: 5 },
];

export const exampleVehicles: Vehicle[] = [
    {
        id: 'truck_1',
        name: '1호차 (1톤 포터)',
        start_site_id: 'depot_gunpo',
        end_site_id: 'depot_gunpo',
        capacity: { weight: 1000, volume: 8 }, // 1000kg, 8 CBM (std 1-ton truck)
        cost: { fixed: 50000, per_km: 1500, per_minute: 200 },
        shift: { start_time: 540, max_duration: 600, standard_duration: 480 }, // 09:00 Start
        break_rule: { interval_minutes: 240, duration_minutes: 60 },
        tags: [],
    },
    {
        id: 'truck_2',
        name: '2호차 (1톤 포터)',
        start_site_id: 'depot_gimpo',
        end_site_id: 'depot_gimpo',
        capacity: { weight: 1000, volume: 8 },
        cost: { fixed: 50000, per_km: 1500, per_minute: 200 },
        shift: { start_time: 540, max_duration: 600, standard_duration: 480 },
        break_rule: { interval_minutes: 240, duration_minutes: 60 },
        tags: [],
    },
    {
        id: 'truck_3',
        name: '3호차 (2.5톤 마이티)',
        start_site_id: 'depot_icheon',
        end_site_id: 'depot_icheon',
        capacity: { weight: 2500, volume: 16 }, // 2500kg, 16 CBM
        cost: { fixed: 120000, per_km: 2500, per_minute: 300 },
        shift: { start_time: 480, max_duration: 720, standard_duration: 480 }, // 08:00 Start
        break_rule: { interval_minutes: 240, duration_minutes: 60 },
        tags: ['heavy'],
    },
    {
        id: 'truck_4',
        name: '4호차 (2.5톤 마이티)',
        start_site_id: 'depot_yongin',
        end_site_id: 'depot_yongin',
        capacity: { weight: 2500, volume: 16 },
        cost: { fixed: 120000, per_km: 2500, per_minute: 300 },
        shift: { start_time: 480, max_duration: 720, standard_duration: 480 },
        break_rule: { interval_minutes: 240, duration_minutes: 60 },
        tags: ['heavy'],
    },
];

// 8 Pickup-Delivery pairs with more realistic weights/volumes
export const exampleShipments: Shipment[] = [
    {
        id: 'ship_1',
        name: '주문 1 (강남→잠실 - 가전)',
        pickup_site_id: 'site_gangnam',
        delivery_site_id: 'site_jamsil',
        pickup_window: { start: 600, end: 720 },
        delivery_window: { start: 780, end: 960 },
        cargo: { weight: 200, volume: 1.5 }, // Large appliance
        required_tags: [],
        priority: 1
    },
    {
        id: 'ship_2',
        name: '주문 2 (서초→올림픽 - 식품)',
        pickup_site_id: 'site_seocho',
        delivery_site_id: 'site_olympic',
        pickup_window: { start: 600, end: 720 },
        delivery_window: { start: 840, end: 1020 }, // 14:00 - 17:00
        cargo: { weight: 50, volume: 0.2 }, // Multiple food boxes
        required_tags: [],
        priority: 1
    },
    {
        id: 'ship_3',
        name: '주문 3 (양재→가락 - 자재)',
        pickup_site_id: 'site_yangjae',
        delivery_site_id: 'site_garak',
        pickup_window: { start: 660, end: 780 },
        delivery_window: { start: 900, end: 1140 },
        cargo: { weight: 500, volume: 2.0 }, // Heavy construction material
        required_tags: [],
        priority: 2
    },
    {
        id: 'ship_4',
        name: '주문 4 (여의도→홍대 - 사무용품)',
        pickup_site_id: 'site_yeouido',
        delivery_site_id: 'site_hongdae',
        pickup_window: { start: 600, end: 840 },
        delivery_window: { start: 900, end: 1200 },
        cargo: { weight: 30, volume: 0.1 },
        required_tags: [],
        priority: 1
    },
    {
        id: 'ship_5',
        name: '주문 5 (마포→종로 - 의류)',
        pickup_site_id: 'site_mapo',
        delivery_site_id: 'site_jongno',
        pickup_window: { start: 720, end: 900 },
        delivery_window: { start: 960, end: 1200 },
        cargo: { weight: 150, volume: 0.8 }, // Clothing racks
        required_tags: [],
        priority: 1
    },
    {
        id: 'ship_6',
        name: '주문 6 (명동→서울역 - 서적)',
        pickup_site_id: 'site_myeongdong',
        delivery_site_id: 'site_seoul_st',
        pickup_window: { start: 840, end: 960 }, // 14:00 - 16:00
        delivery_window: { start: 1020, end: 1260 }, // 17:00 - 21:00
        cargo: { weight: 800, volume: 1.2 }, // Heavy books
        required_tags: [],
        priority: 1
    },
    {
        id: 'ship_7',
        name: '주문 7 (노원→수유 - 가구)',
        pickup_site_id: 'site_nowon',
        delivery_site_id: 'site_suyu',
        pickup_window: { start: 600, end: 840 },
        delivery_window: { start: 900, end: 1200 },
        cargo: { weight: 1200, volume: 5.0 }, // Furniture set -> Needs large truck
        required_tags: ['heavy'],
        priority: 1
    },
    {
        id: 'ship_8',
        name: '주문 8 (잠실→강남 - 전자제품)',
        pickup_site_id: 'site_jamsil',
        delivery_site_id: 'site_gangnam',
        pickup_window: { start: 900, end: 1080 }, // 15:00 - 18:00
        delivery_window: { start: 1140, end: 1320 }, // 19:00 - 22:00
        cargo: { weight: 100, volume: 0.5 },
        required_tags: [],
        priority: 2
    },
];

// ============================================================================
// EXAMPLE DATA 2: Hub & Spoke (CJ Logistics Style)
// Scenario: All parcels sorted at Gunpo Hub, drivers load up and deliver.
// ============================================================================

export const exampleHubSpokeSites: Site[] = [
    // Hub (Central Depot)
    { id: 'depot_gunpo', name: 'CJ 군포허브 (Terminal)', type: 'depot', coords: { lat: 37.3616, lng: 126.9352 }, service_duration: 0, zone_id: 0 },

    // Delivery Zones (Gangnam, Seocho, Songpa, Mapo, etc.)
    { id: 'site_gangnam', name: '강남역', type: 'customer', coords: { lat: 37.4979, lng: 127.0276 }, service_duration: 5, zone_id: 1 },
    { id: 'site_seocho', name: '서초동', type: 'customer', coords: { lat: 37.4837, lng: 127.0324 }, service_duration: 5, zone_id: 1 },
    { id: 'site_yangjae', name: '양재역', type: 'customer', coords: { lat: 37.4846, lng: 127.0344 }, service_duration: 5, zone_id: 1 },
    { id: 'site_jamsil', name: '잠실역', type: 'customer', coords: { lat: 37.5133, lng: 127.1001 }, service_duration: 5, zone_id: 2 },
    { id: 'site_olympic', name: '올림픽공원', type: 'customer', coords: { lat: 37.5209, lng: 127.1215 }, service_duration: 5, zone_id: 2 },
    { id: 'site_garak', name: '가락시장', type: 'customer', coords: { lat: 37.4925, lng: 127.1180 }, service_duration: 5, zone_id: 2 },
    { id: 'site_yeouido', name: '여의도', type: 'customer', coords: { lat: 37.5219, lng: 126.9245 }, service_duration: 5, zone_id: 3 },
    { id: 'site_hongdae', name: '홍대입구', type: 'customer', coords: { lat: 37.5563, lng: 126.9237 }, service_duration: 5, zone_id: 3 },
    { id: 'site_mapo', name: '마포구청', type: 'customer', coords: { lat: 37.5663, lng: 126.9014 }, service_duration: 5, zone_id: 3 },
    { id: 'site_jongno', name: '종로3가', type: 'customer', coords: { lat: 37.5714, lng: 126.9920 }, service_duration: 5, zone_id: 4 },
    { id: 'site_myeongdong', name: '명동', type: 'customer', coords: { lat: 37.5636, lng: 126.9869 }, service_duration: 5, zone_id: 4 },
    { id: 'site_seoul_st', name: '서울역', type: 'customer', coords: { lat: 37.5547, lng: 126.9707 }, service_duration: 5, zone_id: 4 },
    { id: 'site_nowon', name: '노원역', type: 'customer', coords: { lat: 37.6554, lng: 127.0614 }, service_duration: 5, zone_id: 5 },
    { id: 'site_suyu', name: '수유역', type: 'customer', coords: { lat: 37.6377, lng: 127.0252 }, service_duration: 5, zone_id: 5 },
];

export const exampleHubSpokeVehicles: Vehicle[] = [
    {
        id: 'cj_truck_1', name: 'CJ대한통운 1호', start_site_id: 'depot_gunpo', end_site_id: 'depot_gunpo',
        capacity: { weight: 1000, volume: 8 },
        cost: { fixed: 50000, per_km: 1000, per_minute: 150 },
        shift: { start_time: 540, max_duration: 660, standard_duration: 540 }, // 09:00 - 20:00
        break_rule: { interval_minutes: 240, duration_minutes: 60 },
        tags: []
    },
    {
        id: 'cj_truck_2', name: 'CJ대한통운 2호', start_site_id: 'depot_gunpo', end_site_id: 'depot_gunpo',
        capacity: { weight: 1000, volume: 8 },
        cost: { fixed: 50000, per_km: 1000, per_minute: 150 },
        shift: { start_time: 540, max_duration: 660, standard_duration: 540 },
        break_rule: { interval_minutes: 240, duration_minutes: 60 },
        tags: []
    },
    {
        id: 'cj_truck_3', name: 'CJ대한통운 3호', start_site_id: 'depot_gunpo', end_site_id: 'depot_gunpo',
        capacity: { weight: 1000, volume: 8 },
        cost: { fixed: 50000, per_km: 1000, per_minute: 150 },
        shift: { start_time: 540, max_duration: 660, standard_duration: 540 },
        break_rule: { interval_minutes: 240, duration_minutes: 60 },
        tags: []
    },
    {
        id: 'cj_truck_4', name: 'CJ대한통운 4호', start_site_id: 'depot_gunpo', end_site_id: 'depot_gunpo',
        capacity: { weight: 1000, volume: 8 },
        cost: { fixed: 50000, per_km: 1000, per_minute: 150 },
        shift: { start_time: 540, max_duration: 660, standard_duration: 540 },
        break_rule: { interval_minutes: 240, duration_minutes: 60 },
        tags: []
    },
    {
        id: 'cj_truck_5', name: 'CJ대한통운 5호', start_site_id: 'depot_gunpo', end_site_id: 'depot_gunpo',
        capacity: { weight: 1000, volume: 8 },
        cost: { fixed: 50000, per_km: 1000, per_minute: 150 },
        shift: { start_time: 540, max_duration: 660, standard_duration: 540 },
        break_rule: { interval_minutes: 240, duration_minutes: 60 },
        tags: []
    }
];

export const exampleHubSpokeShipments: Shipment[] = [
    // Zone 1
    { id: 's_gj_1', name: '배송-강남01 (의류)', pickup_site_id: 'depot_gunpo', delivery_site_id: 'site_gangnam', pickup_window: { start: 540, end: 1200 }, delivery_window: { start: 540, end: 1320 }, cargo: { weight: 5, volume: 0.1 }, required_tags: [], priority: 1 },
    { id: 's_gj_2', name: '배송-강남02 (생수)', pickup_site_id: 'depot_gunpo', delivery_site_id: 'site_gangnam', pickup_window: { start: 540, end: 1200 }, delivery_window: { start: 540, end: 1320 }, cargo: { weight: 24, volume: 0.2 }, required_tags: [], priority: 1 },
    { id: 's_sc_1', name: '배송-서초01 (문구)', pickup_site_id: 'depot_gunpo', delivery_site_id: 'site_seocho', pickup_window: { start: 540, end: 1200 }, delivery_window: { start: 540, end: 1320 }, cargo: { weight: 3, volume: 0.05 }, required_tags: [], priority: 1 },
    { id: 's_sc_2', name: '배송-서초02 (식품)', pickup_site_id: 'depot_gunpo', delivery_site_id: 'site_seocho', pickup_window: { start: 540, end: 1200 }, delivery_window: { start: 540, end: 1320 }, cargo: { weight: 10, volume: 0.3 }, required_tags: [], priority: 1 },
    { id: 's_yj_1', name: '배송-양재01 (가전)', pickup_site_id: 'depot_gunpo', delivery_site_id: 'site_yangjae', pickup_window: { start: 540, end: 1200 }, delivery_window: { start: 540, end: 1320 }, cargo: { weight: 15, volume: 0.5 }, required_tags: [], priority: 1 },

    // Zone 2
    { id: 's_js_1', name: '배송-잠실01 (책)', pickup_site_id: 'depot_gunpo', delivery_site_id: 'site_jamsil', pickup_window: { start: 540, end: 1200 }, delivery_window: { start: 540, end: 1320 }, cargo: { weight: 8, volume: 0.1 }, required_tags: [], priority: 1 },
    { id: 's_ol_1', name: '배송-올림픽01 (운동기구)', pickup_site_id: 'depot_gunpo', delivery_site_id: 'site_olympic', pickup_window: { start: 540, end: 1200 }, delivery_window: { start: 540, end: 1320 }, cargo: { weight: 20, volume: 0.8 }, required_tags: [], priority: 1 },
    { id: 's_gr_1', name: '배송-가락01 (청과)', pickup_site_id: 'depot_gunpo', delivery_site_id: 'site_garak', pickup_window: { start: 540, end: 1200 }, delivery_window: { start: 540, end: 1320 }, cargo: { weight: 12, volume: 0.4 }, required_tags: [], priority: 1 },

    // Zone 3
    { id: 's_yi_1', name: '배송-여의도01 (서류)', pickup_site_id: 'depot_gunpo', delivery_site_id: 'site_yeouido', pickup_window: { start: 540, end: 1200 }, delivery_window: { start: 540, end: 1320 }, cargo: { weight: 1, volume: 0.01 }, required_tags: [], priority: 1 },
    { id: 's_yi_2', name: '배송-여의도02 (노트북)', pickup_site_id: 'depot_gunpo', delivery_site_id: 'site_yeouido', pickup_window: { start: 540, end: 1200 }, delivery_window: { start: 540, end: 1320 }, cargo: { weight: 3, volume: 0.05 }, required_tags: [], priority: 1 },
    { id: 's_hd_1', name: '배송-홍대01 (옷)', pickup_site_id: 'depot_gunpo', delivery_site_id: 'site_hongdae', pickup_window: { start: 540, end: 1200 }, delivery_window: { start: 540, end: 1320 }, cargo: { weight: 2, volume: 0.1 }, required_tags: [], priority: 1 },
    { id: 's_mp_1', name: '배송-마포01 (신발)', pickup_site_id: 'depot_gunpo', delivery_site_id: 'site_mapo', pickup_window: { start: 540, end: 1200 }, delivery_window: { start: 540, end: 1320 }, cargo: { weight: 2, volume: 0.1 }, required_tags: [], priority: 1 },

    // Zone 4
    { id: 's_jn_1', name: '배송-종로01 (부품)', pickup_site_id: 'depot_gunpo', delivery_site_id: 'site_jongno', pickup_window: { start: 540, end: 1200 }, delivery_window: { start: 540, end: 1320 }, cargo: { weight: 5, volume: 0.1 }, required_tags: [], priority: 1 },
    { id: 's_md_1', name: '배송-명동01 (화장품)', pickup_site_id: 'depot_gunpo', delivery_site_id: 'site_myeongdong', pickup_window: { start: 540, end: 1200 }, delivery_window: { start: 540, end: 1320 }, cargo: { weight: 4, volume: 0.1 }, required_tags: [], priority: 1 },
    { id: 's_st_1', name: '배송-서울역01 (잡화)', pickup_site_id: 'depot_gunpo', delivery_site_id: 'site_seoul_st', pickup_window: { start: 540, end: 1200 }, delivery_window: { start: 540, end: 1320 }, cargo: { weight: 6, volume: 0.2 }, required_tags: [], priority: 1 },

    // Zone 5
    { id: 's_nw_1', name: '배송-노원01 (쌀)', pickup_site_id: 'depot_gunpo', delivery_site_id: 'site_nowon', pickup_window: { start: 540, end: 1200 }, delivery_window: { start: 540, end: 1320 }, cargo: { weight: 20, volume: 0.2 }, required_tags: [], priority: 1 },
    { id: 's_nw_2', name: '배송-노원02 (기저귀)', pickup_site_id: 'depot_gunpo', delivery_site_id: 'site_nowon', pickup_window: { start: 540, end: 1200 }, delivery_window: { start: 540, end: 1320 }, cargo: { weight: 5, volume: 0.2 }, required_tags: [], priority: 1 },
    { id: 's_sy_1', name: '배송-수유01 (휴지)', pickup_site_id: 'depot_gunpo', delivery_site_id: 'site_suyu', pickup_window: { start: 540, end: 1200 }, delivery_window: { start: 540, end: 1320 }, cargo: { weight: 8, volume: 0.3 }, required_tags: [], priority: 1 },
];

export const exampleHubSpokeMatrix: MatrixData = {
    durations: [
        [0, 21, 21, 21, 26, 29, 25, 27, 31, 31, 30, 29, 28, 40, 38],
        [21, 0, 4, 4, 7, 11, 10, 13, 16, 18, 10, 10, 12, 21, 18],
        [20, 4, 0, 3, 9, 13, 10, 16, 19, 21, 13, 13, 15, 23, 20],
        [20, 4, 2, 0, 9, 13, 10, 14, 17, 19, 13, 13, 13, 23, 20],
        [25, 7, 9, 7, 0, 5, 4, 17, 20, 22, 14, 15, 16, 19, 19],
        [29, 11, 13, 12, 5, 0, 7, 21, 24, 26, 18, 19, 20, 22, 22],
        [25, 10, 10, 9, 4, 6, 0, 20, 23, 25, 17, 18, 19, 22, 22],
        [26, 14, 16, 17, 20, 24, 22, 0, 7, 9, 10, 10, 7, 24, 20],
        [31, 15, 18, 18, 22, 26, 24, 7, 0, 5, 9, 9, 7, 22, 18],
        [30, 18, 20, 21, 24, 28, 27, 8, 4, 0, 11, 12, 10, 23, 19],
        [30, 10, 13, 13, 16, 20, 18, 11, 9, 11, 0, 3, 6, 14, 10],
        [29, 9, 13, 12, 16, 20, 19, 10, 9, 11, 3, 0, 5, 16, 12],
        [28, 12, 14, 15, 18, 22, 21, 7, 7, 9, 5, 5, 0, 18, 14],
        [39, 21, 23, 22, 18, 22, 21, 24, 22, 23, 15, 16, 19, 0, 5],
        [37, 18, 20, 19, 18, 22, 21, 19, 18, 18, 10, 12, 15, 6, 0]
    ],
    distances: [
        [0, 20690, 20102, 20418, 25782, 27705, 25308, 25707, 29715, 28304, 29086, 27815, 27391, 40947, 37654],
        [20668, 0, 2268, 3259, 6756, 9441, 9554, 12406, 13169, 15596, 9509, 9024, 9847, 20658, 17002],
        [20069, 2139, 0, 1778, 7570, 10255, 8888, 14092, 15611, 18038, 11581, 11096, 12288, 22734, 19014],
        [20408, 2306, 794, 0, 7894, 10579, 9213, 13739, 15257, 17684, 11748, 11263, 11935, 23059, 19339],
        [25760, 6739, 7789, 6994, 0, 2787, 2900, 18972, 20163, 22859, 13885, 14133, 15761, 17364, 18912],
        [28419, 9397, 10447, 9653, 2658, 0, 4428, 21630, 22821, 25518, 16543, 16791, 18420, 19721, 20132],
        [25422, 9656, 9193, 8398, 2916, 3875, 0, 21889, 23080, 25776, 16802, 17050, 18678, 20178, 21263],
        [26951, 13907, 14239, 15548, 19648, 22333, 22445, 0, 6031, 7492, 9155, 8569, 6387, 22189, 18731],
        [29457, 13038, 15175, 16303, 19654, 22339, 22452, 5943, 0, 2957, 7175, 6927, 5182, 20164, 16706],
        [28181, 15541, 18743, 18807, 24152, 26837, 26950, 7424, 2955, 0, 10027, 9654, 7909, 22033, 17069],
        [30465, 9496, 12138, 12162, 13588, 16273, 16386, 9497, 7605, 10019, 0, 1428, 4514, 13346, 9888],
        [29542, 8574, 11216, 11839, 15190, 17875, 17988, 9376, 6764, 9461, 1373, 0, 3759, 14442, 10983],
        [27061, 10680, 12116, 13945, 17296, 19981, 20094, 5942, 5245, 7941, 4006, 2809, 0, 17075, 13617],
        [40952, 20641, 22961, 22166, 17356, 19804, 20154, 23135, 21243, 21143, 13838, 15066, 18152, 0, 4235],
        [37801, 17057, 19180, 18385, 17669, 20118, 20467, 18900, 17008, 16908, 9603, 10831, 13917, 4413, 0]
    ]
};
