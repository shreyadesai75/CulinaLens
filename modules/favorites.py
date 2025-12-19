import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

_PREFERENCES_PATH = Path("data") / "user_preferences.json"
_PREFERENCES_PATH.parent.mkdir(parents=True, exist_ok=True)

def _load_preferences_data() -> Dict[str, Any]:
    if not _PREFERENCES_PATH.exists():
        return {"favorites": [], "shopping_list": {}, "cooking_history": []}
    try:
        with open(_PREFERENCES_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            if not isinstance(data, dict):
                if isinstance(data, list):
                    return {"favorites": data, "shopping_list": {}, "cooking_history": []}
                return {"favorites": [], "shopping_list": {}, "cooking_history": []}
            if "favorites" not in data:
                data["favorites"] = []
            if "shopping_list" not in data:
                data["shopping_list"] = {}
            if "cooking_history" not in data:
                data["cooking_history"] = []
            return data
    except json.JSONDecodeError:
        return {"favorites": [], "shopping_list": {}, "cooking_history": []}
    except Exception as e:
        print(f"ERROR: Failed to read preferences file: {e}")
        return {"favorites": [], "shopping_list": {}, "cooking_history": []}

def _save_preferences_data(data: Dict[str, Any]):
    try:
        with open(_PREFERENCES_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"ERROR: Could not save to _PREFERENCES_PATH: {e}")
        return

def _load_all_favorites() -> List[Dict[str, Any]]:
    return _load_preferences_data().get("favorites", [])

def _save_all_favorites(all_list: List[Dict[str, Any]]):
    try:
        data = _load_preferences_data()
        data["favorites"] = all_list
        _save_preferences_data(data)
    except Exception as e:
        print(f"ERROR: Could not save favorites: {e}")

def save_favorite(recipe: Dict[str, Any], note: Optional[str] = None, rating: Optional[int] = None,
                  tags: Optional[List[str]] = None):
    if not recipe or not recipe.get("title"):
        raise ValueError("Recipe must have a title to be saved as favorite.")
    all_list = _load_all_favorites()
    entry = {
        "title": recipe.get("title"),
        "ingredients": recipe.get("ingredients", []),
        "steps": recipe.get("steps", []),
        "image_url": recipe.get("image_url"),
        "note": note,
        "rating": int(rating) if rating is not None else None,
        "tags": list(tags) if tags else [],
        "added_on": datetime.utcnow().isoformat() + "Z"
    }
    all_list = [r for r in all_list if r.get("title") != entry["title"]]
    all_list.insert(0, entry)
    _save_all_favorites(all_list)

def list_favorites() -> List[Dict[str, Any]]:
    return _load_all_favorites()

def remove_favorite(title: str):
    if not title:
        return
    all_list = [r for r in _load_all_favorites() if r.get("title") != title]
    _save_all_favorites(all_list)

def log_recipe_view(recipe_title: str):
    if not recipe_title:
        return
    data = _load_preferences_data()
    history = data.get("cooking_history", [])
    entry = {
        "title": recipe_title,
        "viewed_on": datetime.utcnow().isoformat() + "Z"
    }
    history = [e for e in history if e.get("title") != recipe_title]
    history.insert(0, entry)
    data["cooking_history"] = history[:50]
    _save_preferences_data(data)

def list_cooking_history() -> List[Dict[str, Any]]:
    return _load_preferences_data().get("cooking_history", [])