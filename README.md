# Food Entity NLP Project

This project is a Python-based NLP pipeline for extracting food entities from text using a hybrid approach (rule-based + spaCy NER). It includes training scripts, a custom spaCy model, and utilities for preprocessing and extraction.

## Structure

- `app.py` — Main application entry point.
- `nlp/` — NLP extraction modules:
  - `hybrid_extractor.py` — Combines rule-based and spaCy-based extraction.
  - `rules.py` — Rule-based ingredient/quantity/unit extraction.
  - `spacy_model.py` — Loads trained spaCy model.
  - `preprocessing.py` — Text preprocessing utilities.
- `train/` — Model training scripts:
  - `train_spacy.py` — Trains spaCy NER model on food entities.
  - `prepare_data.py` — Prepares training data.
- `data/food_samples.json` — Annotated training samples.
- `models/food_ner/` — Trained spaCy model and config.
- `usda/` — USDA FoodData API integration.
- `.env` — Environment variables (not tracked by git).
- `requirements.txt` — Python dependencies.

## Setup

1. **Install dependencies:**
   ```sh
   pip install -r requirements.txt
   ```

2. **Train the spaCy model:**
   ```sh
   python train/train_spacy.py
   ```

3. **Run extraction:**
   Use `nlp/hybrid_extractor.py` functions to extract food entities from text.

## Usage Example

```python
from nlp.hybrid_extractor import hybrid_extract

text = "I ate rice and chicken curry for dinner"
entities = hybrid_extract(text)
print(entities)
```

## Data Format

Training data in `data/food_samples.json`:
```json
[
  ["I ate rice and chicken curry for dinner", {"entities": [[6, 10, "FOOD"], [15, 22, "FOOD"]]}],
  ...
]
```

## Notes

- The `.gitignore` excludes model artifacts, cache, and environment files.
- For API integration, see [`usda.fooddata_api`](usda/fooddata_api.py).
- For custom rules, see [`nlp.rules`](nlp/rules.py).

## License

MIT License.