"""
inventory_catalog.py

Master inventory catalog for
Maitri and Bharati Stations.
"""

INVENTORY_ITEMS = [

# =====================================================
# FOOD
# =====================================================

{
    "item":"Rice",
    "category":"Food",
    "unit":"kg",
    "capacity":6000,
    "quantity":6000,
    "minimum":1200,
    "critical":500,
    "daily_per_person":0.35,
    "supplier":"India Supply Vessel",
    "lead_time":120,
    "expiry_days":730
},

{
    "item":"Flour",
    "category":"Food",
    "unit":"kg",
    "capacity":3500,
    "quantity":3500,
    "minimum":700,
    "critical":250,
    "daily_per_person":0.15,
    "supplier":"India Supply Vessel",
    "lead_time":120,
    "expiry_days":365
},

{
    "item":"Sugar",
    "category":"Food",
    "unit":"kg",
    "capacity":1200,
    "quantity":1200,
    "minimum":250,
    "critical":80,
    "daily_per_person":0.04,
    "supplier":"India Supply Vessel",
    "lead_time":120,
    "expiry_days":1825
},

{
    "item":"Salt",
    "category":"Food",
    "unit":"kg",
    "capacity":800,
    "quantity":800,
    "minimum":120,
    "critical":40,
    "daily_per_person":0.01,
    "supplier":"India Supply Vessel",
    "lead_time":120,
    "expiry_days":3650
},

{
    "item":"Cooking Oil",
    "category":"Food",
    "unit":"liters",
    "capacity":1500,
    "quantity":1500,
    "minimum":300,
    "critical":100,
    "daily_per_person":0.03,
    "supplier":"India Supply Vessel",
    "lead_time":120,
    "expiry_days":540
},

{
    "item":"Milk Powder",
    "category":"Food",
    "unit":"kg",
    "capacity":900,
    "quantity":900,
    "minimum":180,
    "critical":70,
    "daily_per_person":0.02,
    "supplier":"India Supply Vessel",
    "lead_time":120,
    "expiry_days":540
},

{
    "item":"Frozen Vegetables",
    "category":"Food",
    "unit":"kg",
    "capacity":2200,
    "quantity":2200,
    "minimum":500,
    "critical":180,
    "daily_per_person":0.18,
    "supplier":"India Supply Vessel",
    "lead_time":120,
    "expiry_days":365
},

{
    "item":"Frozen Meat",
    "category":"Food",
    "unit":"kg",
    "capacity":2800,
    "quantity":2800,
    "minimum":500,
    "critical":180,
    "daily_per_person":0.22,
    "supplier":"India Supply Vessel",
    "lead_time":120,
    "expiry_days":365
},

{
    "item":"Pulses",
    "category":"Food",
    "unit":"kg",
    "capacity":2000,
    "quantity":2000,
    "minimum":400,
    "critical":120,
    "daily_per_person":0.08,
    "supplier":"India Supply Vessel",
    "lead_time":120,
    "expiry_days":730
},

# =====================================================
# MEDICAL
# =====================================================

{
    "item":"Antibiotics",
    "category":"Medical",
    "unit":"packs",
    "capacity":600,
    "quantity":600,
    "minimum":120,
    "critical":50,
    "daily_per_person":0.003,
    "supplier":"Medical Logistics",
    "lead_time":150,
    "expiry_days":730
},

{
    "item":"Painkillers",
    "category":"Medical",
    "unit":"packs",
    "capacity":1200,
    "quantity":1200,
    "minimum":250,
    "critical":80,
    "daily_per_person":0.005,
    "supplier":"Medical Logistics",
    "lead_time":150,
    "expiry_days":730
},

{
    "item":"IV Fluids",
    "category":"Medical",
    "unit":"bags",
    "capacity":300,
    "quantity":300,
    "minimum":60,
    "critical":25,
    "daily_per_person":0.001,
    "supplier":"Medical Logistics",
    "lead_time":150,
    "expiry_days":365
},

{
    "item":"Bandages",
    "category":"Medical",
    "unit":"packs",
    "capacity":500,
    "quantity":500,
    "minimum":120,
    "critical":40,
    "daily_per_person":0.002,
    "supplier":"Medical Logistics",
    "lead_time":150,
    "expiry_days":1825
},

{
    "item":"Oxygen Cylinders",
    "category":"Medical",
    "unit":"count",
    "capacity":80,
    "quantity":80,
    "minimum":15,
    "critical":6,
    "daily_per_person":0.0005,
    "supplier":"Medical Logistics",
    "lead_time":150,
    "expiry_days":3650
},
# =====================================================
# LABORATORY
# =====================================================

{
    "item":"Chemical Reagents",
    "category":"Laboratory",
    "unit":"kits",
    "capacity":500,
    "quantity":500,
    "minimum":100,
    "critical":40,
    "daily_per_person":0.02,
    "supplier":"Research Supplier",
    "lead_time":180,
    "expiry_days":730
},

{
    "item":"Sample Containers",
    "category":"Laboratory",
    "unit":"pieces",
    "capacity":3000,
    "quantity":3000,
    "minimum":500,
    "critical":150,
    "daily_per_person":0.40,
    "supplier":"Research Supplier",
    "lead_time":180,
    "expiry_days":3650
},

{
    "item":"Test Kits",
    "category":"Laboratory",
    "unit":"kits",
    "capacity":350,
    "quantity":350,
    "minimum":80,
    "critical":30,
    "daily_per_person":0.01,
    "supplier":"Research Supplier",
    "lead_time":180,
    "expiry_days":730
},

# =====================================================
# POWER
# =====================================================

{
    "item":"Engine Oil",
    "category":"Power",
    "unit":"liters",
    "capacity":1200,
    "quantity":1200,
    "minimum":250,
    "critical":100,
    "daily_per_person":0.0,
    "supplier":"Engineering",
    "lead_time":150,
    "expiry_days":1825
},

{
    "item":"Coolant",
    "category":"Power",
    "unit":"liters",
    "capacity":700,
    "quantity":700,
    "minimum":150,
    "critical":60,
    "daily_per_person":0.0,
    "supplier":"Engineering",
    "lead_time":150,
    "expiry_days":1825
},

{
    "item":"Fuel Filters",
    "category":"Power",
    "unit":"pieces",
    "capacity":250,
    "quantity":250,
    "minimum":50,
    "critical":20,
    "daily_per_person":0.0,
    "supplier":"Engineering",
    "lead_time":150,
    "expiry_days":3650
},

{
    "item":"Generator Spare Parts",
    "category":"Power",
    "unit":"sets",
    "capacity":120,
    "quantity":120,
    "minimum":30,
    "critical":10,
    "daily_per_person":0.0,
    "supplier":"Engineering",
    "lead_time":180,
    "expiry_days":3650
},

# =====================================================
# WATER
# =====================================================

{
    "item":"Water Filters",
    "category":"Water",
    "unit":"pieces",
    "capacity":250,
    "quantity":250,
    "minimum":60,
    "critical":20,
    "daily_per_person":0.0,
    "supplier":"Engineering",
    "lead_time":150,
    "expiry_days":1825
},

{
    "item":"Chlorine Tablets",
    "category":"Water",
    "unit":"packs",
    "capacity":450,
    "quantity":450,
    "minimum":90,
    "critical":30,
    "daily_per_person":0.005,
    "supplier":"Engineering",
    "lead_time":150,
    "expiry_days":1825
},
# =====================================================
# MAINTENANCE
# =====================================================

{
    "item": "Electrical Cables",
    "category": "Maintenance",
    "unit": "meters",
    "capacity": 2000,
    "quantity": 2000,
    "minimum": 400,
    "critical": 150,
    "daily_per_person": 0.0,
    "supplier": "Engineering",
    "lead_time": 180,
    "expiry_days": 9999
},

{
    "item": "LED Lights",
    "category": "Maintenance",
    "unit": "pieces",
    "capacity": 500,
    "quantity": 500,
    "minimum": 100,
    "critical": 30,
    "daily_per_person": 0.0,
    "supplier": "Engineering",
    "lead_time": 180,
    "expiry_days": 9999
},

{
    "item": "Lubricants",
    "category": "Maintenance",
    "unit": "liters",
    "capacity": 600,
    "quantity": 600,
    "minimum": 120,
    "critical": 40,
    "daily_per_person": 0.0,
    "supplier": "Engineering",
    "lead_time": 150,
    "expiry_days": 1460
},

{
    "item": "Bearings",
    "category": "Maintenance",
    "unit": "pieces",
    "capacity": 350,
    "quantity": 350,
    "minimum": 70,
    "critical": 25,
    "daily_per_person": 0.0,
    "supplier": "Engineering",
    "lead_time": 180,
    "expiry_days": 9999
},

{
    "item": "Bolts",
    "category": "Maintenance",
    "unit": "pieces",
    "capacity": 5000,
    "quantity": 5000,
    "minimum": 800,
    "critical": 250,
    "daily_per_person": 0.0,
    "supplier": "Engineering",
    "lead_time": 180,
    "expiry_days": 9999
}

]