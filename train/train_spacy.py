import spacy
from spacy.training.example import Example
import random
import json
import pathlib

# Paths
DATA_PATH = pathlib.Path("data/food_samples.json")
OUTPUT_DIR = pathlib.Path("models/food_ner")

def load_data():
    with open(DATA_PATH, "r") as f:
        raw_data = json.load(f)
    return raw_data

def main():
    # Load blank English model
    nlp = spacy.blank("en")
    ner = nlp.add_pipe("ner")

    # Add "FOOD" label
    ner.add_label("FOOD")

    # Load training data
    TRAIN_DATA = load_data()

    # Training loop
    optimizer = nlp.begin_training()
    for itn in range(20):  # 20 iterations (small dataset, keep low)
        random.shuffle(TRAIN_DATA)
        losses = {}
        for text, annotations in TRAIN_DATA:
            doc = nlp.make_doc(text)
            example = Example.from_dict(doc, annotations)
            nlp.update([example], drop=0.2, losses=losses, sgd=optimizer)
        print(f"Iteration {itn} Losses {losses}")

    # Save model
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    nlp.to_disk(OUTPUT_DIR)
    print(f"Model saved to {OUTPUT_DIR}")

if __name__ == "__main__":
    main()
