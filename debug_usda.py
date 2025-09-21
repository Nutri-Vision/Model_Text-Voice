# debug_usda_test.py
from usda.fooddata_api import get_nutrition_for_item

items = [
    {"ingredient": "whole wheat bread", "quantity": 2.0, "unit": "slice"},
    {"ingredient": "apple", "quantity": 1.0, "unit": "serving"}
]

for it in items:
    out = get_nutrition_for_item(it)
    import json
    print(json.dumps(out, indent=2))
