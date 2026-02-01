import json
import os
from collections import Counter

def generate_glossary(input_path, output_path, limit_recipes=100000, min_freq=5):
    print(f"Loading recipes from {input_path}...")
    if not os.path.exists(input_path):
        print("Input file not found.")
        return

    with open(input_path, 'r') as f:
        recipes = json.load(f)

    print(f"Counting ingredients in top {limit_recipes} recipes...")
    counts = Counter()
    for r in recipes[:limit_recipes]:
        counts.update(r.get('ingredients', []))

    # Basic normalization and filtering
    normalized = {}
    for ing, count in counts.items():
        if count < min_freq:
            continue
        
        name = ing.lower().strip()
        if not name:
            continue
            
        # Very basic plural normalization: if "eggs" exists and "egg" exists, use "egg"
        # Since we are iterating, we can do a second pass
        normalized[name] = count

    # Second pass for plural merging
    final_counts = Counter()
    sorted_names = sorted(normalized.keys(), key=len) # Process shorter names first
    
    seen_singulars = {}
    
    for name in sorted_names:
        count = normalized[name]
        # Heuristic: if name ends in 's' and singular exists, merge
        if name.endswith('s') and name[:-1] in seen_singulars:
            final_counts[name[:-1]] += count
        else:
            final_counts[name] = count
            seen_singulars[name] = True

    # Group by first letter
    glossary = {}
    for name, count in sorted(final_counts.items()):
        first_char = name[0].upper()
        if not first_char.isalpha():
            first_char = "#"
        
        if first_char not in glossary:
            glossary[first_char] = []
        
        glossary[first_char].append({
            "name": name,
            "count": count
        })

    print(f"Saving glossary with {len(final_counts)} items to {output_path}...")
    with open(output_path, 'w') as f:
        json.dump(glossary, f, indent=2)

if __name__ == "__main__":
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    INPUT = os.path.join(BASE_DIR, "../../recipe1M_layers/processed_layer1.json")
    OUTPUT = os.path.join(BASE_DIR, "static/glossary.json")
    generate_glossary(INPUT, OUTPUT)
