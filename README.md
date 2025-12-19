CulinaLens 
Turn your fridge chaos into dinner plans.

CulinaLens is a smart kitchen assistant that uses AI to figure out what you can cook based on what you actually have. Snap a photo of your ingredients, and it uses computer vision to detect them and recommend the perfect recipe.

What it does
AI Ingredient Detection: Upload a photo of your groceries, and the app uses a custom Computer Vision model (PyTorch + OpenCV) to list out your ingredients.

Smart Recipe Match: It doesn't just look for keywords; it ranks recipes based on how well they match your available items and taste preferences.

Nutrition Tracking: Every recipe comes with a breakdown of calories, protein, carbs, and fats.

Local Flavors: Detects your location to suggest relevant regional dishes.

Substitution Logic: Missing an egg? The app automatically suggests substitutes like bananas or yogurt so you can keep cooking.

Tech Stack
Core: Python, Flask

AI/ML: PyTorch, OpenCV, Scikit-Learn

Frontend: HTML5, Bootstrap 5, JavaScript