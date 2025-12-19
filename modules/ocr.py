
from typing import List, Tuple, Optional, Set
import re
import unicodedata
from difflib import get_close_matches

try:
    import cv2  
except Exception:
    cv2 = None  

try:
    import pytesseract  
except Exception:
    pytesseract = None 


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


KNOWN_INGREDIENTS_BASE = {
    "eggs", "onion", "tomato", "green chili", "salt", "pepper", "oil",
    "potato", "wheat flour", "chili powder", "ghee", "coriander",
    "bread", "peanut butter",
    "garlic", "ginger", "butter", "milk", "sugar", "turmeric", "cumin",
    "cilantro", "spinach", "cheddar cheese", "olive oil", "chicken breast",
    "green chilli", "green chilies", "green chillies"
}

STOPWORDS = {
    "mrp", "amount", "subtotal", "tax", "total", "balance", "cash", "tender",
    "qty", "quantity", "price", "rs", "usd", "inr", "each", "pcs", "pc",
    "kg", "g", "gm", "gram", "grams", "ml", "l", "ltr", "litre", "liter",
    "bottle", "pack", "dozen", "net", "wt", "weight", "discount", "saved"
}

PRICE_RE = re.compile(
    r"(?:rs\.?|₹|\$|usd|inr)\s*\d+(?:[.,]\d+)?|\b\d+[.,]\d{2}\b",
    re.IGNORECASE
)

QTY_UNIT_RE = re.compile(
    r"(?:(?:^|\s)(?:x\s*)?\d+(?:\.\d+)?\s*(?:kg|g|gm|grams?|ml|l|liters?|litres?|pcs?|pc|pack|dozen)\b)|"
    r"(?:\b\d+(?:\.\d+)?\s*(?:kg|g|gm|grams?|ml|l|liters?|litres?|pcs?|pc|pack|dozen)(?:$|\s))",
    re.IGNORECASE
)

LEADING_KITCHEN_UNITS_RE = re.compile(
    r"^\s*(?:\d+\s*\d*/\d+|\d+(?:\.\d+)?|\d*/\d+)?\s*(?:cups?|cup|tsp|tsps|teaspoons?|tbsp|tbsps|tablespoons?)\b",
    re.IGNORECASE
)

LEADING_BULLETS_RE = re.compile(r"^[\-\u2022\*\•]+", re.UNICODE)

PLURAL_MAP = {
    "tomatoes": "tomato",
    "potatoes": "potato",
    "chilies": "chili",
    "chillies": "chili",
    "green chilli": "green chili",
    "green chilies": "green chili",
    "green chillies": "green chili",
    "chillie": "chili",
    "olive oils": "olive oil",
    "breads": "bread",
    "peppers": "pepper",
    "corriander": "coriander",
    "egg": "eggs",
}


def libs_available() -> Tuple[bool, bool]:
    return (cv2 is not None, pytesseract is not None)

def preprocess_image(path: str):
    if cv2 is None:
        return None
    img = cv2.imread(path)
    if img is None:
        return None
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape[:2]
    scale = 2 if max(h, w) < 1000 else 1
    if scale != 1:
        gray = cv2.resize(gray, (w * scale, h * scale), interpolation=cv2.INTER_CUBIC)
    gray = cv2.bilateralFilter(gray, 9, 75, 75)
    _, th = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return th

def ocr_extract_text(image_path: str) -> Optional[str]:
    if pytesseract is None:
        return None
    try:
        pre = preprocess_image(image_path)
        if pre is not None and cv2 is not None:
            return pytesseract.image_to_string(pre)
        return pytesseract.image_to_string(image_path)
    except Exception as e:
        print(f"Error during Tesseract OCR: {e}")
        return None

def _plural_to_singular_token(token: str) -> str:
    if token in PLURAL_MAP:
        return PLURAL_MAP[token]
    if token.endswith("ies") and len(token) > 3:
        return token[:-3] + "y"
    if token.endswith("s") and not token.endswith("ss"):
        return token[:-1]
    return token

def _strip_units_prices_noise(s: str) -> str:
    s = LEADING_BULLETS_RE.sub("", s).strip()
    s = PRICE_RE.sub(" ", s)
    s = QTY_UNIT_RE.sub(" ", s)
    s = LEADING_KITCHEN_UNITS_RE.sub(" ", s)
    s = re.sub(r"\([^)]*\)", " ", s)  
    s = re.sub(r"\b\d+(?:\.\d+)?\b", " ", s)  
    s = re.sub(r"\s+", " ", s).strip()
    return s

def _drop_stopwords_tokens(tokens: List[str]) -> List[str]:
    return [t for t in tokens if t and t not in STOPWORDS and len(t) > 1]

def parse_text_to_ingredients(raw_text: str, known_db: Optional[Set[str]] = None) -> List[str]:
    if not raw_text:
        return []

    known = {normalize(k) for k in KNOWN_INGREDIENTS_BASE}
    if known_db:
        known |= {normalize(k) for k in known_db}

    chunks: List[str] = []
    for line in raw_text.splitlines():
        for chunk in re.split(r"[,\;]+", line):
            s = normalize(chunk)
            if not s:
                continue
            s = _strip_units_prices_noise(s)
            if not s:
                continue
            chunks.append(s)

    cleaned: List[str] = []
    for ch in chunks:
        ch = ch.replace("chilli", "chili") 
        tokens = [normalize(t) for t in ch.split()]
        tokens = _drop_stopwords_tokens(tokens)
        if not tokens:
            continue

        cand = " ".join(_plural_to_singular_token(t) for t in tokens)
        cand = normalize(cand) 

        if not cand or cand in STOPWORDS:
            continue


        if cand in known:
            cleaned.append(cand)
            continue

        match = get_close_matches(cand, list(known), n=1, cutoff=0.84)
        if match:
            cleaned.append(match[0])
            continue

        if re.fullmatch(r"[a-z][a-z\s]+", cand) and len(cand) >= 3:
            cleaned.append(cand)

    seen = set()
    result = []
    for x in cleaned:
        if x not in seen:
            seen.add(x)
            result.append(x)
    return result

def image_to_ingredient_list(image_path: str, known_db: Optional[Set[str]] = None) -> Tuple[List[str], Optional[str]]:
    text = ocr_extract_text(image_path)
    if text is None:
        if pytesseract is None:
            return [], "OCR libraries not available. Install 'pytesseract' and the Tesseract-OCR engine."
        return [], "OCR failed to extract any text from the image."
        
    ings = parse_text_to_ingredients(text, known_db=known_db)
    if not ings:
        return [], "No readable ingredients found in the image text."
        
    return ings, None