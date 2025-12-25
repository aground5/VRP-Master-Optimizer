"""
Verify the site visit overlap issue.
"""

TEST_DATA = {
    "shipments": [
        {"id": "ship_1", "name": "주문 1 (강남→잠실)", "pickup_site_id": "site_gangnam", "delivery_site_id": "site_jamsil"},
        {"id": "ship_2", "name": "주문 2 (서초→올림픽)", "pickup_site_id": "site_seocho", "delivery_site_id": "site_olympic"},
        {"id": "ship_3", "name": "주문 3 (양재→가락)", "pickup_site_id": "site_yangjae", "delivery_site_id": "site_garak"},
        {"id": "ship_4", "name": "주문 4 (여의도→홍대)", "pickup_site_id": "site_yeouido", "delivery_site_id": "site_hongdae"},
        {"id": "ship_5", "name": "주문 5 (마포→종로)", "pickup_site_id": "site_mapo", "delivery_site_id": "site_jongno"},
        {"id": "ship_6", "name": "주문 6 (명동→서울역)", "pickup_site_id": "site_myeongdong", "delivery_site_id": "site_seoul_st"},
        {"id": "ship_7", "name": "주문 7 (노원→수유)", "pickup_site_id": "site_nowon", "delivery_site_id": "site_suyu"},
        {"id": "ship_8", "name": "주문 8 (잠실→강남)", "pickup_site_id": "site_jamsil", "delivery_site_id": "site_gangnam"},
    ]
}

from collections import defaultdict

print("="*60)
print("SITE VISIT FREQUENCY ANALYSIS")
print("="*60)

site_visits = defaultdict(list)

for ship in TEST_DATA["shipments"]:
    site_visits[ship["pickup_site_id"]].append(f"{ship['name']} (pickup)")
    site_visits[ship["delivery_site_id"]].append(f"{ship['name']} (delivery)")

print("\nSites that need multiple visits:")
for site_id, visits in site_visits.items():
    if len(visits) > 1:
        print(f"\n❌ {site_id} needs {len(visits)} visits:")
        for v in visits:
            print(f"   - {v}")

print("\n" + "="*60)
print("CONCLUSION")
print("="*60)
print("""
The current routing constraint enforces:
  sum(visits_bools) == is_served[c]

Where is_served[c] is a BOOLEAN (0 or 1).

This means each location can only be visited AT MOST ONCE.

But in the problem data:
  - site_gangnam: pickup for ship_1, delivery for ship_8 (needs 2 visits)
  - site_jamsil: delivery for ship_1, pickup for ship_8 (needs 2 visits)

This is INFEASIBLE by design!

SOLUTION OPTIONS:
1. Change the model to track per-shipment visits, not per-location visits
2. Allow multiple visits to the same location
3. Split pickup/delivery into separate "virtual" locations
""")
