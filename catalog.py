"""Demo catalog for VELORA — fictional operators, vehicles, routes."""

FLEET_OS_URL = "https://fleet-dispatch-demo-8c37.surge.sh/"

FX = {
    "TWD": 1.0,
    "USD": 0.031,
    "EUR": 0.028,
    "JPY": 4.6,
    "KRW": 42.0,
    "GBP": 0.024,
    "AED": 0.114,
    "SAR": 0.116,
}

SYMBOL = {
    "TWD": "NT$",
    "USD": "$",
    "EUR": "€",
    "JPY": "¥",
    "KRW": "₩",
    "GBP": "£",
    "AED": "AED",
    "SAR": "SAR",
}

FEATURE_FLAGS = {
    "car_rental": False,
    "intercity": False,
    "events": False,
    "corporate": False,
    "loyalty": False,
}

OPERATORS = [
    {"id": "op-aurora", "name": "Aurora Chauffeurs", "rating": 4.92, "rides": 18420, "city": "Taipei"},
    {"id": "op-lumen", "name": "Lumen Transfer Co.", "rating": 4.88, "rides": 12110, "city": "Taipei"},
    {"id": "op-pacific", "name": "Pacific Black Car", "rating": 4.95, "rides": 8604, "city": "Kaohsiung"},
    {"id": "op-formosa", "name": "Formosa Fleet", "rating": 4.81, "rides": 9902, "city": "Taichung"},
    {"id": "op-jade", "name": "Jade Green Mobility", "rating": 4.90, "rides": 5403, "city": "Taipei"},
]

CLASSES = [
    {"id": "economy", "name": "Economy Sedan", "example": "Toyota Corolla or similar", "pax": 3, "bags": 2, "doors": 4, "ac": True, "auto": True, "ev": False, "premium": False, "wheelchair": False, "meet": True, "child": True, "mult": 1.0, "img": "https://images.unsplash.com/photo-1549317661-bd32c8ce0db2?auto=format&fit=crop&w=1200&q=70"},
    {"id": "standard", "name": "Standard Sedan", "example": "Toyota Camry or similar", "pax": 3, "bags": 3, "doors": 4, "ac": True, "auto": True, "ev": False, "premium": False, "wheelchair": False, "meet": True, "child": True, "mult": 1.15, "img": "https://images.unsplash.com/photo-1552519507-da3b142c6e3d?auto=format&fit=crop&w=1200&q=70"},
    {"id": "business", "name": "Business Sedan", "example": "Mercedes-Benz E-Class or similar", "pax": 3, "bags": 3, "doors": 4, "ac": True, "auto": True, "ev": False, "premium": True, "wheelchair": False, "meet": True, "child": True, "mult": 1.85, "img": "https://images.unsplash.com/photo-1618843479313-40f8afb4b4d8?auto=format&fit=crop&w=1200&q=70"},
    {"id": "luxury", "name": "Luxury Sedan", "example": "Mercedes-Benz S-Class or similar", "pax": 3, "bags": 3, "doors": 4, "ac": True, "auto": True, "ev": False, "premium": True, "wheelchair": False, "meet": True, "child": True, "mult": 2.6, "img": "https://images.unsplash.com/photo-1563720360172-67b8f3dce741?auto=format&fit=crop&w=1200&q=70"},
    {"id": "suv", "name": "SUV", "example": "Toyota RAV4 or similar", "pax": 4, "bags": 4, "doors": 5, "ac": True, "auto": True, "ev": False, "premium": False, "wheelchair": False, "meet": True, "child": True, "mult": 1.4, "img": "https://images.unsplash.com/photo-1519641471654-76ce0107ad1b?auto=format&fit=crop&w=1200&q=70"},
    {"id": "premium_suv", "name": "Premium SUV", "example": "Mercedes-Benz GLS or similar", "pax": 5, "bags": 5, "doors": 5, "ac": True, "auto": True, "ev": False, "premium": True, "wheelchair": False, "meet": True, "child": True, "mult": 2.2, "img": "https://images.unsplash.com/photo-1503376780353-7e6692767b70?auto=format&fit=crop&w=1200&q=70"},
    {"id": "mpv", "name": "MPV", "example": "Toyota Alphard or similar", "pax": 6, "bags": 6, "doors": 5, "ac": True, "auto": True, "ev": False, "premium": True, "wheelchair": False, "meet": True, "child": True, "mult": 1.95, "img": "https://images.unsplash.com/photo-1544620341-11cb2cd49d66?auto=format&fit=crop&w=1200&q=70"},
    {"id": "van", "name": "Van", "example": "Volkswagen Multivan or similar", "pax": 7, "bags": 7, "doors": 5, "ac": True, "auto": True, "ev": False, "premium": False, "wheelchair": True, "meet": True, "child": True, "mult": 1.75, "img": "https://images.unsplash.com/photo-1464219789935-c2d9d9aba894?auto=format&fit=crop&w=1200&q=70"},
    {"id": "minibus", "name": "Minibus", "example": "Toyota Coaster or similar", "pax": 14, "bags": 14, "doors": 3, "ac": True, "auto": True, "ev": False, "premium": False, "wheelchair": True, "meet": True, "child": True, "mult": 2.8, "img": "https://images.unsplash.com/photo-1570125909232-eb263c188f7e?auto=format&fit=crop&w=1200&q=70"},
    {"id": "ev", "name": "Electric Sedan", "example": "Tesla Model 3 or similar", "pax": 3, "bags": 2, "doors": 4, "ac": True, "auto": True, "ev": True, "premium": True, "wheelchair": False, "meet": True, "child": True, "mult": 1.55, "img": "https://images.unsplash.com/photo-1560958089-b8a1929cea89?auto=format&fit=crop&w=1200&q=70"},
]

VEHICLES = [
    {"id": "v01", "class_id": "economy", "operator_id": "op-aurora", "brand": "Toyota", "model": "Corolla", "year": 2023, "color": "Silver", "plate": "TPE-4410", "fuel": "hybrid", "status": "active"},
    {"id": "v02", "class_id": "economy", "operator_id": "op-formosa", "brand": "Honda", "model": "Civic", "year": 2022, "color": "White", "plate": "TXG-2291", "fuel": "petrol", "status": "active"},
    {"id": "v03", "class_id": "standard", "operator_id": "op-aurora", "brand": "Toyota", "model": "Camry", "year": 2024, "color": "Black", "plate": "TPE-8801", "fuel": "hybrid", "status": "active"},
    {"id": "v04", "class_id": "standard", "operator_id": "op-lumen", "brand": "Nissan", "model": "Altima", "year": 2023, "color": "Grey", "plate": "TPE-1024", "fuel": "petrol", "status": "active"},
    {"id": "v05", "class_id": "business", "operator_id": "op-aurora", "brand": "Mercedes-Benz", "model": "E-Class", "year": 2024, "color": "Obsidian", "plate": "TPE-6666", "fuel": "hybrid", "status": "active"},
    {"id": "v06", "class_id": "business", "operator_id": "op-pacific", "brand": "BMW", "model": "5 Series", "year": 2023, "color": "Navy", "plate": "KHH-3388", "fuel": "petrol", "status": "active"},
    {"id": "v07", "class_id": "luxury", "operator_id": "op-pacific", "brand": "Mercedes-Benz", "model": "S-Class", "year": 2024, "color": "Black", "plate": "KHH-0007", "fuel": "hybrid", "status": "active"},
    {"id": "v08", "class_id": "luxury", "operator_id": "op-aurora", "brand": "BMW", "model": "7 Series", "year": 2023, "color": "White", "plate": "TPE-7001", "fuel": "petrol", "status": "active"},
    {"id": "v09", "class_id": "suv", "operator_id": "op-lumen", "brand": "Toyota", "model": "RAV4", "year": 2024, "color": "Pearl", "plate": "TPE-5520", "fuel": "hybrid", "status": "active"},
    {"id": "v10", "class_id": "suv", "operator_id": "op-formosa", "brand": "Honda", "model": "CR-V", "year": 2023, "color": "Blue", "plate": "TXG-4419", "fuel": "petrol", "status": "active"},
    {"id": "v11", "class_id": "premium_suv", "operator_id": "op-aurora", "brand": "Mercedes-Benz", "model": "GLS", "year": 2024, "color": "Black", "plate": "TPE-9111", "fuel": "petrol", "status": "active"},
    {"id": "v12", "class_id": "premium_suv", "operator_id": "op-jade", "brand": "BMW", "model": "X7", "year": 2023, "color": "Grey", "plate": "TPE-7710", "fuel": "petrol", "status": "active"},
    {"id": "v13", "class_id": "mpv", "operator_id": "op-lumen", "brand": "Toyota", "model": "Alphard", "year": 2024, "color": "Pearl", "plate": "TPE-3330", "fuel": "hybrid", "status": "active"},
    {"id": "v14", "class_id": "mpv", "operator_id": "op-formosa", "brand": "Toyota", "model": "Vellfire", "year": 2023, "color": "Black", "plate": "TXG-2218", "fuel": "hybrid", "status": "active"},
    {"id": "v15", "class_id": "van", "operator_id": "op-pacific", "brand": "Volkswagen", "model": "Multivan", "year": 2022, "color": "Silver", "plate": "KHH-4410", "fuel": "diesel", "status": "active"},
    {"id": "v16", "class_id": "van", "operator_id": "op-formosa", "brand": "Hyundai", "model": "Staria", "year": 2024, "color": "White", "plate": "TXG-9088", "fuel": "diesel", "status": "active"},
    {"id": "v17", "class_id": "minibus", "operator_id": "op-pacific", "brand": "Toyota", "model": "Coaster", "year": 2021, "color": "White", "plate": "KHH-1200", "fuel": "diesel", "status": "active"},
    {"id": "v18", "class_id": "minibus", "operator_id": "op-formosa", "brand": "Fuso", "model": "Rosa", "year": 2020, "color": "White", "plate": "TXG-1502", "fuel": "diesel", "status": "maintenance"},
    {"id": "v19", "class_id": "ev", "operator_id": "op-jade", "brand": "Tesla", "model": "Model 3", "year": 2024, "color": "White", "plate": "TPE-EV03", "fuel": "electric", "status": "active"},
    {"id": "v20", "class_id": "ev", "operator_id": "op-jade", "brand": "Tesla", "model": "Model Y", "year": 2024, "color": "Black", "plate": "TPE-EV19", "fuel": "electric", "status": "active"},
]

DRIVERS = [
    {"id": "d01", "first": "Wei", "last": "Lin", "photo": "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?auto=format&fit=crop&w=200&q=60", "rating": 4.97, "lang": ["en", "zh-TW"], "vehicle_id": "v03", "operator_id": "op-aurora", "status": "online", "lat": 25.06, "lng": 121.30},
    {"id": "d02", "first": "Mei", "last": "Chen", "photo": "https://images.unsplash.com/photo-1544005313-94ddf0286df2?auto=format&fit=crop&w=200&q=60", "rating": 4.93, "lang": ["zh-TW"], "vehicle_id": "v09", "operator_id": "op-lumen", "status": "online", "lat": 25.04, "lng": 121.52},
    {"id": "d03", "first": "Kenji", "last": "Takahashi", "photo": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&w=200&q=60", "rating": 5.0, "lang": ["en", "ja", "zh-TW"], "vehicle_id": "v05", "operator_id": "op-aurora", "status": "busy", "lat": 25.08, "lng": 121.24},
    {"id": "d04", "first": "Amina", "last": "Hassan", "photo": "https://images.unsplash.com/photo-1531123897727-8f129e1688ce?auto=format&fit=crop&w=200&q=60", "rating": 4.91, "lang": ["en", "ar"], "vehicle_id": "v19", "operator_id": "op-jade", "status": "online", "lat": 25.03, "lng": 121.56},
    {"id": "d05", "first": "Hao", "last": "Wang", "photo": "https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?auto=format&fit=crop&w=200&q=60", "rating": 4.88, "lang": ["zh-TW", "en"], "vehicle_id": "v13", "operator_id": "op-lumen", "status": "online", "lat": 25.047, "lng": 121.517},
    {"id": "d06", "first": "Sofia", "last": "Reyes", "photo": "https://images.unsplash.com/photo-1524504388940-b1c1722653e1?auto=format&fit=crop&w=200&q=60", "rating": 4.94, "lang": ["en"], "vehicle_id": "v07", "operator_id": "op-pacific", "status": "offline", "lat": 22.63, "lng": 120.30},
    {"id": "d07", "first": "Jun", "last": "Park", "photo": "https://images.unsplash.com/photo-1507591064344-4c6ce005b128?auto=format&fit=crop&w=200&q=60", "rating": 4.86, "lang": ["ko", "en"], "vehicle_id": "v06", "operator_id": "op-pacific", "status": "online", "lat": 22.58, "lng": 120.35},
    {"id": "d08", "first": "Yuna", "last": "Huang", "photo": "https://images.unsplash.com/photo-1487412720507-e7ab37603c6f?auto=format&fit=crop&w=200&q=60", "rating": 4.99, "lang": ["zh-TW", "en"], "vehicle_id": "v11", "operator_id": "op-aurora", "status": "online", "lat": 25.07, "lng": 121.55},
    {"id": "d09", "first": "Omar", "last": "Khalid", "photo": "https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?auto=format&fit=crop&w=200&q=60", "rating": 4.84, "lang": ["ar", "en"], "vehicle_id": "v15", "operator_id": "op-pacific", "status": "busy", "lat": 22.62, "lng": 120.31},
    {"id": "d10", "first": "Lina", "last": "Wu", "photo": "https://images.unsplash.com/photo-1438761681033-6461ffad8d80?auto=format&fit=crop&w=200&q=60", "rating": 4.90, "lang": ["zh-CN", "en"], "vehicle_id": "v20", "operator_id": "op-jade", "status": "online", "lat": 25.05, "lng": 121.50},
]

LOCATIONS = [
    {"id": "tpe", "name": "Taoyuan International Airport (TPE)", "city": "Taoyuan", "kind": "airport", "lat": 25.0777, "lng": 121.2328, "terminals": ["T1", "T2"]},
    {"id": "tsa", "name": "Taipei Songshan Airport (TSA)", "city": "Taipei", "kind": "airport", "lat": 25.0694, "lng": 121.5525, "terminals": ["Main"]},
    {"id": "khh", "name": "Kaohsiung International Airport (KHH)", "city": "Kaohsiung", "kind": "airport", "lat": 22.5771, "lng": 120.3500, "terminals": ["I", "D"]},
    {"id": "rmq", "name": "Taichung International Airport (RMQ)", "city": "Taichung", "kind": "airport", "lat": 24.2647, "lng": 120.6206, "terminals": ["Main"]},
    {"id": "nrt", "name": "Narita International Airport (NRT)", "city": "Tokyo", "kind": "airport", "lat": 35.7720, "lng": 140.3929, "terminals": ["T1", "T2", "T3"]},
    {"id": "taipei-101", "name": "Taipei 101 / Xinyi", "city": "Taipei", "kind": "landmark", "lat": 25.0330, "lng": 121.5654},
    {"id": "taipei-main", "name": "Taipei Main Station", "city": "Taipei", "kind": "landmark", "lat": 25.0478, "lng": 121.5170},
    {"id": "ximen", "name": "Ximending", "city": "Taipei", "kind": "landmark", "lat": 25.0420, "lng": 121.5080},
    {"id": "beitou", "name": "Beitou Hot Springs", "city": "Taipei", "kind": "landmark", "lat": 25.1365, "lng": 121.5065},
    {"id": "jiufen", "name": "Jiufen Old Street", "city": "New Taipei", "kind": "landmark", "lat": 25.1097, "lng": 121.8443},
    {"id": "hsr-ty", "name": "THSR Taoyuan Station", "city": "Taoyuan", "kind": "landmark", "lat": 25.0132, "lng": 121.2152},
    {"id": "w-hotel", "name": "W Taipei", "city": "Taipei", "kind": "hotel", "lat": 25.0398, "lng": 121.5665},
    {"id": "mandarin", "name": "Mandarin Oriental Taipei", "city": "Taipei", "kind": "hotel", "lat": 25.0542, "lng": 121.5250},
    {"id": "grand-hilai", "name": "Grand Hi-Lai Kaohsiung", "city": "Kaohsiung", "kind": "hotel", "lat": 22.6193, "lng": 120.3060},
    {"id": "formosa-blvd", "name": "Formosa Boulevard", "city": "Kaohsiung", "kind": "landmark", "lat": 22.6314, "lng": 120.3019},
    {"id": "taichung-st", "name": "Taichung Station", "city": "Taichung", "kind": "landmark", "lat": 24.1368, "lng": 120.6850},
    {"id": "kenting", "name": "Kenting Main Street", "city": "Pingtung", "kind": "landmark", "lat": 21.9483, "lng": 120.7794},
    {"id": "office-nangang", "name": "Nangang Software Park", "city": "Taipei", "kind": "address", "lat": 25.0568, "lng": 121.6127},
]

FIXED_ROUTES = {
    ("tpe", "taipei-101"): 1380,
    ("tpe", "taipei-main"): 1280,
    ("tpe", "ximen"): 1250,
    ("tpe", "w-hotel"): 1420,
    ("tpe", "jiufen"): 1680,
    ("tpe", "hsr-ty"): 420,
    ("tsa", "taipei-101"): 480,
    ("khh", "formosa-blvd"): 520,
    ("khh", "grand-hilai"): 490,
    ("rmq", "taichung-st"): 650,
}

POPULAR = [
    {"id": "tpe-101", "from": "tpe", "to": "taipei-101", "mins": 55},
    {"id": "tpe-main", "from": "tpe", "to": "taipei-main", "mins": 50},
    {"id": "tpe-ximen", "from": "tpe", "to": "ximen", "mins": 48},
    {"id": "tpe-jiufen", "from": "tpe", "to": "jiufen", "mins": 70},
    {"id": "tsa-101", "from": "tsa", "to": "taipei-101", "mins": 20},
    {"id": "khh-city", "from": "khh", "to": "formosa-blvd", "mins": 25},
    {"id": "rmq-tc", "from": "rmq", "to": "taichung-st", "mins": 30},
    {"id": "tpe-hsr", "from": "tpe", "to": "hsr-ty", "mins": 15},
]

EXTRAS = [
    {"id": "child", "name": "Child seat", "price": 200},
    {"id": "infant", "name": "Infant seat", "price": 220},
    {"id": "booster", "name": "Booster seat", "price": 150},
    {"id": "meet", "name": "Meet & greet with name sign", "price": 180},
    {"id": "wait", "name": "Extra waiting time (30 min)", "price": 250},
    {"id": "stop", "name": "Additional stop", "price": 180},
    {"id": "luggage", "name": "Extra luggage handling", "price": 120},
    {"id": "wheelchair", "name": "Wheelchair assistance", "price": 0},
    {"id": "guarantee", "name": "Premium vehicle guarantee", "price": 350},
]

PROMOS = {
    "VELORA10": {"type": "pct", "value": 10, "min": 800, "label": "10% off"},
    "AIRPORT200": {"type": "flat", "value": 200, "min": 1000, "label": "NT$200 airport"},
    "NEWGUEST": {"type": "flat", "value": 150, "min": 0, "label": "New guest NT$150"},
}

PRICING = {
    "base": 420,
    "per_km": 28,
    "per_min": 6,
    "min_fare": 520,
    "airport": 80,
    "night": 0.18,
    "weekend": 0.08,
    "stop": 180,
    "service_fee": 0.04,
    "waiting": 8,
}

REVIEWS = [
    {"id": "rv1", "name": "Elena M.", "stars": 5, "ride": "TPE → Taipei 101", "text": "Driver waited after a delayed flight. Quiet, spotless Camry.", "date": "2026-08-12", "cats": {"driver": 5, "clean": 5, "punctual": 5, "comfort": 5, "safety": 5, "value": 5}},
    {"id": "rv2", "name": "Kenji T.", "stars": 5, "ride": "TPE → Jiufen", "text": "Alphard fit family luggage. Clear name sign at arrivals.", "date": "2026-08-28", "cats": {"driver": 5, "clean": 5, "punctual": 5, "comfort": 5, "safety": 5, "value": 4}},
    {"id": "rv3", "name": "Sara A.", "stars": 4, "ride": "KHH → Formosa Boulevard", "text": "Transparent NT$ total. Night surcharge shown before pay.", "date": "2026-09-02", "cats": {"driver": 4, "clean": 5, "punctual": 5, "comfort": 4, "safety": 5, "value": 5}},
    {"id": "rv4", "name": "Noah P.", "stars": 5, "ride": "TSA → Xinyi", "text": "Seven minutes from gate to car. Business sedan as booked.", "date": "2026-09-05", "cats": {"driver": 5, "clean": 5, "punctual": 5, "comfort": 5, "safety": 5, "value": 4}},
]

FAQ = [
    {"q": "How will I find my driver?", "a": "For meet & greet, your driver waits in arrivals with a name sign. Otherwise they message the pickup pin and plate."},
    {"q": "What if my flight is delayed?", "a": "Enable flight tracking. We update pickup, notify the driver, and apply the waiting policy automatically."},
    {"q": "How much luggage can I bring?", "a": "Each vehicle lists suitcase capacity. Add extra luggage handling if you exceed it."},
    {"q": "Can I book for someone else?", "a": "Yes. Enter booker and passenger details separately at checkout."},
    {"q": "Can I cancel?", "a": "Eligible rides: free >24h, partial 6–24h, none under 6h. Exact rule is shown before pay."},
    {"q": "Are tolls included?", "a": "On most Taipei airport routes tolls are estimated in the total. The breakdown says included vs separate."},
    {"q": "Can I request a child seat?", "a": "Yes — child, infant, or booster as paid extras, subject to stock."},
    {"q": "How long will the driver wait?", "a": "Airport pickups include 45 minutes after landing when flight tracking is on. Extra waiting can be added."},
]

HELP = [
    {"id": "booking", "title": "Booking"},
    {"id": "payment", "title": "Payment"},
    {"id": "cancellation", "title": "Cancellation"},
    {"id": "driver", "title": "Driver"},
    {"id": "airport", "title": "Airport pickup"},
    {"id": "lost", "title": "Lost property"},
    {"id": "refund", "title": "Refund"},
    {"id": "account", "title": "Account"},
]

DRIVER_REVIEWS = [
    {"id": "rv1", "driver_id": "d01", "name": "E. Chen", "stars": 5, "text": "Wei was at T2 with a name sign before we cleared immigration.", "date": "2026-08-12", "verified": True, "punctuality": 5, "cleanliness": 5, "safety": 5},
    {"id": "rv2", "driver_id": "d01", "name": "M. Sato", "stars": 5, "text": "Quiet cabin, water, and a perfect Xinyi drop-off.", "date": "2026-08-28", "verified": True, "punctuality": 5, "cleanliness": 5, "safety": 5},
    {"id": "rv3", "driver_id": "d02", "name": "A. Khan", "stars": 4, "text": "Slight traffic delay, Mei messaged ETA twice.", "date": "2026-09-02", "verified": True, "punctuality": 4, "cleanliness": 5, "safety": 5},
    {"id": "rv4", "driver_id": "d08", "name": "L. Park", "stars": 5, "text": "Yuna’s GLS was immaculate. Kids loved the booster.", "date": "2026-09-05", "verified": True, "punctuality": 5, "cleanliness": 5, "safety": 5},
]
