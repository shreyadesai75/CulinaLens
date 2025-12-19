import json
import os
from typing import List, Dict, Any, Set
from collections import defaultdict

_DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
_LIST_PATH = os.path.join(_DATA_DIR, "shopping_list_cache.json")
os.makedirs(_DATA_DIR, exist_ok=True)

_CATEGORIES = {
    "Produce": [
        "onion", "tomato", "garlic", "ginger", "potato", "spinach",
        "lettuce", "coriander", "parsley", "lemon", "avocado", "chili",
        "carrot", "peas", "apple", "banana", "orange", "grapes", "capsicum"
    ],
    "Dairy & Eggs": [
        "eggs", "milk", "cheese", "butter", "yogurt", "cream", "ghee", "paneer"
    ],
    "Meat & Protein": [
        "chicken", "tofu", "chickpeas", "dal", "beef", "pork", "fish"
    ],
    "Pantry & Dry Goods": [
        "spaghetti", "pasta", "quinoa", "rice", "flour", "bread", "oil",
        "sauce", "peanut butter", "honey", "sugar", "noodles", "water"
    ],
    "Spices & Seasoning": [
        "salt", "pepper", "powder", "flakes", "spices", "masala", "cumin",
        "turmeric", "mustard seeds", "curry leaves"
    ]
}
_DEFAULT_CATEGORY = "Other"

def _find_category(ingredient: str) -> str:
    ing_lower = ingredient.lower()
    for category, keywords in _CATEGORIES.items():
        for keyword in keywords:
            if keyword in ing_lower:
                return category
    return _DEFAULT_CATEGORY

def load_list() -> Dict[str, List[str]]:
    if not os.path.exists(_LIST_PATH):
        return {}
    try:
        with open(_LIST_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Warning: Could not load shopping list: {e}")
        return {}

def save_list(shopping_list: Dict[str, List[str]]):
    try:
        with open(_LIST_PATH, 'w', encoding='utf-8') as f:
            json.dump(shopping_list, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error: Could not save shopping list: {e}")

def _merge_lists(
    list1: Dict[str, List[str]],
    list2: Dict[str, List[str]]
) -> Dict[str, List[str]]:
    merged = defaultdict(set)
    
    for category, items in list1.items():
        merged[category].update(items)
        
    for category, items in list2.items():
        merged[category].update(items)
        
    final_dict = {
        category: sorted(list(items))
        for category, items in merged.items()
    }
    return final_dict

def generate_shopping_list(recipes: List[Dict[str, Any]]) -> Dict[str, List[str]]:
    all_ingredients: Set[str] = set()
    for recipe in recipes:
        for ing in recipe.get('ingredients', []):
            all_ingredients.add(ing)
            
    categorized_list = defaultdict(list)
    for ing in all_ingredients:
        category = _find_category(ing)
        categorized_list[category].append(ing)
        
    final_dict = {
        category: sorted(items)
        for category, items in categorized_list.items()
    }
    return final_dict

def add_recipes_to_list(recipes: List[Dict[str, Any]]) -> Dict[str, List[str]]:
    current_list = load_list()
    new_list = generate_shopping_list(recipes)
    merged_list = _merge_lists(current_list, new_list)
    save_list(merged_list)
    return merged_list