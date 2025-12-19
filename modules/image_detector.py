
import os
import time
from typing import List, Tuple

try:
    import cv2  
except ImportError:
    print("WARNING: opencv-python is not installed. Image detection will not work.")
    print("Install with: pip install opencv-python")
    cv2 = None

net = None
LABELS = []


def detect_ingredients(image_path: str) -> Tuple[List[str], str | None]:
    
    if cv2 is None:
        return [], "OpenCV (cv2) library is not installed."

    if not os.path.exists(image_path):
        return [], "Image file not found at path."

    
    print(f"[image_detector STUB] Simulating model analysis for: {image_path}")
    
    try:
        img = cv2.imread(image_path)
        if img is None:
            return [], "Could not read image file. It may be corrupt."
            
        print(f"[image_detector STUB] Image loaded successfully, shape={img.shape}")
    except Exception as e:
        return [], f"OpenCV failed to read image: {e}"

    time.sleep(1.5)

    detected_ingredients = [
        "eggs",
        "milk",
        "spinach",
        "lettuce"
    ]
    
    print(f"[image_detector STUB] Detection complete. Found: {detected_ingredients}")

    return detected_ingredients, None