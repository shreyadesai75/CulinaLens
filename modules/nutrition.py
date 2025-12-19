# modules/nutrition.py


import os
import csv
import unicodedata
import re
from typing import Dict, Optional, List, Any

_NUTRITION_DB: Dict[str, Dict[str, float]] = {}


_NON_PRINTABLE_RE = re.compile(r"[\u200B\u200C\u200D\uFEFF]")
_MULTI_SPACE_RE = re.compile(r"\s+")

def normalize(text: str) -> str:
    """Cleans and lowercases text for matching."""
    if not isinstance(text, str):
        return ""
    s = unicodedata.normalize("NFKC", text)
    s = _NON_PRINTABLE_RE.sub("", s)
    s = s.replace("\u00A0", " ")
    s = s.strip()
    s = _MULTI_SPACE_RE.sub(" ", s)
    s = s.strip(" \t\n\r\"'“”‘’.,;:()[]")
    return s.lower()


def load_nutrition_from_csv(file_path: str):
    
    global _NUTRITION_DB
    
    if not os.path.exists(file_path):
        print(f"ERROR [Nutrition]: Nutrition file not found at {file_path}. No nutrition data will be available.")
        return

    print(f"INFO [Nutrition]: Loading nutrition database from {file_path}...")
    
    temp_db = {}
    try:
        with open(file_path, mode='r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            count = 0
            for row in reader:
                try:
                    # Normalize the ingredient name to use as the key
                    name = normalize(row['ingredient_name'])
                    if not name:
                        continue
                        
                    temp_db[name] = {
                        "calories": float(row.get('calories_100g', 0.0) or 0.0),
                        "protein": float(row.get('protein_100g', 0.0) or 0.0),
                        "carbs": float(row.get('carbs_100g', 0.0) or 0.0),
                        "fat": float(row.get('fat_100g', 0.0) or 0.0)
                    }
                    count += 1
                except (ValueError, TypeError):
                    print(f"WARN [Nutrition]: Skipping invalid row for '{row.get('ingredient_name')}'")
                except KeyError:
                    print("ERROR [Nutrition]: CSV file must have columns: 'ingredient_name', 'calories_100g', 'protein_100g', 'carbs_100g', 'fat_100g'")
                    _NUTRITION_DB = {} # Clear db on fatal error
                    return

    except FileNotFoundError:
        print(f"ERROR [Nutrition]: File not found at {file_path}.")
        return
    except Exception as e:
        print(f"ERROR [Nutrition]: Failed to read CSV file: {e}")
        return

    _NUTRITION_DB = temp_db
    print(f"INFO [Nutrition]: Successfully loaded {len(_NUTRITION_DB)} items.")


def lookup(ingredient: str) -> Optional[Dict[str, float]]:
    """
    Return per-100g nutrition dict or None from the in-memory database.
    """
    if not ingredient or not isinstance(ingredient, str):
        return None
        
    norm_key = normalize(ingredient)
    
    data = _NUTRITION_DB.get(norm_key)
    if data:
        return data
        
    if norm_key.endswith('s'):
        singular_key = norm_key[:-1]
        data = _NUTRITION_DB.get(singular_key)
        if data:
            return data
            
    if not norm_key.endswith('s'):
        plural_key = norm_key + 's'
        data = _NUTRITION_DB.get(plural_key)
        if data:
            return data

    return None


def summarize(ingredients: List[str]) -> Dict[str, float]:
    
    totals = {"calories": 0.0, "protein": 0.0, "carbs": 0.0, "fat": 0.0}
    if not ingredients:
        return totals
        
    for ing in ingredients:
        info = lookup(ing)
        if not info:
            continue
        for k in totals:
            totals[k] += float(info.get(k, 0.0))
            
    return totals


def calculate_recipe_nutrition(recipe: Dict[str, Any], servings: int = 1) -> Dict[str, Dict[str, float]]:
   
    if not recipe or not isinstance(recipe, dict):
        empty_totals = {"calories": 0.0, "protein": 0.0, "carbs": 0.0, "fat": 0.0}
        return {"total": empty_totals, "per_serving": empty_totals}
        
    ings = recipe.get("ingredients", []) or []
    total = summarize(ings) # This is the sum of all ingredients per-100g
    
    recipe_servings = int(recipe.get("servings", 1) or 1)
    
    per_serving = {k: (float(total.get(k, 0.0)) / recipe_servings) for k in total}
    
    return {"total": total, "per_serving": per_serving}