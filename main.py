import os
import csv
import json
from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
from modules.suggestor import load_recipes, advanced_suggest_recipes
from modules.ocr import image_to_ingredient_list
import modules.favorites as favorites
import modules.nutrition as nutrition
import modules.substitutes as substitutes
import modules.image_detector as image_detector
import modules.local_discovery as local_discovery
import modules.shopping_list as shopping_list

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

try:
    RECIPES_PATH = os.path.join(DATA_DIR, "recipes_sample.json")
    ALL_RECIPES = load_recipes(RECIPES_PATH)
    print(f" [App] Successfully loaded {len(ALL_RECIPES)} recipes.")

    NUTRITION_PATH = os.path.join(DATA_DIR, "nutrition.csv")
    nutrition.load_nutrition_from_csv(NUTRITION_PATH)
    
    SUBSTITUTIONS_PATH = os.path.join(DATA_DIR, "substitutions.json")
    substitutes.load_substitutions_from_json(SUBSTITUTIONS_PATH)

except Exception as e:
    print(f"CRITICAL ERROR: Could not load data files on startup.")
    print(e)
    ALL_RECIPES = []

@app.route("/")
def page_home():
    return render_template("index.html")

@app.route("/results")
def page_results():
    return render_template("results.html")

@app.route("/recipe/<recipe_title>")
def page_recipe_detail(recipe_title):
    return render_template("recipe.html", recipe_title=recipe_title)

@app.route("/profile")
def page_profile():
    return render_template("profile.html")

@app.route("/api/suggest", methods=['POST'])
def api_suggest_recipes():
    data = request.json
    user_ingredients = data.get("ingredients", [])
    
    prefs = {
        "cuisine": data.get("cuisine"),
        "taste": data.get("taste"),
        "diet": data.get("diet"),
        "allergies": data.get("allergies", []),
        "max_time": int(data.get("max_time", 0)),
        "skill_level": data.get("skill_level", "intermediate"),
        "servings": int(data.get("servings", 1))
    }
    
    suggestions = advanced_suggest_recipes(
        user_ingredients=user_ingredients,
        recipes=ALL_RECIPES,
        preferences=prefs,
        top_n=10, 
        nutrition_module=nutrition,
        substitutes_module=substitutes
    )
    
    return jsonify(suggestions)

@app.route("/api/recipe-details/<recipe_title>")
def api_get_recipe_details(recipe_title):
    recipe = next((r for r in ALL_RECIPES if r['title'] == recipe_title), None)
    
    if not recipe:
        return jsonify({"error": "Recipe not found"}), 404
        
    favorites.log_recipe_view(recipe_title)
    
    nutrition_details = nutrition.calculate_recipe_nutrition(
        recipe, 
        recipe.get('servings', 1)
    )
    
    full_data = {
        "recipe": recipe,
        "detailed_nutrition": nutrition_details
    }
    
    return jsonify(full_data)

@app.route("/api/upload-receipt-ocr", methods=['POST'])
def api_upload_receipt_ocr():
    if 'image' not in request.files:
        return jsonify({"error": "No image file provided"}), 400
        
    file = request.files['image']
    
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
        
    if file:
        filename = secure_filename(file.filename)
        temp_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(temp_path)
        
        known_db = {ing for r in ALL_RECIPES for ing in r.get("ingredients", [])}
        
        ingredients, err = image_to_ingredient_list(temp_path, known_db=known_db)
        
        os.remove(temp_path)
        
        if err:
            return jsonify({"error": err}), 500
            
        return jsonify({"ingredients": ingredients})

@app.route("/api/favorites", methods=['GET', 'POST'])
def api_manage_favorites():
    if request.method == 'GET':
        all_favorites = favorites.list_favorites()
        return jsonify(all_favorites)
        
    elif request.method == 'POST':
        data = request.json
        recipe_title = data.get('title')
        
        if not recipe_title:
            return jsonify({"error": "Recipe title is required"}), 400
            
        recipe_obj = next((r for r in ALL_RECIPES if r['title'] == recipe_title), None)
        
        if not recipe_obj:
            return jsonify({"error": "Recipe not found"}), 404
            
        try:
            favorites.save_favorite(
                recipe_obj, 
                note=data.get('note'), 
                rating=data.get('rating')
            )
            return jsonify({"status": "success", "message": f"Saved '{recipe_title}' to favorites."})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

@app.route("/api/upload-fridge-photo", methods=['POST'])
def api_upload_fridge_photo():
    if 'image' not in request.files:
        return jsonify({"error": "No image file provided"}), 400
        
    file = request.files['image']
    
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
        
    if file:
        filename = secure_filename(file.filename)
        temp_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(temp_path)
        
        ingredients, err = image_detector.detect_ingredients(temp_path)
        
        os.remove(temp_path)
        
        if err:
            return jsonify({"error": err}), 500
            
        return jsonify({"ingredients": ingredients})

@app.route("/api/local-dishes")
def api_get_local_dishes():
    location = request.args.get('location', 'Mumbai') 
    dishes = local_discovery.get_dishes_by_location(location)
    
    return jsonify(dishes)
    
@app.route("/api/shopping-list", methods=['GET', 'POST'])
def api_manage_shopping_list():
    if request.method == 'GET':
        current_list = shopping_list.load_list()
        return jsonify(current_list)
        
    elif request.method == 'POST':
        data = request.json
        recipe_titles = data.get('recipes', []) 
        
        if not recipe_titles:
            return jsonify({"error": "No recipe titles provided"}), 400
            
        recipes_to_shop = [r for r in ALL_RECIPES if r['title'] in recipe_titles]
        
        if not recipes_to_shop:
            return jsonify({"error": "None of the specified recipes were found"}), 404
        
        new_list = shopping_list.add_recipes_to_list(recipes_to_shop)
        
        return jsonify(new_list)

if __name__ == "__main__":
    print(" Starting FIntrack Pro Flask Server...")
    print(f"   Mode: {'DEBUG' if app.debug else 'PRODUCTION'}")
    print(f"   URL:  http://127.0.0.1:5000")
    app.run(debug=True, port=5000)