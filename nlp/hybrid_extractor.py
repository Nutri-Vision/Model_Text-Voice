from .rules import rule_based_extraction
from .spacy_model import load_trained_model

nlp_model = load_trained_model()  # loads or returns None

def spacy_extract(nlp, text: str):
    doc = nlp(text)
    results = []
    # expect label "FOOD" used during training
    for ent in doc.ents:
        if ent.label_ == "FOOD":
            results.append(ent.text.lower())
    return results

def hybrid_extract(text: str):
    # always run rule extractor (gives quantities/units)
    rule_items = rule_based_extraction(text)  # list of dicts {ingredient,quantity,unit}

    # if model available, use it to enhance ingredient extraction (names only)
    spacy_foods = []
    if nlp_model:
        try:
            spacy_foods = spacy_extract(nlp_model, text)
        except Exception as e:
            print("spaCy model error:", e)
            spacy_foods = []

    # merge: if spaCy recognized a token, replace the rule-based ingredient name with spaCy canonical
    final_items = []
    for item in rule_items:
        matched = False
        for s in spacy_foods:
            if s in item["ingredient"] or item["ingredient"] in s:
                final_items.append({"ingredient": s, "quantity": item["quantity"], "unit": item["unit"]})
                matched = True
                break
        if not matched:
            final_items.append(item)
    # dedupe by ingredient name
    seen = {}
    for it in final_items:
        key = it["ingredient"]
        if key in seen:
            # sum quantities (assuming same unit; in production convert to grams)
            seen[key]["quantity"] += it["quantity"]
        else:
            seen[key] = it
    return list(seen.values())
