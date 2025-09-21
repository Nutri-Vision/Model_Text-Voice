#!/usr/bin/env python3
"""
Quick test for the fixed NLP extraction
"""

import sys
import re
from pathlib import Path

# Simulate the fixed rules (copy the key functions here for testing)
from word2number import w2n

UNIT_ALIASES = {
    "grams": "g", "gram": "g", "g": "g",
    "kg": "kg", "kilogram": "kg", "kilograms": "kg",
    "ml": "ml", "l": "l", "litre": "l", "liter": "l",
    "cup": "cup", "cups": "cup",
    "slice": "slice", "slices": "slice",
    "piece": "piece", "pieces": "piece",
    "tbsp": "tbsp", "tablespoon": "tbsp", "tablespoons": "tbsp",
    "tsp": "tsp", "teaspoon": "tsp", "teaspoons": "tsp",
    "glass": "glass", "glasses": "glass",
    "serving": "serving", "servings": "serving",
    "oz": "oz", "ounce": "oz", "ounces": "oz",
    "lb": "lb", "pound": "lb", "pounds": "lb",
    "bowl": "bowl", "bowls": "bowl",
    "plate": "plate", "plates": "plate",
    "portion": "serving", "portions": "serving"
}

COMMON_FOODS = [
    "rice", "bread", "pasta", "noodles", "quinoa", "oats", "wheat", "barley",
    "potato", "sweet potato", "corn", "tortilla", "bagel", "cereal",
    "chicken", "beef", "pork", "fish", "salmon", "tuna", "egg", "eggs",
    "tofu", "beans", "lentils", "chickpeas", "paneer", "cheese",
    "apple", "banana", "orange", "grapes", "strawberry", "blueberry",
    "mango", "pineapple", "watermelon", "peach", "pear",
    "broccoli", "spinach", "carrot", "tomato", "onion", "garlic",
    "lettuce", "cucumber", "bell pepper", "mushroom",
    "milk", "yogurt", "butter", "cream",
    "oil", "salt", "sugar", "honey", "nuts", "almonds", "peanuts"
]

# Improved regex patterns
PATTERNS = [
    # Pattern 1: "two slices of bread", "200 g of rice", "1 cup rice"
    re.compile(
        r"(?P<qty>(?:\d+\.?\d*|half|quarter|one|two|three|four|five|six|seven|eight|nine|ten|a|an))\s+(?P<unit>slice|slices|cup|cups|g|gram|grams|kg|ml|l|tbsp|tsp|glass|glasses|bowl|bowls|piece|pieces|serving|servings|oz|ounce|ounces|lb|pound|pounds)s?\s+(?:of\s+)?(?P<ingredient>(?:[a-zA-Z]+(?:\s+[a-zA-Z]+)*))(?=\s*(?:and|,|with|$))",
        flags=re.I
    ),
    
    # Pattern 2: "chicken breast 200g", "rice 2 cups"  
    re.compile(
        r"(?P<ingredient>(?:[a-zA-Z]+(?:\s+[a-zA-Z]+)*?))\s+(?P<qty>(?:\d+\.?\d*|half|quarter|one|two|three|four|five|six|seven|eight|nine|ten|a|an))\s*(?P<unit>slice|slices|cup|cups|g|gram|grams|kg|ml|l|tbsp|tsp|glass|glasses|bowl|bowls|piece|pieces|serving|servings|oz|ounce|ounces|lb|pound|pounds)?s?(?=\s*(?:and|,|with|$))",
        flags=re.I
    ),
    
    # Pattern 3: Just quantity + ingredient: "2 eggs", "3 apples"
    re.compile(
        r"(?P<qty>(?:\d+\.?\d*|half|quarter|one|two|three|four|five|six|seven|eight|nine|ten|a|an))\s+(?P<ingredient>(?:[a-zA-Z]+(?:\s+[a-zA-Z]+)*))(?=\s*(?:and|,|with|$))",
        flags=re.I
    ),
    
    # Pattern 4: Just ingredient
    re.compile(
        r"(?P<ingredient>(?:[a-zA-Z]+(?:\s+[a-zA-Z]+)*))(?=\s*(?:and|,|with|$|\.|\n))",
        flags=re.I
    )
]

def parse_number(qty_str):
    if not qty_str:
        return 1.0
    
    qty_str = qty_str.strip().lower()
    
    try:
        return float(qty_str)
    except ValueError:
        pass
    
    if "/" in qty_str:
        try:
            parts = qty_str.split("/")
            return float(parts[0]) / float(parts[1])
        except (ValueError, ZeroDivisionError):
            pass
    
    word_numbers = {
        "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
        "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
        "half": 0.5, "quarter": 0.25, "a": 1, "an": 1
    }
    
    if qty_str in word_numbers:
        return float(word_numbers[qty_str])
    
    try:
        return float(w2n.word_to_num(qty_str))
    except (ValueError, AttributeError):
        pass
    
    return 1.0

def clean_ingredient(ingredient):
    if not ingredient:
        return ""
    
    ingredient = re.sub(r'\s+', ' ', ingredient.strip().lower())
    
    prefixes = ["some", "a", "an", "the", "fresh", "organic", "raw", "cooked"]
    suffixes = ["meat", "fish", "vegetable", "fruit"]
    
    words = ingredient.split()
    
    while words and words[0] in prefixes:
        words.pop(0)
    
    while len(words) > 1 and words[-1] in suffixes:
        words.pop()
    
    return " ".join(words).strip()

def is_likely_food(ingredient):
    if not ingredient:
        return False
    
    ingredient_lower = ingredient.lower()
    
    for food in COMMON_FOODS:
        if food in ingredient_lower or ingredient_lower in food:
            return True
    
    food_indicators = [
        "chicken", "beef", "pork", "fish", "meat", "bread", "rice", "pasta",
        "apple", "banana", "fruit", "vegetable", "milk", "cheese", "egg",
        "potato", "tomato", "onion", "garlic", "oil", "butter", "yogurt"
    ]
    
    for indicator in food_indicators:
        if indicator in ingredient_lower:
            return True
    
    if 2 <= len(ingredient_lower) <= 50 and re.match(r'^[a-z\s\-]+$', ingredient_lower):
        return True
    
    return False

def parse_clause(clause):
    clause = clause.strip()
    if not clause:
        return None
    
    # Clean up the clause
    clause = re.sub(r'^(i\s+had|i\s+ate|we\s+ordered|lunch\s+was|breakfast\s+was|dinner\s+was|for\s+breakfast|for\s+lunch|for\s+dinner)\s+', '', clause, flags=re.I)
    clause = re.sub(r'^(a|an|some|the)\s+', '', clause, flags=re.I)
    
    best_match = None
    best_score = 0
    
    for i, pattern in enumerate(PATTERNS):
        match = pattern.search(clause)
        if match:
            groups = match.groupdict()
            
            ingredient = clean_ingredient(groups.get("ingredient", ""))
            qty_str = groups.get("qty", "1")
            unit = groups.get("unit", "serving")
            
            if not ingredient or len(ingredient) < 2:
                continue
            
            score = 0
            if is_likely_food(ingredient):
                score += 3
            if qty_str and qty_str != "1":
                score += 2
            if unit and unit != "serving":
                score += 1
            
            score += (4 - i) * 0.1
            
            if score > best_score:
                best_score = score
                quantity = parse_number(qty_str)
                unit_norm = UNIT_ALIASES.get(unit.lower() if unit else "serving", 
                                           unit.lower() if unit else "serving")
                
                best_match = {
                    "ingredient": ingredient,
                    "quantity": quantity,
                    "unit": unit_norm
                }
    
    return best_match

def rule_based_extraction(text):
    if not text:
        return []
    
    text = re.sub(r'\s+', ' ', text.strip())
    
    # Split more carefully
    separators = r'(?:,\s*|\s+and\s+|\s+with\s+|;\s*)'
    parts = re.split(separators, text, flags=re.I)
    
    items = []
    seen_ingredients = set()
    
    for part in parts:
        part = part.strip()
        if not part or len(part) < 2:
            continue
        
        # Skip non-food phrases
        skip_phrases = ['for breakfast', 'for lunch', 'for dinner', 'i had', 'i ate', 'we ordered', 'lunch was', 'breakfast was']
        if any(phrase in part.lower() for phrase in skip_phrases):
            continue
        
        parsed = parse_clause(part)
        if parsed and parsed["ingredient"] not in seen_ingredients:
            items.append(parsed)
            seen_ingredients.add(parsed["ingredient"])
    
    if not items:
        # Try manual patterns
        and_match = re.search(r'(.+?)\s+and\s+(.+)', text, re.I)
        if and_match:
            part1, part2 = and_match.groups()
            for part in [part1.strip(), part2.strip()]:
                parsed = parse_clause(part)
                if parsed and parsed["ingredient"] not in seen_ingredients:
                    items.append(parsed)
                    seen_ingredients.add(parsed["ingredient"])
        
        if not items:
            parsed = parse_clause(text)
            if parsed:
                items.append(parsed)
    
    return items

# Test the fixed extraction
test_cases = [
    "I had two slices of whole wheat bread and one apple",
    "Chicken breast 200g", 
    "I ate one bowl of rice and a glass of milk",
    "We ordered 200 g chicken breast",
    "A banana and some yogurt",
    "2 cups of cooked rice with 1 tbsp oil",
    "Half cup oats with milk",
    "3 eggs and 2 slices toast"
]

print("TESTING FIXED NLP EXTRACTION")
print("="*50)

for i, test_text in enumerate(test_cases, 1):
    print(f"\nTest {i}: '{test_text}'")
    result = rule_based_extraction(test_text)
    
    if result:
        for item in result:
            print(f"  ✓ {item['quantity']} {item['unit']} of {item['ingredient']}")
    else:
        print("  ✗ No items extracted")