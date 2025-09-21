from fastapi import FastAPI
from pydantic import BaseModel
from nlp.hybrid_extractor import hybrid_extract
from usda.fooddata_api import get_nutrition_for_item, extract_core_macros, scale_macros, _normalize_macros_map

app = FastAPI(title="Nutri-Vision Text Service")

class TextIn(BaseModel):
    description: str

def _format_item_nutrition(item, nutrition_result):
    """
    Return only calories, protein_g, carbs_g, fat_g for a single item.
    nutrition_result is the dict returned by get_nutrition_for_item()
    """
    # If get_nutrition_for_item returned 'macros' already scaled, use it.
    macros = nutrition_result.get("macros") or {}
    # But some flows may return macros_map (per 100g) — handle both
    if not macros and nutrition_result.get("candidate"):
        # try to extract core macros from candidate detail (fallback)
        detail = nutrition_result.get("detail")
        if detail:
            macros_map = extract_core_macros(detail)
            grams = nutrition_result.get("grams", 100.0)
            macros = scale_macros(macros_map, grams, base=100.0)

    # Normalize to the four keys, rounded
    normalized = _normalize_macros_map(macros)
    return normalized

@app.post("/analyze-text")
def analyze_text(payload: TextIn):
    text = payload.description
    items = hybrid_extract(text)  # expects list of dicts {ingredient,quantity,unit}

    items_out = []
    totals = {"calories": 0.0, "protein_g": 0.0, "carbs_g": 0.0, "fat_g": 0.0}

    for it in items:
        nut = get_nutrition_for_item(it)
        # get_nutrition_for_item returns {'candidate', 'grams', 'macros', 'score'} or an error
        if nut.get("error"):
            macros = {"calories": 0.0, "protein_g": 0.0, "carbs_g": 0.0, "fat_g": 0.0}
            items_out.append({
                "ingredient": it.get("ingredient"),
                "quantity": it.get("quantity"),
                "unit": it.get("unit"),
                "macros": macros,
                "note": nut.get("error")
            })
            continue

        macros = _normalize_macros_map(nut.get("macros"))
        # accumulate totals
        for k in totals:
            totals[k] += macros.get(k, 0.0)

        items_out.append({
            "ingredient": it.get("ingredient"),
            "quantity": it.get("quantity"),
            "unit": it.get("unit"),
            "macros": macros,
            "usda_match_score": nut.get("score", None)
        })

    # Round totals to 2 decimals
    totals = {k: round(v, 2) for k, v in totals.items()}

    return {
        "input": text,
        "items": items_out,
        "totals": totals
    }
