import re
from word2number import w2n

# Minimal unit normalization map
UNIT_ALIASES = {
    "grams": "g", "gram": "g", "g": "g",
    "kg": "kg", "kilogram": "kg",
    "ml": "ml", "l": "l", "litre": "l",
    "cup": "cup", "cups": "cup",
    "slice": "slice", "slices": "slice",
    "piece": "piece", "pieces": "piece",
    "tbsp": "tbsp", "tsp": "tsp", "glass": "glass",
    "serving": "serving", "servings": "serving",
    "oz": "oz", "ounce": "oz", "ounces": "oz"
}

# Expand this keyword list or generate dynamically from USDA food names
COMMON_FOODS = ["rice","chicken","apple","banana","bread","milk","egg","pasta","salad","yogurt","fish","potato","dal","paneer"]

# regex extracts patterns like "two slices of bread", "200 g rice", "1 cup milk"
QUANTITY_UNIT_RE = re.compile(
    r"(?P<qty>(?:\d+\/\d+|\d+\.\d+|\d+|\w+))\s*(?P<unit>[a-zA-Z]+)?\s*(?:of)?\s*(?P<ingredient>[a-zA-Z \-]+)",
    flags=re.I
)

def parse_clause(clause: str):
    clause = clause.strip()
    m = QUANTITY_UNIT_RE.search(clause)
    if not m:
        # fallback: ingredient only
        return {"ingredient": clause, "quantity": 1.0, "unit": "serving"}
    qty = m.group("qty")
    unit = m.group("unit") or "serving"
    ingredient = m.group("ingredient").strip()
    # convert words to numbers where possible
    try:
        if qty.isalpha():
            qty_val = float(w2n.word_to_num(qty))
        elif "/" in qty:
            # fraction 1/2
            nums = qty.split("/")
            qty_val = float(nums[0]) / float(nums[1])
        else:
            qty_val = float(qty)
    except Exception:
        qty_val = 1.0
    unit_norm = UNIT_ALIASES.get(unit.lower(), unit.lower())
    return {"ingredient": ingredient.lower(), "quantity": qty_val, "unit": unit_norm}

def rule_based_extraction(text: str):
    # Split sentences/clauses by comma / ' and '
    parts = re.split(r",|\band\b", text)
    items = []
    for p in parts:
        p = p.strip()
        if not p:
            continue
        parsed = parse_clause(p)
        # basic filter: check ingredient token contains a known food word or assume it's a food
        # You can improve: fuzzy match with USDA names before accepting
        items.append(parsed)
    return items