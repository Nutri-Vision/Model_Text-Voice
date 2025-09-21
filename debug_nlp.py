# debug_nlp_test.py
from nlp.rules import parse_clause, rule_based_extraction
from nlp.hybrid_extractor import hybrid_extract
import json

tests = [
    "I had two slices of whole wheat bread and one apple",
    "Chicken",
    "I ate one bowl of rice and a glass of milk",
    "We ordered 200 g chicken breast"
]

print("\n--- Clause parsing tests ---")
for t in tests:
    parts = __import__('re').split(r",|\band\b", t)
    print(f"\nInput: {t}")
    for p in parts:
        p = p.strip()
        if not p:
            continue
        print(" clause:", p, " -> ", parse_clause(p))

print("\n--- Hybrid extractor tests ---")
for t in tests:
    print(f"\nInput: {t} -> {hybrid_extract(t)}")
