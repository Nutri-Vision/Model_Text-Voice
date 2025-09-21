# ---------- Robust USDA nutrient helpers ----------
def _get_nutrient_value(nutrient_entry):
    """
    Accept a USDA nutrient entry dict and return float value or None.
    Handles cases where value is numeric or nested.
    """
    if nutrient_entry is None:
        return None
    if isinstance(nutrient_entry, (int, float)):
        return float(nutrient_entry)
    if isinstance(nutrient_entry, dict):
        # Common key is "value" (numeric) — but be defensive
        for key in ("value", "amount", "nutrientValue"):
            if key in nutrient_entry and nutrient_entry[key] is not None:
                try:
                    return float(nutrient_entry[key])
                except Exception:
                    pass
        # fallback: look for numeric-like keys
        for v in nutrient_entry.values():
            try:
                return float(v)
            except Exception:
                continue
    try:
        return float(nutrient_entry)
    except Exception:
        return None

def extract_core_macros(food_detail: dict):
    """
    Extract four macros from food_detail['foodNutrients'] using fuzzy substring matching.
    Returns a dict like {'calories':{'value':..,'unit':..}, ...}.
    """
    out = {}
    mapping_keys = {
        "energy": "calories",
        "protein": "protein_g",
        "carbohydrate": "carbs_g",
        "carbohydrate, by difference": "carbs_g",
        "lipid": "fat_g",
        "total lipid": "fat_g",
        "total lipid (fat)": "fat_g",
        "total lipid (fat)": "fat_g",
    }

    for n in food_detail.get("foodNutrients", []):
        name = (n.get("nutrientName") or "").strip()
        unit = n.get("unitName") or ""
        # try nutrientNumber/nutrientId as fallback
        nutrient_number = str(n.get("nutrientNumber") or n.get("nutrientId") or "")
        val = _get_nutrient_value(n)
        lname = name.lower()
        matched = None

        # substring checks first
        if "energy" in lname:
            matched = "calories"
        elif "protein" in lname and "amino" not in lname:
            matched = "protein_g"
        elif "carbohydrate" in lname or nutrient_number in ("1005",):
            matched = "carbs_g"
        elif "lipid" in lname or "fat" in lname or nutrient_number in ("1004",):
            matched = "fat_g"
        # ensure we only record if value is not None
        if matched:
            out[matched] = {"value": (val if val is not None else 0.0), "unit": unit}

    # Ensure keys exist
    for key in ("calories", "protein_g", "carbs_g", "fat_g"):
        out.setdefault(key, {"value": 0.0, "unit": ""})
    return out

def _determine_base_grams(food_detail: dict):
    """
    Determine the grams that the USDA nutrient values correspond to (serving size or first portion gramWeight).
    Default to 100g.
    """
    sv = food_detail.get("servingSize")
    sunit = (food_detail.get("servingSizeUnit") or "").lower()
    if sv and sunit in ("g", "gram", "grams"):
        try:
            return float(sv)
        except Exception:
            pass

    # Try foodPortions list
    parts = food_detail.get("foodPortions") or []
    for p in parts:
        gw = p.get("gramWeight")
        if gw:
            try:
                return float(gw)
            except Exception:
                continue

    # fallback
    return 100.0

def scale_macros(macros_map: dict, grams: float, base: float = 100.0):
    """
    Scale macros_map values (assumed per `base` grams) to `grams`.
    Returns simple numeric dict with keys calories, protein_g, carbs_g, fat_g.
    """
    out = {}
    for k in ("calories", "protein_g", "carbs_g", "fat_g"):
        entry = macros_map.get(k) or {}
        val = _get_nutrient_value(entry)
        try:
            if val is None:
                out[k] = 0.0
            else:
                out[k] = round((float(val) / float(base)) * float(grams), 2)
        except Exception:
            out[k] = 0.0
    return out


# ---------- end helpers ----------
