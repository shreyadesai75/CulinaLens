import os
import json
import unicodedata
import re
from typing import List, Dict, Set, Any

_SUB_MAP: Dict[str, List[str]] = {}

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

def load_substitutions_from_json(file_path: str):
    global _SUB_MAP
    
    if not os.path.exists(file_path):
        print(f"ERROR [Substitutes]: File not found at {file_path}. No substitutions will be available.")
        return

    print(f"INFO [Substitutes]: Loading substitutions database from {file_path}...")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data_raw = json.load(f)
            
            temp_db = {}
            for key, values in data_raw.items():
                norm_key = normalize(key)
                norm_values = [normalize(v) for v in values if isinstance(v, str)]
                temp_db[norm_key] = norm_values
                
            _SUB_MAP = temp_db
            print(f"INFO [Substitutes]: Successfully loaded {len(_SUB_MAP)} substitution rules.")

    except FileNotFoundError:
        print(f"ERROR [Substitutes]: File not found at {file_path}.")
        return
    except json.JSONDecodeError:
        print(f"ERROR [Substitutes]: Failed to decode JSON from {file_path}.")
    except Exception as e:
        print(f"ERROR [Substitutes]: Failed to read file: {e}")
        return

def suggest_substitutes(missing: List[str], available: Set[str]) -> Dict[str, List[str]]:
    out = {}
    
    avail_lower = {normalize(a) for a in available}
    
    for miss in missing:
        miss_l = normalize(miss)
        
        candidates = [] 
        provided = [] 
        
        subs = _SUB_MAP.get(miss_l, [])
        
        for s in subs:
            if s in avail_lower:
                provided.append(s)
            else:
                candidates.append(s)
                
        if provided:
            out[miss] = provided
        elif candidates:
            out[miss] = candidates
        else:
            out[miss] = []
            
    return out