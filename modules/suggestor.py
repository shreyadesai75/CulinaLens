from typing import List, Dict, Any, Optional, Set
import json
import os
import unicodedata
import re
from collections import defaultdict
import modules.nutrition as nutrition_module_local
import modules.substitutes as submod_local

_NON_PRINTABLE_RE = re.compile(r"[\u200B\u200C\u200D\uFEFF]")
_MULTI_SPACE_RE = re.compile(r"\s+")

def normalize(text: str) -> str:
    if not isinstance(text, str):
        return ""
    s = unicodedata.normalize("NFKC", text)
    s = _NON_PRINTABLE_RE.sub("", s)
    s = s.replace("\u00A0", " ")
    s = s.strip()
    s = _MULTI_SPACE_RE.sub(" ", s)
    s = s.strip(" \t\n\r\"'“”‘’.,;:()[]")
    return s.lower()

def load_recipes(file_path: str) -> List[Dict[str, Any]]:
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Recipes file not found: {file_path}")
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    normalized = []
    for rec in data:
        title = rec.get("title", "Untitled Recipe")
        ings = [normalize(i) for i in rec.get("ingredients", [])]
        steps = rec.get("steps", [])
        image_url = rec.get("image_url", "")
        
        cuisine = normalize(rec.get("cuisine", "")) if rec.get("cuisine") else ""
        diet = [normalize(d) for d in rec.get("diet", [])] if isinstance(rec.get("diet"), list) else []
        time_min = rec.get("time", rec.get("cook_time", 0)) or 0
        skill = normalize(rec.get("skill", "intermediate"))
        servings = int(rec.get("servings", 1) or 1)
        taste_tags = [normalize(t) for t in rec.get("taste_tags", [])] if rec.get("taste_tags") else []
        
        normalized.append({
            "title": title,
            "ingredients": ings,
            "steps": steps,
            "image_url": image_url,
            "cuisine": cuisine,
            "diet": diet,
            "time": int(time_min),
            "skill": skill,
            "servings": servings,
            "taste_tags": taste_tags
        })
    return normalized

def suggest_recipes(
    user_ingredients: List[str],
    recipes: List[Dict[str, Any]],
    threshold: float = 0.6
) -> List[Dict[str, Any]]:
    user_set = set(normalize(i) for i in user_ingredients if normalize(i))
    suggestions = []
    for recipe in recipes:
        recipe_set = set(recipe.get("ingredients", []))
        total = len(recipe_set)
        if total == 0:
            continue
        matched = sorted(list(user_set & recipe_set))
        missing = sorted(list(recipe_set - user_set))
        match_count = len(matched)
        ratio = match_count / total
        if ratio >= threshold:
            suggestions.append({
                "title": recipe["title"],
                "image_url": recipe.get("image_url", ""),
                "match_count": match_count,
                "total_required": total,
                "match_ratio": ratio,
                "matched": matched,
                "missing": missing,
                "ingredients": list(recipe_set),
                "steps": recipe.get("steps", [])
            })
    suggestions.sort(key=lambda x: (x["match_ratio"], x["match_count"]), reverse=True)
    return suggestions

def _skill_to_rank(skill: str) -> int:
    mapping = {"beginner": 1, "intermediate": 2, "expert": 3}
    return mapping.get(skill.lower(), 2)

def _safe_div(a: float, b: float) -> float:
    try:
        return (a / b) if b else 0.0
    except Exception:
        return 0.0

def _compute_recipe_nutrition(recipe: Dict[str, Any], nutrition_module) -> Dict[str, float]:
    nm = nutrition_module or nutrition_module_local
    totals = {"calories": 0.0, "protein": 0.0, "carbs": 0.0, "fat": 0.0}
    for ing in recipe.get("ingredients", []):
        info = nm.lookup(ing)
        if not info:
            continue
        for k in totals:
            totals[k] += float(info.get(k, 0.0))
            
    servings = int(recipe.get("servings", 1) or 1)
    per_serving = {k: (totals[k] / servings) for k in totals}
    return per_serving

def advanced_suggest_recipes(
    user_ingredients: List[str],
    recipes: List[Dict[str, Any]],
    preferences: Optional[Dict[str, Any]] = None,
    top_n: int = 10,
    nutrition_module=None,
    substitutes_module=None
) -> List[Dict[str, Any]]:
    if preferences is None:
        preferences = {}
        
    prefs_cuisine = normalize(preferences.get("cuisine") or "")
    prefs_taste = normalize(preferences.get("taste") or "")
    prefs_diet = normalize(preferences.get("diet") or "")
    prefs_allergies = {normalize(a) for a in preferences.get("allergies", [])} if preferences.get("allergies") else set()
    prefs_max_time = int(preferences.get("max_time", 0) or 0)
    prefs_skill = normalize(preferences.get("skill_level") or "intermediate")

    user_set = set(normalize(i) for i in user_ingredients if normalize(i))
    out = []
    
    w = {
        "ingredient": 0.55,
        "cuisine": 0.12,
        "taste": 0.08,
        "diet": 0.08,
        "time": 0.05,
        "skill": 0.02,
        "missing_penalty": 0.20
    }

    nm = nutrition_module or nutrition_module_local
    smod = substitutes_module or submod_local

    for recipe in recipes:
        recipe_ings = set(recipe.get("ingredients", []))

        if prefs_allergies:
            skip = False
            for allerg in prefs_allergies:
                if not allerg:
                    continue
                for ing in recipe_ings:
                    if allerg in ing:
                        skip = True
                        break
                if skip:
                    break
            if skip:
                continue

        total = len(recipe_ings) or 1
        matched = sorted(list(user_set & recipe_ings))
        missing = sorted(list(recipe_ings - user_set))
        match_count = len(matched)
        match_ratio = match_count / total
        ingredient_score = match_ratio

        if prefs_cuisine:
            cuisine_score = 1.0 if prefs_cuisine == (recipe.get("cuisine") or "").lower() else 0.0
        else:
            cuisine_score = 1.0

        if prefs_taste:
            taste_score = 1.0 if prefs_taste in (recipe.get("taste_tags") or []) else 0.0
        else:
            taste_score = 1.0

        recipe_diets = [d.lower() for d in (recipe.get("diet") or [])]
        if prefs_diet:
            diet_score = 1.0 if (prefs_diet in recipe_diets) else 0.0
        else:
            diet_score = 1.0

        rec_time = int(recipe.get("time", 0) or 0)
        if prefs_max_time and rec_time:
            time_score = max(0.0, 1.0 - max(0, rec_time - prefs_max_time) / max(1, prefs_max_time))
        else:
            time_score = 1.0

        user_skill_rank = _skill_to_rank(prefs_skill)
        recipe_skill_rank = _skill_to_rank(recipe.get("skill", "intermediate"))
        skill_score = 1.0 if user_skill_rank >= recipe_skill_rank else (_safe_div(user_skill_rank, recipe_skill_rank))

        missing_pen = (len(missing) / total) if total else 0.0

        raw_score = (
            w["ingredient"] * ingredient_score +
            w["cuisine"] * cuisine_score +
            w["taste"] * taste_score +
            w["diet"] * diet_score +
            w["time"] * time_score +
            w["skill"] * skill_score
        ) - (w["missing_penalty"] * missing_pen)
        
        if raw_score <= 0.0:
            continue

        nutrition_est = _compute_recipe_nutrition(recipe, nm)
        sub_suggestions = smod.suggest_substitutes(missing, user_set)

        out.append({
            "title": recipe.get("title"),
            "image_url": recipe.get("image_url", ""),
            "score": float(raw_score),
            "matched": matched,
            "missing": missing,
            "match_ratio": match_ratio,
            "match_count": match_count,
            "total_required": total,
            "ingredients": list(recipe_ings),
            "steps": recipe.get("steps", []),
            "nutrition": nutrition_est,
            "substitutes": sub_suggestions,
            "meta": {
                "cuisine": recipe.get("cuisine", ""),
                "diet": recipe.get("diet", []),
                "time": recipe.get("time", 0),
                "skill": recipe.get("skill", "intermediate"),
                "servings": recipe.get("servings", 1),
                "taste_tags": recipe.get("taste_tags", [])
            }
        })

    out.sort(key=lambda r: (r["score"], r["match_ratio"], r["match_count"]), reverse=True)
    
    return out[:top_n]