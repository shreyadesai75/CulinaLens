import json
import os
from typing import List, Dict, Any

_DISH_DATABASE: List[Dict[str, Any]] = []

_DATA_PATH = os.path.join(
    os.path.dirname(__file__),
    '..',
    'data',
    'local_dishes.json'
)

try:
    if os.path.exists(_DATA_PATH):
        with open(_DATA_PATH, 'r', encoding='utf-8') as f:
            _DISH_DATABASE = json.load(f)
        
        print(f"✅ [local_discovery] Successfully loaded {len(_DISH_DATABASE)} local dishes from JSON.")
    
    else:
        print(f"⚠️ [local_discovery] WARNING: Could not find 'data/local_dishes.json'.")
        print(f"    -> Searched at path: {_DATA_PATH}")

except Exception as e:
    print(f"❌ [local_discovery] CRITICAL ERROR loading 'data/local_dishes.json': {e}")
    _DISH_DATABASE = []


def get_dishes_by_location(location: str) -> List[Dict[str, Any]]:
    if not location or not _DISH_DATABASE:
        return []

    search_location = location.strip().lower()

    results = [
        dish for dish in _DISH_DATABASE
        if str(dish.get('location', '')).strip().lower() == search_location
    ]

    return results